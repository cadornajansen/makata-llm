"""Training-only runtime. Imports are lazy so offline input tests need no GPU stack."""
from __future__ import annotations

import importlib.metadata
import json
import math
from pathlib import Path
import platform
import shutil
import time
from typing import Any

from qlora_smoke import (ResponseCollator, encode_example, file_hash, load_inputs, load_plan,
                         source_hashes, utc_now, write_json, json_bytes)


def environment() -> dict[str, str]:
    names = ("torch", "transformers", "peft", "trl", "accelerate", "bitsandbytes",
             "datasets", "tokenizers", "huggingface-hub", "safetensors", "numpy", "psutil")
    return {"python": platform.python_version(), **{name: importlib.metadata.version(name) for name in names}}


def hardware_check(plan: dict[str, Any], location: Path) -> dict[str, Any]:
    import torch
    import psutil
    versions = environment()
    for name, expected in plan["environment"].items():
        if versions[name] != expected:
            raise RuntimeError(f"{name} must be {expected}; found {versions[name]}")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("Exactly one CUDA T4 is required; CPU fallback is forbidden.")
    device = torch.cuda.get_device_properties(0)
    if "T4" not in device.name or device.total_memory < 14 * 1024**3:
        raise RuntimeError(f"Expected a T4 with >=14 GiB physical VRAM; found {device.name}.")
    free, _ = torch.cuda.mem_get_info()
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(location)
    if free < 12 * 1024**3 or memory.available < 6 * 1024**3 or disk.free < 20 * 1024**3:
        raise RuntimeError("Need >=12 GiB free VRAM, 6 GiB available host RAM and 20 GiB free disk before loading weights.")
    probe = torch.ones((16, 16), device="cuda", dtype=torch.float16)
    if not bool(torch.isfinite(probe @ probe).all()):
        raise RuntimeError("CUDA FP16 matrix multiplication failed.")
    torch.cuda.synchronize()
    return {"gpu": device.name, "gpu_count": 1, "vram_bytes": device.total_memory,
            "free_vram_bytes": free, "host_available_bytes": memory.available,
            "host_total_bytes": memory.total, "disk_free_bytes": disk.free,
            "cuda": torch.version.cuda, "capability": list(torch.cuda.get_device_capability()),
            "environment": versions}


def preflight(output: Path, plan_path: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    result = hardware_check(load_plan(plan_path), output)
    write_json(output / "preflight.json", result)
    return result


def get_tokenizer(plan: dict[str, Any]) -> Any:
    from transformers import AutoTokenizer
    pin = plan["model"]
    tokenizer = AutoTokenizer.from_pretrained(pin["tokenizer"], revision=pin["tokenizer_revision"], trust_remote_code=False)
    if tokenizer.eos_token_id != pin["eos_token_id"]:
        raise ValueError("Pinned tokenizer EOS mismatch.")
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def tokenizer_check(inputs: Path, output: Path, plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    rows, manifest = load_inputs(inputs, plan)
    if manifest["plan_sha256"] != file_hash(plan_path):
        raise ValueError("Plan hash differs from private inputs.")
    tokenizer = get_tokenizer(plan)
    encoded = [encode_example(row, tokenizer, plan["training"]["max_length"]) for row in rows]
    result = {"status": "passed", "model": plan["model"], "chat_template_used": False,
              "vocabulary_size": len(tokenizer), "eos_token_id": tokenizer.eos_token_id,
              "pad_token_id": tokenizer.pad_token_id, "input_manifest_sha256": file_hash(inputs / "subset-manifest.json"),
              "records": [{"id": row["id"], "tokens": len(item["input_ids"]),
                           "supervised_tokens": sum(n != -100 for n in item["labels"])}
                          for row, item in zip(rows, encoded, strict=True)]}
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "tokenizer-check.json", result)
    return result


def quantized_base(plan: dict[str, Any]) -> Any:
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import prepare_model_for_kbit_training
    quantization = dict(plan["quantization"])
    quantization["bnb_4bit_compute_dtype"] = torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        plan["model"]["repository"], revision=plan["model"]["revision"],
        torch_dtype=torch.float16, quantization_config=BitsAndBytesConfig(**quantization),
        device_map={"": 0}, attn_implementation="eager", trust_remote_code=False,
    )
    if not getattr(model, "is_loaded_in_4bit", False):
        raise RuntimeError("Base model was not loaded in 4-bit mode.")
    model.config.use_cache = False
    # Reapply this on reload too: it fixes the nonquantized layer dtypes.
    return prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                          gradient_checkpointing_kwargs={"use_reentrant": False})


def tensor_digest(tensors: dict[str, Any]) -> dict[str, str]:
    import hashlib
    return {name: hashlib.sha256(value.detach().cpu().float().contiguous().numpy().tobytes()).hexdigest()
            for name, value in sorted(tensors.items())}


def adapter_state(model: Any) -> dict[str, Any]:
    from peft import get_peft_model_state_dict
    return {k: v.detach().cpu().contiguous().clone() for k, v in get_peft_model_state_dict(model).items()}


def checked_train(model: Any, tokenizer: Any, encoded: list[dict[str, Any]], output: Path,
                  plan: dict[str, Any], gpu: bool) -> dict[str, Any]:
    import torch
    from datasets import Dataset
    from transformers import TrainerCallback
    from trl import SFTConfig, SFTTrainer

    settings = plan["training"]
    parameters = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    if not parameters or any("lora_" not in name or parameter.dtype != torch.float32 for name, parameter in parameters):
        raise RuntimeError("Only FP32 LoRA parameters may be trainable.")
    optimizer = torch.optim.AdamW([p for _, p in parameters], lr=settings["learning_rate"], weight_decay=0.0)
    stats: dict[str, Any] = {"updates": 0, "microbatch_losses": [], "started": time.perf_counter()}

    def before_step(opt: Any, _args: Any, _kwargs: Any) -> None:
        gradients = [p.grad for _, p in parameters if p.grad is not None]
        if not gradients or any(not bool(torch.isfinite(grad).all()) for grad in gradients):
            raise FloatingPointError("Missing or nonfinite gradients.")
        stats["grad_norm"] = float(torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g.float()) for g in gradients])))
        stats["lr"] = float(opt.param_groups[0]["lr"])

    def after_step(_opt: Any, _args: Any, _kwargs: Any) -> None:
        stats["updates"] += 1
        losses = stats["microbatch_losses"]
        if len(losses) != settings["gradient_accumulation_steps"]:
            raise RuntimeError("Unexpected number of microbatches per optimizer update.")
        if gpu:
            torch.cuda.synchronize()
        row = {"step": stats["updates"], "loss": sum(losses) / len(losses),
               "learning_rate": stats["lr"], "gradient_norm_after_clipping": stats["grad_norm"],
               "gradients_finite": True, "microbatches": len(losses),
               "elapsed_seconds": time.perf_counter() - stats["started"],
               "peak_allocated_bytes": torch.cuda.max_memory_allocated() if gpu else None,
               "peak_reserved_bytes": torch.cuda.max_memory_reserved() if gpu else None}
        with (output / "training-log.jsonl").open("ab") as stream:
            stream.write(json_bytes(row))
        print(json.dumps(row), flush=True)
        losses.clear()

    hooks = [optimizer.register_step_pre_hook(before_step), optimizer.register_step_post_hook(after_step)]

    class CheckedTrainer(SFTTrainer):
        def compute_loss(self, model: Any, inputs: Any, return_outputs: bool = False,
                         num_items_in_batch: Any = None) -> Any:
            result = super().compute_loss(model, inputs, return_outputs=return_outputs, num_items_in_batch=num_items_in_batch)
            loss = result[0] if return_outputs else result
            if not bool(torch.isfinite(loss).all()):
                raise FloatingPointError("Nonfinite forward loss.")
            if model.training:
                stats["microbatch_losses"].append(float(loss.detach()))
            return result

    class UpdateGuard(TrainerCallback):
        def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
            if state.global_step != stats["updates"]:
                raise RuntimeError("AMP skipped an optimizer update; run is incomplete.")

    config = SFTConfig(
        output_dir=str(output / "trainer-temporary"), max_steps=settings["max_steps"],
        per_device_train_batch_size=settings["per_device_train_batch_size"],
        gradient_accumulation_steps=settings["gradient_accumulation_steps"],
        learning_rate=settings["learning_rate"], warmup_steps=settings["warmup_steps"],
        lr_scheduler_type=settings["lr_scheduler_type"], max_grad_norm=settings["max_grad_norm"],
        seed=settings["seed"], data_seed=settings["seed"], weight_decay=0.0,
        max_length=settings["max_length"], packing=False, padding_free=False,
        dataset_kwargs={"skip_prepare_dataset": True}, remove_unused_columns=False, label_names=["labels"],
        fp16=gpu, bf16=False, tf32=False, use_cpu=not gpu,
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        save_strategy="no", eval_strategy="no", logging_strategy="no", report_to=[],
        push_to_hub=False, dataloader_num_workers=0, dataloader_pin_memory=False,
        optim="adamw_torch", disable_tqdm=True,
    )
    trainer = CheckedTrainer(model=model, args=config, train_dataset=Dataset.from_list(encoded),
                             processing_class=tokenizer, data_collator=ResponseCollator(tokenizer.pad_token_id),
                             optimizers=(optimizer, None), callbacks=[UpdateGuard()])
    if gpu:
        # Set before Accelerator wraps the optimizer. The default 65536 scale
        # overflowed on update 20 in the retained first T4 attempt.
        trainer.accelerator.scaler = torch.amp.GradScaler("cuda", **plan["loss_scaling"])
    # The model loss is averaged over response tokens per microbatch; Trainer scales accumulation.
    trainer.model_accepts_loss_kwargs = False
    try:
        trainer.train()
        if stats["updates"] != settings["max_steps"] or stats["microbatch_losses"]:
            raise RuntimeError("Optimizer-update count mismatch.")
        for state in optimizer.state.values():
            for key in ("exp_avg", "exp_avg_sq"):
                if state[key].dtype != torch.float32 or not bool(torch.isfinite(state[key]).all()):
                    raise FloatingPointError("AdamW state must remain finite FP32.")
        if any(not bool(torch.isfinite(p).all()) for _, p in parameters):
            raise FloatingPointError("Adapter weights became nonfinite.")
        return {"optimizer_updates": stats["updates"], "training_seconds": time.perf_counter() - stats["started"],
                "trainable_parameters": sum(p.numel() for _, p in parameters), "optimizer_state_dtype": "float32",
                "final_loss_scale": trainer.accelerator.scaler.get_scale() if gpu else None}
    finally:
        for hook in hooks:
            hook.remove()


def train(inputs: Path, output: Path, plan_path: Path) -> dict[str, Any]:
    import torch
    from transformers import set_seed
    from peft import LoraConfig, get_peft_model
    from safetensors.torch import save_file
    if output.exists():
        raise FileExistsError("Use a new run directory; incomplete runs are never resumed silently.")
    output.mkdir(parents=True)
    manifest: dict[str, Any] = {"status": "incomplete", "started_at": utc_now(), "training_started": False}
    write_json(output / "run-manifest.json", manifest)
    try:
        plan = load_plan(plan_path)
        hardware = hardware_check(plan, output)
        rows, input_manifest = load_inputs(inputs, plan)
        if input_manifest["plan_sha256"] != file_hash(plan_path):
            raise ValueError("Input and plan hashes differ.")
        manifest.update({"plan_sha256": file_hash(plan_path), "configuration": plan,
                         "source_sha256": source_hashes(), "input_manifest_sha256": file_hash(inputs / "subset-manifest.json"),
                         "hardware": hardware, "environment": environment(), "benchmark_accessed": False})
        manifest["installed_packages"] = dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions()))
        write_json(output / "run-manifest.json", manifest)
        tokenizer_check(inputs, output, plan_path)
        tokenizer = get_tokenizer(plan)
        encoded = [encode_example(row, tokenizer, plan["training"]["max_length"]) for row in rows]
        set_seed(plan["training"]["seed"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()
        model = get_peft_model(quantized_base(plan), LoraConfig(**plan["lora"]))
        for parameter in model.parameters():
            if parameter.requires_grad:
                parameter.data = parameter.data.float()
        initial = tensor_digest(adapter_state(model))
        manifest.update({"training_started": True, "training_started_at": utc_now()})
        write_json(output / "run-manifest.json", manifest)
        metrics = checked_train(model, tokenizer, encoded, output, plan, gpu=True)
        state = adapter_state(model)
        final_hashes = tensor_digest(state)
        if initial == final_hashes:
            raise RuntimeError("No adapter weights changed.")
        model.save_pretrained(output / "adapter", safe_serialization=True, save_embedding_layers=False)
        model.eval()
        batch = ResponseCollator(tokenizer.pad_token_id)([encoded[0]])
        # Accelerate may retain its autocast forward wrapper after training;
        # use the same explicit compute context in the fresh reload process.
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            logits = model(input_ids=batch["input_ids"].cuda(), attention_mask=batch["attention_mask"].cuda()).logits[0, -1].float().cpu()
        if not bool(torch.isfinite(logits).all()):
            raise FloatingPointError("Nonfinite pre-save probe logits.")
        save_file({"input_ids": batch["input_ids"], "attention_mask": batch["attention_mask"], "logits": logits},
                  str(output / "probe-reference.safetensors"))
        write_json(output / "adapter-reference.json", {"tensor_sha256": final_hashes, "initial_tensor_sha256": initial})
        metrics.update({"peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                        "peak_reserved_bytes": torch.cuda.max_memory_reserved()})
        manifest.update({"status": "pending_reload", "training_finished_at": utc_now(), "metrics": metrics,
                         "train_process_id": __import__("os").getpid()})
        manifest["artifacts"] = {p.relative_to(output).as_posix(): file_hash(p) for p in output.rglob("*")
                                 if p.is_file() and p.name != "run-manifest.json" and "trainer-temporary" not in p.parts}
        write_json(output / "run-manifest.json", manifest)
        return {"status": "pending_reload", **metrics}
    except BaseException as error:
        manifest.update({"status": "incomplete", "failed_at": utc_now(), "error_type": type(error).__name__, "error": str(error)})
        write_json(output / "run-manifest.json", manifest)
        raise


def reload_adapter(output: Path, plan_path: Path) -> dict[str, Any]:
    import os
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    manifest_path = output / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        plan = load_plan(plan_path)
        if manifest["status"] != "pending_reload" or manifest["train_process_id"] == os.getpid():
            raise RuntimeError("Reload requires a fresh process after successful training.")
        if manifest["plan_sha256"] != file_hash(plan_path) or manifest["source_sha256"] != source_hashes():
            raise ValueError("Plan/source changed between training and reload.")
        for name, expected in manifest["artifacts"].items():
            if not (output / name).resolve().is_relative_to(output.resolve()) or file_hash(output / name) != expected:
                raise ValueError("Saved artifact was changed before reload.")
        hardware_check(plan, output)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        started = time.perf_counter()
        model = PeftModel.from_pretrained(quantized_base(plan), output / "adapter", is_trainable=False)
        expected = json.loads((output / "adapter-reference.json").read_text())["tensor_sha256"]
        if tensor_digest(adapter_state(model)) != expected:
            raise RuntimeError("Reloaded adapter tensors differ from saved tensors.")
        probe = load_file(str(output / "probe-reference.safetensors"))
        model.eval()
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            actual = model(input_ids=probe["input_ids"].cuda(), attention_mask=probe["attention_mask"].cuda()).logits[0, -1].float().cpu()
        reference = probe["logits"]
        torch.testing.assert_close(actual, reference, **plan["reload_tolerance"])
        if not bool(torch.isfinite(actual).all()) or actual.argmax() != reference.argmax():
            raise RuntimeError("Reload probe is nonfinite or changes the top token.")
        torch.cuda.synchronize()
        result = {"status": "passed", "tensor_equality": True, "probe_finite": True,
                  "probe_argmax_equal": True, "maximum_absolute_logit_error": float((actual - reference).abs().max()),
                  "tolerances": plan["reload_tolerance"], "reload_seconds": time.perf_counter() - started,
                  "fresh_process": True}
        write_json(output / "reload-verification.json", result)
        manifest["artifacts"]["reload-verification.json"] = file_hash(output / "reload-verification.json")
        manifest.update({"status": "complete", "finished_at": utc_now()})
        write_json(manifest_path, manifest)
        return result
    except BaseException as error:
        manifest.update({"status": "incomplete", "failed_at": utc_now(), "error_type": type(error).__name__, "error": str(error)})
        write_json(manifest_path, manifest)
        raise


def integration_check(output: Path, plan_path: Path) -> dict[str, Any]:
    """Small random CPU model exercises actual TRL/PEFT APIs, not NF4 kernels."""
    import copy
    import torch
    from transformers import Qwen3Config, Qwen3ForCausalLM, PreTrainedTokenizerFast, set_seed
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from peft import LoraConfig, get_peft_model, PeftModel
    if output.exists():
        raise FileExistsError("Use a new integration output directory.")
    output.mkdir(parents=True)
    torch.set_num_threads(2)
    plan = copy.deepcopy(load_plan(plan_path))
    plan["training"].update(max_steps=2, gradient_accumulation_steps=2)
    set_seed(1234)
    config = Qwen3Config(vocab_size=32, hidden_size=32, intermediate_size=64, num_hidden_layers=1,
                        num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=128,
                        eos_token_id=1, pad_token_id=1, use_cache=False)
    base = Qwen3ForCausalLM(config)
    initial_base = {key: value.clone() for key, value in base.state_dict().items()}
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=Tokenizer(WordLevel({"[UNK]": 0, "[EOS]": 1}, unk_token="[UNK]")),
                                       unk_token="[UNK]", eos_token="[EOS]", pad_token="[EOS]")
    model = get_peft_model(base, LoraConfig(**plan["lora"]))
    encoded = [{"input_ids": [2, 3, 4, 5, 1], "attention_mask": [1] * 5, "labels": [-100, -100, 4, 5, 1]},
               {"input_ids": [6, 7, 8, 1], "attention_mask": [1] * 4, "labels": [-100, -100, 8, 1]}]
    batch = ResponseCollator(1)(encoded)
    model.eval()
    with torch.no_grad():
        prediction = model(**batch)
    manual_loss = torch.nn.functional.cross_entropy(prediction.logits[:, :-1].contiguous().view(-1, 32),
                                                     batch["labels"][:, 1:].contiguous().view(-1), ignore_index=-100)
    torch.testing.assert_close(manual_loss, prediction.loss)
    initial_adapter = tensor_digest(adapter_state(model))
    metrics = checked_train(model, tokenizer, encoded, output, plan, gpu=False)
    if initial_adapter == tensor_digest(adapter_state(model)):
        raise AssertionError("Tiny adapter did not learn.")
    model.save_pretrained(output / "tiny-adapter", safe_serialization=True, save_embedding_layers=False)
    new_base = Qwen3ForCausalLM(config)
    new_base.load_state_dict(initial_base)
    reloaded = PeftModel.from_pretrained(new_base, output / "tiny-adapter")
    if tensor_digest(adapter_state(reloaded)) != tensor_digest(adapter_state(model)):
        raise AssertionError("Tiny adapter reload mismatch.")
    model.eval()
    reloaded.eval()
    with torch.no_grad():
        torch.testing.assert_close(model(**batch).logits, reloaded(**batch).logits)
    # PEFT inserts .base_layer in projection names; verify all frozen base values.
    for name, value in model.base_model.model.named_parameters():
        if "lora_" not in name:
            torch.testing.assert_close(value, initial_base[name.replace(".base_layer", "")], rtol=0, atol=0)
    result = {"status": "passed", "environment": environment(), "metrics": metrics,
              "causal_loss_matches": True, "adapter_reload_matches": True, "base_weights_unchanged": True,
              "gpu_quantization_verified": False}
    write_json(output / "integration-check.json", result)
    return result

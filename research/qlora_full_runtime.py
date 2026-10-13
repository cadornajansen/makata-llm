"""Explicit one-epoch AMP executor, reusing the immutable smoke model/masking code."""
from __future__ import annotations

from contextlib import nullcontext
import importlib.metadata
import json
import os
from pathlib import Path
import random
import time
from typing import Any, Callable

from qlora_smoke import ResponseCollator, file_hash, json_bytes, read_jsonl, utc_now, write_json
from qlora_training import (adapter_state, environment, get_tokenizer, hardware_check,
                            quantized_base, tensor_digest)
import qlora_full as full


def preflight(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    report = hardware_check(full.load_plan(), output)
    write_json(output / "preflight.json", report)
    return report


def accumulation_windows(order: list[int], size: int) -> list[list[int]]:
    if size < 1 or not order or len(set(order)) != len(order):
        raise ValueError("Require positive accumulation and unique nonempty epoch order.")
    return [order[start:start + size] for start in range(0, len(order), size)]


def trainable_parameters(model: Any) -> list[Any]:
    import torch
    parameters = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    if not parameters or any("lora_" not in n or p.dtype != torch.float32 for n, p in parameters):
        raise RuntimeError("Only FP32 LoRA parameters may be optimized.")
    return [p for _, p in parameters]


def check_optimizer(optimizer: Any, step: int) -> None:
    import torch
    if not optimizer.state:
        raise RuntimeError("Missing optimizer state.")
    for state in optimizer.state.values():
        if int(state["step"]) != step:
            raise RuntimeError("Actual optimizer tensor step differs.")
        for name in ("exp_avg", "exp_avg_sq"):
            value = state[name]
            if value.dtype != torch.float32 or not bool(torch.isfinite(value).all()):
                raise FloatingPointError("Nonfinite/non-FP32 AdamW moment.")


def save_checkpoint(model: Any, optimizer: Any, scheduler: Any, scaler: Any, output: Path,
                    step: int, order: list[int], consumed: int) -> None:
    import numpy as np
    import torch
    directory = output / f"checkpoint-{step}"
    if directory.exists():
        raise FileExistsError("Never overwrite checkpoints.")
    check_optimizer(optimizer, step)
    state = adapter_state(model)
    if any(not bool(torch.isfinite(t).all()) for t in state.values()):
        raise FloatingPointError("Nonfinite adapter weights.")
    model.save_pretrained(directory, safe_serialization=True, save_embedding_layers=False)
    numpy_rng = np.random.get_state()
    torch.save({"step": step, "epoch": 1, "examples_consumed": consumed, "order": order,
                "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(),
                "scaler": scaler.state_dict(), "python_rng": random.getstate(),
                "numpy_rng": [numpy_rng[0], numpy_rng[1].tolist(), *numpy_rng[2:]],
                "torch_rng": torch.get_rng_state(),
                "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []},
               directory / "training-state.pt")
    write_json(directory / "checkpoint-manifest.json", {
        "step": step, "examples_consumed": consumed, "proposal_sha256": full.PROPOSAL_SHA,
        "tensor_sha256": tensor_digest(state),
        "files": {p.name: file_hash(p) for p in directory.iterdir() if p.is_file()}})


def checked_epoch(model: Any, encoded: list[dict[str, Any]], ids: list[str], output: Path,
                  plan: dict[str, Any], gpu: bool,
                  checkpoint: Callable[..., None] = save_checkpoint) -> dict[str, Any]:
    import torch
    from transformers import get_constant_schedule_with_warmup
    parameters = trainable_parameters(model)
    settings = plan["training"]
    optimizer = torch.optim.AdamW(parameters, lr=settings["learning_rate"], weight_decay=0.0)
    scheduler = get_constant_schedule_with_warmup(optimizer, num_warmup_steps=settings["warmup_steps"])
    scaler = torch.amp.GradScaler("cuda", enabled=gpu, **plan["loss_scaling"])
    order = torch.randperm(len(encoded), generator=torch.Generator().manual_seed(settings["data_seed"])).tolist()
    windows = accumulation_windows(order, settings["gradient_accumulation_steps"])
    if len(windows) != settings["expected_optimizer_updates"] or len(ids) != len(encoded):
        raise ValueError("Frozen one-epoch optimizer accounting differs.")
    actual_updates = 0

    def after_step(_optimizer: Any, _args: Any, _kwargs: Any) -> None:
        nonlocal actual_updates
        actual_updates += 1

    hook = optimizer.register_step_post_hook(after_step)
    collator = ResponseCollator(151643)
    device = "cuda" if gpu else "cpu"
    if gpu:
        torch.cuda.synchronize()
    started = time.perf_counter()
    consumed = 0
    model.train()
    try:
        for step, indices in enumerate(windows, 1):
            optimizer.zero_grad(set_to_none=True)
            losses = []
            for index in indices:
                batch = {k: v.to(device) for k, v in collator([encoded[index]]).items()}
                with torch.autocast("cuda", dtype=torch.float16) if gpu else nullcontext():
                    loss = model(**batch).loss
                if not bool(torch.isfinite(loss)):
                    raise FloatingPointError("Nonfinite forward loss.")
                losses.append(float(loss.detach()))
                # Average per-example gradients, including the final three-example window.
                scaler.scale(loss / len(indices)).backward()
            scaler.unscale_(optimizer)
            gradients = [p.grad for p in parameters if p.grad is not None]
            if len(gradients) != len(parameters) or any(not bool(torch.isfinite(g).all()) for g in gradients):
                raise FloatingPointError("Missing/nonfinite unscaled gradients; no skipped updates allowed.")
            norm = torch.nn.utils.clip_grad_norm_(parameters, settings["max_grad_norm"], error_if_nonfinite=True)
            learning_rate = optimizer.param_groups[0]["lr"]
            scaler.step(optimizer)
            scaler.update()
            if actual_updates != step:
                raise RuntimeError("AMP skipped an optimizer update.")
            scheduler.step()
            consumed += len(indices)
            if gpu:
                torch.cuda.synchronize()
            row = {"step": step, "ids": [ids[i] for i in indices], "loss": sum(losses) / len(losses),
                   "microbatch_losses": losses, "microbatches": len(indices), "examples_consumed": consumed,
                   "learning_rate": learning_rate, "gradient_norm_before_clipping": float(norm),
                   "gradients_finite": True, "loss_scale": scaler.get_scale(),
                   "elapsed_seconds": time.perf_counter() - started,
                   "peak_allocated_bytes": torch.cuda.max_memory_allocated() if gpu else None,
                   "peak_reserved_bytes": torch.cuda.max_memory_reserved() if gpu else None}
            with (output / "training-log.jsonl").open("ab") as stream:
                stream.write(json_bytes(row))
            print(json.dumps(row), flush=True)
            if step in plan["checkpoints"]["save_after_updates"]:
                checkpoint(model, optimizer, scheduler, scaler, output, step, order, consumed)
        check_optimizer(optimizer, actual_updates)
        if consumed != len(encoded) or actual_updates != len(windows):
            raise RuntimeError("Incomplete epoch.")
        if gpu:
            torch.cuda.synchronize()
        logs = read_jsonl(output / "training-log.jsonl")
        return {"optimizer_updates": actual_updates, "examples_consumed": consumed,
                "training_seconds": time.perf_counter() - started,
                "initial_training_loss": logs[0]["loss"], "final_training_loss": logs[-1]["loss"],
                "mean_training_loss": sum(sum(r["microbatch_losses"]) for r in logs) / consumed,
                "trainable_parameters": sum(p.numel() for p in parameters),
                "final_loss_scale": scaler.get_scale()}
    finally:
        hook.remove()


def validation_loss(model: Any, encoded: list[dict[str, Any]]) -> float:
    import torch
    model.eval()
    losses = []
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
        for row in encoded:
            batch = {k: v.cuda() for k, v in ResponseCollator()([row]).items()}
            loss = model(**batch).loss
            if not bool(torch.isfinite(loss)):
                raise FloatingPointError("Nonfinite provisional validation loss.")
            losses.append(float(loss))
    torch.cuda.synchronize()
    return sum(losses) / len(losses)


def train(inputs: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("Use a new run directory; preserve prior attempts.")
    import torch
    from peft import LoraConfig, get_peft_model
    from safetensors.torch import save_file
    from transformers import set_seed
    output.mkdir(parents=True)
    manifest: dict[str, Any] = {"status": "incomplete", "started_at": utc_now(), "training_started": False}
    write_json(output / "run-manifest.json", manifest)
    try:
        plan = full.load_plan()
        rows, _, input_manifest = full.load_inputs(inputs)
        hardware = hardware_check(plan, output)
        manifest.update(configuration=plan, proposal_sha256=full.PROPOSAL_SHA,
                        authorization=json.loads(full.AUTHORIZATION.read_text()), source_sha256=full.source_hashes(),
                        input_manifest_sha256=file_hash(inputs / "input-manifest.json"), input_evidence=input_manifest,
                        hardware=hardware, environment=environment(), benchmark_accessed=False, evaluation_scored=False,
                        classification="exploratory internal experiment; not scientifically validated",
                        installed_packages=dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())))
        write_json(output / "run-manifest.json", manifest)
        encoded, validation, token_report = full.tokenize(inputs)
        write_json(output / "tokenizer-check.json", token_report)
        set_seed(1234)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()
        model = get_peft_model(quantized_base(plan), LoraConfig(**plan["lora"]))
        for parameter in model.parameters():
            if parameter.requires_grad:
                parameter.data = parameter.data.float()
        initial = tensor_digest(adapter_state(model))
        diagnostics_start = time.perf_counter()
        before = validation_loss(model, validation)
        before_seconds = time.perf_counter() - diagnostics_start
        manifest.update(training_started=True, training_started_at=utc_now())
        write_json(output / "run-manifest.json", manifest)
        metrics = checked_epoch(model, encoded, [r["id"] for r in rows], output, plan, True)
        final = tensor_digest(adapter_state(model))
        if initial == final:
            raise RuntimeError("Adapter did not change.")
        diagnostics_start = time.perf_counter()
        after = validation_loss(model, validation)
        write_json(output / "validation-diagnostics.json", {"count": 66, "before": before, "after": after,
                   "before_seconds": before_seconds, "after_seconds": time.perf_counter() - diagnostics_start,
                   "validated": False, "used_for_checkpoint_selection": False,
                   "description": "Provisional Aya response-only mean per-example CE; not independent capability evaluation."})
        model.eval()
        batch = ResponseCollator()([encoded[0]])
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            logits = model(input_ids=batch["input_ids"].cuda(), attention_mask=batch["attention_mask"].cuda()).logits[0, -1].float().cpu()
        if not bool(torch.isfinite(logits).all()):
            raise FloatingPointError("Nonfinite reload probe.")
        save_file({"input_ids": batch["input_ids"], "attention_mask": batch["attention_mask"], "logits": logits}, str(output / "probe-reference.safetensors"))
        write_json(output / "adapter-reference.json", {"tensor_sha256": final, "initial_tensor_sha256": initial})
        metrics.update(peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved())
        manifest.update(status="pending_reload", training_finished_at=utc_now(), metrics=metrics, train_process_id=os.getpid())
        manifest["artifacts"] = {p.relative_to(output).as_posix(): file_hash(p) for p in output.rglob("*")
                                 if p.is_file() and p.name != "run-manifest.json"}
        write_json(output / "run-manifest.json", manifest)
        return {"status": "pending_reload", **metrics}
    except BaseException as error:
        manifest.update(status="incomplete", failed_at=utc_now(), error_type=type(error).__name__, error=str(error))
        write_json(output / "run-manifest.json", manifest)
        raise


def reload(output: Path) -> dict[str, Any]:
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    path = output / "run-manifest.json"
    manifest = json.loads(path.read_text())
    try:
        plan = full.load_plan()
        if manifest["status"] != "pending_reload" or manifest["train_process_id"] == os.getpid():
            raise RuntimeError("Reload requires a fresh process after completed training.")
        if manifest["source_sha256"] != full.source_hashes():
            raise ValueError("Source changed before reload.")
        for name, digest in manifest["artifacts"].items():
            if name not in full.RESULT_FILES:
                raise ValueError("Unauthorized artifact path.")
            full.check_hash(output / name, digest)
        for step in (50, 91):
            full.verify_checkpoint(output / f"checkpoint-{step}", step)
        hardware_check(plan, output)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        started = time.perf_counter()
        model = PeftModel.from_pretrained(quantized_base(plan), output / "checkpoint-91", is_trainable=False)
        if tensor_digest(adapter_state(model)) != json.loads((output / "adapter-reference.json").read_text())["tensor_sha256"]:
            raise RuntimeError("Final adapter tensors changed on reload.")
        probe = load_file(str(output / "probe-reference.safetensors"))
        model.eval()
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            actual = model(input_ids=probe["input_ids"].cuda(), attention_mask=probe["attention_mask"].cuda()).logits[0, -1].float().cpu()
        torch.testing.assert_close(actual, probe["logits"], atol=.001, rtol=.001)
        if not bool(torch.isfinite(actual).all()) or actual.argmax() != probe["logits"].argmax():
            raise RuntimeError("Nonfinite or different probe top token.")
        torch.cuda.synchronize()
        result = {"status": "passed", "tensor_equality": True, "probe_finite": True, "probe_argmax_equal": True,
                  "fresh_process": True, "train_process_id": manifest["train_process_id"], "reload_process_id": os.getpid(),
                  "maximum_absolute_logit_error": float((actual - probe["logits"]).abs().max()),
                  "tolerances": {"atol": .001, "rtol": .001}, "reload_seconds": time.perf_counter() - started}
        write_json(output / "reload-verification.json", result)
        manifest["artifacts"]["reload-verification.json"] = file_hash(output / "reload-verification.json")
        manifest.update(status="complete", finished_at=utc_now())
        write_json(path, manifest)
        return result
    except BaseException as error:
        manifest.update(status="incomplete", failed_at=utc_now(), error_type=type(error).__name__, error=str(error))
        write_json(path, manifest)
        raise


def integration(output: Path) -> dict[str, Any]:
    """Actual installed-library check on a tiny random CPU model, with a 3-item remainder."""
    import copy
    import torch
    from transformers import Qwen3Config, Qwen3ForCausalLM, set_seed
    from peft import LoraConfig, get_peft_model, PeftModel
    if output.exists():
        raise FileExistsError("Preserve previous integration results.")
    output.mkdir(parents=True)
    torch.set_num_threads(2)
    set_seed(1234)
    plan = copy.deepcopy(full.load_plan())
    plan["training"]["expected_optimizer_updates"] = 2
    plan["checkpoints"]["save_after_updates"] = [2]
    config = Qwen3Config(vocab_size=151644, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                        num_attention_heads=1, num_key_value_heads=1, head_dim=16, max_position_embeddings=64,
                        eos_token_id=151643, pad_token_id=151643, use_cache=False)
    base = Qwen3ForCausalLM(config)
    base_state = {k: v.clone() for k, v in base.state_dict().items()}
    model = get_peft_model(base, LoraConfig(**plan["lora"]))
    encoded = [{"input_ids": [2, 3, 4, 151643], "attention_mask": [1] * 4, "labels": [-100, -100, 4, 151643]}] * 7
    result = checked_epoch(model, encoded, [f"synthetic-{n}" for n in range(7)], output, plan, False)
    assert [r["microbatches"] for r in read_jsonl(output / "training-log.jsonl")] == [4, 3]
    state = torch.load(output / "checkpoint-2/training-state.pt", weights_only=True)
    assert state["step"] == 2 and state["examples_consumed"] == 7
    new_base = Qwen3ForCausalLM(config)
    new_base.load_state_dict(base_state)
    reloaded = PeftModel.from_pretrained(new_base, output / "checkpoint-2")
    assert tensor_digest(adapter_state(reloaded)) == tensor_digest(adapter_state(model))
    for name, value in model.base_model.model.named_parameters():
        if "lora_" not in name:
            torch.testing.assert_close(value, base_state[name.replace(".base_layer", "")], atol=0, rtol=0)
    model.eval()
    reloaded.eval()
    batch = ResponseCollator()([encoded[0]])
    with torch.inference_mode():
        torch.testing.assert_close(model(**batch).logits, reloaded(**batch).logits)
    report = {"status": "passed", "metrics": result, "remainder_three": True, "base_unchanged": True,
              "adapter_reload_equal": True, "checkpoint_state_loadable": True, "gpu_verified": False}
    write_json(output / "integration-check.json", report)
    return report

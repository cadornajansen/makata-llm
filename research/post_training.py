"""Evaluate final checkpoint 91 once through the unchanged FilBench evaluator."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any
from unittest.mock import patch
import zipfile

import evaluate
from colab.run import configuration, verify_artifacts
from protocol import ROOT, OFFICIAL_TASK, RunConfig, file_hash, write_json

PLAN = ROOT / "post-training-plan.json"
SOURCE_FILES = ("evaluate.py", "protocol.py", "preflight.py", "baseline-plan.json",
                "requirements.txt", "requirements-colab.txt", "colab/run.py",
                "fixtures/development.json", "post_training.py", "post-training-plan.json",
                "requirements-post-training-colab.txt")
INPUT_FILES = {"adapter/adapter_model.safetensors", "adapter/adapter_config.json", "provenance.json"}
RESULT_FILES = {"profile.json", "attempt.json", "adapter-check.json", "development-check.json",
                "manifest.json", "metrics.json", "samples.jsonl", "qualitative-review.json",
                "archive-manifest.json", "evaluation.log"}


def load_plan() -> dict[str, Any]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["task"] != OFFICIAL_TASK or plan["checkpoint"] != 91 or plan["benchmark_runs"] != 1:
        raise ValueError("Only the frozen final-checkpoint evaluation is authorized.")
    if plan["configuration"] != asdict(configuration(0, "evaluate")):
        raise ValueError("Evaluation settings differ from the frozen baseline.")
    for name, digest in plan["historical_source_sha256"].items():
        if file_hash(ROOT / name) != digest:
            raise ValueError(f"Historical source changed: {name}")
    return plan


def source_hashes() -> dict[str, str]:
    return {name: file_hash(ROOT / name) for name in SOURCE_FILES}


def checked_hash(path: Path, digest: str) -> None:
    if file_hash(path) != digest:
        raise ValueError(f"Checksum differs: {path.name}")


def fresh_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)


def zip_files(root: Path, names: set[str], destination: Path) -> None:
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, (root / name).read_bytes())


def extract(archive: Path, output: Path, allowed: set[str], limit: int) -> None:
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        if len(names) != len(set(names)) or not set(names) <= allowed:
            raise ValueError("Unexpected, duplicate or unsafe archive names.")
        if sum(item.file_size for item in source.infolist()) > limit:
            raise ValueError("Archive exceeds safety limit.")
        fresh_directory(output)
        for name in names:
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(name))


def prepare(training: Path, baseline: Path, output: Path) -> dict[str, Any]:
    from qlora_full import verify as verify_training
    from colab.import_results import verify_session

    plan = load_plan()
    verify_training(training)
    base_report = verify_session(baseline)
    if base_report["status"] != "complete":
        raise ValueError("Original baselines must both be verified.")
    original = baseline / plan["baseline_directory"]
    for name, digest in plan["baseline_sha256"].items():
        checked_hash(original / name, digest)
    checked_hash(training / "run-manifest.json", plan["training_manifest_sha256"])
    checked_hash(training / "local-verification.json", plan["training_verification_sha256"])
    fresh_directory(output)
    (output / "adapter").mkdir()
    for name, digest in plan["adapter_sha256"].items():
        source = training / "checkpoint-91" / name
        checked_hash(source, digest)
        shutil.copyfile(source, output / "adapter" / name)
    provenance = {"checkpoint": 91, "plan_sha256": file_hash(PLAN),
                  "training_manifest_sha256": plan["training_manifest_sha256"],
                  "training_verification_sha256": plan["training_verification_sha256"],
                  "adapter_sha256": plan["adapter_sha256"], "contains_training_or_evaluation_text": False}
    write_json(output / "provenance.json", provenance)
    zip_files(output, INPUT_FILES, output / "private-adapter.zip")
    return {"status": "verified", "archive_sha256": file_hash(output / "private-adapter.zip")}


def verify_inputs(inputs: Path) -> dict[str, Any]:
    plan = load_plan()
    names = {p.relative_to(inputs).as_posix() for p in inputs.rglob("*") if p.is_file()}
    if names != INPUT_FILES:
        raise ValueError("Only adapter files and provenance may be uploaded.")
    provenance = json.loads((inputs / "provenance.json").read_text())
    if (provenance["plan_sha256"] != file_hash(PLAN) or provenance["checkpoint"] != 91
            or provenance["training_manifest_sha256"] != plan["training_manifest_sha256"]
            or provenance["training_verification_sha256"] != plan["training_verification_sha256"]
            or provenance["contains_training_or_evaluation_text"] is not False):
        raise ValueError("Adapter provenance differs from the frozen verified run.")
    for name, digest in plan["adapter_sha256"].items():
        checked_hash(inputs / "adapter" / name, digest)
    config = json.loads((inputs / "adapter/adapter_config.json").read_text())
    if config["r"] != 16 or config["base_model_name_or_path"] != plan["configuration"]["model"]:
        raise ValueError("Adapter architecture/base changed.")
    return provenance


def attach_adapter(base: Any, adapter: Path) -> Any:
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from peft.utils.save_and_load import get_peft_model_state_dict

    model = PeftModel.from_pretrained(base, str(adapter), is_trainable=False,
                                     autocast_adapter_dtype=False)
    model.eval()
    model.requires_grad_(False)
    if any(p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("Base and adapters must remain float32 for baseline parity.")
    saved = load_file(str(adapter / "adapter_model.safetensors"))
    loaded = get_peft_model_state_dict(model)
    if set(saved) != set(loaded) or any(not torch.equal(saved[k], loaded[k].cpu()) for k in saved):
        raise ValueError("Loaded adapter tensors differ from checkpoint91.")
    return model


def development_check(reference_logits: Any, adapted: Any) -> dict[str, Any]:
    """A fixed synthetic input checks wrapper equivalence, never benchmark answers."""
    import torch
    tokens = torch.tensor([[1, 2, 3, 4]], device=next(adapted.parameters()).device)
    with torch.no_grad():
        with adapted.disable_adapter():
            disabled = adapted(tokens).logits.detach()
        active = adapted(tokens).logits.detach()
    if not torch.equal(reference_logits, disabled):
        raise ValueError("Disabling adapter does not reproduce the original base logits.")
    if not torch.isfinite(active).all() or torch.equal(active, disabled):
        raise ValueError("Adapter is nonfinite or inactive on the synthetic probe.")
    return {"base_disabled_bitwise_equal": True, "active_finite": True,
            "active_changes_logits": True,
            "active_disabled_max_absolute_difference": float((active - disabled).abs().max()),
            "synthetic_token_ids": [1, 2, 3, 4], "benchmark_accessed": False}


def freeze(inputs: Path, output: Path) -> dict[str, Any]:
    import torch
    import psutil

    plan = load_plan()
    provenance = verify_inputs(inputs)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "T4" not in torch.cuda.get_device_name(0):
        raise RuntimeError("A free single T4 is required; no CPU or paid fallback.")
    free, total = torch.cuda.mem_get_info()
    if (free < 12 * 1024**3 or psutil.virtual_memory().available < 6 * 1024**3
            or shutil.disk_usage(ROOT).free < 20 * 1024**3):
        raise RuntimeError("Need12GiB free VRAM,6GiB host RAM,20GiB disk before evaluation.")
    for package, version in plan["environment"].items():
        if importlib.metadata.version(package) != version:
            raise RuntimeError(f"Wrong environment version: {package}")
    fresh_directory(output)
    profile = {"created_at": datetime.now(timezone.utc).isoformat(),
               "source_sha256": source_hashes(), "plan": plan, "input": provenance,
               "gpu": torch.cuda.get_device_name(0), "vram_bytes": total,
               "free_vram_bytes": free, "cuda": torch.version.cuda,
               "benchmark_accessed_at_freeze": False}
    write_json(output / "profile.json", profile)
    return profile


def execute(inputs: Path, output: Path) -> None:
    import torch

    plan = load_plan()
    verify_inputs(inputs)
    profile = json.loads((output / "profile.json").read_text())
    if profile["source_sha256"] != source_hashes() or profile["plan"] != plan:
        raise ValueError("Frozen source or plan changed.")
    if (output / "attempt.json").exists():
        raise RuntimeError("An evaluation was already attempted; do not rerun the benchmark.")
    write_json(output / "attempt.json", {"status": "incomplete", "benchmark_runs_authorized": 1})
    original_loader = evaluate.load_model
    original_manifest = evaluate.manifest_for

    def load_adapted(config: RunConfig) -> Any:
        wrapper = original_loader(config)
        wrapper.model.eval()
        tokens = torch.tensor([[1, 2, 3, 4]], device=wrapper.device)
        with torch.no_grad():
            reference = wrapper.model(tokens).logits.detach().clone()
        wrapper.model = attach_adapter(wrapper.model, inputs / "adapter")
        check = development_check(reference, wrapper.model)
        write_json(output / "adapter-check.json", check)
        return wrapper

    def manifest(config: RunConfig) -> dict[str, Any]:
        result = original_manifest(config)
        result["purpose"] = "post-training-final-checkpoint91"
        result["adapter"] = verify_inputs(inputs)
        return result

    try:
        with patch.object(evaluate, "load_model", load_adapted), patch.object(evaluate, "manifest_for", manifest):
            directory = evaluate.run(configuration(0, "evaluate"), output, execution_profile=profile)
        # Keep a flat, explicitly allowlisted export without rewriting original files.
        for name in ("manifest.json", "metrics.json", "samples.jsonl", "qualitative-review.json"):
            shutil.copyfile(directory / name, output / name)
        verify_artifacts(output, 900, configuration(0, "evaluate"))
        write_json(output / "attempt.json", {"status": "complete", "directory": directory.name})
    except BaseException as error:
        write_json(output / "attempt.json", {"status": "incomplete", "error": f"{type(error).__name__}: {error}"})
        raise


def verify_result(output: Path) -> dict[str, Any]:
    plan = load_plan()
    profile = json.loads((output / "profile.json").read_text())
    if profile["source_sha256"] != source_hashes() or profile["plan"] != plan:
        raise ValueError("Post-training source/plan mismatch.")
    manifest = verify_artifacts(output, 900, configuration(0, "evaluate"))
    if (manifest["purpose"] != "post-training-final-checkpoint91"
            or manifest["execution_profile"] != profile or manifest["adapter"] != profile["input"]
            or manifest["filbench_revision"] != plan["filbench_revision"]
            or manifest["protocol"] != plan["protocol"]
            or manifest["hardware"].get("tf32") is not False):
        raise ValueError("Protocol or adapter provenance changed.")
    check = json.loads((output / "adapter-check.json").read_text())
    if any(check.get(k) is not True for k in ("base_disabled_bitwise_equal", "active_finite", "active_changes_logits")):
        raise ValueError("Adapter equivalence/activation check failed.")
    if json.loads((output / "attempt.json").read_text())["status"] != "complete":
        raise ValueError("Incomplete evaluation.")
    rows = read_rows(output / "samples.jsonl")
    return {"status": "verified", "correct": int(sum(r["accuracy"] for r in rows)),
            "sample_count": 900, "runtime_seconds": manifest["runtime_seconds"],
            "inference_seconds": manifest["inference_seconds"], "samples_sha256": file_hash(output / "samples.jsonl")}


def read_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def passage_key(row: dict[str, Any]) -> str:
    # The pinned official Filipino MCF query adds this localized question label.
    prompt = row["official_detail"]["example"]
    if "\nTanong: " not in prompt:
        raise ValueError("Unexpected official prompt structure; cannot identify passage clusters.")
    return hashlib.sha256(prompt.rsplit("\nTanong: ", 1)[0].encode()).hexdigest()


def paired_comparison(base: list[dict[str, Any]], adapted: list[dict[str, Any]], replicates: int = 10000) -> dict[str, Any]:
    import numpy as np

    indexed = {r["prompt_sha256"]: r for r in base}
    if len(indexed) != len(base) or len(adapted) != len(base) or {r["prompt_sha256"] for r in adapted} != set(indexed):
        raise ValueError("Paired question identities differ or are duplicated.")
    counts: Counter[str] = Counter()
    clusters: dict[str, list[int]] = defaultdict(list)
    paired = []
    for row in sorted(adapted, key=lambda r: r["prompt_sha256"]):
        prior = indexed[row["prompt_sha256"]]
        a, b = prior["official_detail"], row["official_detail"]
        if any(hashlib.sha256(r["official_detail"]["full_prompt"].encode()).hexdigest() != r["prompt_sha256"]
               for r in (prior, row)):
            raise ValueError("Prompt hash disagrees with saved text.")
        for key in ("full_prompt", "input_tokens", "cont_tokens", "gold_index", "choices", "instruction"):
            if a[key] != b[key]:
                raise ValueError(f"Paired prompt/tokenization differs: {key}")
        if prior["gold_index"] != row["gold_index"]:
            raise ValueError("Paired gold answers differ.")
        before, after = int(prior["accuracy"]), int(row["accuracy"])
        category = ("both_correct" if before and after else "regressed" if before
                    else "improved" if after else "both_wrong")
        counts[category] += 1
        cluster = passage_key(row)
        clusters[cluster].append(after - before)
        paired.append({"prompt_sha256": row["prompt_sha256"], "passage_sha256": cluster,
                       "base_prediction": prior["predicted_index"], "adapter_prediction": row["predicted_index"],
                       "gold_index": row["gold_index"], "category": category})
    # Resample passages, retaining every question in a sampled passage. This
    # respects within-passage dependence; question counts may vary per replicate.
    summaries = [(sum(v), len(v)) for _, v in sorted(clusters.items())]
    sums = np.array([v[0] for v in summaries], dtype=float)
    sizes = np.array([v[1] for v in summaries], dtype=float)
    rng = np.random.default_rng(1234)
    draws = rng.integers(0, len(summaries), size=(replicates, len(summaries)))
    differences = sums[draws].sum(axis=1) / sizes[draws].sum(axis=1)
    interval = np.quantile(differences, [.025, .975], method="linear").tolist()
    n = len(base)
    base_correct = sum(int(r["accuracy"]) for r in base)
    adapted_correct = sum(int(r["accuracy"]) for r in adapted)
    return {"sample_count": n, "base_correct": base_correct, "adapter_correct": adapted_correct,
            "base_accuracy": base_correct / n, "adapter_accuracy": adapted_correct / n,
            "difference_percentage_points": 100 * (adapted_correct - base_correct) / n,
            "paired_counts": {k: counts[k] for k in ("both_correct", "improved", "regressed", "both_wrong")},
            "passage_clusters": len(clusters), "cluster_sizes": dict(sorted(Counter(map(len, clusters.values())).items())),
            "uncertainty": {"method": "paired passage-cluster percentile bootstrap", "replicates": replicates,
                            "seed": 1234, "confidence_level": .95, "quantile_method": "linear",
                            "difference_interval_percentage_points": [100 * v for v in interval],
                            "limitations": "Conditional on this translated benchmark and one training run; not training-seed or contamination uncertainty."},
            "pairs": paired}


def compare(output: Path, baseline: Path, destination: Path) -> dict[str, Any]:
    verify_result(output)
    plan = load_plan()
    for name, digest in plan["baseline_sha256"].items():
        checked_hash(baseline / name, digest)
    verify_artifacts(baseline, 900, configuration(0, "evaluate"))
    report = paired_comparison(read_rows(baseline / "samples.jsonl"), read_rows(output / "samples.jsonl"))
    report["provenance"] = {"base_samples_sha256": file_hash(baseline / "samples.jsonl"),
                            "adapter_samples_sha256": file_hash(output / "samples.jsonl"), "plan_sha256": file_hash(PLAN)}
    if destination.exists():
        raise FileExistsError(destination)
    write_json(destination, report)
    return {k: v for k, v in report.items() if k != "pairs"}


def archive(output: Path, destination: Path) -> dict[str, Any]:
    names = {p.name for p in output.iterdir() if p.is_file()} & (RESULT_FILES - {"archive-manifest.json"})
    write_json(output / "archive-manifest.json", {"sha256": {n: file_hash(output / n) for n in sorted(names)}})
    zip_files(output, names | {"archive-manifest.json"}, destination)
    return {"archive_sha256": file_hash(destination), "bytes": destination.stat().st_size}


def import_result(archive_path: Path, output: Path) -> dict[str, Any]:
    extract(archive_path, output, RESULT_FILES, 256 * 1024**2)
    receipt = json.loads((output / "archive-manifest.json").read_text())["sha256"]
    actual = {p.name for p in output.iterdir() if p.is_file()} - {"archive-manifest.json"}
    if actual != set(receipt):
        raise ValueError("Result archive inventory differs.")
    for name, digest in receipt.items():
        checked_hash(output / name, digest)
    result = verify_result(output)
    write_json(output / "local-verification.json", result | {"archive_sha256": file_hash(archive_path)})
    return result


def integration(output: Path) -> dict[str, Any]:
    import torch
    from transformers import Qwen3Config, Qwen3ForCausalLM
    from peft import LoraConfig, get_peft_model

    fresh_directory(output)
    torch.manual_seed(1234)
    config = Qwen3Config(vocab_size=32, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
                         num_attention_heads=2, num_key_value_heads=1, head_dim=8)
    model = Qwen3ForCausalLM(config).float().eval()
    saved_base = {k: v.clone() for k, v in model.state_dict().items()}
    adapter = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))
    with torch.no_grad():
        for name, parameter in adapter.named_parameters():
            if "lora_B" in name:
                parameter.fill_(.01)
    adapter.save_pretrained(output / "adapter", safe_serialization=True)
    restored_base = Qwen3ForCausalLM(config).float().eval()
    restored_base.load_state_dict(saved_base)
    with torch.no_grad():
        reference = restored_base(torch.tensor([[1, 2, 3, 4]])).logits.clone()
    restored = attach_adapter(restored_base, output / "adapter")
    result = development_check(reference, restored)
    assert all(torch.equal(restored.get_base_model().state_dict()[k.replace('.weight', '.base_layer.weight')]
                           if k.endswith(('q_proj.weight', 'v_proj.weight')) else restored.get_base_model().state_dict()[k], v)
               for k, v in saved_base.items())
    write_json(output / "integration.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "unpack", "freeze", "evaluate", "verify", "archive", "import", "compare", "integration"))
    for name in ("training-run", "baseline", "output", "inputs", "archive", "destination"):
        parser.add_argument(f"--{name}", type=Path)
    args = parser.parse_args()
    command = args.command
    if command == "prepare":
        result = prepare(args.training_run, args.baseline, args.output)
    elif command == "unpack":
        extract(args.archive, args.output, INPUT_FILES, 80 * 1024**2)
        result = verify_inputs(args.output)
    elif command == "freeze":
        result = freeze(args.inputs, args.output)
    elif command == "evaluate":
        execute(args.inputs, args.output)
        result = verify_result(args.output)
    elif command == "verify":
        result = verify_result(args.output)
    elif command == "archive":
        result = archive(args.output, args.archive)
    elif command == "import":
        result = import_result(args.archive, args.output)
    elif command == "compare":
        result = compare(args.output, args.baseline, args.destination)
    else:
        result = integration(args.output)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

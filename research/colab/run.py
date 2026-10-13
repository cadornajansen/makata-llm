"""Run the frozen study on one explicitly selected Colab CUDA device."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import evaluate
from preflight import read_plan
from protocol import ROOT, RunConfig, checked_prediction, file_hash, write_json

GIB = 1024**3
SOURCE_FILES = ("evaluate.py", "protocol.py", "preflight.py", "baseline-plan.json",
                "requirements.txt", "requirements-colab.txt", "colab/run.py", "fixtures/development.json")


def source_hashes() -> dict[str, str]:
    return {name: file_hash(ROOT / name) for name in SOURCE_FILES}


def configuration(index: int, mode: str) -> RunConfig:
    candidate = read_plan()["candidates"][index]
    return RunConfig(mode, candidate["model"], candidate["model_revision"],
                     candidate["tokenizer"], candidate["tokenizer_revision"],
                     device="cuda", dtype="float32", threads=4)


def verify_artifacts(directory: Path, count: int, config: RunConfig) -> dict[str, Any]:
    manifest = json.loads((directory / "manifest.json").read_text())
    rows = [json.loads(line) for line in (directory / "samples.jsonl").read_text().splitlines()]
    if manifest["status"] != "complete" or len(rows) != count or manifest["sample_count"] != count:
        raise RuntimeError("Missing complete full-run evidence.")
    if len({row["sample_id"] for row in rows}) != count:
        raise RuntimeError("Duplicate saved examples.")
    from dataclasses import asdict

    if manifest["configuration"] != asdict(config):
        raise RuntimeError("Saved run does not match the frozen candidate/configuration.")
    if manifest["samples_sha256"] != file_hash(directory / "samples.jsonl"):
        raise RuntimeError("Sample checksum mismatch.")
    if manifest["baseline_plan_sha256"] != file_hash(ROOT / "baseline-plan.json"):
        raise RuntimeError("Frozen plan changed.")
    if config.mode == "evaluate":
        from protocol import DATASET_ID, DATASET_REVISION, DATASET_SUBSET, OFFICIAL_TASK

        if not manifest["benchmark_accessed"] or manifest["task"] != OFFICIAL_TASK:
            raise RuntimeError("Missing official benchmark execution.")
        if (manifest["data"]["repository"], manifest["data"]["revision"], manifest["data"]["subset"]) != (
            DATASET_ID, DATASET_REVISION, DATASET_SUBSET
        ):
            raise RuntimeError("Dataset pin mismatch.")
    for name, digest in manifest["code_sha256"].items():
        if file_hash(ROOT / name) != digest:
            raise RuntimeError(f"Run source changed: {name}")
    for row in rows:
        if checked_prediction(row["choice_log_likelihoods"], [row["gold_index"]], row["accuracy"]) != row["predicted_index"]:
            raise RuntimeError("Prediction mismatch.")
        detail = row["official_detail"]
        if any(detail["truncated"]) or detail["num_asked_few_shots"] or detail["num_effective_few_shots"]:
            raise RuntimeError("Truncation or few-shot example detected.")
    metrics = json.loads((directory / "metrics.json").read_text())
    scores = [value["acc"] for key, value in metrics["official_task_metrics"].items() if key != "all" and "acc" in value]
    accuracy = sum(row["accuracy"] for row in rows) / count
    if len(scores) != 1 or not math.isclose(scores[0], accuracy, abs_tol=1e-12):
        raise RuntimeError("Official aggregate disagrees with saved samples.")
    return manifest


def freeze(session: Path) -> None:
    import torch

    evaluate.initialize_runtime(configuration(0, "pilot"))
    if torch.__version__ != "2.7.1+cu126" or torch.version.cuda != "12.6":
        raise RuntimeError("Use the pinned CUDA environment; do not use Colab's preinstalled packages.")
    if torch.cuda.device_count() != 1:
        raise RuntimeError("Set CUDA_VISIBLE_DEVICES=0 before Python starts; use one GPU.")
    free, total = torch.cuda.mem_get_info()
    hardware = evaluate.hardware_snapshot()
    if free < 12 * GIB or hardware["ram_available_bytes"] < 8 * GIB or hardware["disk_free_bytes"] < 25 * GIB:
        raise RuntimeError("Need 12 GiB free GPU memory, 8 GiB free host RAM, and 25 GiB free disk for planning.")
    profile = {
        "study": read_plan()["study"], "created_at": datetime.now(timezone.utc).isoformat(),
        "execution": {"device": "cuda", "dtype": "float32", "threads": 4, "tf32": False,
                      "quantization": False, "batch_size": 1, "maximum_baseline_seconds": 14400},
        "source_sha256": source_hashes(), "hardware": hardware,
        "gpu": torch.cuda.get_device_name(0), "gpu_free_bytes": free, "gpu_total_bytes": total,
        "torch_version": torch.__version__, "cuda_build": torch.version.cuda,
        "nvidia_smi": subprocess.check_output(["nvidia-smi"], text=True),
        "benchmark_accessed_at_freeze": False,
        "notice": "CUDA execution amendment; model, tokenizer, dataset, task and float32 scoring are unchanged.",
    }
    session.mkdir(parents=True, exist_ok=True)
    path = session / "execution-profile.json"
    if path.exists():
        validate_profile(session)
        print(f"Existing frozen GPU profile retained: {path}")
        return
    write_json(path, profile)
    print(f"GPU profile frozen before loading candidate weights or benchmark examples: {path}")


def validate_profile(session: Path) -> dict[str, Any]:
    profile = json.loads((session / "execution-profile.json").read_text())
    if profile["source_sha256"] != source_hashes():
        raise RuntimeError("Source/plan changed after the GPU profile was frozen.")
    import torch

    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != profile["gpu"]:
        raise RuntimeError("Frozen GPU unavailable or changed; no CPU fallback.")
    return profile


def smoke(session: Path, index: int) -> None:
    profile = validate_profile(session)
    directory = evaluate.run(configuration(index, "pilot"), session, execution_profile=profile)
    manifest = verify_artifacts(directory, 20, configuration(index, "pilot"))
    if manifest["benchmark_accessed"]:
        raise RuntimeError("Synthetic smoke test accessed benchmark data.")
    rows = [json.loads(line) for line in (directory / "samples.jsonl").read_text().splitlines()]
    lengths = [len(tokens) for row in rows for tokens in row["official_detail"]["input_tokens"]]
    # Planning extrapolation, not a promised runtime or a cap on benchmark inputs.
    estimate = manifest["inference_seconds"] * 45 * (2048 / (sum(lengths) / len(lengths))) + 600
    write_json(session / f"smoke-{index}.json", {
        "directory": str(directory), "candidate": index, "source_sha256": source_hashes(),
        "estimated_baseline_seconds_at_2048_average_tokens": estimate,
        "notice": "20 synthetic development questions only; not a benchmark result. Estimate is approximate.",
    })
    print(f"Candidate {index}: CUDA smoke verified; conservative runtime screen {estimate / 60:.1f} minutes.")


def baseline(session: Path, index: int) -> None:
    profile = validate_profile(session)
    for required in (0, 1):
        evidence = json.loads((session / f"smoke-{required}.json").read_text())
        if evidence["source_sha256"] != source_hashes():
            raise RuntimeError("Both candidates need current synthetic smoke tests before benchmark access.")
        verify_artifacts(Path(evidence["directory"]), 20, configuration(required, "pilot"))
    smoke_result = json.loads((session / f"smoke-{index}.json").read_text())
    if smoke_result["source_sha256"] != source_hashes():
        raise RuntimeError("Stale synthetic smoke test.")
    verify_artifacts(Path(smoke_result["directory"]), 20, configuration(index, "pilot"))
    if smoke_result["estimated_baseline_seconds_at_2048_average_tokens"] > profile["execution"]["maximum_baseline_seconds"]:
        raise RuntimeError("Estimated baseline exceeds the four-hour execution budget; stop before benchmark access.")
    marker = session / f"baseline-{index}.json"
    if marker.exists():
        directory = Path(json.loads(marker.read_text())["directory"])
        verify_artifacts(directory, 900, configuration(index, "evaluate"))
        print(f"Existing complete baseline retained; not rerunning held-out evaluation: {directory}")
        return
    directory = evaluate.run(configuration(index, "evaluate"), session, execution_profile=profile)
    verify_artifacts(directory, 900, configuration(index, "evaluate"))
    write_json(marker, {"directory": str(directory), "candidate": index})
    print(f"Verified full 900-question baseline: {directory}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "smoke", "evaluate"))
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--candidate", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.session)
    elif args.command == "smoke":
        smoke(args.session, args.candidate)
    else:
        baseline(args.session, args.candidate)


if __name__ == "__main__":
    main()

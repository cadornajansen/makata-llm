"""Bounded full-run inputs and local verification; never loads benchmark data."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

from qlora_smoke import (check_hash, content_hash, deterministic_zip, encode_example,
                         file_hash, json_bytes, read_jsonl, safe_extract, utc_now, write_json)

ROOT = Path(__file__).resolve().parent
PROPOSAL = ROOT / "aya-training-proposal.json"
AUTHORIZATION = ROOT / "qlora-full-authorization.json"
PROPOSAL_SHA = "9ab753aa10954de2832187df4486b95507dd33e4446cb9b6402c9ad9588e6ac8"
TRAIN_SHA = "33a8edcaddee3c5b3fca12513b17ac906525b6d69745588b8a4c6cb848a071ac"
VALIDATION_SHA = "a4b41287eee61c509f06ca5069338605233aeef90a684d19d1706fee89140705"
INPUT_FILES = {"train.jsonl", "validation.jsonl", "NOTICE.md", "input-manifest.json"}
SOURCE_FILES = ("qlora_full.py", "qlora_full_runtime.py", "qlora_smoke.py", "qlora_training.py",
                "qlora-smoke-plan.json", "aya-training-proposal.json", "qlora-full-authorization.json",
                "requirements-qlora-colab.txt")
TOP_ARTIFACTS = {"training-log.jsonl", "validation-diagnostics.json", "tokenizer-check.json",
                 "adapter-reference.json", "probe-reference.safetensors", "reload-verification.json"}
CHECKPOINT_ARTIFACTS = {"adapter_model.safetensors", "adapter_config.json", "README.md",
                        "training-state.pt", "checkpoint-manifest.json"}
RESULT_FILES = TOP_ARTIFACTS | {"run-manifest.json", "archive-manifest.json"} | {
    f"checkpoint-{step}/{name}" for step in (50, 91) for name in CHECKPOINT_ARTIFACTS}


def load_plan() -> dict[str, Any]:
    check_hash(PROPOSAL, PROPOSAL_SHA)
    plan = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if (authorization["proposal_sha256"] != PROPOSAL_SHA or authorization["training_authorized"] is not True
            or authorization["paid_compute_authorized"] is not False
            or authorization["evaluation_scoring_authorized"] is not False
            or authorization["publication_authorized"] is not False
            or authorization["provisional_validation_diagnostics_authorized"] is not True):
        raise ValueError("Missing or changed bounded authorization.")
    return plan


def source_hashes() -> dict[str, str]:
    return {name: file_hash(ROOT / name) for name in SOURCE_FILES}


def validate_rows(rows: list[dict[str, Any]], validation: list[dict[str, Any]], plan: dict[str, Any]) -> None:
    if len(rows) != 363 or len(validation) != 66:
        raise ValueError("Require exactly363 training and66 provisional validation records.")
    if [r["id"] for r in rows] != [r["id"] for r in plan["selection"]]:
        raise ValueError("Training selection/order changed.")
    if {r["id"] for r in validation} != set(plan["validation"]["eligible_ids"]):
        raise ValueError("Validation selection changed.")
    if len({r["id"] for r in rows + validation}) != 429:
        raise ValueError("Duplicate IDs.")
    if len({r["group_id"] for r in rows}) != 363:
        raise ValueError("Training groups must be unique.")
    if {r["group_id"] for r in rows} & {r["group_id"] for r in validation}:
        raise ValueError("Training/validation group leakage.")
    for row in rows + validation:
        if content_hash(row) != row["content_sha256"]:
            raise ValueError("Changed text.")
        if row["assigned_split"] != ("train" if row in rows else "validation"):
            raise ValueError("Changed split.")
        if row["provenance"]["revision"] != "a3af2fde4b4cb5b2775830b11244a1a20b5f004f":
            raise ValueError("Changed Aya provenance.")
    for row, item in zip(rows, plan["selection"], strict=True):
        if any(row[key] != item[key] for key in ("id", "group_id", "content_sha256")):
            raise ValueError("Changed selection evidence.")


def prepare(source: Path, packet: Path, output: Path) -> dict[str, Any]:
    """Recheck original eligibility locally; upload no review/evaluation questions."""
    from prepare_training_readiness import select_rows, validate_risk_review, validation_reviews
    if output.exists():
        raise FileExistsError("Never overwrite a previous input bundle.")
    plan = load_plan()
    for name, digest in plan["source_files"].items():
        check_hash(source / name, digest)
    for name, digest in plan["preserved_smoke_files"].items():
        check_hash(ROOT / name, digest)
    risk_path = ROOT / plan["risk_review"]["file"]
    check_hash(risk_path, plan["risk_review"]["sha256"])
    risk = json.loads(risk_path.read_text(encoding="utf-8"))
    training, validation = read_jsonl(source / "train.jsonl"), read_jsonl(source / "validation.jsonl")
    validate_risk_review(plan, risk, training + validation)
    validation_reviews(validation, plan, risk)
    history_path = ROOT / plan["prior_proposal_review"]["file"]
    check_hash(history_path, plan["prior_proposal_review"]["sha256"])
    history = json.loads(history_path.read_text(encoding="utf-8"))
    reviews = read_jsonl(source / "review-decisions.jsonl") + read_jsonl(source / "prior-review-decisions.jsonl")
    reviews += [{**item, "disposition": "accept"} for item in history["selection"]]
    selected = select_rows(training, read_jsonl(source / "dispositions.jsonl"), reviews, plan["selection"], True)
    check_hash(packet / "train.jsonl", TRAIN_SHA)
    check_hash(packet / "validation-provisional.jsonl", VALIDATION_SHA)
    if selected != read_jsonl(packet / "train.jsonl"):
        raise ValueError("Packet is not the eligible frozen selection.")
    candidate_validation = [r for r in validation if r["id"] in plan["validation"]["eligible_ids"]]
    validate_rows(selected, candidate_validation, plan)
    output.mkdir(parents=True)
    for name, origin in (("train.jsonl", packet / "train.jsonl"),
                         ("validation.jsonl", packet / "validation-provisional.jsonl"),
                         ("NOTICE.md", source / "NOTICE.md")):
        (output / name).write_bytes(origin.read_bytes())
    manifest = {"status": "complete", "proposal_sha256": PROPOSAL_SHA,
                "authorization_sha256": file_hash(AUTHORIZATION), "counts": {"training": 363, "validation": 66},
                "screening_only_training_records": 283, "legal_clearance": False,
                "human_validated": False, "benchmark_accessed": False, "evaluation_items_included": False,
                "outputs": {n: file_hash(output / n) for n in INPUT_FILES - {"input-manifest.json"}}}
    write_json(output / "input-manifest.json", manifest)
    deterministic_zip(output, INPUT_FILES, output / "private-full-inputs.zip")
    return {"status": "prepared", "counts": manifest["counts"], "archive_sha256": file_hash(output / "private-full-inputs.zip")}


def load_inputs(inputs: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    plan = load_plan()
    manifest = json.loads((inputs / "input-manifest.json").read_text(encoding="utf-8"))
    if (manifest["status"] != "complete" or manifest["proposal_sha256"] != PROPOSAL_SHA
            or manifest["authorization_sha256"] != file_hash(AUTHORIZATION)
            or manifest["evaluation_items_included"] is not False or manifest["benchmark_accessed"] is not False
            or manifest["human_validated"] is not False or manifest["legal_clearance"] is not False):
        raise ValueError("Changed input boundaries or authorization.")
    if set(manifest["outputs"]) != INPUT_FILES - {"input-manifest.json"}:
        raise ValueError("Unauthorized input files.")
    for name, digest in manifest["outputs"].items():
        check_hash(inputs / name, digest)
    check_hash(inputs / "train.jsonl", TRAIN_SHA)
    check_hash(inputs / "validation.jsonl", VALIDATION_SHA)
    check_hash(inputs / "NOTICE.md", plan["source_files"]["NOTICE.md"])
    rows, validation = read_jsonl(inputs / "train.jsonl"), read_jsonl(inputs / "validation.jsonl")
    validate_rows(rows, validation, plan)
    return rows, validation, manifest


def tokenize(inputs: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    from qlora_training import get_tokenizer
    plan = load_plan()
    rows, validation, _ = load_inputs(inputs)
    tokenizer = get_tokenizer(plan)
    training_tokens = [encode_example(r, tokenizer, 512) for r in rows]
    validation_tokens = [encode_example(r, tokenizer, 512) for r in validation]
    if [len(r["input_ids"]) for r in training_tokens] != [r["tokens"] for r in plan["token_lengths"]]:
        raise ValueError("Token lengths changed from frozen proposal.")
    report = {"status": "passed", "chat_template_used": False, "eos_token_id": tokenizer.eos_token_id,
              "pad_token_id": tokenizer.pad_token_id, "records": [
                  {"id": row["id"], "tokens": len(item["input_ids"]), "supervised_tokens": sum(x != -100 for x in item["labels"])}
                  for row, item in zip(rows, training_tokens, strict=True)],
              "validation_records": len(validation_tokens), "truncation": False}
    return training_tokens, validation_tokens, report


def verify_checkpoint(directory: Path, step: int, deep: bool = True) -> dict[str, Any]:
    report = json.loads((directory / "checkpoint-manifest.json").read_text(encoding="utf-8"))
    required = CHECKPOINT_ARTIFACTS - {"checkpoint-manifest.json", "README.md"}
    if (report["step"] != step or report["examples_consumed"] != min(step * 4, 363)
            or report["proposal_sha256"] != PROPOSAL_SHA or not required <= set(report["files"])
            or not set(report["files"]) <= CHECKPOINT_ARTIFACTS - {"checkpoint-manifest.json"}):
        raise ValueError("Invalid checkpoint position/files.")
    for name, digest in report["files"].items():
        check_hash(directory / name, digest)
    if deep:
        import torch
        from safetensors.torch import load_file
        from qlora_training import tensor_digest
        tensors = load_file(str(directory / "adapter_model.safetensors"))
        if tensor_digest(tensors) != report["tensor_sha256"] or any(not bool(torch.isfinite(t).all()) for t in tensors.values()):
            raise ValueError("Checkpoint adapter tensors differ or are nonfinite.")
        state = torch.load(directory / "training-state.pt", map_location="cpu", weights_only=True)
        if (state["step"] != step or state["examples_consumed"] != min(step * 4, 363)
                or state["scheduler"]["last_epoch"] != step or len(set(state["order"])) != 363
                or sorted(state["order"]) != list(range(363))):
            raise ValueError("Checkpoint optimizer/data position differs.")
        moments = state["optimizer"]["state"]
        if not moments or len(moments) != len(tensors):
            raise ValueError("Missing optimizer parameter states.")
        for moment in moments.values():
            if int(moment["step"]) != step:
                raise ValueError("Optimizer tensor step differs.")
            for key in ("exp_avg", "exp_avg_sq"):
                if moment[key].dtype != torch.float32 or not bool(torch.isfinite(moment[key]).all()):
                    raise ValueError("Invalid optimizer moment.")
        config = json.loads((directory / "adapter_config.json").read_text())
        if config["r"] != 16 or config["base_model_name_or_path"] != "Qwen/Qwen3-1.7B-Base":
            raise ValueError("Changed adapter configuration.")
    return report


def verify(output: Path, deep: bool = True) -> dict[str, Any]:
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["proposal_sha256"] != PROPOSAL_SHA:
        raise ValueError("Full run is not complete.")
    if manifest["source_sha256"] != source_hashes() or manifest["configuration"] != load_plan():
        raise ValueError("Source/configuration mismatch.")
    if manifest["benchmark_accessed"] is not False or manifest["evaluation_scored"] is not False:
        raise ValueError("Research isolation violated.")
    required = TOP_ARTIFACTS | {f"checkpoint-{step}/{n}" for step in (50, 91)
                               for n in CHECKPOINT_ARTIFACTS - {"README.md"}}
    if not required <= set(manifest["artifacts"]) or not set(manifest["artifacts"]) <= RESULT_FILES - {"run-manifest.json", "archive-manifest.json"}:
        raise ValueError("Missing or unexpected artifacts.")
    for name, digest in manifest["artifacts"].items():
        check_hash(output / name, digest)
    logs = read_jsonl(output / "training-log.jsonl")
    if len(logs) != 91 or [r["step"] for r in logs] != list(range(1, 92)):
        raise ValueError("Expected91 actual optimizer updates.")
    ids = []
    for index, row in enumerate(logs):
        if (row["microbatches"] != (3 if index == 90 else 4) or row["gradients_finite"] is not True
                or len(row["ids"]) != row["microbatches"] or not math.isfinite(row["loss"])
                or abs(row["learning_rate"] - .0002 * min(index / 5, 1)) > 1e-12):
            raise ValueError("Invalid loss, scheduler or accumulation log.")
        ids.extend(row["ids"])
    if Counter(ids) != Counter(s["id"] for s in load_plan()["selection"]):
        raise ValueError("One-epoch example accounting differs.")
    metrics = manifest["metrics"]
    if metrics["optimizer_updates"] != 91 or metrics["initial_training_loss"] != logs[0]["loss"] or metrics["final_training_loss"] != logs[-1]["loss"]:
        raise ValueError("Summary/log mismatch.")
    for key in ("training_seconds", "peak_allocated_bytes", "peak_reserved_bytes"):
        if not math.isfinite(metrics[key]) or metrics[key] <= 0:
            raise ValueError("Invalid resource measurement.")
    for step in (50, 91):
        verify_checkpoint(output / f"checkpoint-{step}", step, deep)
    reload_report = json.loads((output / "reload-verification.json").read_text())
    for key in ("tensor_equality", "probe_finite", "probe_argmax_equal", "fresh_process"):
        if reload_report.get(key) is not True:
            raise ValueError("Final reload check failed.")
    if (reload_report["status"] != "passed" or reload_report["train_process_id"] == reload_report["reload_process_id"]
            or reload_report["tolerances"] != {"atol": .001, "rtol": .001}):
        raise ValueError("Invalid fresh-process reload evidence.")
    diagnostics = json.loads((output / "validation-diagnostics.json").read_text())
    if diagnostics["count"] != 66 or diagnostics["validated"] is not False or diagnostics["used_for_checkpoint_selection"] is not False:
        raise ValueError("Provisional diagnostics mislabeled.")
    if any(not math.isfinite(diagnostics[k]) for k in ("before", "after")):
        raise ValueError("Nonfinite validation diagnostics.")
    return {"status": "verified", "metrics": metrics, "reload": reload_report,
            "checkpoint_steps": [50, 91], "classification": "exploratory internal experiment; not scientifically validated"}


def archive_results(output: Path, archive: Path) -> dict[str, Any]:
    names = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()} & (RESULT_FILES - {"archive-manifest.json"})
    if "run-manifest.json" not in names:
        raise ValueError("Cannot archive an unidentified run.")
    write_json(output / "archive-manifest.json", {"files": {n: file_hash(output / n) for n in sorted(names)}})
    deterministic_zip(output, names | {"archive-manifest.json"}, archive)
    return {"files": len(names) + 1, "archive_sha256": file_hash(archive)}


def import_results(archive: Path, output: Path) -> dict[str, Any]:
    safe_extract(archive, output, RESULT_FILES, 2 * 1024**3)
    receipt = json.loads((output / "archive-manifest.json").read_text())["files"]
    names = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()} - {"archive-manifest.json"}
    if set(receipt) != names:
        raise ValueError("Archive ledger differs from files.")
    for name, digest in receipt.items():
        check_hash(output / name, digest)
    result = verify(output)
    write_json(output / "local-verification.json", {**result, "verified_at": utc_now(), "archive_sha256": file_hash(archive)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "unpack", "preflight", "tokenize", "train", "reload", "verify", "archive", "import", "integration"))
    for name in ("source", "packet", "inputs", "archive"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(HF_HUB_DISABLE_TELEMETRY="1", WANDB_DISABLED="true", TOKENIZERS_PARALLELISM="false")
    try:
        if args.command == "prepare":
            result = prepare(args.source, args.packet, args.output)
        elif args.command == "unpack":
            safe_extract(args.archive, args.output, INPUT_FILES, 4 * 1024**2)
            rows, validation, _ = load_inputs(args.output)
            result = {"training": len(rows), "provisional_validation": len(validation)}
        elif args.command == "tokenize":
            _, _, result = tokenize(args.inputs)
            args.output.mkdir(parents=True, exist_ok=True)
            write_json(args.output / "tokenizer-check.json", result)
        elif args.command == "verify":
            result = verify(args.output)
        elif args.command == "archive":
            result = archive_results(args.output, args.archive)
        elif args.command == "import":
            result = import_results(args.archive, args.output)
        else:
            import qlora_full_runtime as runtime
            if args.command == "train":
                result = runtime.train(args.inputs, args.output)
            else:
                result = getattr(runtime, args.command)(args.output)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

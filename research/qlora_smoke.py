"""Isolated, fail-closed input and artifact tools for the 20-update QLoRA test.

No evaluation module, benchmark loader, or dataset download is imported here.
Heavy training libraries are imported only by commands that need them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
from datetime import datetime, timezone
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parent
DEFAULT_PLAN = ROOT / "qlora-smoke-plan.json"
MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
SELECTED_IDS = [f"aya-fil-{n}" for n in (127, 132, 149, 181, 188, 312, 372, 564, 652, 680, 686, 820, 916, 961, 1102, 1199)]
INPUT_FILES = {"subset.jsonl", "subset-manifest.json", "NOTICE.md"}
RESULT_FILES = {
    "run-manifest.json", "training-log.jsonl", "probe-reference.safetensors",
    "adapter-reference.json", "tokenizer-check.json", "reload-verification.json",
    "adapter/adapter_model.safetensors", "adapter/adapter_config.json", "adapter/README.md",
    "preflight.json", "archive-manifest.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_plan(path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("loss_scaling") != {"init_scale": 1024.0, "growth_factor": 2.0, "backoff_factor": 0.5, "growth_interval": 2000}:
        raise ValueError("FP16 loss-scaling settings differ from the corrected smoke plan.")
    if (plan["source"]["revision"] != "a3af2fde4b4cb5b2775830b11244a1a20b5f004f"
            or plan["source"]["sha256"] != "8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc"
            or plan["aya_manifest_sha256"] != "e1bcfee1b264aa527b3d53ad940e2410ff59f28a5bbb190cc491e8d40bf49cc2"):
        raise ValueError("Aya source/audit pins changed.")
    model = plan["model"]
    if (model["repository"] != "Qwen/Qwen3-1.7B-Base"
            or model["tokenizer"] != model["repository"]
            or model["revision"] != MODEL_REVISION
            or model["tokenizer_revision"] != MODEL_REVISION
            or model["eos_token_id"] != 151643):
        raise ValueError("Only the frozen Qwen model and tokenizer are authorized.")
    expected_training = {"max_steps": 20, "max_length": 512, "per_device_train_batch_size": 1,
                         "gradient_accumulation_steps": 4, "learning_rate": 0.0002,
                         "warmup_steps": 2, "lr_scheduler_type": "constant_with_warmup",
                         "max_grad_norm": 1.0, "seed": 1234, "weight_decay": 0.0}
    if plan["training"] != expected_training:
        raise ValueError("Training configuration differs from the authorized 20-update smoke test.")
    if plan["quantization"] != {"load_in_4bit": True, "bnb_4bit_quant_type": "nf4",
                               "bnb_4bit_use_double_quant": True, "bnb_4bit_compute_dtype": "float16"}:
        raise ValueError("Quantization settings changed.")
    if plan["lora"] != {"r": 16, "lora_alpha": 32, "lora_dropout": 0.05, "bias": "none",
                        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                        "task_type": "CAUSAL_LM"}:
        raise ValueError("LoRA configuration changed.")
    selection = plan["selection"]
    if [row["id"] for row in selection] != SELECTED_IDS or len({r["group_id"] for r in selection}) != 16:
        raise ValueError("The selection must contain the 16 authorized independent groups.")
    for row in selection:
        if len(row["content_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["content_sha256"]):
            raise ValueError("Invalid content hash in selection ledger.")
    if plan["clearance"]["full_training_authorized"] or plan["clearance"]["legal_clearance"]:
        raise ValueError("Smoke-test inputs must retain provisional status.")
    return plan


def source_hashes() -> dict[str, str]:
    names = ("qlora_smoke.py", "qlora_training.py", "qlora-smoke-plan.json", "requirements-qlora-colab.txt")
    return {name: file_hash(ROOT / name) for name in names}


def check_hash(path: Path, expected: str) -> None:
    if file_hash(path) != expected:
        raise ValueError(f"Checksum mismatch: {path.name}")


def content_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(json_bytes([row["prompt"], row["response"]])).hexdigest()


def validate_selected(rows: list[dict[str, Any]], plan: dict[str, Any]) -> None:
    if [row["id"] for row in rows] != [r["id"] for r in plan["selection"]]:
        raise ValueError("Input IDs/order differ from the authorized selection.")
    for row, selected in zip(rows, plan["selection"], strict=True):
        if row.get("assigned_split") != "train" or row.get("group_id") != selected["group_id"]:
            raise ValueError("Only frozen training records and groups are permitted.")
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("prompt", "response")):
            raise ValueError("Empty or invalid prompt/response.")
        if row.get("content_sha256") != selected["content_sha256"] or content_hash(row) != selected["content_sha256"]:
            raise ValueError(f"Changed text: {row['id']}")
        provenance = row["provenance"]
        for key in ("repository", "revision", "file", "license_declaration"):
            if provenance[key] != plan["source"][key]:
                raise ValueError(f"Source provenance differs: {key}")
        if provenance["language"] != "fil" or provenance["source_split"] != "train" or provenance["dataset_name"] != "Aya-Dataset":
            raise ValueError("Unexpected source composition.")


def select_eligible(source: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    check_hash(source / "manifest.json", plan["aya_manifest_sha256"])
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["source"] != plan["source"]:
        raise ValueError("Aya v2 provenance/status differs from the frozen selection.")
    for name, expected in plan["aya_files"].items():
        check_hash(source / name, expected)
    training = read_jsonl(source / "train.jsonl")
    if len({r["id"] for r in training}) != len(training):
        raise ValueError("Duplicate training IDs.")
    by_id = {r["id"]: r for r in training}
    rows = [by_id[selected["id"]] for selected in plan["selection"]]
    validate_selected(rows, plan)
    dispositions = read_jsonl(source / "dispositions.jsonl")
    reviews = read_jsonl(source / "review-decisions.jsonl") + read_jsonl(source / "prior-review-decisions.jsonl")
    for row in rows:
        members = [r for r in dispositions if r.get("group_id") == row["group_id"]]
        own = [r for r in members if r["id"] == row["id"]]
        if len(own) != 1 or own[0]["content_sha256"] != row["content_sha256"]:
            raise ValueError("Missing or changed disposition evidence.")
        if any(r.get("quality_flags") or r["disposition"] not in ("provisional_candidate", "excluded_exact_duplicate") for r in members):
            raise ValueError(f"Unresolved quality concern in group: {row['group_id']}")
        member_ids = {r["id"] for r in members}
        if any(r["id"] in member_ids and r["disposition"] in ("hold", "reject") for r in reviews):
            raise ValueError("A selected group has an explicit hold or rejection.")
        if not any(r["id"] == row["id"] and r["content_sha256"] == row["content_sha256"]
                   and r["disposition"] == "accept" and r["reviewer_type"] == "agent" for r in reviews):
            raise ValueError("Missing prior agent acceptance observation.")
    return rows


def deterministic_zip(root: Path, names: set[str], destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Not a regular file: {name}")
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(entry, path.read_bytes())


def prepare(source: Path, output: Path, plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    try:
        plan = load_plan(plan_path)
        rows = select_eligible(source, plan)
        (output / "subset.jsonl").write_bytes(b"".join(json_bytes(row) for row in rows))
        shutil.copyfile(source / "NOTICE.md", output / "NOTICE.md")
        manifest = {"status": "complete", "version": plan["version"], "count": len(rows),
                    "plan_sha256": file_hash(plan_path), "aya_manifest_sha256": plan["aya_manifest_sha256"],
                    "source": plan["source"], "selection": plan["selection"], "clearance": plan["clearance"],
                    "outputs": {name: file_hash(output / name) for name in ("subset.jsonl", "NOTICE.md")},
                    "benchmark_data_accessed": False}
        write_json(output / "subset-manifest.json", manifest)
        deterministic_zip(output, INPUT_FILES, output / "private-inputs.zip")
        return {"status": "prepared", "count": len(rows), "archive_sha256": file_hash(output / "private-inputs.zip")}
    except BaseException as error:
        write_json(output / "incomplete.json", {"status": "incomplete", "error_type": type(error).__name__, "finished_at": utc_now()})
        raise


def load_inputs(inputs_dir: Path, plan: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads((inputs_dir / "subset-manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["count"] != 16 or manifest["selection"] != plan["selection"]:
        raise ValueError("Incomplete or changed input selection.")
    if manifest["source"] != plan["source"] or manifest["aya_manifest_sha256"] != plan["aya_manifest_sha256"]:
        raise ValueError("Input provenance differs from the frozen source.")
    # Compare semantic canonical content, while the file hash is checked by the caller/notebook.
    if manifest["clearance"] != plan["clearance"] or manifest["benchmark_data_accessed"] is not False:
        raise ValueError("Provisional status or data boundary changed.")
    if set(manifest["outputs"]) != {"subset.jsonl", "NOTICE.md"}:
        raise ValueError("Unexpected input files.")
    for name, expected in manifest["outputs"].items():
        check_hash(inputs_dir / name, expected)
    rows = read_jsonl(inputs_dir / "subset.jsonl")
    validate_selected(rows, plan)
    return rows, manifest


def safe_extract(archive_path: Path, output: Path, allowed: set[str], maximum: int) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or not names or not set(names) <= allowed:
            raise ValueError("Archive contains duplicate or unauthorized files.")
        if sum(entry.file_size for entry in entries) > maximum:
            raise ValueError("Archive exceeds size limit.")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Unsafe archive path or symlink.")
        output.mkdir(parents=True)
        for entry in entries:
            target = output / entry.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)


def unpack(archive: Path, output: Path, plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    safe_extract(archive, output, INPUT_FILES, 2 * 1024 * 1024)
    try:
        rows, _ = load_inputs(output, load_plan(plan_path))
        check_hash(plan_path, json.loads((output / "subset-manifest.json").read_text())["plan_sha256"])
        return {"status": "verified", "count": len(rows)}
    except BaseException as error:
        write_json(output / "incomplete.json", {"status": "incomplete", "error_type": type(error).__name__})
        raise


def encode_example(row: dict[str, Any], tokenizer: Any, max_length: int = 512) -> dict[str, list[int]]:
    if tokenizer.eos_token_id != 151643:
        raise ValueError("Unexpected EOS token; vocabulary must not change.")
    prefix = f"### Panuto:\n{row['prompt']}\n\n### Sagot:\n"
    response = row["response"]
    for text in (prefix, response):
        if any(token in text for token in tokenizer.all_special_tokens):
            raise ValueError("Input contains a tokenizer control token.")
    prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
    response_ids = tokenizer.encode(response, add_special_tokens=False)
    if not response_ids:
        raise ValueError("An empty response cannot supervise training.")
    for text, ids in ((prefix, prefix_ids), (response, response_ids)):
        if tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) != text:
            raise ValueError("Tokenizer failed exact text roundtrip.")
    input_ids = prefix_ids + response_ids + [151643]
    if tokenizer.decode(input_ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False) != prefix + response:
        raise ValueError("Combined token stream failed exact text roundtrip.")
    if len(input_ids) > max_length:
        raise ValueError(f"Sequence has {len(input_ids)} tokens; limit {max_length}; truncation forbidden.")
    return {"input_ids": input_ids, "attention_mask": [1] * len(input_ids),
            "labels": [-100] * len(prefix_ids) + response_ids + [151643]}


class ResponseCollator:
    """Right-pad by length so real EOS remains a supervised target."""

    def __init__(self, pad_token_id: int = 151643) -> None:
        self.pad_token_id = pad_token_id

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        import torch
        length = max(len(row["input_ids"]) for row in features)
        batch: dict[str, list[list[int]]] = {"input_ids": [], "attention_mask": [], "labels": []}
        for row in features:
            size = len(row["input_ids"])
            if len(row["labels"]) != size or len(row["attention_mask"]) != size:
                raise ValueError("Token/label/mask length mismatch.")
            batch["input_ids"].append(row["input_ids"] + [self.pad_token_id] * (length - size))
            batch["attention_mask"].append(row["attention_mask"] + [0] * (length - size))
            batch["labels"].append(row["labels"] + [-100] * (length - size))
        return {name: torch.tensor(values, dtype=torch.long) for name, values in batch.items()}


def verify(output: Path) -> dict[str, Any]:
    manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError("Run is incomplete; training plus a fresh adapter reload are required.")
    reload_report = json.loads((output / "reload-verification.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "complete" or reload_report.get("status") != "passed":
        raise ValueError("Training/reload is incomplete; no successful smoke test can be claimed.")
    if manifest.get("configuration") != load_plan() or manifest.get("plan_sha256") != file_hash(DEFAULT_PLAN):
        raise ValueError("Result uses a different frozen configuration.")
    if manifest.get("benchmark_accessed") is not False:
        raise ValueError("Benchmark isolation not recorded.")
    for key in ("tensor_equality", "probe_finite", "probe_argmax_equal", "fresh_process"):
        if reload_report.get(key) is not True:
            raise ValueError(f"Reload verification missing: {key}")
    required = {"training-log.jsonl", "probe-reference.safetensors", "adapter-reference.json",
                "tokenizer-check.json", "adapter/adapter_model.safetensors", "adapter/adapter_config.json",
                "reload-verification.json"}
    if not required <= set(manifest.get("artifacts", {})):
        raise ValueError("Result is missing required hashed artifacts.")
    metrics = manifest.get("metrics", {})
    if metrics.get("optimizer_updates") != 20:
        raise ValueError("Manifest optimizer count differs.")
    for key in ("training_seconds", "peak_allocated_bytes", "peak_reserved_bytes"):
        value = metrics.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"Invalid measurement: {key}")
    logs = read_jsonl(output / "training-log.jsonl")
    if len(logs) != 20 or [row["step"] for row in logs] != list(range(1, 21)):
        raise ValueError("Expected exactly 20 logged optimizer updates.")
    for row in logs:
        if not isinstance(row.get("loss"), (int, float)) or not math.isfinite(row["loss"]):
            raise ValueError("Nonfinite or missing training loss.")
        if row.get("gradients_finite") is not True or row.get("microbatches") != 4:
            raise ValueError("Gradient or accumulation checks failed.")
    for name, expected in manifest.get("artifacts", {}).items():
        if name not in RESULT_FILES:
            raise ValueError("Unexpected result artifact path.")
        check_hash(output / name, expected)
    return {"status": "verified", "optimizer_updates": len(logs), "reload": reload_report}


def archive_results(output: Path, archive: Path) -> dict[str, Any]:
    names = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    names &= RESULT_FILES - {"archive-manifest.json"}
    if "run-manifest.json" not in names:
        raise ValueError("Missing run manifest; cannot package an unidentified run.")
    write_json(output / "archive-manifest.json", {"files": {name: file_hash(output / name) for name in sorted(names)}})
    deterministic_zip(output, names | {"archive-manifest.json"}, archive)
    return {"archive_sha256": file_hash(archive), "files": len(names) + 1}


def import_results(archive: Path, output: Path) -> dict[str, Any]:
    safe_extract(archive, output, RESULT_FILES, 400 * 1024 * 1024)
    ledger = json.loads((output / "archive-manifest.json").read_text(encoding="utf-8"))["files"]
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()} - {"archive-manifest.json"}
    if set(ledger) != actual:
        raise ValueError("Result archive ledger mismatch.")
    for name, expected in ledger.items():
        check_hash(output / name, expected)
    return verify(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "unpack", "preflight", "tokenize", "integration", "train", "reload", "verify", "archive", "import"))
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    os.environ.update({"HF_HUB_DISABLE_TELEMETRY": "1", "WANDB_DISABLED": "true", "TOKENIZERS_PARALLELISM": "false"})
    try:
        if args.command == "prepare":
            if args.source is None:
                parser.error("prepare requires --source")
            result = prepare(args.source, args.output, args.plan)
        elif args.command in ("unpack", "import", "archive"):
            if args.archive is None:
                parser.error("this command requires --archive")
            if args.command == "unpack":
                result = unpack(args.archive, args.output, args.plan)
            elif args.command == "import":
                result = import_results(args.archive, args.output)
            else:
                result = archive_results(args.output, args.archive)
        elif args.command == "verify":
            result = verify(args.output)
        else:
            import qlora_training
            if args.command in ("train", "tokenize"):
                if args.inputs is None:
                    parser.error("train/tokenize requires --inputs")
                function = qlora_training.train if args.command == "train" else qlora_training.tokenizer_check
                result = function(args.inputs, args.output, args.plan)
            else:
                function = {"preflight": qlora_training.preflight, "integration": qlora_training.integration_check,
                            "reload": qlora_training.reload_adapter}[args.command]
                result = function(args.output, args.plan)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

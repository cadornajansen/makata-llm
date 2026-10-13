"""Import a downloaded Colab results ZIP and verify it without requiring CUDA."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from colab.run import configuration, source_hashes, verify_artifacts
from protocol import ROOT, file_hash, write_json


def extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as source:
        if sum(item.file_size for item in source.infolist()) > 256 * 1024**2:
            raise ValueError("Result archive exceeds the 256 MiB safety limit.")
        for item in source.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Result archive contains an unsafe path.")
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.suffix not in (".json", ".jsonl", ".log"):
                raise ValueError("Result archives must contain only JSON, JSONL, and logs.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(item))


def verify_session(directory: Path) -> dict[str, Any]:
    profile = json.loads((directory / "execution-profile.json").read_text())
    if profile["source_sha256"] != source_hashes():
        raise RuntimeError("Archived source differs from this checkout; retain the original notebook snapshot.")
    profile_hash = hashlib.sha256(json.dumps(profile, sort_keys=True, allow_nan=False).encode()).hexdigest()
    verified = []
    for index in (0, 1):
        marker = directory / f"baseline-{index}.json"
        if not marker.exists():
            continue
        # Preserve original remote paths; resolve their final directory names locally.
        target = directory / Path(json.loads(marker.read_text())["directory"]).name
        manifest = verify_artifacts(target, 900, configuration(index, "evaluate"))
        if manifest["execution_profile"] != profile or manifest["execution_profile_sha256"] != profile_hash:
            raise RuntimeError("Run execution profile does not match the frozen session profile.")
        samples = [json.loads(line) for line in (target / "samples.jsonl").read_text().splitlines()]
        correct = sum(row["accuracy"] for row in samples)
        verified.append({
            "model": manifest["configuration"]["model"], "directory": str(target),
            "samples": 900, "correct": int(correct), "accuracy": correct / 900,
            "runtime_seconds": manifest["runtime_seconds"], "inference_seconds": manifest["inference_seconds"],
            "maximum_input_tokens": manifest["maximum_input_tokens"],
            "peak_gpu_allocated_bytes": manifest["hardware"]["peak_gpu_allocated_bytes"],
            "samples_sha256": manifest["samples_sha256"],
        })
    return {"status": "complete" if len(verified) == 2 else "incomplete",
            "gpu": profile["gpu"], "execution_profile_sha256": profile_hash, "baselines": verified}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        parser.error("Use Python's UTF-8 mode on Windows: python -X utf8 research/colab/import_results.py ARCHIVE.zip")
    directory = ROOT / "runs" / f"colab-import-{uuid.uuid4().hex[:12]}"
    directory.mkdir(parents=True)
    report: dict[str, Any] = {"status": "incomplete", "archive_sha256": file_hash(args.archive)}
    try:
        extract(args.archive, directory)
        report.update(verify_session(directory))
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        write_json(directory / "verification.json", report)
    print(json.dumps(report, indent=2))
    print(f"Local evidence: {directory}")
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

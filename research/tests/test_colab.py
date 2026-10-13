"""Offline checks of notebook packaging and free-GPU execution safeguards."""

from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("colab_run", ROOT / "colab/run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

from protocol import PILOT_MODEL, file_hash, write_json


class ColabTests(unittest.TestCase):
    def test_gpu_configuration_preserves_pins_and_float32(self) -> None:
        for index in (0, 1):
            config = runner.configuration(index, "pilot")
            self.assertEqual((config.device, config.dtype, config.threads), ("cuda", "float32", 4))
            self.assertNotEqual(config.model, PILOT_MODEL)
            self.assertEqual(config.model_revision, config.tokenizer_revision)

    def test_changed_sources_reject_frozen_profile_before_cuda(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_json(path / "execution-profile.json", {"source_sha256": {"old": "source"}})
            with self.assertRaisesRegex(RuntimeError, "Source/plan changed"):
                runner.validate_profile(path)

    def test_missing_cuda_stops_freeze_without_writing_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("torch.cuda.is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "no CPU fallback"):
                runner.freeze(Path(directory))
            self.assertFalse((Path(directory) / "execution-profile.json").exists())

    def test_saved_sample_integrity_and_prediction_are_checked(self) -> None:
        config = runner.configuration(0, "pilot")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            rows = [{"sample_id": f"dev-{index}", "choice_log_likelihoods": [-0.1, -2, -3, -4],
                     "gold_index": 0, "predicted_index": 0, "accuracy": 1,
                     "official_detail": {"truncated": [0], "num_asked_few_shots": 0,
                                         "num_effective_few_shots": 0}} for index in range(20)]
            sample_path = path / "samples.jsonl"
            sample_path.write_text("\n".join(json.dumps(row) for row in rows))
            manifest = {"status": "complete", "sample_count": 20, "configuration": asdict(config),
                        "samples_sha256": file_hash(sample_path), "code_sha256": {},
                        "baseline_plan_sha256": file_hash(ROOT / "baseline-plan.json")}
            write_json(path / "manifest.json", manifest)
            write_json(path / "metrics.json", {"official_task_metrics": {"pilot": {"acc": 1}}})
            runner.verify_artifacts(path, 20, config)
            sample_path.write_text("modified")
            with self.assertRaises((RuntimeError, json.JSONDecodeError)):
                runner.verify_artifacts(path, 20, config)

    def test_notebook_cells_and_allowlisted_payload(self) -> None:
        path = ROOT / "colab/makata-baselines.ipynb"
        if not path.exists():
            self.skipTest("Packaging is verified locally; exported runtime contains source instead of the notebook itself.")
        notebook = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(notebook["nbformat"], 4)
        payload = None
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            self.assertEqual(cell["outputs"], [])
            tree = ast.parse("".join(cell["source"]))
            for item in tree.body:
                if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name) and item.targets[0].id == "PAYLOAD":
                    payload = base64.b64decode(ast.literal_eval(item.value))
        self.assertIsNotNone(payload)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), notebook["metadata"]["makata"]["bundle_sha256"])
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            manifest = json.loads(archive.read("bundle-manifest.json"))
            for name, digest in manifest["files_sha256"].items():
                self.assertNotIn(".cache/", name)
                self.assertNotIn("runs/", name)
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                self.assertEqual(file_hash(ROOT.parent / name), digest)


if __name__ == "__main__":
    unittest.main()

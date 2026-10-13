"""Offline safeguards for the single frozen post-training evaluation."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import post_training as subject


def row(number: int, correct: bool, passage: str = "Isang talata.") -> dict:
    prompt = f"{passage}\nTanong: Tanong {number}?\n A. Oo\n B. Hindi\n C. Iba\n D. Wala\nSagot:"
    return {"prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "gold_index": 0,
            "accuracy": float(correct), "predicted_index": 0 if correct else 1,
            "official_detail": {"example": prompt, "full_prompt": prompt, "input_tokens": [[1, number]],
                                "cont_tokens": [[2]], "gold_index": [0], "choices": ["A", "B", "C", "D"],
                                "instruction": ""}}


class PostTrainingTests(unittest.TestCase):
    def test_frozen_scope_and_historical_source(self) -> None:
        plan = subject.load_plan()
        self.assertEqual(plan["checkpoint"], 91)
        self.assertEqual(plan["configuration"]["dtype"], "float32")
        self.assertEqual(plan["protocol"]["batch_size"], 1)
        with patch.object(subject, "file_hash", return_value="changed"):
            with self.assertRaisesRegex(ValueError, "Historical source"):
                subject.load_plan()

    def test_paired_counts_and_reordering(self) -> None:
        base = [row(i, i < 2, "Talata A." if i < 2 else "Talata B.") for i in range(4)]
        adapted = [row(i, i in (0, 2), "Talata A." if i < 2 else "Talata B.") for i in range(4)]
        result = subject.paired_comparison(base, adapted, 1000)
        self.assertEqual(result["paired_counts"], {"both_correct": 1, "improved": 1, "regressed": 1, "both_wrong": 1})
        self.assertEqual(result["difference_percentage_points"], 0)
        self.assertEqual(result["passage_clusters"], 2)
        self.assertEqual(result, subject.paired_comparison(list(reversed(base)), list(reversed(adapted)), 1000))

    def test_cluster_interval_deterministic_and_degenerate(self) -> None:
        base = [row(i, False, f"Talata {i}.") for i in range(3)]
        adapted = [row(i, True, f"Talata {i}.") for i in range(3)]
        result = subject.paired_comparison(base, adapted, 100)
        self.assertEqual(result["uncertainty"]["difference_interval_percentage_points"], [100, 100])
        self.assertEqual(subject.passage_key(row(1, True)), subject.passage_key(row(2, False)))

    def test_pair_mismatch_and_tokenization_rejected(self) -> None:
        base = [row(1, True)]
        for field in ("input_tokens", "cont_tokens", "gold_index", "choices", "instruction", "full_prompt"):
            adapted = copy.deepcopy(base)
            adapted[0]["official_detail"][field] = "changed"
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.paired_comparison(base, adapted, 10)
        with self.assertRaises(ValueError):
            subject.paired_comparison(base, [row(2, True)], 10)
        with self.assertRaises(ValueError):
            subject.paired_comparison(base * 2, base * 2, 10)

    def test_archive_allowlist_duplicates_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as stream:
                stream.writestr("../private", "bad")
            with self.assertRaises(ValueError):
                subject.extract(archive, root / "output", subject.INPUT_FILES, 100)
            self.assertFalse((root / "output").exists())
            archive.unlink()
            with zipfile.ZipFile(archive, "w") as stream:
                stream.writestr("provenance.json", "{}")
            subject.extract(archive, root / "output", subject.INPUT_FILES, 100)
            with self.assertRaises(FileExistsError):
                subject.extract(archive, root / "output", subject.INPUT_FILES, 100)

    def test_input_tampering_and_no_dataset_upload(self) -> None:
        plan = subject.load_plan()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "adapter").mkdir()
            for name in plan["adapter_sha256"]:
                (root / "adapter" / name).write_text("altered")
            subject.write_json(root / "provenance.json", {
                "checkpoint": 91, "plan_sha256": subject.file_hash(subject.PLAN),
                "training_manifest_sha256": plan["training_manifest_sha256"],
                "training_verification_sha256": plan["training_verification_sha256"],
                "contains_training_or_evaluation_text": False})
            with self.assertRaisesRegex(ValueError, "Checksum"):
                subject.verify_inputs(root)
            (root / "train.jsonl").write_text("not allowed")
            with self.assertRaisesRegex(ValueError, "Only adapter"):
                subject.verify_inputs(root)

    def test_separate_environment_preserves_all_baseline_pins(self) -> None:
        baseline = (subject.ROOT / "requirements-colab.txt").read_text()
        changed = (subject.ROOT / "requirements-post-training-colab.txt").read_text()
        self.assertTrue(changed.startswith(baseline))
        self.assertIn("peft==0.16.0", changed)

    def test_benchmark_attempt_guard_before_model_or_dataset_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subject.write_json(root / "profile.json", {"source_sha256": subject.source_hashes(), "plan": subject.load_plan()})
            subject.write_json(root / "attempt.json", {"status": "incomplete"})
            with patch.object(subject, "verify_inputs"), patch.object(subject.evaluate, "load_model") as loader:
                with self.assertRaisesRegex(RuntimeError, "already attempted"):
                    subject.execute(root, root)
                loader.assert_not_called()

    def test_notebook_packaging_if_present(self) -> None:
        path = subject.ROOT / "colab/makata-post-training.ipynb"
        if not path.exists():
            self.skipTest("Notebook not packaged in exported source.")
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])
                compile("".join(cell["source"]), "notebook", "exec")


if __name__ == "__main__":
    unittest.main()

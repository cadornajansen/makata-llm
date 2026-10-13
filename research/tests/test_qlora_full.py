"""Offline full-run safeguards. Synthetic tensors only; no benchmark/model downloads."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import qlora_full as full
import qlora_full_runtime as runtime
from qlora_smoke import file_hash, json_bytes, read_jsonl, safe_extract, write_json


class FullRunTests(unittest.TestCase):
    def test_authorization_keeps_proposal_and_scope(self) -> None:
        plan = full.load_plan()
        self.assertEqual(len(plan["selection"]), 363)
        self.assertFalse(plan["training_authorized"])  # Historical proposal is unchanged.
        self.assertEqual(plan["training"]["expected_optimizer_updates"], 91)
        self.assertEqual(plan["checkpoints"]["save_after_updates"], [50, 91])
        self.assertEqual(sum(s["review_basis"] == "automated_screening_only" for s in plan["selection"]), 283)

    def test_changed_proposal_or_paid_authorization_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            changed = root / "changed.json"
            changed.write_text("{}")
            with patch.object(full, "PROPOSAL", changed), self.assertRaises(ValueError):
                full.load_plan()
            auth = json.loads(full.AUTHORIZATION.read_text())
            auth["paid_compute_authorized"] = True
            write_json(changed, auth)
            with patch.object(full, "AUTHORIZATION", changed), self.assertRaises(ValueError):
                full.load_plan()

    def test_single_epoch_windows_remainder_and_unique_coverage(self) -> None:
        windows = runtime.accumulation_windows(list(range(363)), 4)
        self.assertEqual(len(windows), 91)
        self.assertEqual([len(w) for w in windows], [4] * 90 + [3])
        self.assertEqual([i for w in windows for i in w], list(range(363)))
        for order, size in (([], 4), ([1, 1], 4), ([1], 0)):
            with self.assertRaises(ValueError):
                runtime.accumulation_windows(order, size)

    def test_partial_window_gradients_are_averaged_over_three(self) -> None:
        import torch
        from types import SimpleNamespace

        class TinyModel(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.lora_weight = torch.nn.Parameter(torch.tensor(0.0))

            def forward(self, input_ids: torch.Tensor, **_kwargs: object) -> SimpleNamespace:
                return SimpleNamespace(loss=(self.lora_weight - input_ids[0, 0].float()) ** 2)

        plan = copy.deepcopy(full.load_plan())
        plan["training"].update(expected_optimizer_updates=2, max_grad_norm=1000)
        plan["checkpoints"]["save_after_updates"] = []
        rows = [{"input_ids": [i, 151643], "attention_mask": [1, 1], "labels": [-100, 151643]} for i in range(1, 8)]
        with tempfile.TemporaryDirectory() as temporary, patch("sys.stdout", io.StringIO()):
            output = Path(temporary)
            result = runtime.checked_epoch(TinyModel(), rows, [str(i) for i in range(7)], output, plan, False)
            logs = read_jsonl(output / "training-log.jsonl")
            final_indices = [int(i) for i in logs[-1]["ids"]]
            # First optimizer LR is zero, so w remains zero. MSE derivative is -2*x.
            expected_norm = 2 * sum(i + 1 for i in final_indices) / 3
            self.assertAlmostEqual(logs[-1]["gradient_norm_before_clipping"], expected_norm, places=5)
            self.assertEqual(result["optimizer_updates"], 2)
            self.assertEqual(logs[-1]["microbatches"], 3)

    def test_base_parameters_are_not_trainable(self) -> None:
        import torch
        with self.assertRaises(RuntimeError):
            runtime.trainable_parameters(torch.nn.Linear(2, 2))

    def test_checkpoint_integrity_and_safe_optimizer_state(self) -> None:
        import torch
        from safetensors.torch import save_file
        from qlora_training import tensor_digest
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = {"model.lora_A.weight": torch.ones((2, 2))}
            save_file(state, str(root / "adapter_model.safetensors"))
            write_json(root / "adapter_config.json", {"r": 16, "base_model_name_or_path": "Qwen/Qwen3-1.7B-Base"})
            torch.save({"step": 91, "examples_consumed": 363, "order": list(range(363)),
                        "scheduler": {"last_epoch": 91}, "optimizer": {"state": {0: {
                            "step": torch.tensor(91.), "exp_avg": torch.ones((2, 2)), "exp_avg_sq": torch.ones((2, 2))}}}}, root / "training-state.pt")
            report = {"step": 91, "examples_consumed": 363, "proposal_sha256": full.PROPOSAL_SHA,
                      "tensor_sha256": tensor_digest(state), "files": {p.name: file_hash(p) for p in root.iterdir()}}
            write_json(root / "checkpoint-manifest.json", report)
            full.verify_checkpoint(root, 91)
            (root / "adapter_model.safetensors").write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                full.verify_checkpoint(root, 91)

    def test_archive_excludes_inputs_and_rejects_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "run"
            output.mkdir()
            write_json(output / "run-manifest.json", {"status": "incomplete"})
            (output / "train.jsonl").write_text("must not export raw examples")
            archive = root / "result.zip"
            full.archive_results(output, archive)
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(set(z.namelist()), {"run-manifest.json", "archive-manifest.json"})
            bad = root / "bad.zip"
            with zipfile.ZipFile(bad, "w") as z:
                z.writestr("../outside", "bad")
            with self.assertRaises(ValueError):
                safe_extract(bad, root / "extract", full.RESULT_FILES, 1000)
            with self.assertRaises(FileExistsError):
                full.archive_results(output, archive)

    def test_incomplete_cannot_be_verified_or_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(root / "run-manifest.json", {"status": "incomplete"})
            with self.assertRaises(ValueError):
                full.verify(root)
            with self.assertRaises(FileExistsError):
                runtime.train(root, root)

    def test_no_benchmark_imports_or_evaluation_upload(self) -> None:
        import ast
        for module in (full, runtime):
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertTrue(imports.isdisjoint({"evaluate", "protocol", "datasets"}))
        self.assertEqual(full.INPUT_FILES, {"train.jsonl", "validation.jsonl", "NOTICE.md", "input-manifest.json"})


if __name__ == "__main__":
    unittest.main()

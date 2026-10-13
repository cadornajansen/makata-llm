"""Offline engineering checks with invented text; no benchmark or model downloads."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import qlora_smoke as smoke


class CharacterTokenizer:
    eos_token_id = 151643
    all_special_tokens = ["<|endoftext|>"]

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        if add_special_tokens:
            raise AssertionError("No implicit chat/control tokens allowed.")
        return [ord(c) for c in text]

    def decode(self, tokens: list[int], **kwargs: object) -> str:
        return "".join(chr(n) for n in tokens)


class QLoRASmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.plan = copy.deepcopy(smoke.load_plan())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def synthetic_source(self) -> Path:
        source = self.root / "source"
        source.mkdir()
        rows, reviews, dispositions = [], [], []
        for selected in self.plan["selection"]:
            row = {"id": selected["id"], "prompt": f"Test instruction {selected['id']}", "response": "Invented answer.",
                   "assigned_split": "train", "group_id": selected["group_id"],
                   "provenance": {**{k: self.plan["source"][k] for k in ("repository", "revision", "file", "license_declaration")},
                                  "language": "fil", "source_split": "train", "dataset_name": "Aya-Dataset"}}
            row["content_sha256"] = smoke.content_hash(row)
            selected["content_sha256"] = row["content_sha256"]
            rows.append(row)
            reviews.append({"id": row["id"], "content_sha256": row["content_sha256"], "reviewer_type": "agent", "disposition": "accept"})
            dispositions.append({"id": row["id"], "group_id": row["group_id"], "content_sha256": row["content_sha256"],
                                 "disposition": "provisional_candidate", "quality_flags": []})
        for name, records in (("train.jsonl", rows), ("dispositions.jsonl", dispositions),
                              ("review-decisions.jsonl", reviews), ("prior-review-decisions.jsonl", [])):
            (source / name).write_bytes(b"".join(smoke.json_bytes(r) for r in records))
        (source / "NOTICE.md").write_text("Synthetic fixture; no source dataset text.")
        smoke.write_json(source / "manifest.json", {"status": "complete", "source": self.plan["source"]})
        self.repin(source)
        return source

    def repin(self, source: Path) -> None:
        self.plan["aya_manifest_sha256"] = smoke.file_hash(source / "manifest.json")
        for name in self.plan["aya_files"]:
            self.plan["aya_files"][name] = smoke.file_hash(source / name)

    def test_authorized_plan_is_narrow(self) -> None:
        for key, value in (("max_steps", 21), ("max_length", 1024), ("seed", 42)):
            plan = copy.deepcopy(self.plan)
            plan["training"][key] = value
            path = self.root / "plan.json"
            smoke.write_json(path, plan)
            with self.assertRaises(ValueError):
                smoke.load_plan(path)

    def test_model_and_source_revision_enforced(self) -> None:
        for section, key in (("model", "revision"), ("model", "tokenizer_revision"), ("source", "revision")):
            plan = copy.deepcopy(self.plan)
            plan[section][key] = "a" * 40
            path = self.root / "plan.json"
            smoke.write_json(path, plan)
            with self.assertRaises(ValueError):
                smoke.load_plan(path)

    def test_selection_and_agent_review(self) -> None:
        source = self.synthetic_source()
        self.assertEqual(len(smoke.select_eligible(source, self.plan)), 16)
        (source / "prior-review-decisions.jsonl").write_bytes(smoke.json_bytes({"id": smoke.SELECTED_IDS[0], "disposition": "hold"}))
        self.repin(source)
        with self.assertRaisesRegex(ValueError, "hold"):
            smoke.select_eligible(source, self.plan)

    def test_group_member_quality_blocks_selection(self) -> None:
        source = self.synthetic_source()
        with (source / "dispositions.jsonl").open("ab") as stream:
            stream.write(smoke.json_bytes({"id": "not-selected", "group_id": self.plan["selection"][0]["group_id"],
                                          "quality_flags": ["third_party_creative_text"], "disposition": "quarantine"}))
        self.repin(source)
        with self.assertRaisesRegex(ValueError, "quality"):
            smoke.select_eligible(source, self.plan)

    def test_tampered_source_fails_before_export(self) -> None:
        source = self.synthetic_source()
        with (source / "train.jsonl").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "Checksum"):
            smoke.select_eligible(source, self.plan)

    def test_changed_text_fails_even_if_file_hash_replaced(self) -> None:
        source = self.synthetic_source()
        rows = smoke.read_jsonl(source / "train.jsonl")
        rows[0]["response"] = "Altered"
        (source / "train.jsonl").write_bytes(b"".join(smoke.json_bytes(r) for r in rows))
        self.repin(source)
        with self.assertRaisesRegex(ValueError, "Changed text"):
            smoke.select_eligible(source, self.plan)

    def test_no_validation_records(self) -> None:
        source = self.synthetic_source()
        rows = smoke.read_jsonl(source / "train.jsonl")
        rows[0]["assigned_split"] = "validation"
        with self.assertRaises(ValueError):
            smoke.validate_selected(rows, self.plan)

    def test_preparation_determinism_no_benchmark_reads(self) -> None:
        source = self.synthetic_source()
        plan_path = self.root / "fixture-plan.json"
        smoke.write_json(plan_path, self.plan)
        original_open = Path.open
        accessed: list[str] = []

        def guarded_open(path: Path, *args: object, **kwargs: object):
            accessed.append(path.name)
            if "benchmark" in path.name or path.name in ("validation.jsonl", "quarantine.jsonl", "samples.jsonl"):
                raise AssertionError("Forbidden data access")
            return original_open(path, *args, **kwargs)

        with patch.object(smoke, "load_plan", return_value=self.plan), patch.object(Path, "open", guarded_open):
            for name in ("a", "b"):
                smoke.prepare(source, self.root / name, plan_path)
        self.assertEqual(smoke.file_hash(self.root / "a/private-inputs.zip"), smoke.file_hash(self.root / "b/private-inputs.zip"))
        self.assertNotIn("samples.jsonl", accessed)
        with zipfile.ZipFile(self.root / "a/private-inputs.zip") as bundle:
            self.assertEqual(set(bundle.namelist()), smoke.INPUT_FILES)

    def test_failure_manifest_and_overwrite_protection(self) -> None:
        source = self.synthetic_source()
        output = self.root / "failed"
        with patch.object(smoke, "load_plan", side_effect=ValueError("test")), self.assertRaises(ValueError):
            smoke.prepare(source, output)
        self.assertEqual(json.loads((output / "incomplete.json").read_text())["status"], "incomplete")
        with self.assertRaises(FileExistsError):
            smoke.prepare(source, output)

    def test_response_mask_and_eos(self) -> None:
        row = smoke.encode_example({"prompt": "Tanong", "response": "Sagot"}, CharacterTokenizer())
        prefix = "### Panuto:\nTanong\n\n### Sagot:\n"
        self.assertEqual(row["labels"][:len(prefix)], [-100] * len(prefix))
        self.assertEqual(row["labels"][len(prefix):], [ord(c) for c in "Sagot"] + [151643])
        self.assertEqual(row["input_ids"][-1], 151643)

    def test_padding_does_not_mask_real_eos(self) -> None:
        rows = [smoke.encode_example({"prompt": "x", "response": answer}, CharacterTokenizer()) for answer in ("a", "abcd")]
        batch = smoke.ResponseCollator()(rows)
        eos_index = len(rows[0]["input_ids"]) - 1
        self.assertEqual(batch["labels"][0, eos_index].item(), 151643)
        self.assertTrue((batch["labels"][0, eos_index + 1:] == -100).all())
        self.assertTrue((batch["attention_mask"][0, eos_index + 1:] == 0).all())

    def test_no_truncation_control_tokens_or_empty_response(self) -> None:
        for response in ("x" * 513, "<|endoftext|>", ""):
            with self.assertRaises(ValueError):
                smoke.encode_example({"prompt": "x", "response": response}, CharacterTokenizer())

    def test_archive_paths_duplicates_and_limits(self) -> None:
        for index, names in enumerate((("../subset.jsonl",), ("subset.jsonl", "subset.jsonl"), ("weights.bin",))):
            archive = self.root / f"bad{index}.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                for name in names:
                    bundle.writestr(name, "{}")
            with self.assertRaises(ValueError):
                smoke.safe_extract(archive, self.root / f"out{index}", smoke.INPUT_FILES, 100)
        archive = self.root / "large.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("subset.jsonl", "a" * 200)
        with self.assertRaises(ValueError):
            smoke.safe_extract(archive, self.root / "large", smoke.INPUT_FILES, 100)

    def test_incomplete_run_cannot_pass_verification(self) -> None:
        smoke.write_json(self.root / "run-manifest.json", {"status": "pending_reload"})
        smoke.write_json(self.root / "reload-verification.json", {"status": "passed"})
        with self.assertRaises(ValueError):
            smoke.verify(self.root)

    def test_training_code_has_no_benchmark_loader(self) -> None:
        import ast
        for name in ("qlora_smoke.py", "qlora_training.py"):
            tree = ast.parse((smoke.ROOT / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, ("evaluate", "protocol", "prepare_dataset"))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotEqual(node.func.id, "load_dataset")


if __name__ == "__main__":
    unittest.main()

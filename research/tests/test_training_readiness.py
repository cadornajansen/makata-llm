"""Offline planning safeguards with synthetic records, never benchmark examples."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_training_readiness as prep
from qlora_smoke import content_hash, file_hash, json_bytes


def example() -> tuple[dict, dict, dict]:
    row = {"id": "synthetic-1", "prompt": "Synthetic task", "response": "Synthetic answer",
           "assigned_split": "train", "group_id": "group-one"}
    row["content_sha256"] = content_hash(row)
    disposition = {**row, "disposition": "provisional_candidate", "quality_flags": []}
    selection = {k: row[k] for k in ("id", "group_id", "content_sha256")}
    selection.update(reviewer_type="agent", rationale="Synthetic review only")
    return row, disposition, selection


def evaluation() -> list[dict]:
    return [{"id": f"eval-{c}-{n}", "category": c, "prompt": f"{c}{n}",
             "reference_answer": "Synthetic reference", "content_criteria": "Correct content",
             "format_criteria": "Requested format", "author_type": "agent",
             "human_review_status": "pending",
             "provenance": "Newly agent-authored for Makata; no external passage copied."}
            for c in sorted(prep.CATEGORIES) for n in range(4)]


class TrainingReadinessTests(unittest.TestCase):
    def test_screening_only_requires_explicit_policy_and_honest_label(self) -> None:
        row, disposition, selected = example()
        selected.update(reviewer_type="screening", review_basis="automated_screening_only")
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [], [selected])
        self.assertEqual(prep.select_rows([row], [disposition], [], [selected], True), [row])
        selected["review_basis"] = "human_review"
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [], [selected], True)

    def test_prior_acceptance_must_match_hash_and_reviewer(self) -> None:
        row, disposition, selected = example()
        selected["review_basis"] = "prior_agent_review"
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [], [selected], True)
        review = {"id": row["id"], "content_sha256": row["content_sha256"],
                  "reviewer_type": "agent", "disposition": "accept"}
        self.assertEqual(prep.select_rows([row], [disposition], [review], [selected], True), [row])
        review["content_sha256"] = "stale"
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [review], [selected], True)

    def test_update_count_preserves_final_partial_accumulation(self) -> None:
        self.assertEqual(prep.optimizer_updates(363, 1, 4, 1), 91)
        self.assertEqual(prep.optimizer_updates(24, 1, 4, 1), 6)
        self.assertEqual(prep.optimizer_updates(363, 1, 4, 2), 182)
        with self.assertRaises(ValueError):
            prep.optimizer_updates(0, 1, 4, 1)

    def test_risk_review_cannot_override_group_flags_or_holds(self) -> None:
        row, _, selection = example()
        selection.update(review_basis="current_risk_sample", human_validated=False)
        observation = {"id": row["id"], "content_sha256": row["content_sha256"],
                       "reviewer_type": "agent", "human_approval": False, "disposition": "provisional_retain"}
        plan = {"selection": [selection], "risk_review": {"sample_count": 1, "new_holds": 0}}
        ledger = {"observations": [observation], "sample_ids": [row["id"]],
                  "all_record_flags": {row["id"]: []}, "group_flags": {row["group_id"]: []}}
        prep.validate_risk_review(plan, ledger, [row])
        for field, key in (("all_record_flags", row["id"]), ("group_flags", row["group_id"])):
            changed = copy.deepcopy(ledger)
            changed[field][key] = ["unresolved_copyright"]
            with self.assertRaises(ValueError):
                prep.validate_risk_review(plan, changed, [row])
        observation["disposition"] = "hold"
        plan["risk_review"]["new_holds"] = 1
        with self.assertRaises(ValueError):
            prep.validate_risk_review(plan, ledger, [row])

    def test_risk_review_rejects_stale_hash_or_false_human_status(self) -> None:
        row, _, selection = example()
        selection.update(review_basis="current_risk_sample", human_validated=False)
        observation = {"id": row["id"], "content_sha256": "stale", "reviewer_type": "agent",
                       "human_approval": False, "disposition": "provisional_retain"}
        plan = {"selection": [selection], "risk_review": {"sample_count": 1, "new_holds": 0}}
        ledger = {"observations": [observation], "sample_ids": [row["id"]],
                  "all_record_flags": {row["id"]: []}, "group_flags": {row["group_id"]: []}}
        with self.assertRaises(ValueError):
            prep.validate_risk_review(plan, ledger, [row])
        observation["content_sha256"] = row["content_sha256"]
        observation["human_approval"] = True
        with self.assertRaises(ValueError):
            prep.validate_risk_review(plan, ledger, [row])

    def test_validation_review_holds_are_not_loss_candidates(self) -> None:
        row, _, _ = example()
        row["assigned_split"] = "validation"
        other = {**row, "id": "other", "group_id": "other-group"}
        plan = {"validation": {"source_count": 2, "provisional_loss_count": 1, "eligible_ids": [row["id"]]}}
        ledger = {"all_record_flags": {row["id"]: [], other["id"]: ["quality_hold"]},
                  "group_flags": {row["group_id"]: [], other["group_id"]: ["quality_hold"]}}
        decisions = prep.validation_reviews([row, other], plan, ledger)
        self.assertEqual([d["proposed_disposition"] for d in decisions], ["provisional_loss_candidate", "hold"])
        self.assertTrue(all(d["human_review_status"] == "pending" for d in decisions))
        plan["validation"].update(eligible_ids=[row["id"], other["id"]], provisional_loss_count=2)
        with self.assertRaises(ValueError):
            prep.validation_reviews([row, other], plan, ledger)

    def test_selection_retains_text_and_group(self) -> None:
        row, disposition, selected = example()
        self.assertEqual(prep.select_rows([row], [disposition], [], [selected]), [row])

    def test_revised_packet_is_deterministic_and_private_review_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            row, disposition, selected = example()
            selected.update(reviewer_type="screening", review_basis="automated_screening_only", human_validated=False)
            validation = {**row, "id": "validation-1", "group_id": "validation-group", "assigned_split": "validation"}
            data = {"train.jsonl": [row], "validation.jsonl": [validation], "dispositions.jsonl": [disposition],
                    "review-decisions.jsonl": [], "prior-review-decisions.jsonl": []}
            for name, rows in data.items():
                (source / name).write_bytes(b"".join(json_bytes(r) for r in rows))
            (source / "NOTICE.md").write_text("Synthetic attribution", encoding="utf-8")
            eval_file = root / "eval.jsonl"
            eval_file.write_bytes(b"".join(json_bytes(r) for r in evaluation()))
            ledger = {"observations": [], "sample_ids": [],
                      "all_record_flags": {row["id"]: [], validation["id"]: []},
                      "group_flags": {row["group_id"]: [], validation["group_id"]: []}}
            risk = root / "risk.json"
            risk.write_bytes(json_bytes(ledger))
            plan = {"approval_status": "pending", "training_authorized": False,
                    "source_files": {p.name: file_hash(p) for p in source.iterdir()},
                    "preserved_smoke_files": {}, "evaluation": {"draft_sha256": file_hash(eval_file)},
                    "selection": [selected], "risk_review": {"file": str(risk), "sha256": file_hash(risk),
                        "sample_count": 0, "new_holds": 0, "review_every_training_item_required": False},
                    "training": {"epochs": 1, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 4,
                                 "drop_last": False, "expected_optimizer_updates": 1},
                    "validation": {"source_count": 1, "provisional_loss_count": 1, "eligible_ids": [validation["id"]]}}
            plan_file = root / "plan.json"
            plan_file.write_bytes(json_bytes(plan))
            with patch.object(prep, "PLAN", plan_file):
                first = prep.prepare(source, eval_file, root / "one")
                second = prep.prepare(source, eval_file, root / "two")
                self.assertEqual(first, second)
                self.assertEqual(first["training_review_basis"], {"automated_screening_only": 1})
                template = prep.read_jsonl(root / "one" / "human-review-template.jsonl")
                self.assertEqual(len(template), 33)
                self.assertEqual({r["role"] for r in template}, {"validation", "evaluation"})
                self.assertEqual((root / "one" / "validation-candidates.jsonl").read_bytes(),
                                 (source / "validation.jsonl").read_bytes())
                risk.write_text("tampered", encoding="utf-8")
                with self.assertRaises(ValueError):
                    prep.prepare(source, eval_file, root / "three")

    def test_tampering_or_validation_record_fails(self) -> None:
        for key, value in (("response", "altered"), ("assigned_split", "validation"), ("group_id", "other")):
            row, disposition, selected = example()
            row[key] = value
            with self.assertRaises(ValueError):
                prep.select_rows([row], [disposition], [], [selected])

    def test_group_quality_hold_and_rejection_block(self) -> None:
        row, disposition, selected = example()
        for extra in ({**disposition, "id": "sibling", "quality_flags": ["copyright"]},
                      {**disposition, "id": "sibling", "disposition": "quarantine"}):
            with self.assertRaises(ValueError):
                prep.select_rows([row], [disposition, extra], [], [selected])
        for decision in ("hold", "reject"):
            with self.assertRaises(ValueError):
                prep.select_rows([row], [disposition], [{"id": row["id"], "disposition": decision}], [selected])

    def test_one_per_group_and_unique_ids(self) -> None:
        row, disposition, selected = example()
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [], [selected, selected])
        sibling = {**row, "id": "synthetic-2"}
        with self.assertRaises(ValueError):
            prep.select_rows([row, sibling], [disposition, {**disposition, "id": sibling["id"]}], [],
                             [selected, {**selected, "id": sibling["id"]}])

    def test_missing_review_or_disposition_fails(self) -> None:
        row, disposition, selected = example()
        with self.assertRaises(ValueError):
            prep.select_rows([row], [], [], [selected])
        selected["reviewer_type"] = "human"
        with self.assertRaises(ValueError):
            prep.select_rows([row], [disposition], [], [selected])

    def test_overlap_normalization_spans_and_near_match(self) -> None:
        self.assertTrue(prep.overlap("HALO, mundo!", "halo mundo"))
        span = " ".join(f"word{n}" for n in range(12))
        self.assertTrue(prep.overlap("prefix " + span, span + " suffix"))
        self.assertTrue(prep.overlap("one two three four five six", "one two three four five six seven"))
        self.assertFalse(prep.overlap("isang bagay", "isang ibang bagay"))

    def test_evaluation_count_categories_and_review_status(self) -> None:
        rows = evaluation()
        prep.validate_evaluation(rows)
        for changed in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                prep.validate_evaluation(changed)
        rows[0]["human_review_status"] = "validated"
        with self.assertRaises(ValueError):
            prep.validate_evaluation(rows)

    def test_evaluation_leakage_and_duplicates_fail(self) -> None:
        rows = evaluation()
        with self.assertRaises(ValueError):
            prep.screen_evaluation(rows, [{"id": "train", "prompt": rows[0]["prompt"], "response": "other"}])
        rows[1]["prompt"] = rows[0]["prompt"]
        with self.assertRaises(ValueError):
            prep.screen_evaluation(rows, [])

    def test_deterministic_outputs_tamper_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            row, disposition, selection = example()
            data = {"train.jsonl": [row], "validation.jsonl": [], "dispositions.jsonl": [disposition],
                    "review-decisions.jsonl": [], "prior-review-decisions.jsonl": []}
            for name, rows in data.items():
                (source / name).write_bytes(b"".join(json_bytes(r) for r in rows))
            (source / "NOTICE.md").write_text("Synthetic attribution", encoding="utf-8")
            eval_file = root / "evaluation.jsonl"
            eval_file.write_bytes(b"".join(json_bytes(r) for r in evaluation()))
            plan = {"approval_status": "pending", "training_authorized": False,
                    "source_files": {p.name: file_hash(p) for p in source.iterdir()},
                    "preserved_smoke_files": {}, "evaluation": {"draft_sha256": file_hash(eval_file)},
                    "selection": [selection]}
            plan_file = root / "plan.json"
            plan_file.write_bytes(json_bytes(plan))
            with patch.object(prep, "PLAN", plan_file):
                first = prep.prepare(source, eval_file, root / "one")
                second = prep.prepare(source, eval_file, root / "two")
                self.assertEqual(first, second)
                self.assertFalse(first["training_authorized"])
                self.assertFalse(first["model_inference_performed"])
                self.assertEqual(first["training_count"], 1)
                with self.assertRaises(FileExistsError):
                    prep.prepare(source, eval_file, root / "one")
                eval_file.write_text("tampered", encoding="utf-8")
                with self.assertRaises(ValueError):
                    prep.prepare(source, eval_file, root / "three")

    def test_no_training_or_benchmark_entrypoint(self) -> None:
        import ast
        tree = ast.parse(Path(prep.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertTrue(imports.isdisjoint({"evaluate", "protocol", "datasets", "qlora_training", "transformers"}))
        self.assertFalse(hasattr(prep, "train"))


if __name__ == "__main__":
    unittest.main()

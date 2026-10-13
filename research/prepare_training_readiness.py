"""Prepare approval materials only: no model loading, training, or benchmark access."""
from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from qlora_smoke import check_hash, content_hash, file_hash, json_bytes, read_jsonl, write_json

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "aya-training-proposal.json"
SMOKE_PLAN_SHA = "4241ccf9a3c3a8b3ec217a5c7d95085efe4ba85ce6ce65e6a1323c036ffc71f0"
CATEGORIES = {"extraction", "classification", "structured_output", "rewriting",
              "ordering", "arithmetic", "insufficient_information", "summarization"}


def words(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold())


def overlap(first: str, second: str) -> bool:
    """Conservative lexical screen; a negative result is not semantic independence."""
    a, b = words(first), words(second)
    if a == b:
        return True
    spans = {tuple(a[i:i + 12]) for i in range(max(0, len(a) - 11))}
    if any(tuple(b[i:i + 12]) in spans for i in range(max(0, len(b) - 11))):
        return True
    if min(len(a), len(b)) < 5:
        return False
    sa, sb = set(a), set(b)
    x, y = " ".join(a), " ".join(b)
    return (len(sa & sb) / len(sa | sb) >= .85
            or (min(len(x), len(y)) / max(len(x), len(y)) >= .85
                and SequenceMatcher(None, x, y, autojunk=False).ratio() >= .92))


def validate_evaluation(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 32 or len({r["id"] for r in rows}) != 32:
        raise ValueError("Require exactly 32 unique evaluation items.")
    if {r["category"] for r in rows} != CATEGORIES:
        raise ValueError("Evaluation category coverage differs.")
    for category in CATEGORIES:
        if sum(r["category"] == category for r in rows) != 4:
            raise ValueError("Require four items per category.")
    for row in rows:
        if row.get("author_type") != "agent" or row.get("human_review_status") != "pending":
            raise ValueError("Draft evaluation must retain honest authorship/review status.")
        for key in ("prompt", "reference_answer", "content_criteria", "format_criteria"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing evaluation field: {key}")
        if row.get("provenance") != "Newly agent-authored for Makata; no external passage copied.":
            raise ValueError("Unexpected evaluation provenance.")


def select_rows(training: list[dict[str, Any]], dispositions: list[dict[str, Any]],
                reviews: list[dict[str, Any]], selection: list[dict[str, Any]],
                allow_screening_only: bool = False) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in training}
    if len(by_id) != len(training) or len({s["id"] for s in selection}) != len(selection):
        raise ValueError("Duplicate training/selection ID.")
    selected = []
    for item in selection:
        row = by_id[item["id"]]
        if (row["assigned_split"] != "train" or row["group_id"] != item["group_id"]
                or content_hash(row) != item["content_sha256"]
                or row["content_sha256"] != item["content_sha256"]):
            raise ValueError("Changed text, group or split.")
        members = [d for d in dispositions if d.get("group_id") == row["group_id"]]
        own = [d for d in members if d["id"] == row["id"]]
        if len(own) != 1 or own[0]["content_sha256"] != row["content_sha256"]:
            raise ValueError("Missing matching disposition evidence.")
        if any(d.get("quality_flags") or d["disposition"] not in
               ("provisional_candidate", "excluded_exact_duplicate") for d in members):
            raise ValueError("Unresolved group concern.")
        ids = {d["id"] for d in members}
        if any(r["id"] in ids and r["disposition"] in ("hold", "reject") for r in reviews):
            raise ValueError("Explicit hold/rejection in selected group.")
        allowed = {"agent", "screening"} if allow_screening_only else {"agent"}
        if item.get("reviewer_type") not in allowed or not item.get("rationale"):
            raise ValueError("Missing review evidence or screening policy authorization.")
        if item.get("reviewer_type") == "screening" and item.get("review_basis") != "automated_screening_only":
            raise ValueError("Screening must not be represented as individual review.")
        if item.get("review_basis") == "prior_agent_review" and not any(
                r["id"] == row["id"] and r.get("content_sha256") == row["content_sha256"]
                and r["disposition"] == "accept" and r.get("reviewer_type") == "agent" for r in reviews):
            raise ValueError("Missing prior acceptance evidence.")
        selected.append(row)
    if len({r["group_id"] for r in selected}) != len(selected):
        raise ValueError("Only one record per prompt group is allowed.")
    return selected


def validate_risk_review(plan: dict[str, Any], ledger: dict[str, Any],
                         rows: list[dict[str, Any]]) -> None:
    """A sampled acceptance can never override a known concern elsewhere in its group."""
    by_id = {r["id"]: r for r in rows}
    observations = {r["id"]: r for r in ledger["observations"]}
    if (len(observations) != plan["risk_review"]["sample_count"]
            or set(observations) != set(ledger["sample_ids"])
            or sum(r["disposition"] == "hold" for r in observations.values()) != plan["risk_review"]["new_holds"]):
        raise ValueError("Risk sample accounting differs.")
    for observation in observations.values():
        if (content_hash(by_id[observation["id"]]) != observation["content_sha256"]
                or observation["reviewer_type"] != "agent" or observation["human_approval"] is not False):
            raise ValueError("Stale or misrepresented risk observation.")
    held_groups = {by_id[r["id"]]["group_id"] for r in observations.values() if r["disposition"] == "hold"}
    for item in plan["selection"]:
        if (ledger["all_record_flags"][item["id"]] or ledger["group_flags"][item["group_id"]]
                or item["group_id"] in held_groups):
            raise ValueError("Selected record has a frozen risk concern.")
        if item["review_basis"] == "current_risk_sample":
            if observations.get(item["id"], {}).get("disposition") != "provisional_retain":
                raise ValueError("Missing sampled retention evidence.")
        if item.get("human_validated") is not False:
            raise ValueError("Agent screening is not human validation.")


def optimizer_updates(records: int, microbatch: int, accumulation: int, epochs: int) -> int:
    if min(records, microbatch, accumulation, epochs) < 1:
        raise ValueError("Training dimensions must be positive.")
    microbatches = (records + microbatch - 1) // microbatch
    return epochs * ((microbatches + accumulation - 1) // accumulation)


def validation_reviews(rows: list[dict[str, Any]], plan: dict[str, Any],
                       ledger: dict[str, Any]) -> list[dict[str, Any]]:
    eligible = set(plan["validation"]["eligible_ids"])
    if (len(rows) != plan["validation"]["source_count"] or not eligible <= {r["id"] for r in rows}
            or len(eligible) != plan["validation"]["provisional_loss_count"]):
        raise ValueError("Validation count/selection differs.")
    result = []
    for row in rows:
        flags = sorted(set(ledger["all_record_flags"][row["id"]] + ledger["group_flags"][row["group_id"]]))
        if row["assigned_split"] != "validation" or content_hash(row) != row["content_sha256"]:
            raise ValueError("Changed validation content or split.")
        if (row["id"] in eligible) != (not flags):
            raise ValueError("Validation eligibility does not match frozen concerns.")
        result.append({"id": row["id"], "content_sha256": row["content_sha256"], "flags": flags,
                       "proposed_disposition": "provisional_loss_candidate" if not flags else "hold",
                       "human_review_status": "pending"})
    return result


def screen_evaluation(evaluation: list[dict[str, Any]], aya: list[dict[str, Any]]) -> None:
    for index, item in enumerate(evaluation):
        # Screen task wording and supplied context, not trivial short answer words.
        for source in aya:
            if overlap(item["prompt"], source["prompt"]) or overlap(item["prompt"], source["response"]):
                raise ValueError(f"Review lexical overlap: {item['id']} / {source['id']}")
        if any(overlap(item["prompt"], other["prompt"]) for other in evaluation[:index]):
            raise ValueError(f"Near-duplicate evaluation prompt: {item['id']}")


def prepare(source: Path, evaluation_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("Refusing to overwrite approval materials.")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    check_hash(ROOT / "qlora-smoke-plan.json", SMOKE_PLAN_SHA)
    for name, expected in plan["source_files"].items():
        check_hash(source / name, expected)
    for name, expected in plan["preserved_smoke_files"].items():
        check_hash(ROOT / name, expected)
    if plan["approval_status"] != "pending" or plan["training_authorized"] is not False:
        raise ValueError("This preparer cannot authorize training.")
    check_hash(evaluation_path, plan["evaluation"]["draft_sha256"])
    training = read_jsonl(source / "train.jsonl")
    validation = read_jsonl(source / "validation.jsonl")
    dispositions = read_jsonl(source / "dispositions.jsonl")
    reviews = read_jsonl(source / "review-decisions.jsonl") + read_jsonl(source / "prior-review-decisions.jsonl")
    if "prior_proposal_review" in plan:
        history_path = ROOT / plan["prior_proposal_review"]["file"]
        check_hash(history_path, plan["prior_proposal_review"]["sha256"])
        historical = json.loads(history_path.read_text(encoding="utf-8"))
        reviews += [{**item, "disposition": "accept"} for item in historical["selection"]
                    if item.get("reviewer_type") == "agent"]
    ledger = None
    validation_decisions = []
    if "risk_review" in plan:
        risk_path = ROOT / plan["risk_review"]["file"]
        check_hash(risk_path, plan["risk_review"]["sha256"])
        ledger = json.loads(risk_path.read_text(encoding="utf-8"))
        validate_risk_review(plan, ledger, training + validation)
        validation_decisions = validation_reviews(validation, plan, ledger)
        config = plan["training"]
        if (config["drop_last"] or optimizer_updates(len(plan["selection"]),
                config["per_device_train_batch_size"], config["gradient_accumulation_steps"],
                config["epochs"]) != config["expected_optimizer_updates"]):
            raise ValueError("Optimizer update accounting differs.")
    selected = select_rows(training, dispositions, reviews, plan["selection"],
                           allow_screening_only=ledger is not None and
                           plan["risk_review"]["review_every_training_item_required"] is False)
    if {r["group_id"] for r in selected} & {r["group_id"] for r in validation}:
        raise ValueError("Selected group appears in Aya validation.")
    evaluation = read_jsonl(evaluation_path)
    validate_evaluation(evaluation)
    screen_evaluation(evaluation, training + validation)
    output.mkdir(parents=True)
    try:
        (output / "train.jsonl").write_bytes(b"".join(json_bytes(r) for r in selected))
        (output / "evaluation-draft.jsonl").write_bytes(evaluation_path.read_bytes())
        (output / "NOTICE.md").write_bytes((source / "NOTICE.md").read_bytes())
        if ledger is not None:
            write_json(output / "risk-review.json", ledger)
            (output / "validation-candidates.jsonl").write_bytes((source / "validation.jsonl").read_bytes())
            eligible = set(plan["validation"]["eligible_ids"])
            (output / "validation-provisional.jsonl").write_bytes(b"".join(json_bytes(r) for r in validation if r["id"] in eligible))
            (output / "validation-review.jsonl").write_bytes(b"".join(json_bytes(r) for r in validation_decisions))
            packet = ["# All Aya validation candidates — human review pending",
                      "Do not move these records into training. Flagged records remain held; unflagged records require review before loss monitoring."]
            for row, decision in zip(validation, validation_decisions, strict=True):
                packet.extend([f"## {row['id']} — {decision['proposed_disposition']}",
                               f"Hash: `{row['content_sha256']}`; group: `{row['group_id']}`",
                               "Flags: " + (", ".join(decision["flags"]) or "none detected; not verified"),
                               "**Original prompt**", row["prompt"], "**Original response**", row["response"]])
            (output / "validation-review-packet.md").write_text("\n\n".join(packet) + "\n", encoding="utf-8", newline="\n")
        selected_ids = {r["id"] for r in selected}
        selected_groups = {r["group_id"] for r in selected}
        decisions = []
        for row in training:
            members = [d for d in dispositions if d.get("group_id") == row["group_id"]]
            if row["id"] in selected_ids:
                reason = "selected_provisional_" + next(s.get("review_basis", "agent_review") for s in plan["selection"] if s["id"] == row["id"])
            elif ledger is not None and ledger["group_flags"][row["group_id"]]:
                reason = "excluded_frozen_risk_concern"
            elif any(d.get("quality_flags") or d["disposition"] not in
                     ("provisional_candidate", "excluded_exact_duplicate") for d in members):
                reason = "excluded_from_proposal_due_to_group_concern"
            elif row["group_id"] in selected_groups:
                reason = "omitted_variant_one_record_per_group"
            else:
                reason = "not_selected_no_current_low_risk_clearance"
            decisions.append({"id": row["id"], "content_sha256": row["content_sha256"], "reason": reason,
                              "flags": ledger["group_flags"][row["group_id"]] if ledger is not None else []})
        (output / "selection-dispositions.jsonl").write_bytes(b"".join(json_bytes(r) for r in decisions))
        template = []
        review_roles = (("validation", validation), ("evaluation", evaluation)) if ledger is not None else (("training", selected), ("evaluation", evaluation))
        for role, rows in review_roles:
            for row in rows:
                template.append({"role": role, "id": row["id"],
                                 "content_sha256": content_hash(row) if role != "evaluation" else hashlib.sha256(json_bytes(row)).hexdigest(),
                                 "reviewer_type": "human", "reviewer": None, "reviewed_at": None,
                                 "independent_of_authoring_and_training": None,
                                 "language": "pending", "correctness": "pending", "rights_or_provenance": "pending",
                                 "ambiguity_and_scoring": "pending", "disposition": "pending", "rationale": None})
        (output / "human-review-template.jsonl").write_bytes(b"".join(json_bytes(r) for r in template))
        packet = ["# Private review packet — draft, not validated",
                  "Do not train on the evaluation items. All observations so far are agent-assisted.",
                  "Complete human-review-template.jsonl in a NEW file; preserve this packet unchanged.",
                  "## Proposed Aya training records"]
        for row in selected:
            packet.extend([f"### {row['id']}", f"Content hash: `{row['content_sha256']}`",
                           "**Original prompt**", row["prompt"], "**Original response**", row["response"]])
        packet.append("## Untouched evaluation draft — independent human review required")
        for row in evaluation:
            packet.extend([f"### {row['id']} — {row['category']}", row["prompt"],
                           "**Illustrative reference; accept valid equivalents unless exact form is requested**",
                           row["reference_answer"], "**Content criteria:** " + row["content_criteria"],
                           "**Format criteria:** " + row["format_criteria"]])
        (output / "review-packet.md").write_text("\n\n".join(packet) + "\n", encoding="utf-8", newline="\n")
        names = [p.name for p in output.iterdir() if p.is_file()]
        manifest = {"status": "prepared_for_review", "training_authorized": False,
                    "native_speaker_validated": False, "legal_clearance": False,
                    "evaluation_validated": False, "model_inference_performed": False,
                    "benchmark_examples_accessed": False, "training_count": len(selected),
                    "evaluation_count": len(evaluation), "source_files": plan["source_files"],
                    "plan_sha256": file_hash(PLAN), "preparer_sha256": file_hash(Path(__file__)),
                    "outputs": {name: file_hash(output / name) for name in sorted(names)},
                    "screening": "Lexical comparison against all 951 Aya v2 train and 89 validation candidates, plus evaluation self-comparison. No benchmark access; no proof of semantic independence."}
        if ledger is not None:
            manifest.update(validation_candidate_count=len(validation),
                            provisional_validation_count=plan["validation"]["provisional_loss_count"],
                            training_review_basis=dict(Counter(s["review_basis"] for s in plan["selection"])),
                            training_dispositions=dict(Counter(d["reason"] for d in decisions)),
                            risk_sample_count=len(ledger["observations"]),
                            risk_sample_dispositions=dict(Counter(r["disposition"] for r in ledger["observations"])),
                            expected_optimizer_updates=plan["training"]["expected_optimizer_updates"],
                            risk_review_sha256=plan["risk_review"]["sha256"])
        write_json(output / "manifest.json", manifest)
        return manifest
    except BaseException:
        write_json(output / "incomplete.json", {"status": "incomplete", "training_authorized": False})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.evaluation, args.output), ensure_ascii=False))

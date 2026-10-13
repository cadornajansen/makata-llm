"""Prepare provisional Aya Filipino data; never train or run model evaluation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import sys
import unicodedata
from typing import Any

ROOT = Path(__file__).resolve().parent
VERSION = "aya-filipino-preparation-v2"
PRIOR_MANIFEST_SHA256 = "34497dae172bfab8770c5b2fff8c0c0aebed57bf6564dbe5e13388edb0ddc97f"
GROUPING_SIGNALS = {"answer_variants", "near_duplicate_prompt"}
REPOSITORY = "CohereLabs/aya_collection_language_split"
REVISION = "a3af2fde4b4cb5b2775830b11244a1a20b5f004f"
SOURCE_FILE = "filipino/train-00000-of-00001.parquet"
SOURCE_SHA256 = "8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc"
CARD_SHA256 = "453f2533dff0f575876bd5919e695db17f0b9c1d1b76b7d35e85ee0e9845bed1"
BENCHMARK_SHA256 = "e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512"
FIXTURE_SHA256 = "cf22ec6cc0043a53cc6564f05ab959c24874437cff6e353af6f32ebf09b1e24b"
TASK = "filbench|belebele_fil_mcf|0|0"
RECORDED_TASK = "filbench|belebele_fil_mcf|0"
SEED = 1234
COLUMNS = {"id", "inputs", "targets", "dataset_name", "sub_dataset_name", "task_type",
           "template_id", "language", "split", "script"}
RULES = {
    "normalization": "NFC, LF line endings, outer trim; comparison keys casefold and remove punctuation",
    "near_prompt": {"minimum_words": 5, "jaccard": 0.85, "character_ratio": 0.92, "length_ratio": 0.85},
    "split": "SHA256(seed:group_id), first 64 bits < floor(2**64/10) => validation",
    "benchmark_shared_span_words": 12,
    "sample_size": 60,
    "readiness": "provisional; automation and agent observations do not establish human or legal clearance",
    "grouping": "Grouping signals never quarantine; substantive flags and explicit holds do.",
    "claim_exceptions": "Percentage complement exercises and temporal words inside illustrative language prompts only.",
    "code_exception": "C++ standard includes and stream operators in explicit C++ examples only; other markup remains flagged.",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def file_hash(path: Path) -> str:
    return digest(path.read_bytes())


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold())


def comparison_key(text: str) -> str:
    return " ".join(words(text))


def fetch_source(offline: bool, revision: str = REVISION) -> tuple[Path, Path]:
    if revision != REVISION:
        raise ValueError("Only the frozen Aya dataset revision is permitted.")
    from huggingface_hub import hf_hub_download

    paths = []
    for filename, expected in ((SOURCE_FILE, SOURCE_SHA256), ("README.md", CARD_SHA256)):
        path = Path(hf_hub_download(
            repo_id=REPOSITORY, repo_type="dataset", revision=revision, filename=filename,
            cache_dir=ROOT / ".cache" / "dataset-preparation", token=False,
            local_files_only=offline,
        ))
        if file_hash(path) != expected:
            raise ValueError(f"Source checksum mismatch: {filename}")
        paths.append(path)
    card = paths[1].read_text(encoding="utf-8")
    if not re.search(r"license:\s*apache-2\.0", card):
        raise ValueError("Pinned dataset card does not declare the expected Apache-2.0 license.")
    return paths[0], paths[1]


def validate_rows(rows: list[dict[str, Any]], expected_count: int = 1241) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(rows) != expected_count:
        raise ValueError(f"Expected {expected_count} source records; got {len(rows)}.")
    seen: set[int] = set()
    valid, excluded = [], []
    for row in rows:
        if set(row) != COLUMNS:
            raise ValueError("Unexpected source schema.")
        source_id = row["id"]
        if type(source_id) is not int or source_id in seen:
            raise ValueError("Source IDs must be unique integers.")
        seen.add(source_id)
        if (row["language"], row["dataset_name"], row["split"], row["script"]) != ("fil", "Aya-Dataset", "train", "Latn"):
            raise ValueError("Unexpected source composition; no other languages, sources, or splits permitted.")
        record_id = f"aya-fil-{source_id}"
        if any(not isinstance(row[key], str) or not normalize_text(row[key]) for key in ("inputs", "targets")):
            excluded.append({"id": record_id, "source_ids": [source_id], "reason": "invalid_text_fields"})
            continue
        prompt, response = normalize_text(row["inputs"]), normalize_text(row["targets"])
        valid.append({
            "id": record_id, "source_id": source_id, "prompt": prompt, "response": response,
            "content_sha256": digest(json_bytes([prompt, response])),
            "provenance": {"repository": REPOSITORY, "revision": REVISION, "file": SOURCE_FILE,
                           "source_ids": [source_id], "dataset_name": row["dataset_name"],
                           "source_split": "train", "language": "fil", "license_declaration": "Apache-2.0"},
        })
    return sorted(valid, key=lambda row: row["source_id"]), excluded


def deduplicate(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    retained: dict[tuple[str, str], dict[str, Any]] = {}
    excluded = []
    for row in sorted(rows, key=lambda row: row["source_id"]):
        key = row["prompt"], row["response"]
        if key in retained:
            kept = retained[key]
            kept["provenance"]["source_ids"].append(row["source_id"])
            excluded.append({"id": row["id"], "source_ids": [row["source_id"]],
                             "reason": "exact_duplicate_pair", "duplicate_of": kept["id"]})
        else:
            retained[key] = row
    return list(retained.values()), excluded


def near_prompt(left: str, right: str) -> bool:
    a, b = words(left), words(right)
    if min(len(a), len(b)) < 5:
        return False
    a_set, b_set = set(a), set(b)
    if len(a_set & b_set) / len(a_set | b_set) >= 0.85:
        return True
    a_text, b_text = " ".join(a), " ".join(b)
    if min(len(a_text), len(b_text)) / max(len(a_text), len(b_text)) < 0.85:
        return False
    matcher = SequenceMatcher(None, a_text, b_text, autojunk=False)
    return matcher.quick_ratio() >= 0.92 and matcher.ratio() >= 0.92


def group_prompts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[comparison_key(row["prompt"])].append(row)
    keys = sorted(by_key)
    parent = {key: key for key in keys}

    def find(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    near_keys: set[str] = set()
    edges = []
    for index, left in enumerate(keys):
        for right in keys[index + 1:]:
            if near_prompt(left, right):
                a, b = find(left), find(right)
                parent[max(a, b)] = min(a, b)
                near_keys.update((left, right))
                edges.append({"left_id": by_key[left][0]["id"], "right_id": by_key[right][0]["id"]})
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key in keys:
        groups[find(key)].extend(by_key[key])
    for key, members in groups.items():
        group_id = "pg-" + digest(key.encode("utf-8"))
        variants = len({row["response"] for row in members}) > 1
        near = any(comparison_key(row["prompt"]) in near_keys for row in members)
        for row in members:
            row["group_id"] = group_id
            row["grouping_signals"] = (["answer_variants"] if variants else []) + (["near_duplicate_prompt"] if near else [])
            row["flags"] = []
    return edges


def heuristic_flags(row: dict[str, Any]) -> list[str]:
    prompt, response = row["prompt"], row["response"]
    text = prompt + "\n" + response
    flags = []
    if re.search(r"\b(liriko|lyrics|tula|poem|saknong|awitin|kanta|song)\b", text, re.I):
        flags.append("third_party_creative_text")
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+63|09)[\d\s-]{9,}", text):
        flags.append("possible_personal_information")
    if re.search(r"\b(patayin|pumatay|suicide|magpakamatay|panggagahasa|rape|bomba|bomb|droga|methamphetamine)\b", text, re.I):
        flags.append("sensitive_or_unsafe_content")
    if re.search(r"\b(glutathione|gluthatione|gamot|doktor|bakterya|sanitizer|kalusugan|medikal|medical|melatonin|melanin|maghugas|hugasan)\b", text, re.I):
        flags.append("medical_or_health_claim")
    formatting_text = text
    if re.search(r"C\+\+", prompt, re.I) and "#include" in response and "int main(" in response:
        formatting_text = re.sub(r"#include\s*<(?:iostream|iomanip|string|vector|cmath|cstdio)>", "", text)
        formatting_text = re.sub(r"\b(?:std::)?(?:cout|cin)\s*(?:<<|>>)", "STREAM ", formatting_text)
    if (not words(prompt) or re.search(r"https?://|<[^>]+>|\ufffd|\b(?:system|assistant):", formatting_text, re.I)
            or len(text) > 12000 or any(unicodedata.category(ch) == "Cc" and ch not in "\n\t" for ch in text)):
        flags.append("suspicious_formatting")
    filipino_markers = {"ang", "ng", "mga", "sa", "na", "ay", "at", "ito", "si", "kung", "hindi", "isang", "para", "ano", "paano"}
    if len(words(text)) >= 15 and not set(words(text)) & filipino_markers:
        flags.append("possible_language_mismatch")
    claim_text = text
    if re.search(r"\b(pahayag|pangungusap|sitwasyon|konteksto)\b", prompt, re.I):
        claim_text = re.sub(r"\bngayon\b", "", prompt, flags=re.I) + "\n" + response
    if (re.search(r"\b(posibilidad|probabilidad)\b.*\d+\s*%", prompt, re.I | re.S)
            and re.search(r"\bhindi\b", prompt, re.I)):
        claim_text = re.sub(r"\d+(?:\.\d+)?\s*%", "", claim_text)
    if re.search(r"\b(kasalukuyan|ngayon|pinakabago|latest|current|presidente|pangulo|populasyon|porsiyento|percent|chatgpt|gpt-3\.5)\b|\d+(?:\.\d+)?\s*%", claim_text, re.I):
        flags.append("time_sensitive_or_unsupported_claim")
    return flags


def protected_texts(path: Path, expected_hash: str = BENCHMARK_SHA256) -> tuple[list[str], dict[str, Any]]:
    if file_hash(path) != expected_hash:
        raise ValueError("Retained benchmark artifact checksum mismatch.")
    texts = []
    sample_ids = set()
    rows = path.read_text(encoding="utf-8").splitlines()
    if len(rows) != 900:
        raise ValueError("Benchmark guard requires exactly 900 retained questions.")
    for line in rows:
        row = json.loads(line)
        if row["task"] != RECORDED_TASK or row["sample_id"] in sample_ids:
            raise ValueError("Unexpected benchmark task or duplicate sample ID.")
        sample_ids.add(row["sample_id"])
        # Intentionally never inspect prediction, gold, likelihood, or accuracy fields.
        prompt = row["official_detail"]["example"]
        match = re.fullmatch(r"(.*)\nTanong: (.*?)\n\s*A\. (.*?)\n\s*B\. (.*?)\n\s*C\. (.*?)\n\s*D\. (.*?)\nSagot:", prompt, re.S)
        if match is None:
            raise ValueError("Cannot parse the frozen official benchmark prompt safely.")
        texts.extend(match.groups())
    fixture_path = ROOT / "fixtures" / "development.json"
    fixture_bytes = fixture_path.read_bytes()
    if digest(fixture_bytes) != FIXTURE_SHA256:
        raise ValueError("Engineering fixture checksum mismatch.")
    fixture = json.loads(fixture_bytes)
    if fixture["provenance"] != "makata-original-synthetic-development" or len(fixture["examples"]) != 20:
        raise ValueError("Unexpected engineering fixture provenance or count.")
    for row in fixture["examples"]:
        texts.extend([row["flores_passage"], row["question"], *(row[f"mc_answer{i}"] for i in range(1, 5))])
    return texts, {"benchmark_sha256": expected_hash, "task": TASK, "questions": 900,
                   "dataset_revision": "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2",
                   "engineering_fixture_sha256": digest(fixture_bytes), "engineering_questions": 20,
                   "coverage": "Retained Tagalog Belebele and local engineering fixtures only; not all benchmarks."}


def overlap_index(texts: list[str]) -> tuple[set[str], set[tuple[str, ...]]]:
    exact, spans = set(), set()
    for offset, text in enumerate(texts):
        tokens = words(text)
        # Short, commonplace answer choices are not evidence of contamination.
        # Each reference example contributes passage, question, then four choices.
        if tokens and offset % 6 < 2:
            exact.add(" ".join(tokens))
        spans.update(tuple(tokens[i:i + 12]) for i in range(len(tokens) - 11))
    return exact, spans


def overlaps(row: dict[str, Any], index: tuple[set[str], set[tuple[str, ...]]]) -> bool:
    exact, spans = index
    for text in (row["prompt"], row["response"]):
        tokens = words(text)
        if " ".join(tokens) in exact:
            return True
        if any(tuple(tokens[i:i + 12]) in spans for i in range(len(tokens) - 11)):
            return True
    return False


def load_reviews(path: Path | None, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    known = {row["id"]: row for row in rows}
    decisions = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        review = json.loads(line)
        record_id = review["id"]
        if record_id not in known or record_id in decisions:
            raise ValueError("Unknown or duplicate review ID.")
        if review.get("content_sha256") != known[record_id]["content_sha256"]:
            raise ValueError("Stale review content hash.")
        if review.get("disposition") not in ("accept", "reject", "hold") or review.get("reviewer_type") not in ("human", "agent"):
            raise ValueError("Invalid review disposition or reviewer type.")
        if not isinstance(review.get("rationale"), str) or not review["rationale"].strip():
            raise ValueError("Reviews require a rationale.")
        if not isinstance(review.get("references"), list) or any(not isinstance(url, str) for url in review["references"]):
            raise ValueError("Review references must be a list of strings.")
        decisions[record_id] = review
    return decisions


def split_for(group_id: str, seed: int = SEED) -> str:
    bucket = int(digest(f"{seed}:{group_id}".encode())[:16], 16)
    return "validation" if bucket < (1 << 64) // 10 else "train"


def select_review(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    ordered = sorted(rows, key=lambda row: digest(f"{SEED}:review:{row['id']}".encode()))
    selected = {row["id"]: ["seeded_sample"] for row in ordered[:60]}
    categories = sorted({flag for row in rows for flag in row["flags"]})
    for category in categories:
        row = next(row for row in ordered if category in row["flags"])
        selected.setdefault(row["id"], []).append("flag_category:" + category)
    return selected


def prepare_records(
    source: list[dict[str, Any]], protected: list[str], review_path: Path | None = None,
    expected_count: int = 1241, prior: dict[str, Any] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rows, invalid = validate_rows(source, expected_count)
    raw_pairs = {(row["inputs"], row["targets"]) for row in source
                 if isinstance(row["inputs"], str) and isinstance(row["targets"], str)}
    rows, duplicates = deduplicate(rows)
    edges = group_prompts(rows)
    index = overlap_index(protected)
    # Reference loader emits passage, question, and four choices for every example.
    protected_questions = protected[1::6]
    decisions = dict(prior["decisions"]) if prior else {}
    for record_id, decision in load_reviews(review_path, rows).items():
        previous = decisions.get(record_id)
        if previous and previous["disposition"] in ("hold", "reject") and decision != previous:
            raise ValueError("Prior explicit holds/rejections cannot be overridden in this revision.")
        decisions[record_id] = decision
    outputs: dict[str, list[dict[str, Any]]] = {
        "train": [], "validation": [], "quarantine": [], "exclusions": invalid + duplicates, "review": [],
        "dispositions": [],
    }
    benchmark_matches = set()
    for row in rows:
        row["flags"] = sorted(set(row["flags"] + heuristic_flags(row)))
        if prior:
            if prior["hashes"].get(row["id"]) != row["content_sha256"]:
                raise ValueError("Prior screening cannot be reused for changed or missing text.")
            previous = prior["records"].get(row["id"])
            if previous and (previous["group_id"] != row["group_id"] or previous["assigned_split"] != split_for(row["group_id"])):
                raise ValueError("Prior prompt groups/splits changed.")
            if row["id"] in prior["overlaps"]:
                benchmark_matches.add(row["id"])
            if row["id"] in prior["near_overlaps"]:
                row["flags"].append("possible_benchmark_question_overlap")
        elif overlaps(row, index):
            benchmark_matches.add(row["id"])
        elif any(near_prompt(row["prompt"], question) for question in protected_questions):
            row["flags"].append("possible_benchmark_question_overlap")
    selected = select_review(rows)
    for row in rows:
        decision = decisions.get(row["id"])
        export = {key: row[key] for key in ("id", "group_id", "prompt", "response", "content_sha256", "provenance", "grouping_signals")}
        export["assigned_split"] = split_for(row["group_id"])
        if row["id"] in benchmark_matches:
            disposition = "excluded_benchmark_overlap"
            outputs["exclusions"].append({"id": row["id"], "source_ids": row["provenance"]["source_ids"], "reason": "protected_evaluation_overlap"})
        elif decision and decision["disposition"] == "reject":
            disposition = "excluded_review"
            outputs["exclusions"].append({"id": row["id"], "source_ids": row["provenance"]["source_ids"], "reason": "review_rejection", "review": decision})
        else:
            cleared = decision and decision["reviewer_type"] == "human" and decision["disposition"] == "accept"
            if (row["flags"] and not cleared) or (decision and decision["disposition"] == "hold"):
                disposition = "quarantined"
                outputs["quarantine"].append({**export, "flags": row["flags"], "decision": decision})
            else:
                disposition = "provisional_candidate"
                outputs[export["assigned_split"]].append(export)
        if row["id"] in selected or decision:
            outputs["review"].append({**export, "flags": row["flags"], "selection": selected.get(row["id"], ["explicit_review"]),
                                      "output_disposition": disposition, "observation": decision,
                                      "review_status": "unreviewed" if decision is None else decision["reviewer_type"] + "_reviewed"})
        outputs["dispositions"].append({"id": row["id"], "content_sha256": row["content_sha256"],
            "group_id": row["group_id"], "grouping_signals": row["grouping_signals"], "quality_flags": row["flags"],
            "assigned_split": export["assigned_split"], "disposition": disposition,
            "previous_disposition": prior["classifications"].get(row["id"]) if prior else None,
            "reason": "protected_evaluation_overlap" if row["id"] in benchmark_matches else
                ("explicit_review_" + decision["disposition"] if decision and decision["disposition"] in ("hold", "reject") else
                 "unresolved_quality_flags" if disposition == "quarantined" else "no_blocking_quality_flag_or_review_hold"),
            "review": decision})
    for excluded in invalid + duplicates:
        outputs["dispositions"].append({"id": excluded["id"], "disposition": "excluded",
            "previous_disposition": prior["classifications"].get(excluded["id"]) if prior else None,
            "reason": excluded["reason"], "duplicate_of": excluded.get("duplicate_of")})
    for values in outputs.values():
        values.sort(key=lambda row: int(row["id"].rsplit("-", 1)[1]))
    classified = [row["id"] for name in ("train", "validation", "quarantine", "exclusions") for row in outputs[name]]
    if len(classified) != len(source) or len(set(classified)) != len(source):
        raise ValueError("Source record accounting does not reconcile.")
    if {row["group_id"] for row in outputs["train"]} & {row["group_id"] for row in outputs["validation"]}:
        raise ValueError("Prompt groups crossed the training/validation boundary.")
    counts = {name: len(values) for name, values in outputs.items()}
    counts.update({"original": len(source), "raw_unique_pairs": len(raw_pairs), "raw_exact_duplicate_excess": len(source) - len(raw_pairs),
                   "normalized_exact_duplicate_excess": len(duplicates), "invalid": len(invalid),
                   "unique_raw_prompts": len({row["inputs"] for row in source if isinstance(row["inputs"], str)}),
                   "prompt_groups": len({row["group_id"] for row in rows}), "near_prompt_edges": len(edges),
                   "usable_candidates": len(outputs["train"]) + len(outputs["validation"]),
                   "excluded_original_records": len(outputs["exclusions"]),
                   "train_groups": len({row["group_id"] for row in outputs["train"]}),
                   "validation_groups": len({row["group_id"] for row in outputs["validation"]})})
    return outputs, {"counts": counts, "exclusion_reasons": dict(Counter(row["reason"] for row in outputs["exclusions"])),
                     "flag_counts": dict(sorted(Counter(flag for row in rows for flag in row["flags"]).items())),
                     "grouping_signal_counts": dict(sorted(Counter(flag for row in rows for flag in row["grouping_signals"]).items())),
                     "near_prompt_edges": edges,
                     "split_statistics": {"validation_record_fraction": counts["validation"] / max(1, counts["usable_candidates"]),
                                          "validation_group_fraction": counts["validation_groups"] / max(1, counts["train_groups"] + counts["validation_groups"])},
                     "readiness": {"status": "provisional", "ready_for_training": False,
                                   "human_review_complete": False, "third_party_rights_cleared": False,
                                   "independent_untouched_evaluation_set": "outstanding"}}


def load_prior_screening(directory: Path) -> dict[str, Any]:
    """Reuse only the audited v1 receipt, without opening any benchmark file."""
    manifest_path = directory / "manifest.json"
    if file_hash(manifest_path) != PRIOR_MANIFEST_SHA256:
        raise ValueError("Prior screening manifest is not the pinned audited v1 receipt.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest["status"] != "complete" or manifest["source"]["sha256"] != SOURCE_SHA256
            or manifest["source"]["revision"] != REVISION
            or manifest["benchmark_screening"]["benchmark_sha256"] != BENCHMARK_SHA256
            or manifest["benchmark_screening"]["engineering_fixture_sha256"] != FIXTURE_SHA256
            or manifest["benchmark_screening"]["task"] != TASK):
        raise ValueError("Prior receipt source/protocol mismatch.")
    for name, expected in manifest["outputs"].items():
        if Path(name).name != name or file_hash(directory / name) != expected:
            raise ValueError("Prior screening output checksum mismatch.")
    if file_hash(ROOT / "fixtures" / "development.json") != FIXTURE_SHA256:
        raise ValueError("Engineering fixtures changed since prior screening.")
    result: dict[str, Any] = {"hashes": {}, "records": {}, "classifications": {},
                            "decisions": {}, "overlaps": set(), "near_overlaps": set(),
                            "coverage": {**manifest["benchmark_screening"], "mode": "reused_for_identical_source_text",
                                         "prior_manifest_sha256": PRIOR_MANIFEST_SHA256,
                                         "benchmark_examples_read_this_run": False}}
    for name in ("train", "validation", "quarantine", "exclusions"):
        for line in (directory / (name + ".jsonl")).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["id"] in result["classifications"]:
                raise ValueError("Duplicate prior classification.")
            result["classifications"][row["id"]] = name
            if name != "exclusions":
                if digest(json_bytes([row["prompt"], row["response"]])) != row["content_sha256"]:
                    raise ValueError("Prior record content hash mismatch.")
                result["hashes"][row["id"]] = row["content_sha256"]
                result["records"][row["id"]] = row
                if "possible_benchmark_question_overlap" in row.get("flags", []):
                    result["near_overlaps"].add(row["id"])
            elif row["reason"] == "protected_evaluation_overlap":
                # This audited receipt has no such rows; fail if a future receipt lacks their text hashes.
                raise ValueError("Cannot reuse an exclusion without a screened content hash.")
    for line in (directory / "review-decisions.jsonl").read_text(encoding="utf-8").splitlines():
        decision = json.loads(line)
        result["decisions"][decision["id"]] = decision
        result["hashes"][decision["id"]] = decision["content_sha256"]
    if len(result["classifications"]) != 1241 or len(result["hashes"]) != 1233:
        raise ValueError("Prior receipt does not cover the complete deduplicated source.")
    return result


def write_outputs(directory: Path, outputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    hashes = {}
    for name, rows in outputs.items():
        data = b"".join(json_bytes(row) for row in rows)
        path = directory / (name + ".jsonl")
        path.write_bytes(data)
        hashes[path.name] = digest(data)
    return hashes


def execute(output: Path, benchmark: Path | None, offline: bool, reviews: Path | None = None,
            previous: Path | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {"status": "incomplete", "version": VERSION, "seed": SEED,
                               "execution": {"started_at": datetime.now(timezone.utc).isoformat()},
                               "readiness": {"ready_for_training": False}}
    manifest_path = output / "manifest.json"
    manifest_path.write_bytes(json_bytes(manifest))
    try:
        if sys.version_info[:2] != (3, 12):
            raise RuntimeError("Use the isolated Python 3.12 environment.")
        if (benchmark is None) == (previous is None):
            raise ValueError("Provide exactly one benchmark reference or audited previous preparation.")
        prior = load_prior_screening(previous) if previous else None
        if prior:
            protected, coverage = [], prior["coverage"]
        else:
            assert benchmark is not None
            protected, coverage = protected_texts(benchmark)
        source_path, card_path = fetch_source(offline)
        import pyarrow.parquet as parquet

        source = parquet.read_table(source_path).to_pylist()
        outputs, summary = prepare_records(source, protected, reviews, prior=prior)
        hashes = write_outputs(output, outputs)
        attribution = (
            "Aya Filipino subset — provisional local research preparation\n\n"
            "Source: Aya Open Science Initiative / Cohere Labs, Singh et al. (2024).\n"
            "Paper: https://arxiv.org/abs/2402.06619\n"
            f"Repository: https://huggingface.co/datasets/{REPOSITORY}/tree/{REVISION}\n"
            "Publisher-declared license: Apache-2.0.\n"
            "License terms: https://www.apache.org/licenses/LICENSE-2.0\n"
            "Changes: NFC/LF/outer trim, duplicate removal, grouping, screening, provisional splits.\n"
            "Third-party passages may have separate rights; unresolved flagged material is quarantined.\n"
            "Not human-validated, legally cleared, or approved for training/release.\n"
        )
        for name, data in (("source-card.md", card_path.read_bytes()), ("NOTICE.md", attribution.encode("utf-8"))):
            (output / name).write_bytes(data)
            hashes[name] = digest(data)
        if reviews is not None:
            review_bytes = reviews.read_bytes()
            (output / "review-decisions.jsonl").write_bytes(review_bytes)
            hashes["review-decisions.jsonl"] = digest(review_bytes)
        if prior:
            receipt = (previous / "manifest.json").read_bytes()
            (output / "prior-screening-manifest.json").write_bytes(receipt)
            hashes["prior-screening-manifest.json"] = digest(receipt)
            retained_reviews = (previous / "review-decisions.jsonl").read_bytes()
            (output / "prior-review-decisions.jsonl").write_bytes(retained_reviews)
            hashes["prior-review-decisions.jsonl"] = digest(retained_reviews)
        if not outputs["train"] or not outputs["validation"]:
            raise ValueError("Both provisional splits must contain records; no automatic rebalancing performed.")
        manifest.update({**summary, "rules": RULES,
                         "intended_experiment": {"model": "Qwen/Qwen3-1.7B-Base",
                                                 "model_revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
                                                 "method": "supervised fine-tuning, proposed only", "training_started": False},
                         "source": {"repository": REPOSITORY, "revision": REVISION,
                         "file": SOURCE_FILE, "sha256": file_hash(source_path), "card_sha256": file_hash(card_path),
                         "license_declaration": "Apache-2.0", "attribution": "Aya Open Science Initiative / Cohere Labs; Singh et al. (2024)",
                         "rights_limit": "Publisher declaration does not establish rights to every third-party passage."},
                         "benchmark_screening": coverage, "script_sha256": file_hash(Path(__file__)),
                         "review_input_sha256": file_hash(reviews) if reviews else None,
                         "requirements_sha256": file_hash(ROOT / "requirements.txt"),
                         "environment": {"python": platform.python_version(), "platform": platform.system(),
                                         "huggingface-hub": importlib.metadata.version("huggingface-hub"),
                                         "pyarrow": importlib.metadata.version("pyarrow")},
                         "outputs": hashes, "status": "complete"})
    except BaseException as error:
        manifest["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        manifest["execution"]["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_bytes(json_bytes(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    reference = parser.add_mutually_exclusive_group(required=True)
    reference.add_argument("--benchmark-records", type=Path)
    reference.add_argument("--previous-preparation", type=Path,
                           help="Reuse pinned v1 screening for unchanged text; never open benchmark examples.")
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    manifest = execute(args.output.resolve(), args.benchmark_records.resolve() if args.benchmark_records else None,
                       args.offline, args.reviews, args.previous_preparation)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "readiness": manifest["readiness"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

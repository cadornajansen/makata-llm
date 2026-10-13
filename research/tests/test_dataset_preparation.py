"""Synthetic, offline preparation tests; never retrieve benchmark examples."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_dataset as preparation


def source_row(source_id: int, prompt: str | None = None, response: str | None = None) -> dict:
    return {"id": source_id, "inputs": prompt if prompt is not None else f"Tanong{source_id}?",
            "targets": response if response is not None else f"Sagot{source_id}.",
            "dataset_name": "Aya-Dataset", "sub_dataset_name": "-", "task_type": "-",
            "template_id": 0, "language": "fil", "split": "train", "script": "Latn"}


def prepared(rows: list[dict], reviews: Path | None = None, protected: list[str] | None = None) -> tuple[dict, dict]:
    return preparation.prepare_records(rows, protected or [], reviews, expected_count=len(rows))


class DatasetPreparationTests(unittest.TestCase):
    def test_schema_and_source_composition_fail_closed(self) -> None:
        original = source_row(1)
        for field, value in (("language", "eng"), ("split", "test"), ("dataset_name", "Belebele"),
                             ("id", "1"), ("script", "Arab")):
            row = {**original, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                preparation.validate_rows([row], 1)
        with self.assertRaises(ValueError):
            preparation.validate_rows([{**original, "unexpected": "field"}], 1)
        with self.assertRaises(ValueError):
            preparation.validate_rows([original, original], 2)
        with self.assertRaises(ValueError):
            preparation.validate_rows([original])

    def test_invalid_text_excluded_with_reason(self) -> None:
        for invalid in (None, 12, "", " \n"):
            row = source_row(1)
            row["inputs"] = invalid
            valid, excluded = preparation.validate_rows([row], 1)
            self.assertEqual(valid, [])
            self.assertEqual(excluded[0]["reason"], "invalid_text_fields")

    def test_normalization_preserves_internal_structure(self) -> None:
        self.assertEqual(preparation.normalize_text("  cafe\u0301\r\n\r\n  text \r "), "café\n\n  text")
        self.assertEqual(preparation.comparison_key("  ANO—ito?! "), "ano ito")

    def test_exact_duplicates_keep_lowest_source_id_and_all_provenance(self) -> None:
        outputs, summary = prepared([source_row(9, "A?", "B."), source_row(2, "A?", "B.")])
        retained = outputs["train"] + outputs["validation"]
        self.assertEqual(retained[0]["id"], "aya-fil-2")
        self.assertEqual(retained[0]["provenance"]["source_ids"], [2, 9])
        self.assertEqual(outputs["exclusions"][0]["duplicate_of"], "aya-fil-2")
        self.assertEqual(summary["counts"]["normalized_exact_duplicate_excess"], 1)

    def test_raw_and_normalized_duplicate_counts_are_distinct(self) -> None:
        _, summary = prepared([source_row(1, "A?", "B."), source_row(2, " A? ", "B.\r\n")])
        self.assertEqual(summary["counts"]["raw_exact_duplicate_excess"], 0)
        self.assertEqual(summary["counts"]["normalized_exact_duplicate_excess"], 1)

    def test_short_prompts_only_group_on_exact_comparison_key(self) -> None:
        rows, _ = preparation.validate_rows([source_row(1, "Ano ito?"), source_row(2, "ANO ITO!"), source_row(3, "Ano iyon?")], 3)
        preparation.group_prompts(rows)
        self.assertEqual(rows[0]["group_id"], rows[1]["group_id"])
        self.assertNotEqual(rows[0]["group_id"], rows[2]["group_id"])
        self.assertFalse(preparation.near_prompt("Ano ito?", "Ano iyon?"))

    def test_transitive_near_prompt_components_stay_together(self) -> None:
        base = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"
        texts = [base, base.replace("one", "first"), base.replace("one", "first").replace("fifteen", "last")]
        rows, _ = preparation.validate_rows([source_row(i, text) for i, text in enumerate(texts)], 3)
        edges = preparation.group_prompts(rows)
        self.assertGreaterEqual(len(edges), 2)
        self.assertEqual(len({row["group_id"] for row in rows}), 1)
        self.assertTrue(all("near_duplicate_prompt" in row["grouping_signals"] for row in rows))

    def test_near_prompt_length_and_word_guards(self) -> None:
        self.assertFalse(preparation.near_prompt("one two three", "one two four"))
        self.assertFalse(preparation.near_prompt("a b c d e", "completely different long text with no matching words"))
        self.assertTrue(preparation.near_prompt("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen",
                                                "one two three four five six seven eight nine ten eleven twelve thirteen fourteen other"))

    def test_answer_variants_are_grouping_signals_not_quality_verdicts(self) -> None:
        outputs, _ = prepared([source_row(1, "Ano ito?", "Una."), source_row(2, "Ano ito?", "Ikalawa.")])
        candidates = outputs["train"] + outputs["validation"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len({row["assigned_split"] for row in candidates}), 1)
        self.assertTrue(all("answer_variants" in row["grouping_signals"] for row in candidates))
        self.assertEqual(outputs["quarantine"], [])
        self.assertEqual(outputs["exclusions"], [])

    def test_each_quality_flag_has_a_synthetic_example(self) -> None:
        examples = {
            "third_party_creative_text": "Ibigay ang lyrics ng kanta.",
            "possible_personal_information": "Email: someone@example.test",
            "sensitive_or_unsafe_content": "Paano gumawa ng bomba?",
            "medical_or_health_claim": "Ano ang epekto ng glutathione?",
            "suspicious_formatting": "<script>content</script>",
            "time_sensitive_or_unsupported_claim": "Sino ang kasalukuyang pangulo?",
            "possible_language_mismatch": "These English words contain lengthy instructions about writing useful answers without using Filipino language markers anywhere throughout this example.",
        }
        for flag, prompt in examples.items():
            with self.subTest(flag=flag):
                self.assertIn(flag, preparation.heuristic_flags({"prompt": prompt, "response": "Response."}))

    def test_split_is_deterministic_and_input_order_independent(self) -> None:
        source = [source_row(i) for i in range(120)]
        first, a = prepared(copy.deepcopy(source))
        second, b = prepared(list(reversed(copy.deepcopy(source))))
        self.assertEqual(first, second)
        self.assertEqual(a, b)
        self.assertGreater(len(first["validation"]), 0)
        self.assertFalse({r["group_id"] for r in first["train"]} & {r["group_id"] for r in first["validation"]})

    def review_file(self, directory: str, row: dict, reviewer_type: str, disposition: str = "accept") -> Path:
        review = {"id": row["id"], "content_sha256": row["content_sha256"], "reviewer_type": reviewer_type,
                  "disposition": disposition, "rationale": "Synthetic test review, not a real approval.", "references": []}
        path = Path(directory) / "reviews.jsonl"
        path.write_bytes(preparation.json_bytes(review))
        return path

    def test_agent_accept_cannot_clear_flags_but_human_decision_can(self) -> None:
        source = [source_row(1, "Ibigay ang lyrics.")]
        initial, _ = prepared(source)
        row = initial["quarantine"][0]
        with tempfile.TemporaryDirectory() as directory:
            agent, _ = prepared(source, self.review_file(directory, row, "agent"))
            human, summary = prepared(source, self.review_file(directory, row, "human"))
        self.assertEqual(len(agent["quarantine"]), 1)
        self.assertEqual(len(human["train"]) + len(human["validation"]), 1)
        self.assertFalse(summary["readiness"]["ready_for_training"])

    def test_review_rejection_and_hold_do_not_rewrite_text(self) -> None:
        source = [source_row(1)]
        initial, _ = prepared(source)
        row = (initial["train"] + initial["validation"])[0]
        with tempfile.TemporaryDirectory() as directory:
            held, _ = prepared(source, self.review_file(directory, row, "agent", "hold"))
            rejected, _ = prepared(source, self.review_file(directory, row, "agent", "reject"))
        self.assertEqual(held["quarantine"][0]["prompt"], source[0]["inputs"])
        self.assertEqual(rejected["exclusions"][0]["reason"], "review_rejection")

    def test_reviews_reject_unknown_ids_stale_hashes_and_missing_reasons(self) -> None:
        source = [source_row(1)]
        rows, _ = preparation.validate_rows(source, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = self.review_file(directory, rows[0], "human")
            original = json.loads(path.read_text(encoding="utf-8"))
            for change in ({"id": "unknown"}, {"content_sha256": "0" * 64}, {"rationale": ""}, {"reviewer_type": "native-speaker"}):
                path.write_bytes(preparation.json_bytes({**original, **change}))
                with self.subTest(change=change), self.assertRaises(ValueError):
                    preparation.load_reviews(path, rows)

    def test_review_cannot_change_group_assignments(self) -> None:
        source = [source_row(1, "Ano ito?", "Una."), source_row(2, "ANO ITO?", "Ikalawa.")]
        initial, _ = prepared(source)
        with tempfile.TemporaryDirectory() as directory:
            reviewed, _ = prepared(source, self.review_file(directory, (initial["train"] + initial["validation"])[0], "human"))
        retained = reviewed["train"] + reviewed["validation"] + reviewed["quarantine"]
        self.assertEqual(len({row["group_id"] for row in retained}), 1)
        self.assertEqual(len({row["assigned_split"] for row in retained}), 1)

    def test_protected_exact_and_twelve_word_spans_are_excluded(self) -> None:
        phrase = "one two three four five six seven eight nine ten eleven twelve"
        index = preparation.overlap_index(["Protected question?", phrase])
        self.assertTrue(preparation.overlaps({"prompt": "PROTECTED QUESTION!", "response": "x"}, index))
        self.assertTrue(preparation.overlaps({"prompt": "x", "response": "prefix " + phrase + " suffix"}, index))
        self.assertFalse(preparation.overlaps({"prompt": "Unrelated question?", "response": "A different answer."}, index))
        outputs, _ = prepared([source_row(1, "Protected question?")], protected=["Protected question?"])
        self.assertEqual(outputs["exclusions"][0]["reason"], "protected_evaluation_overlap")

    def test_human_review_cannot_override_exact_benchmark_exclusion(self) -> None:
        source = [source_row(1)]
        rows, _ = preparation.validate_rows(source, 1)
        with tempfile.TemporaryDirectory() as directory:
            outputs, _ = prepared(source, self.review_file(directory, rows[0], "human"), [source[0]["inputs"]])
        self.assertEqual(outputs["exclusions"][0]["reason"], "protected_evaluation_overlap")

    def test_common_answer_choices_alone_are_not_contamination(self) -> None:
        references = ["Long protected passage", "Specific protected question?", "Oo", "Hindi", "Una", "Wala"]
        self.assertFalse(preparation.overlaps({"prompt": "Ibang tanong?", "response": "Oo"}, preparation.overlap_index(references)))

    def test_benchmark_guard_reads_only_text_not_outcomes(self) -> None:
        prompt = "A protected passage.\nTanong: A protected question?\n A. First\n B. Second\n C. Third\n D. Fourth\nSagot:"
        rows = [{"task": preparation.RECORDED_TASK, "sample_id": str(i), "official_detail": {"example": prompt},
                 "accuracy": "intentionally unusable", "predicted_index": {"never": "consulted"}} for i in range(900)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.jsonl"
            path.write_bytes(b"".join(preparation.json_bytes(row) for row in rows))
            texts, coverage = preparation.protected_texts(path, preparation.file_hash(path))
            self.assertEqual(coverage["questions"], 900)
            self.assertEqual(texts[:2], ["A protected passage.", "A protected question?"])
            self.assertEqual(len(texts), 920 * 6)
            with self.assertRaises(ValueError):
                preparation.protected_texts(path)
            rows[0]["task"] = "another|task|0"
            path.write_bytes(b"".join(preparation.json_bytes(row) for row in rows))
            with self.assertRaises(ValueError):
                preparation.protected_texts(path, preparation.file_hash(path))

    def test_benchmark_guard_rejects_unparseable_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.jsonl"
            rows = [{"task": preparation.RECORDED_TASK, "sample_id": str(i), "official_detail": {"example": "unexpected"}} for i in range(900)]
            path.write_bytes(b"".join(preparation.json_bytes(row) for row in rows))
            with self.assertRaisesRegex(ValueError, "parse"):
                preparation.protected_texts(path, preparation.file_hash(path))

    def test_download_is_exactly_allowlisted_and_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data.parquet"
            card = Path(directory) / "README.md"
            data.write_bytes(b"synthetic parquet placeholder")
            card.write_text("license: apache-2.0\n", encoding="utf-8")
            with patch("huggingface_hub.hf_hub_download", side_effect=[str(data), str(card)]) as download, \
                 patch.object(preparation, "SOURCE_SHA256", preparation.file_hash(data)), \
                 patch.object(preparation, "CARD_SHA256", preparation.file_hash(card)):
                preparation.fetch_source(True)
            self.assertEqual(download.call_count, 2)
            self.assertEqual([call.kwargs["filename"] for call in download.call_args_list], [preparation.SOURCE_FILE, "README.md"])
            for call in download.call_args_list:
                self.assertEqual(call.kwargs["revision"], preparation.REVISION)
                self.assertEqual(call.kwargs["repo_type"], "dataset")
                self.assertTrue(call.kwargs["local_files_only"])
            with self.assertRaises(ValueError):
                preparation.fetch_source(True, "main")
            with patch("huggingface_hub.hf_hub_download", return_value=str(data)), self.assertRaises(ValueError):
                preparation.fetch_source(True)

    def test_representative_sample_is_seeded_and_covers_flags(self) -> None:
        rows = [{"id": f"aya-fil-{i}", "flags": ["flag-one"] if i == 0 else []} for i in range(100)]
        selected = preparation.select_review(rows)
        self.assertEqual(selected, preparation.select_review(list(reversed(rows))))
        self.assertEqual(sum("seeded_sample" in reasons for reasons in selected.values()), 60)
        self.assertIn("aya-fil-0", selected)

    def test_output_format_hashes_and_count_reconciliation(self) -> None:
        source = [source_row(i) for i in range(80)] + [source_row(99, "Tanong0?", "Sagot0.")]
        outputs, summary = prepared(source)
        counts = summary["counts"]
        self.assertEqual(counts["original"], counts["train"] + counts["validation"] + counts["quarantine"] + counts["exclusions"])
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            first.mkdir()
            second.mkdir()
            hashes = preparation.write_outputs(first, outputs)
            self.assertEqual(hashes, preparation.write_outputs(second, outputs))
            for name, value in hashes.items():
                self.assertEqual(value, preparation.file_hash(first / name))
            row = json.loads((first / "train.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(set(row), {"id", "group_id", "prompt", "response", "content_sha256", "provenance", "assigned_split", "grouping_signals"})
            self.assertEqual(row["provenance"]["revision"], preparation.REVISION)

    def test_execution_manifest_and_offline_output_reproduction(self) -> None:
        import pyarrow as arrow
        import pyarrow.parquet as parquet

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path, card_path = root / "synthetic.parquet", root / "README.md"
            parquet.write_table(arrow.Table.from_pylist([source_row(i) for i in range(1241)]), source_path)
            card_path.write_text("license: apache-2.0\n", encoding="utf-8")
            with patch.object(preparation, "protected_texts", return_value=([], {"questions": 900})), \
                 patch.object(preparation, "fetch_source", return_value=(source_path, card_path)):
                first = preparation.execute(root / "first", root / "benchmark", True)
                second = preparation.execute(root / "second", root / "benchmark", True)
            self.assertEqual(first["status"], "complete")
            self.assertEqual(first["outputs"], second["outputs"])
            self.assertEqual(first["seed"], 1234)
            self.assertEqual(first["source"]["revision"], preparation.REVISION)
            self.assertEqual(first["script_sha256"], preparation.file_hash(Path(preparation.__file__)))
            self.assertIn("pyarrow", first["environment"])
            self.assertIn("started_at", first["execution"])
            self.assertFalse(first["readiness"]["ready_for_training"])
            with self.assertRaises(FileExistsError):
                preparation.execute(root / "first", root / "benchmark", True)

    def test_failed_and_interrupted_runs_remain_incomplete(self) -> None:
        for failure in (ValueError("Invalid reference"), KeyboardInterrupt()):
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "failed"
                with patch.object(preparation, "protected_texts", side_effect=failure), self.assertRaises(type(failure)):
                    preparation.execute(output, Path("unused"), True)
                manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "incomplete")
                self.assertFalse(manifest["readiness"]["ready_for_training"])
                self.assertIn("finished_at", manifest["execution"])

    def test_percentage_complement_not_population_claim(self) -> None:
        flags = preparation.heuristic_flags({"prompt": "Ang posibilidad na umulan ay 70%. Ano ang posibilidad na hindi umulan?", "response": "30%. Dahil 100% - 70% ay 30%."})
        self.assertNotIn("time_sensitive_or_unsupported_claim", flags)
        flags = preparation.heuristic_flags({"prompt": "Ilan ang mga residente?", "response": "70% ang populasyon ngayon."})
        self.assertIn("time_sensitive_or_unsupported_claim", flags)

    def test_illustrative_temporal_word_keeps_other_claim_signals(self) -> None:
        harmless = {"prompt": 'Ano ang kahulugan sa pangungusap: "Baka ang ulam ngayon"?', "response": "Hayop ang baka."}
        self.assertNotIn("time_sensitive_or_unsupported_claim", preparation.heuristic_flags(harmless))
        risky = {**harmless, "response": "Ang kasalukuyan na pangulo ang nagsabi nito."}
        self.assertIn("time_sensitive_or_unsupported_claim", preparation.heuristic_flags(risky))

    def test_cpp_syntax_exception_does_not_hide_script_markup_or_urls(self) -> None:
        example = {"prompt": "Magbigay ng C++ code.", "response": '#include <iostream>\nint main() { std::cout << "Ano?"; std::cin >> x; }'}
        self.assertNotIn("suspicious_formatting", preparation.heuristic_flags(example))
        for suffix in ("<script>bad</script>", " https://example.test", " <iframe>x</iframe>"):
            self.assertIn("suspicious_formatting", preparation.heuristic_flags({**example, "response": example["response"] + suffix}))

    def test_substantive_flags_and_explicit_holds_survive_grouping_change(self) -> None:
        source = [source_row(1, "Ano ang lyrics?", "Una."), source_row(2, "Ano ang lyrics?", "Ikalawa.")]
        outputs, _ = prepared(source)
        self.assertEqual(len(outputs["quarantine"]), 2)
        self.assertTrue(all("third_party_creative_text" in r["flags"] for r in outputs["quarantine"]))
        source = [source_row(1, "Ano ito?", "Una."), source_row(2, "Ano ito?", "Ikalawa.")]
        rows, _ = preparation.validate_rows(source, 2)
        with tempfile.TemporaryDirectory() as directory:
            outputs, _ = prepared(source, self.review_file(directory, rows[0], "agent", "hold"))
        self.assertEqual([r["id"] for r in outputs["quarantine"]], ["aya-fil-1"])

    def prior_for(self, source: list[dict]) -> dict:
        outputs, _ = prepared(source)
        records = {r["id"]: r for r in outputs["train"] + outputs["validation"] + outputs["quarantine"]}
        return {"records": records, "hashes": {key: r["content_sha256"] for key, r in records.items()},
                "classifications": {key: "quarantine" for key in records}, "decisions": {},
                "overlaps": set(), "near_overlaps": set(), "coverage": {"questions": 900}}

    def test_receipt_reuse_never_calls_benchmark_loader_or_overlap_scan(self) -> None:
        source = [source_row(1), source_row(2)]
        prior = self.prior_for(source)
        with patch.object(preparation, "protected_texts", side_effect=AssertionError("Benchmark access forbidden")), \
             patch.object(preparation, "overlaps", side_effect=AssertionError("Benchmark access forbidden")):
            outputs, _ = preparation.prepare_records(source, [], expected_count=2, prior=prior)
        self.assertEqual(len(outputs["dispositions"]), 2)
        self.assertTrue(all(r["previous_disposition"] == "quarantine" for r in outputs["dispositions"]))

    def test_receipt_rejects_changed_text_or_groups(self) -> None:
        source = [source_row(1), source_row(2)]
        prior = self.prior_for(source)
        changed = copy.deepcopy(source)
        changed[0]["targets"] = "Changed text"
        with self.assertRaisesRegex(ValueError, "changed or missing text"):
            preparation.prepare_records(changed, [], expected_count=2, prior=prior)
        prior["records"]["aya-fil-1"]["group_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "groups/splits changed"):
            preparation.prepare_records(source, [], expected_count=2, prior=prior)

    def test_receipt_exact_and_near_overlap_protections_remain_binding(self) -> None:
        source = [source_row(1), source_row(2)]
        prior = self.prior_for(source)
        prior["overlaps"].add("aya-fil-1")
        prior["near_overlaps"].add("aya-fil-2")
        with tempfile.TemporaryDirectory() as directory:
            review = self.review_file(directory, prior["records"]["aya-fil-1"], "human")
            outputs, _ = preparation.prepare_records(source, [], review, 2, prior)
        self.assertEqual(outputs["exclusions"][0]["reason"], "protected_evaluation_overlap")
        self.assertIn("possible_benchmark_question_overlap", outputs["quarantine"][0]["flags"])

    def test_prior_explicit_holds_and_rejections_cannot_be_cleared(self) -> None:
        source = [source_row(1)]
        for disposition in ("hold", "reject"):
            with tempfile.TemporaryDirectory() as directory:
                prior = self.prior_for(source)
                decision_path = self.review_file(directory, prior["records"]["aya-fil-1"], "agent", disposition)
                prior["decisions"]["aya-fil-1"] = json.loads(decision_path.read_text())
                outputs, _ = preparation.prepare_records(source, [], expected_count=1, prior=prior)
                self.assertEqual(len(outputs["quarantine"] if disposition == "hold" else outputs["exclusions"]), 1)
                self.review_file(directory, prior["records"]["aya-fil-1"], "human", "accept")
                with self.assertRaisesRegex(ValueError, "cannot be overridden"):
                    preparation.prepare_records(source, [], decision_path, 1, prior)

    def test_untrusted_or_missing_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with self.assertRaises(FileNotFoundError):
                preparation.load_prior_screening(path)
            (path / "manifest.json").write_text('{"status": "complete"}')
            with self.assertRaisesRegex(ValueError, "pinned audited"):
                preparation.load_prior_screening(path)

    def test_trusted_receipt_requires_every_output_and_source_pin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            rows = [{"id": f"aya-fil-{i}", "prompt": f"Tanong{i}?", "response": f"Sagot{i}.",
                     "content_sha256": preparation.digest(preparation.json_bytes([f"Tanong{i}?", f"Sagot{i}."])),
                     "group_id": f"test-group-{i}", "assigned_split": "train"} for i in range(1233)]
            outputs = {"train": rows, "validation": [], "quarantine": [],
                       "exclusions": [{"id": f"aya-fil-{i}", "reason": "exact_duplicate_pair", "duplicate_of": "aya-fil-0"}
                                      for i in range(1233, 1241)], "review-decisions": []}
            hashes = preparation.write_outputs(path, outputs)
            manifest = {"status": "complete", "source": {"sha256": preparation.SOURCE_SHA256, "revision": preparation.REVISION},
                        "benchmark_screening": {"benchmark_sha256": preparation.BENCHMARK_SHA256,
                            "engineering_fixture_sha256": preparation.FIXTURE_SHA256, "task": preparation.TASK},
                        "outputs": hashes}
            receipt = path / "manifest.json"
            receipt.write_bytes(preparation.json_bytes(manifest))
            with patch.object(preparation, "PRIOR_MANIFEST_SHA256", preparation.file_hash(receipt)), \
                 patch.object(preparation, "protected_texts", side_effect=AssertionError("Do not open benchmark")):
                prior = preparation.load_prior_screening(path)
                self.assertEqual(len(prior["hashes"]), 1233)
                self.assertFalse(prior["coverage"]["benchmark_examples_read_this_run"])
                (path / "train.jsonl").write_text("changed")
                with self.assertRaisesRegex(ValueError, "checksum"):
                    preparation.load_prior_screening(path)
            manifest["source"]["revision"] = "main"
            receipt.write_bytes(preparation.json_bytes(manifest))
            with patch.object(preparation, "PRIOR_MANIFEST_SHA256", preparation.file_hash(receipt)):
                with self.assertRaisesRegex(ValueError, "source/protocol"):
                    preparation.load_prior_screening(path)

    def test_reuse_execution_does_not_open_benchmark_and_records_receipt(self) -> None:
        import pyarrow as arrow
        import pyarrow.parquet as parquet

        source = [source_row(i) for i in range(1241)]
        prior = self.prior_for(source)
        prior["coverage"] = {"mode": "reused_for_identical_source_text", "benchmark_examples_read_this_run": False}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path, card_path = root / "synthetic.parquet", root / "README.md"
            parquet.write_table(arrow.Table.from_pylist(source), source_path)
            card_path.write_text("license: apache-2.0\n")
            previous = root / "previous"
            previous.mkdir()
            (previous / "manifest.json").write_text('{"synthetic": true}')
            (previous / "review-decisions.jsonl").write_text("")
            with patch.object(preparation, "load_prior_screening", return_value=prior), \
                 patch.object(preparation, "fetch_source", return_value=(source_path, card_path)), \
                 patch.object(preparation, "protected_texts", side_effect=AssertionError("Benchmark access forbidden")):
                manifest = preparation.execute(root / "output", None, True, previous=previous)
            self.assertEqual(manifest["status"], "complete")
            self.assertFalse(manifest["benchmark_screening"]["benchmark_examples_read_this_run"])
            self.assertIn("prior-screening-manifest.json", manifest["outputs"])
            self.assertIn("prior-review-decisions.jsonl", manifest["outputs"])
            self.assertEqual(manifest["counts"]["dispositions"], 1241)

    def test_cpp_exception_and_illustration_do_not_suppress_embedded_concerns(self) -> None:
        code = {"prompt": "C++ halimbawa", "response": '#include <iostream>\nint main() { cout << "Hello"; } <<script>>'}
        self.assertIn("suspicious_formatting", preparation.heuristic_flags(code))
        example = {"prompt": 'Ano ang kahulugan sa pahayag: "ulam ngayon"?', "response": "Ang sagot ngayon ay iba na."}
        self.assertIn("time_sensitive_or_unsupported_claim", preparation.heuristic_flags(example))


if __name__ == "__main__":
    unittest.main()

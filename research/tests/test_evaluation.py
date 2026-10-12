"""Offline protocol checks; these tests must never download benchmark examples."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import evaluate
import protocol


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        protocol.prepare_upstream()

    def setUp(self) -> None:
        self.rows = protocol.load_development()

    def test_development_is_balanced_original_and_complete(self) -> None:
        self.assertEqual(len(self.rows), 20)
        self.assertEqual(len({row["id"] for row in self.rows}), 20)
        for answer in ("1", "2", "3", "4"):
            self.assertEqual(sum(row["correct_answer_num"] == answer for row in self.rows), 5)

    def test_reject_invalid_fixture_provenance_answer_and_duplicate(self) -> None:
        original = json.loads(protocol.FIXTURES.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for change in ("provenance", "answer", "duplicate", "missing-choice"):
                payload = copy.deepcopy(original)
                if change == "provenance":
                    payload["provenance"] = "belebele-test"
                elif change == "answer":
                    payload["examples"][0]["correct_answer_num"] = "0"
                elif change == "duplicate":
                    payload["examples"][1]["id"] = payload["examples"][0]["id"]
                else:
                    del payload["examples"][0]["mc_answer4"]
                protocol.write_json(path, payload)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    protocol.load_development(path)

    def test_pilot_reuses_official_prompt_and_scoring(self) -> None:
        official = protocol.official_task()
        pilot = protocol.task_module("pilot").TASKS_TABLE[0]
        self.assertIs(pilot.prompt_function, official.prompt_function)
        self.assertEqual(pilot.metric, official.metric)
        self.assertEqual([metric.metric_name for metric in pilot.metric], ["acc"])
        for row in self.rows:
            doc = pilot.prompt_function(row, "pilot")
            self.assertEqual(doc.query, official.prompt_function(row, "official").query)
            self.assertEqual(doc.gold_index, [int(row["correct_answer_num"]) - 1])
            self.assertEqual(doc.choices, [" A", " B", " C", " D"])
            for choice in range(4):
                scores = [-8.0] * 4
                scores[choice] = -0.1
                score = official.metric[0].sample_level_fn(
                    gold_ixs=doc.gold_index, choices_logprob=scores, unconditioned_logprob=None,
                    choices_tokens=None, formatted_doc=doc,
                )
                self.assertEqual(score, int(choice == doc.gold_index[0]))
                self.assertEqual(protocol.checked_prediction(scores, doc.gold_index, score), choice)

    def test_official_entry_point_and_revision_only_override(self) -> None:
        module = protocol.task_module("evaluate")
        self.assertTrue(Path(module.__file__).as_posix().endswith("community_tasks/filbench_evals.py"))
        task = next(task for task in module.TASKS_TABLE if task.name == "belebele_fil_mcf")
        self.assertEqual(task.hf_revision, protocol.DATASET_REVISION)
        self.assertEqual(task.hf_subset, "tgl_Latn")
        self.assertEqual(task.hf_repo, "facebook/belebele")
        self.assertEqual(task.evaluation_splits, ("test",))
        self.assertIs(task.prompt_function, protocol.official_task().prompt_function)

    def test_pilot_cannot_load_benchmark_or_any_external_dataset(self) -> None:
        with patch("datasets.load_dataset", side_effect=AssertionError("External data accessed")) as remote:
            loader = protocol.dataset_loader("pilot", self.rows)
            local = loader(protocol.LOCAL_DATASET, "default", False)
            self.assertEqual(len(local["development"]), 20)
            for name in (protocol.DATASET_ID, "another/dataset"):
                with self.assertRaisesRegex(RuntimeError, "blocks every external"):
                    loader(name, "tgl_Latn", False, revision=protocol.DATASET_REVISION)
            remote.assert_not_called()

    def test_benchmark_loader_pins_and_requires_900_without_real_data(self) -> None:
        with patch("datasets.load_dataset", return_value={"test": range(900)}) as remote:
            loader = protocol.dataset_loader("evaluate", [])
            loader(protocol.DATASET_ID, "tgl_Latn", False, revision=protocol.DATASET_REVISION)
            remote.assert_called_once_with(protocol.DATASET_ID, "tgl_Latn",
                                           revision=protocol.DATASET_REVISION, trust_remote_code=False)
            with self.assertRaises(RuntimeError):
                loader(protocol.DATASET_ID, "tgl_Latn", False, revision="main")
            remote.return_value = {"test": range(899)}
            with self.assertRaisesRegex(RuntimeError, "900"):
                loader(protocol.DATASET_ID, "tgl_Latn", False, revision=protocol.DATASET_REVISION)

    def test_invalid_revisions_and_cpu_precision_are_rejected(self) -> None:
        config, _ = evaluate.parse_args(["pilot"])
        self.assertEqual(config.model_revision, protocol.PILOT_REVISION)
        self.assertEqual(config.tokenizer_revision, protocol.PILOT_REVISION)
        for changes in ({"model_revision": "main"}, {"tokenizer_revision": "v1"},
                        {"dtype": "float16"}, {"threads": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(config, **changes)

    def test_baseline_requires_independent_tokenizer_revision(self) -> None:
        config, _ = evaluate.parse_args([
            "evaluate", "--model", "example/model", "--model-revision", "a" * 40,
            "--tokenizer", "example/tokenizer", "--tokenizer-revision", "b" * 40,
        ])
        self.assertEqual(config.model_revision, "a" * 40)
        self.assertEqual(config.tokenizer_revision, "b" * 40)

    def test_likelihood_validation_ties_and_mismatched_metric(self) -> None:
        self.assertEqual(protocol.checked_prediction([-1.0] * 4, [0], 1), 0)
        for scores, gold, score in (([float("nan")] * 4, [0], 1),
                                    ([-1.0] * 3, [0], 1), ([-1.0] * 4, [4], 0),
                                    ([-1.0, -2.0, -3.0, -4.0], [0], 0)):
            with self.assertRaises(ValueError):
                protocol.checked_prediction(scores, gold, score)

    def test_context_preflight_aborts_before_truncation(self) -> None:
        from lighteval.tasks.requests import RequestType

        request = SimpleNamespace(context="text", choice=" A", sample_index=2)
        model = SimpleNamespace(max_length=4, pairwise_tokenization=False,
                                tok_encode_pair=lambda *args, **kwargs: ([1, 2, 3, 4], [5, 6]))
        pipeline = SimpleNamespace(model=model, requests={RequestType.LOGLIKELIHOOD: [request]})
        with self.assertRaisesRegex(RuntimeError, "no truncation"):
            evaluate.check_context_lengths(pipeline)
        model.max_length = 5
        self.assertEqual(evaluate.check_context_lengths(pipeline), 5)

    def test_cpu_selection_and_missing_cuda(self) -> None:
        config, _ = evaluate.parse_args(["pilot", "--device", "cuda"])
        with patch("torch.cuda.is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "no CPU fallback"):
                evaluate.initialize_runtime(config)

    def test_failure_manifest_is_incomplete(self) -> None:
        config, _ = evaluate.parse_args(["pilot"])
        with tempfile.TemporaryDirectory() as directory:
            with patch("evaluate.perform_evaluation", side_effect=RuntimeError("test failure")):
                with self.assertRaises(RuntimeError):
                    evaluate.run(config, Path(directory))
            run_dir = next(Path(directory).iterdir())
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "incomplete")
            self.assertFalse(manifest["benchmark_accessed"])
            self.assertIn("test failure", manifest["error"])
            self.assertFalse((run_dir / "metrics.json").exists())

    def test_portable_samples_are_consistent_with_official_details(self) -> None:
        from lighteval.logging.info_loggers import DetailsLogger

        doc = protocol.official_task().prompt_function(self.rows[0], "pilot")
        detail = DetailsLogger.Detail(
            example=doc.query, full_prompt=doc.query, gold_index=[0],
            num_asked_few_shots=0, num_effective_few_shots=0,
            predictions=[(-0.1, False), (-2.0, False), (-3.0, False), (-4.0, False)],
            truncated=[0, 0, 0, 0], metrics={"acc": 1},
        )
        tracker = SimpleNamespace(details_logger=SimpleNamespace(details={"custom|makata_pilot|0": [detail]}))
        with tempfile.TemporaryDirectory() as directory:
            count, accuracy = evaluate.save_samples(tracker, Path(directory), self.rows)
            sample = json.loads((Path(directory) / "samples.jsonl").read_text(encoding="utf-8"))
            self.assertEqual((count, accuracy), (1, 1.0))
            self.assertEqual(sample["sample_id"], "dev-01")
            self.assertEqual(sample["predicted_index"], sample["gold_index"])
            self.assertEqual(sample["official_detail"]["metrics"], {"acc": 1})
            detail.truncated = [1]
            with self.assertRaisesRegex(RuntimeError, "truncated"):
                evaluate.save_samples(tracker, Path(directory), self.rows)
            detail.truncated = [0]
            detail.num_effective_few_shots = 1
            with self.assertRaisesRegex(RuntimeError, "zero-shot"):
                evaluate.save_samples(tracker, Path(directory), self.rows)

    def test_actual_official_logging_accepts_prompt_strings(self) -> None:
        from lighteval.logging.info_loggers import DetailsLogger
        from lighteval.models.model_output import LoglikelihoodResponse
        from lighteval.tasks.lighteval_task import LightevalTask

        task = LightevalTask("custom|makata_pilot", protocol.task_module("pilot").TASKS_TABLE[0])
        doc = task.formatter(self.rows[0], task.name)
        doc.ctx = doc.query
        logger = DetailsLogger()
        logger.log(task.name, task, doc,
                   [LoglikelihoodResponse(result=(score, False)) for score in (-0.1, -2.0, -3.0, -4.0)],
                   {"acc": 1})
        self.assertEqual(len(logger.hashes[task.name]), 1)
        self.assertEqual(logger.details[task.name][0].gold_index, [0])

    def test_model_and_tokenizer_revisions_reach_separate_loaders(self) -> None:
        config = protocol.RunConfig("evaluate", "example/model", "a" * 40,
                                    "example/tokenizer", "b" * 40)
        with patch("huggingface_hub.HfApi") as api, \
             patch("huggingface_hub.snapshot_download", return_value="C:/pinned-tokenizer") as snapshot, \
             patch("lighteval.models.transformers.transformers_model.TransformersModel") as model:
            api.return_value.model_info.side_effect = lambda repo, revision: SimpleNamespace(sha=revision)
            model.return_value.model.config.is_encoder_decoder = False
            evaluate.load_model(config)
            snapshot.assert_called_once()
            self.assertEqual(snapshot.call_args.args, ("example/tokenizer",))
            self.assertEqual(snapshot.call_args.kwargs["revision"], "b" * 40)
            passed_config = model.call_args.args[0]
            self.assertEqual(passed_config.revision, "a" * 40)
            self.assertEqual(passed_config.tokenizer, "C:/pinned-tokenizer")
            self.assertFalse(passed_config.trust_remote_code)
            self.assertFalse(passed_config.use_chat_template)


if __name__ == "__main__":
    unittest.main()

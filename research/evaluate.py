"""Run the local engineering pilot or the explicitly selected held-out baseline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import shutil
import sys
import time
import uuid
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from protocol import (
    DATASET_ID, DATASET_REVISION, DATASET_SUBSET, FILBENCH_REVISION, FIXTURES,
    OFFICIAL_ENTRY_POINT, OFFICIAL_TASK, PILOT_MODEL, PILOT_REVISION, PILOT_TASK,
    ROOT, Example, RunConfig, checked_prediction, dataset_loader, file_hash,
    load_development, official_task, prepare_upstream, task_module, write_json,
)

if TYPE_CHECKING:
    from lighteval.logging.evaluation_tracker import EvaluationTracker
    from lighteval.models.transformers.transformers_model import TransformersModel
    from lighteval.pipeline import Pipeline


def parse_args(argv: list[str] | None = None) -> tuple[RunConfig, Path]:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for name in ("pilot", "evaluate"):
        command = modes.add_parser(name)
        command.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
        command.add_argument("--dtype", choices=("float32", "float16", "bfloat16"), default="float32")
        command.add_argument("--threads", type=int, default=4)
        command.add_argument("--output", type=Path, default=ROOT / "runs")
        if name == "evaluate":
            command.add_argument("--model", required=True)
            command.add_argument("--model-revision", required=True)
            command.add_argument("--tokenizer", required=True)
            command.add_argument("--tokenizer-revision", required=True)
    args = parser.parse_args(argv)
    if args.mode == "pilot":
        config = RunConfig("pilot", PILOT_MODEL, PILOT_REVISION, PILOT_MODEL, PILOT_REVISION,
                           args.device, args.dtype, args.threads)
    else:
        config = RunConfig("evaluate", args.model, args.model_revision, args.tokenizer,
                           args.tokenizer_revision, args.device, args.dtype, args.threads)
    return config, args.output.resolve()


def initialize_runtime(config: RunConfig) -> None:
    # Accelerate chooses its device from the environment, not just the model config.
    os.environ["ACCELERATE_USE_CPU"] = "true" if config.device == "cpu" else "false"
    os.environ["HF_HOME"] = str(ROOT / ".cache" / "huggingface")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use the isolated Python 3.12 research environment.")
    import torch

    if config.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable; no CPU fallback was performed.")
    if config.dtype == "bfloat16" and not torch.cuda.is_bf16_supported():
        raise RuntimeError("The selected CUDA device does not support bfloat16.")
    if config.device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(config.threads)
    torch.manual_seed(1234)
    prepare_upstream()


def load_model(config: RunConfig) -> TransformersModel:
    from huggingface_hub import HfApi, snapshot_download
    from lighteval.models.transformers.transformers_model import TransformersModel, TransformersModelConfig

    api = HfApi()
    for repo, revision in ((config.model, config.model_revision), (config.tokenizer, config.tokenizer_revision)):
        if api.model_info(repo, revision=revision).sha != revision:
            raise RuntimeError(f"Could not verify immutable revision for {repo}.")
    # The pinned harness has one shared revision field. A local snapshot gives the
    # tokenizer its independent commit without modifying the harness's loader.
    tokenizer_path = snapshot_download(
        config.tokenizer, revision=config.tokenizer_revision,
        allow_patterns=["tokenizer*", "special_tokens_map.json", "added_tokens.json", "config.json",
                        "vocab.*", "merges.txt", "*.model", "chat_template*"],
    )
    model_config = TransformersModelConfig(
        model_name=config.model, revision=config.model_revision, tokenizer=tokenizer_path,
        batch_size=1, dtype=config.dtype, device=config.device, model_parallel=False,
        use_chat_template=False, trust_remote_code=False,
        model_loading_kwargs={"low_cpu_mem_usage": True},
    )
    model = TransformersModel(model_config)
    if model.model.config.is_encoder_decoder:
        raise RuntimeError("This study requires a decoder-only causal language model.")
    return model


def check_context_lengths(pipeline: Pipeline) -> int:
    """Check actual harness requests before its automatic truncation can run."""
    from lighteval.tasks.requests import RequestType

    maximum = 0
    for kind, requests in pipeline.requests.items():
        if kind not in (RequestType.LOGLIKELIHOOD, RequestType.LOGLIKELIHOOD_SINGLE_TOKEN):
            raise RuntimeError("Only likelihood-based multiple-choice requests are allowed.")
        for request in requests:
            if kind == RequestType.LOGLIKELIHOOD:
                context, continuation = pipeline.model.tok_encode_pair(
                    request.context, request.choice, pairwise=pipeline.model.pairwise_tokenization
                )
                required = len(context) + len(continuation) - 1
            else:
                required = len(pipeline.model.tok_encode(request.context))
            maximum = max(maximum, required)
            if required > pipeline.model.max_length:
                raise RuntimeError(
                    f"Sample {request.sample_index} needs {required} tokens, exceeding "
                    f"context {pipeline.model.max_length}; no truncation permitted."
                )
    return maximum


def save_samples(tracker: EvaluationTracker, directory: Path, rows: list[Example]) -> tuple[int, float]:
    from dataclasses import asdict as detail_dict

    source_ids = {official_task().prompt_function(row, "").query: row["id"] for row in rows}
    count, correct = 0, 0.0
    seen: set[str] = set()
    with (directory / "samples.jsonl").open("w", encoding="utf-8") as stream:
        for task_name, details in tracker.details_logger.details.items():
            for detail in details:
                if detail.num_asked_few_shots != 0 or detail.num_effective_few_shots != 0:
                    raise RuntimeError("This study requires zero-shot prompts; few-shot examples were detected.")
                if any(value != 0 for value in detail.truncated):
                    raise RuntimeError("The harness truncated an input; run cannot be reported as complete.")
                scores = [float(value[0] if isinstance(value, (tuple, list)) else value)
                          for value in detail.predictions]
                accuracy = float(detail.metrics["acc"])
                predicted = checked_prediction(scores, detail.gold_index, accuracy)
                prompt_hash = hashlib.sha256(detail.full_prompt.encode("utf-8")).hexdigest()
                sample_id = source_ids.get(detail.example, prompt_hash)
                if sample_id in seen:
                    raise RuntimeError("Duplicate scored sample; run cannot be reported as complete.")
                seen.add(sample_id)
                record = {
                    "sample_id": sample_id,
                    "task": task_name, "prompt_sha256": prompt_hash,
                    "choice_log_likelihoods": scores, "predicted_index": predicted,
                    "gold_index": detail.gold_index[0], "accuracy": accuracy,
                    "official_detail": detail_dict(detail),
                }
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                count += 1
                correct += accuracy
    if not count:
        raise RuntimeError("The harness returned no scored examples.")
    return count, correct / count


def hardware_snapshot() -> dict[str, Any]:
    import psutil

    memory = psutil.virtual_memory()
    return {
        "processor": platform.processor(), "logical_cpus": os.cpu_count(),
        "physical_cpus": psutil.cpu_count(logical=False),
        "ram_total_bytes": memory.total, "ram_available_bytes": memory.available,
        "disk_free_bytes": shutil.disk_usage(ROOT).free,
    }


def manifest_for(config: RunConfig) -> dict[str, Any]:
    return {
        "status": "incomplete", "purpose": "engineering-pilot" if config.mode == "pilot" else "baseline",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "configuration": asdict(config), "filbench_revision": FILBENCH_REVISION,
        "task": PILOT_TASK if config.mode == "pilot" else OFFICIAL_TASK,
        "custom_entry_point": "local development module" if config.mode == "pilot" else OFFICIAL_ENTRY_POINT,
        "data": ({"source": "original-synthetic-development", "sha256": file_hash(FIXTURES), "expected_samples": 20}
                 if config.mode == "pilot" else {"repository": DATASET_ID, "revision": DATASET_REVISION,
                     "subset": DATASET_SUBSET, "split": "test", "expected_samples": 900, "license": "CC-BY-SA-4.0"}),
        "protocol": {"few_shots": 0, "chat_template": False, "system_prompt": None,
                     "batch_size": 1, "seed": 1234, "truncation": "abort", "uploads": False},
        "software": {"python": sys.version, "platform": platform.platform(),
                     "packages": {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()}},
        "code_sha256": {name: file_hash(ROOT / name) for name in (
            "evaluate.py", "protocol.py", "requirements.txt", "requirements-colab.txt", "colab/run.py",
        ) if (ROOT / name).is_file()},
        "baseline_plan_sha256": file_hash(ROOT / "baseline-plan.json"),
        "benchmark_accessed": False,
        "hardware": hardware_snapshot(),
    }


def perform_evaluation(config: RunConfig, directory: Path, manifest: dict[str, Any]) -> None:
    initialize_runtime(config)
    import torch
    from lighteval.logging.evaluation_tracker import EvaluationTracker
    from lighteval.pipeline import ParallelismManager, Pipeline, PipelineParameters

    rows = load_development() if config.mode == "pilot" else []
    module = task_module(config.mode)

    def record_benchmark_access() -> None:
        manifest["benchmark_accessed"] = True
        write_json(directory / "manifest.json", manifest)

    loader = dataset_loader(config.mode, rows, on_benchmark_access=record_benchmark_access)
    manifest["hardware"].update({
        "torch_threads": torch.get_num_threads(), "requested_device": config.device,
        "gpu": torch.cuda.get_device_name(0) if config.device == "cuda" else None,
        "gpu_vram_bytes": torch.cuda.get_device_properties(0).total_memory if config.device == "cuda" else None,
    })
    write_json(directory / "manifest.json", manifest)
    if config.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    model = load_model(config)
    if model.device.type != config.device:
        raise RuntimeError(f"Requested {config.device}, loaded {model.device}; device substitution is forbidden.")
    manifest["hardware"]["device"] = str(model.device)
    manifest["model_context_limit"] = model.max_length
    tracker = EvaluationTracker(output_dir=str(directory), save_details=True,
                                push_to_hub=False, push_to_tensorboard=False, public=False)

    with ExitStack() as boundaries:
        # The old fork has no local-data option. These scoped adapters change only
        # loading, and are restored even if evaluation fails.
        for target in ("lighteval.tasks.lighteval_task.download_dataset_worker",
                       "lighteval.utils.utils.download_dataset_worker"):
            boundaries.enter_context(patch(target, loader))
        if config.mode == "pilot":
            boundaries.enter_context(patch("datasets.load_dataset", side_effect=RuntimeError(
                "Pilot mode cannot load external datasets.")))
        pipeline = Pipeline(
            tasks=PILOT_TASK if config.mode == "pilot" else OFFICIAL_TASK,
            pipeline_parameters=PipelineParameters(
                launcher_type=ParallelismManager.ACCELERATE, custom_tasks_directory=module,
                dataset_loading_processes=1, max_samples=None, use_chat_template=False,
                system_prompt=None, num_fewshot_seeds=1,
            ),
            evaluation_tracker=tracker, model=model,
        )
        manifest["maximum_input_tokens"] = check_context_lengths(pipeline)
        if config.device == "cuda":
            free, _ = torch.cuda.mem_get_info()
            estimate = 2 * manifest["maximum_input_tokens"] * model.model.config.vocab_size * 4 + 2 * 1024**3
            manifest["hardware"].update(gpu_free_before_inference_bytes=free,
                                        gpu_inference_allowance_bytes=estimate, tf32=False)
            if free < estimate:
                raise RuntimeError("Insufficient free GPU memory for logits and runtime allowance; no truncation or CPU fallback.")
        write_json(directory / "manifest.json", manifest)
        if config.device == "cuda":
            torch.cuda.synchronize()
        inference_started = time.perf_counter()
        pipeline.evaluate()
        if config.device == "cuda":
            torch.cuda.synchronize()
            manifest["hardware"].update(
                peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
            )
        manifest["inference_seconds"] = round(time.perf_counter() - inference_started, 6)
        results = pipeline.get_results()["results"]
        count, accuracy = save_samples(tracker, directory, rows)
        if count != manifest["data"]["expected_samples"]:
            raise RuntimeError(f"Incomplete run: scored {count} examples.")
        scored = [value["acc"] for key, value in results.items() if key != "all" and "acc" in value]
        if len(scored) != 1 or abs(float(scored[0]) - accuracy) > 1e-12:
            raise RuntimeError("Aggregate accuracy disagrees with saved per-example scores.")
        write_json(directory / "metrics.json", {
            "purpose": manifest["purpose"], "sample_count": count,
            "official_task_metrics": results,
            "notice": "Synthetic engineering data; not a Filipino benchmark." if config.mode == "pilot"
                      else "Tagalog translated-passage comprehension only; not general Filipino capability.",
        })
        write_json(directory / "qualitative-review.json", {
            "notice": "Separate optional human annotations; never alter benchmark metrics.", "annotations": [],
        })
        manifest.update(status="complete", sample_count=count,
                        samples_sha256=file_hash(directory / "samples.jsonl"))


def run(config: RunConfig, output: Path, execution_profile: dict[str, Any] | None = None) -> Path:
    directory = output / f"{config.mode}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    directory.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    manifest = manifest_for(config)
    if execution_profile is not None:
        manifest["execution_profile"] = execution_profile
        manifest["execution_profile_sha256"] = hashlib.sha256(
            json.dumps(execution_profile, sort_keys=True, allow_nan=False).encode()
        ).hexdigest()
    write_json(directory / "manifest.json", manifest)
    try:
        perform_evaluation(config, directory, manifest)
    except BaseException as error:
        manifest.update(status="incomplete", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        manifest.update(finished_at=datetime.now(timezone.utc).isoformat(),
                        runtime_seconds=round(time.perf_counter() - started, 3))
        write_json(directory / "manifest.json", manifest)
    return directory


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config, output = parse_args(argv)
        directory = run(config, output)
    except Exception as error:
        print(f"Evaluation stopped: {type(error).__name__}: {error}\n"
              "Any created run directory remains marked incomplete. See research/README.md.", file=sys.stderr)
        return 1
    print(f"Verified local {config.mode} artifacts: {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify frozen candidates without downloading weights or benchmark examples."""

from __future__ import annotations

import json
import importlib.metadata
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from evaluate import check_context_lengths, hardware_snapshot
from protocol import (
    DATASET_REVISION, FILBENCH_REVISION, OFFICIAL_TASK, ROOT, RunConfig,
    file_hash, load_development, official_task, prepare_upstream, write_json,
)

PLAN = ROOT / "baseline-plan.json"
GIB = 1024**3


def read_plan() -> dict[str, Any]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if (plan["task"], plan["filbench_revision"], plan["dataset"]["revision"]) != (
        OFFICIAL_TASK, FILBENCH_REVISION, DATASET_REVISION
    ):
        raise ValueError("Frozen study pins disagree with the evaluator.")
    for candidate in plan["candidates"]:
        RunConfig("evaluate", candidate["model"], candidate["model_revision"],
                  candidate["tokenizer"], candidate["tokenizer_revision"])
    return plan


def memory_budget(parameters: int, vocab: int, context: int) -> dict[str, int]:
    # This is a conservative planning screen, not a prediction of peak RSS.
    # The harness materializes both logits and log-softmax over the full input.
    weights = parameters * 4
    logits = context * vocab * 4 * 2
    return {
        "float32_weight_bytes": weights,
        "logits_and_log_softmax_bytes": logits,
        "loading_and_runtime_allowance_bytes": weights + 2 * GIB,
        "required_available_ram_bytes": weights * 2 + logits + 2 * GIB,
    }


def inspect_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    import torch
    from huggingface_hub import HfApi, snapshot_download
    from lighteval.models.transformers.transformers_model import TransformersModel
    from lighteval.tasks.requests import RequestType
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    api = HfApi()
    for repo, revision in ((candidate["model"], candidate["model_revision"]),
                           (candidate["tokenizer"], candidate["tokenizer_revision"])):
        info = api.model_info(repo, revision=revision, files_metadata=True)
        if info.sha != revision or info.gated or info.private:
            raise RuntimeError(f"Checkpoint is not publicly accessible at its pin: {repo}")
        if info.card_data is None or info.card_data.get("license") != "apache-2.0":
            raise RuntimeError(f"Expected the reviewed Apache-2.0 license declaration: {repo}")
    config = AutoConfig.from_pretrained(
        candidate["model"], revision=candidate["model_revision"], trust_remote_code=False,
    )
    if config.model_type != candidate["model_type"] or config.is_encoder_decoder:
        raise RuntimeError("Frozen candidate architecture mismatch.")
    if config.max_position_embeddings != candidate["context_tokens"]:
        raise RuntimeError("Frozen context capacity mismatch.")
    # Meta tensors have shapes but no weight storage; no pretrained weights load.
    with torch.device("meta"):
        empty = AutoModelForCausalLM.from_config(config, trust_remote_code=False)
    parameters = sum(parameter.numel() for parameter in empty.parameters())
    if parameters != candidate["parameters"]:
        raise RuntimeError(f"Parameter count mismatch: {parameters}")
    del empty
    tokenizer_path = snapshot_download(
        candidate["tokenizer"], revision=candidate["tokenizer_revision"],
        allow_patterns=["tokenizer*", "special_tokens_map.json", "added_tokens.json", "config.json",
                        "vocab.*", "merges.txt", "*.model", "chat_template*"],
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=False)
    model = object.__new__(TransformersModel)
    model._tokenizer = tokenizer
    model._add_special_tokens = True
    model._max_length = config.max_position_embeddings
    model.pairwise_tokenization = False
    requests = []
    continuations: set[tuple[int, ...]] = set()
    for row in load_development():
        doc = official_task().prompt_function(row, "development-preflight")
        for choice in doc.choices:
            context, answer = model.tok_encode_pair(doc.query, choice, pairwise=False)
            if not context or not answer or any(token >= config.vocab_size for token in context + answer):
                raise RuntimeError("Invalid tokenizer/model vocabulary alignment.")
            continuations.add(tuple(answer))
            requests.append(SimpleNamespace(context=doc.query, choice=choice, sample_index=row["id"]))
    maximum = check_context_lengths(SimpleNamespace(
        model=model, requests={RequestType.LOGLIKELIHOOD: requests},
    ))
    return {
        "model": candidate["model"], "architecture": config.architectures,
        "parameters": parameters, "context_tokens": config.max_position_embeddings,
        "development_questions": 20, "scoring_requests": len(requests),
        "development_maximum_input_tokens": maximum,
        "answer_token_sequences": sorted(continuations),
        "tokenizer_files_sha256": {
            path.name: file_hash(path) for path in sorted(Path(tokenizer_path).iterdir()) if path.is_file()
        },
        "memory_at_full_context": memory_budget(parameters, config.vocab_size, config.max_position_embeddings),
        "memory_at_2048_tokens": memory_budget(parameters, config.vocab_size, 2048),
        "notice": "Architecture and tokenizer verified; pretrained inference has not been tested.",
    }


def main() -> int:
    # Keep all Hub metadata/tokenizer downloads inside the ignored research cache.
    import os

    os.environ["HF_HOME"] = str(ROOT / ".cache" / "huggingface")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use the isolated Python 3.12 research environment.")
    plan = read_plan()
    prepare_upstream()
    import torch

    report: dict[str, Any] = {
        "purpose": "candidate-preflight", "status": "incomplete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": file_hash(PLAN), "hardware": hardware_snapshot(),
        "torch_version": torch.__version__, "cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "benchmark_accessed": False, "weights_downloaded": False, "candidates": [],
        "code_sha256": {name: file_hash(ROOT / name) for name in (
            "preflight.py", "evaluate.py", "protocol.py", "requirements.txt",
        )},
        "packages": {name: importlib.metadata.version(name) for name in (
            "torch", "transformers", "accelerate", "huggingface-hub", "datasets",
        )},
    }
    directory = ROOT / "runs" / f"preflight-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}"
    directory.mkdir(parents=True)
    path = directory / "preflight.json"
    write_json(path, report)
    try:
        for candidate in plan["candidates"]:
            report["candidates"].append(inspect_candidate(candidate))
            write_json(path, report)
        report["hardware_after_checks"] = hardware_snapshot()
        available = report["hardware_after_checks"]["ram_available_bytes"]
        report["blockers"] = [
            f"{item['model']}: planning budget assuming 2048-token requests is "
            f"{item['memory_at_2048_tokens']['required_available_ram_bytes'] / GIB:.2f} GiB "
            f"available RAM; observed {available / GIB:.2f} GiB."
            for item in report["candidates"]
            if available < item["memory_at_2048_tokens"]["required_available_ram_bytes"]
        ]
        disk_required = sum(item["weight_download_bytes"] for item in plan["candidates"]) * 2 + 2 * GIB
        if report["hardware_after_checks"]["disk_free_bytes"] < disk_required:
            report["blockers"].append(f"Need {disk_required} free disk bytes including cache-copy allowance.")
        report["status"] = "blocked" if report["blockers"] else "checks-passed"
        report["notice"] = "Not authorization to start a long run; estimate runtime before evaluation."
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        write_json(path, report)
    print(f"Candidate preflight {report['status']}: {path}")
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())

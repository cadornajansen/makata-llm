"""Study pins and the boundary between local development data and held-out data."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Literal, TypedDict

if TYPE_CHECKING:
    from datasets import DatasetDict
    from lighteval.tasks.lighteval_task import LightevalTaskConfig

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / ".cache" / "filbench-lighteval"
FIXTURES = ROOT / "fixtures" / "development.json"
FILBENCH_REVISION = "7ad52795d7d218d4679f93a019b58dde4b749c5b"
PILOT_MODEL = "HuggingFaceTB/SmolLM2-135M"
PILOT_REVISION = "93efa2f097d58c2a74874c7e644dbc9b0cee75a2"
DATASET_ID = "facebook/belebele"
DATASET_REVISION = "7899cdfa4e1e0d733fd77c848e2c273cb1d32be2"
DATASET_SUBSET = "tgl_Latn"
OFFICIAL_TASK = "filbench|belebele_fil_mcf|0|0"
PILOT_TASK = "custom|makata_pilot|0|0"
LOCAL_DATASET = "makata/local-development"
OFFICIAL_ENTRY_POINT = "community_tasks.filbench_evals"


class Example(TypedDict):
    id: str
    flores_passage: str
    question: str
    mc_answer1: str
    mc_answer2: str
    mc_answer3: str
    mc_answer4: str
    correct_answer_num: str
    explanation: str


@dataclass(frozen=True)
class RunConfig:
    mode: Literal["pilot", "evaluate"]
    model: str
    model_revision: str
    tokenizer: str
    tokenizer_revision: str
    device: Literal["cpu", "cuda"] = "cpu"
    dtype: Literal["float32", "float16", "bfloat16"] = "float32"
    threads: int = 4

    def __post_init__(self) -> None:
        for revision in (self.model_revision, self.tokenizer_revision):
            if not re.fullmatch(r"[0-9a-f]{40}", revision):
                raise ValueError("Model and tokenizer revisions must be full lowercase commit SHAs.")
        if self.device == "cpu" and self.dtype != "float32":
            raise ValueError("CPU evaluation requires float32.")
        if self.threads < 1:
            raise ValueError("threads must be positive.")


def prepare_upstream() -> None:
    """Use the audited checkout, including task modules absent from the wheel."""
    if not UPSTREAM.is_dir():
        raise RuntimeError("Pinned FilBench checkout missing. Follow research/README.md setup instructions.")
    revision = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != FILBENCH_REVISION:
        raise RuntimeError("FilBench checkout revision does not match the study pin.")
    subprocess.run(["git", "-C", str(UPSTREAM), "diff", "--exit-code", "HEAD"], check=True, capture_output=True)
    sys.path.insert(0, str(UPSTREAM))
    import lighteval

    if not Path(lighteval.__file__).resolve().is_relative_to(UPSTREAM / "src"):
        raise RuntimeError("Lighteval must be installed editable from the pinned FilBench checkout.")


def load_development(path: Path = FIXTURES) -> list[Example]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("provenance") != "makata-original-synthetic-development":
        raise ValueError("Pilot data must have original synthetic development provenance.")
    rows = payload["examples"]
    if len(rows) != 20:
        raise ValueError("The pilot requires exactly 20 development questions.")
    ids: set[str] = set()
    for row in rows:
        required = ("id", "flores_passage", "question", "explanation", *(f"mc_answer{i}" for i in range(1, 5)))
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in required):
            raise ValueError("Every question needs nonempty text, four choices, an ID, and an explanation.")
        if row["id"] in ids or not row["id"].startswith("dev-"):
            raise ValueError("Development IDs must be unique and start with dev-.")
        if row.get("correct_answer_num") not in ("1", "2", "3", "4"):
            raise ValueError("Answer labels must be strings from 1 to 4.")
        if len({row[f"mc_answer{i}"] for i in range(1, 5)}) != 4:
            raise ValueError("Answer choices must be distinct.")
        ids.add(row["id"])
    return rows


def official_task() -> LightevalTaskConfig:
    from filbench.belebele import FILIPINO_BELEBELE_TASKS

    return next(task for task in FILIPINO_BELEBELE_TASKS if task.name == "belebele_fil_mcf")


def task_module(mode: Literal["pilot", "evaluate"]) -> ModuleType:
    if mode == "evaluate":
        module = importlib.import_module(OFFICIAL_ENTRY_POINT)
        selected = next(task for task in module.TASKS_TABLE if task.name == "belebele_fil_mcf")
        selected.hf_revision = DATASET_REVISION
        return module
    module = ModuleType("makata_development_task")
    module.__file__ = str(Path(__file__).resolve())
    # Only the data source and task identity change; prompt and metric objects are reused.
    module.TASKS_TABLE = [replace(  # type: ignore[attr-defined]
        official_task(), name="makata_pilot", suite=("custom",),
        hf_repo=LOCAL_DATASET, hf_subset="default", hf_revision=None,
        evaluation_splits=("development",), hf_avail_splits=("development",),
    )]
    return module


def dataset_loader(mode: Literal["pilot", "evaluate"], rows: list[Example]) -> Callable[..., DatasetDict]:
    """Replace only the harness's data-loading boundary, never prompt or scoring code."""
    from datasets import Dataset, DatasetDict, load_dataset

    def load(
        dataset_path: str, dataset_config_name: str, trust_dataset: bool,
        dataset_filter: Callable[[dict[str, Any]], bool] | None = None,
        revision: str | None = None,
    ) -> DatasetDict:
        if mode == "pilot":
            if (dataset_path, dataset_config_name, revision) != (LOCAL_DATASET, "default", None):
                raise RuntimeError("Pilot mode blocks every external dataset, including Belebele.")
            return DatasetDict({"development": Dataset.from_list(rows)})
        if (dataset_path, dataset_config_name, revision) != (DATASET_ID, DATASET_SUBSET, DATASET_REVISION):
            raise RuntimeError("Benchmark mode requires the pinned Belebele Tagalog subset.")
        if trust_dataset or dataset_filter is not None:
            raise RuntimeError("Remote dataset code and benchmark filtering are not allowed.")
        data = load_dataset(DATASET_ID, DATASET_SUBSET, revision=DATASET_REVISION, trust_remote_code=False)
        if len(data["test"]) != 900:
            raise RuntimeError("Expected all 900 Belebele Tagalog test questions; aborting.")
        return data

    return load


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_prediction(scores: list[float], gold: list[int], accuracy: float) -> int:
    if len(scores) != 4 or any(not math.isfinite(score) for score in scores):
        raise ValueError("Expected four finite answer likelihoods.")
    if len(gold) != 1 or gold[0] not in range(4):
        raise ValueError("Expected one valid zero-based gold index.")
    # Python max and NumPy argmax both select the first index in a tie.
    prediction = max(range(4), key=scores.__getitem__)
    if accuracy != float(prediction == gold[0]):
        raise ValueError("Saved prediction disagrees with the official accuracy metric.")
    return prediction

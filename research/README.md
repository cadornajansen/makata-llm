# First study: evaluation before adaptation

This isolated Python environment supports Makata's [first-study protocol](../docs/first-study.md). The eventual technical objective is Filipino GPU fine-tuning; this first study prepares a reliable baseline evaluation pipeline. No Makata model has been trained and no serious-model baseline has been measured.

The task measures **Tagalog reading comprehension using translated passages**. It does not directly measure Taglish conversation, native cultural knowledge, or general Filipino proficiency. The 20 AI-assisted, original synthetic development questions are deliberately separate from Belebele and are not a validated research benchmark.

## Setup on Windows

Run these commands in PowerShell from the repository root. Use the already installed `uv` and Git. The environment is Python **3.12.13**; no pnpm dependency changes are needed.

```powershell
cd C:\Development\makata-llm\research
uv venv --python 3.12.13 .venv
git clone https://github.com/filbench/lighteval.git .cache/filbench-lighteval
git -C .cache/filbench-lighteval checkout 7ad52795d7d218d4679f93a019b58dde4b749c5b
uv pip sync --python .venv/Scripts/python.exe --torch-backend cpu requirements.txt
uv pip check --python .venv/Scripts/python.exe
```

If `.venv` and the pinned checkout already exist, skip their creation and run the sync/check commands. The runner rejects a different or modified tracked checkout. The editable install is intentional: upstream task modules live outside the installable `src` package. `requirements.txt` pins every installed distribution. PyArrow 20.0.0 is pinned because the fork requires NumPy 1.x, incompatible with PyArrow 26. xxhash 3.5.0 preserves the harness's string-hashing API; version 4 rejects those strings. The official registry imports other multilingual task definitions, so its import dependencies are included even though only one task is selected. Importing that registry can also initialize upstream NLTK resources; it does not load benchmark examples.

This lock is verified on Windows x64 with CPU PyTorch. CUDA execution requires a separately verified CUDA PyTorch environment and hardware; do not treat this CPU lock as a GPU installation recipe. The CLI supports explicit CUDA selection and precision but never silently falls back to CPU. Other operating systems have not been verified.

## Test, then run the pilot

From the repository root:

```powershell
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe research/evaluate.py pilot
```

Pilot mode downloads only the pinned SmolLM2-135M model and tokenizer from Hugging Face (approximately 270 MB of model weights plus dependencies), then scores all 20 local questions on CPU in float32, batch size one, using four CPU threads. Initial imports and downloads can take several minutes. Cached repeat runs avoid downloading weights again. SmolLM2 is primarily English-focused; these outputs are engineering checks, not a meaningful Filipino baseline.

Pilot mode uses an in-memory dataset and rejects **every external dataset request**, including Belebele. Tests use mocked dataset calls for the benchmark branch; they never retrieve its examples. The actual 900-question benchmark must remain untouched during this implementation pass.

Verified locally on 2026-10-12: **15 tests passed** and **20/20 synthetic questions** produced complete, checked CPU artifacts with zero few-shot examples, zero truncations, and no benchmark access. The cached pilot took 103.8 seconds on this machine using four CPU threads. This is an engineering execution measurement, not a model-quality result or a GPU runtime estimate. Model/tokenizer pins and source/artifact hashes were also checked against the saved manifest.

## How the code works

1. `evaluate.py` validates the mode, explicit device, precision, and immutable model/tokenizer revisions.
2. `protocol.py` verifies the audited FilBench checkout and provides either the official task registry or a development task reusing its exact prompt and metric objects.
3. The pilot loads `fixtures/development.json`. A scoped adapter replaces only upstream's dataset-loading boundary; the pinned fork has no local-file option for this task. Benchmark mode instead permits only the pinned `facebook/belebele`, `tgl_Latn` configuration and asserts 900 test questions.
4. The Transformers/Accelerate backend loads the model at its commit. A separate pinned local tokenizer snapshot handles the fork's single shared revision field without changing upstream code. Remote model code is disabled.
5. The official formatter creates a Tagalog passage/question with A–D options and converts the gold answer from 1-based to 0-based indexing. The model scores the answer-label continuations by log likelihood. The highest likelihood wins; the official metric records 0 or 1.
6. Every actual scoring request is checked against the model context limit before inference. Overlength inputs abort; they are not silently truncated.
7. The runner checks finite likelihoods, valid gold/predicted indices, no truncation, the expected sample count, and agreement between per-example scores and official aggregate accuracy before marking a run complete.

All adapters are scoped and restored on success or failure. CPU and CUDA use the same official prompt and metric; precision and hardware are always recorded. Exact floating-point agreement across different hardware is not promised.

The old harness may warn that its default few-shot source is the evaluation split even for a zero-shot task. This runner requests zero examples and verifies that every saved detail contains zero requested and effective few-shot examples; it never adds demonstrations to the prompt.

## Local artifacts

Each run creates a unique directory under ignored `research/runs/`:

| File | Contents |
| --- | --- |
| `manifest.json` | Complete/incomplete status, all revisions, dependency versions, source/fixture hashes, hardware, protocol, runtime, and benchmark-access flag |
| `samples.jsonl` | Stable sample IDs, prompt hashes, four log likelihoods, prediction, gold index, accuracy, and unmodified upstream detail fields |
| `metrics.json` | Official task metrics and an explicit engineering/baseline label |
| `qualitative-review.json` | Separate, initially empty human annotations; these never alter task scores |

The wrapper writes JSON/JSONL instead of upstream's detail filenames containing `|`, which Windows prohibits. It does not call upstream's save/push routine. Hugging Face uploads, TensorBoard, and WandB publishing are disabled. Downloads, environments, and run files remain ignored; no credentials belong in reports. If execution fails or is interrupted, its manifest remains **incomplete**, even if some artifacts exist. A forced process termination can leave the initial incomplete manifest without a finish time.

## Actual baseline: later, explicitly

First select one serious general-purpose multilingual checkpoint and one Filipino- or Southeast Asian-focused checkpoint, if compute/license suitability permits. Read their model cards, record licenses and immutable revisions, and freeze the protocol. A particular model family or size is not required.

The following is a command template, **not a command to run during preparation**. Replace every placeholder with a chosen, reviewed checkpoint and its full 40-character commit SHA:

```powershell
research/.venv/Scripts/python.exe research/evaluate.py evaluate `
  --model MODEL_ORG/MODEL_NAME --model-revision MODEL_COMMIT_SHA `
  --tokenizer TOKENIZER_ORG/TOKENIZER_NAME --tokenizer-revision TOKENIZER_COMMIT_SHA
```

CPU defaults remain float32 and batch size one. Use `--device cuda --dtype float16` or `bfloat16` only in a verified GPU environment. Unsupported architectures, gated model access, missing CUDA, and out-of-memory conditions stop the run. There is no quantization, distributed evaluation, resume, automatic checkpoint selection, or cloud provisioning in this release.

Benchmark mode imports **`community_tasks/filbench_evals.py`** from the pinned fork, selects **`filbench|belebele_fil_mcf|0|0`**, and applies only the dataset revision pin. It uses the full test split, zero-shot prompts, no extra system prompt, and no chat template. Different checkpoints may be sensitive to this fixed prompt; cross-model differences are descriptive, not causal evidence about a training method. Do not report incomplete results as a full baseline or combine this accuracy with Batayan/SEA-HELM metrics.

After baseline measurement, qualitative error review may describe limitations. Do not repeatedly tune against those test failures or turn benchmark examples into training data. **Before any adaptation experiments, establish an additional independently authored, untouched Filipino evaluation set**, separated from training and development. That set is not created by this task. Public benchmark availability also prevents assuming an absence of pretraining contamination.

## Provenance and pinned sources

- [FilBench paper](https://aclanthology.org/2025.emnlp-main.127/) and [official pinned task entry point](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/community_tasks/filbench_evals.py). Fork commit: `7ad52795d7d218d4679f93a019b58dde4b749c5b`; retain its MIT notices in the checkout.
- [Belebele dataset](https://huggingface.co/datasets/facebook/belebele/tree/7899cdfa4e1e0d733fd77c848e2c273cb1d32be2), **CC BY-SA 4.0**; [Bandarkar et al., ACL 2024](https://aclanthology.org/2024.acl-long.44/). Dataset commit: `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`. Any future redistribution of examples must preserve attribution and applicable license conditions.
- [SmolLM2-135M model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M), **Apache 2.0**. Model and tokenizer commit: `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`.

These are external works studied by Makata, not original Makata findings or institutional partnerships. Website teaching examples and tokenizer fixtures are unrelated to this isolated study environment.

# First study: evaluation before adaptation

This isolated environment supports Makata's [first-study protocol](../docs/first-study.md) and completed first development cycle. Milestones 1–4 now include verified external baselines, provisional Aya preparation, a 363-example internal QLoRA run, and one paired post-training evaluation. Checkpoint 91 scored 498/900 versus the retained base's 483/900; the +1.67-point difference has a paired 95% interval of −1.45 to +4.80 and is not statistically established as an improvement. See [Milestone 4](../docs/milestone-4-post-training.md). No weights are released; independent data/evaluation review and rights questions remain unresolved. No AWS credits were used.

The commands and authorization statements in historical sections describe their original scopes. The completed experiments must not be rerun without separate authorization. Publication now covers source and reports only, not restricted data, unreviewed tasks or weights. [Report 002's guide](../docs/research/report-002-reproduce.md) explains exact reproduction requirements and access limits.

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

This lock is verified on Windows x64 with CPU PyTorch. CUDA execution uses the separately verified Linux [Colab environment and workflow](colab/README.md); do not treat this CPU lock as a GPU installation recipe. The CLI supports explicit CUDA selection and precision but never silently falls back to CPU.

## Test, then run the pilot

From the repository root:

```powershell
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe research/evaluate.py pilot
```

Pilot mode downloads only the pinned SmolLM2-135M model and tokenizer from Hugging Face (approximately 270 MB of model weights plus dependencies), then scores all 20 local questions on CPU in float32, batch size one, using four CPU threads. Initial imports and downloads can take several minutes. Cached repeat runs avoid downloading weights again. SmolLM2 is primarily English-focused; these outputs are engineering checks, not a meaningful Filipino baseline.

Pilot mode uses an in-memory dataset and rejects **every external dataset request**, including Belebele. Tests use mocked dataset calls for the benchmark branch; they never retrieve its examples. Milestone 2 permits full benchmark execution only after compute feasibility is established; that condition is not currently met.

Milestone 1 verification on 2026-10-12: **15 tests passed** and **20/20 synthetic questions** produced complete, checked CPU artifacts with zero few-shot examples, zero truncations, and no benchmark access. The cached pilot took 103.8 seconds on this machine using four CPU threads. This is an engineering execution measurement, not a model-quality result or a GPU runtime estimate. Model/tokenizer pins and source/artifact hashes were also checked against the saved manifest. The subsequent Milestone 2 audit and Colab work extended the suite to 27 passing tests.

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

## Frozen baseline candidates and resource checks

For free GPU execution, use the [self-contained Colab notebook and instructions](colab/README.md). It includes current local research fixes, a separate pinned Linux/CUDA environment, a frozen GPU profile, and synthetic candidate checks before benchmark access. AWS credits are not used. Local CPU instructions below remain available.

`baseline-plan.json` freezes Qwen3-1.7B-Base and Sailor2-1B model/tokenizer SHAs and the CPU float32 protocol. The smaller regional checkpoint is a genuine SEA-trained candidate, distinct from the English-focused engineering control. These choices do not define Makata's eventual training-model size. See the report for primary-source justification and limitations.

```powershell
research/.venv/Scripts/python.exe research/preflight.py
```

This checks public checkpoint access, license declarations, native architecture shapes using storage-free meta tensors, parameter counts, tokenizer compatibility on the 20 local fixtures, context limits, RAM and disk. Only metadata and tokenizer files download; no model weights or benchmark examples load. Its ignored `research/runs/preflight-*/preflight.json` records results, hashes, hardware, and planning assumptions. Exit code **2** means checks succeeded but resource screening is blocked; **0** means checks passed, not permission to launch an uncontrolled long run. Exceptions retain an incomplete report.

Memory figures are conservative planning screens, not measured peak usage. The 2048-token assumption is not an input cap and does not override native context checking. A full-native-context estimate is also recorded. Recheck available RAM and estimate runtime before downloading weights. A GPU environment requires separate verification and an explicitly amended frozen configuration; this CPU dependency lock cannot enable CUDA.

## Actual baseline: only when feasible

The two selected checkpoints and immutable revisions are recorded in `baseline-plan.json`. The report provides exact PowerShell commands that read this file and stop on a failed run. Do not substitute the pilot model or a partial benchmark for missing full-run evidence.

The following remains the generic CLI template. Use the frozen plan's values for this study, only after resource checks pass:

```powershell
research/.venv/Scripts/python.exe research/evaluate.py evaluate `
  --model MODEL_ORG/MODEL_NAME --model-revision MODEL_COMMIT_SHA `
  --tokenizer TOKENIZER_ORG/TOKENIZER_NAME --tokenizer-revision TOKENIZER_COMMIT_SHA
```

CPU defaults remain float32 and batch size one. This study's GPU execution also requires explicit `--device cuda --dtype float32`; use the frozen Colab workflow. Other supported precisions require a separately justified and frozen protocol amendment. Unsupported architectures, gated model access, missing CUDA, and out-of-memory conditions stop the run. There is no quantization, distributed evaluation, resume, automatic checkpoint selection, or cloud provisioning in this release.

Benchmark mode imports **`community_tasks/filbench_evals.py`** from the pinned fork, selects **`filbench|belebele_fil_mcf|0|0`**, and applies only the dataset revision pin. It uses the full test split, zero-shot prompts, no extra system prompt, and no chat template. Different checkpoints may be sensitive to this fixed prompt; cross-model differences are descriptive, not causal evidence about a training method. Do not report incomplete results as a full baseline or combine this accuracy with Batayan/SEA-HELM metrics.

After baseline measurement, qualitative error review may describe limitations. Do not repeatedly tune against those test failures or turn benchmark examples into training data. **Before any adaptation experiments, establish an additional independently authored, untouched Filipino evaluation set**, separated from training and development. That set is not created by this task. Public benchmark availability also prevents assuming an absence of pretraining contamination.

## Provenance and pinned sources

- [FilBench paper](https://aclanthology.org/2025.emnlp-main.127/) and [official pinned task entry point](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/community_tasks/filbench_evals.py). Fork commit: `7ad52795d7d218d4679f93a019b58dde4b749c5b`; retain its MIT notices in the checkout.
- [Belebele dataset](https://huggingface.co/datasets/facebook/belebele/tree/7899cdfa4e1e0d733fd77c848e2c273cb1d32be2), **CC BY-SA 4.0**; [Bandarkar et al., ACL 2024](https://aclanthology.org/2024.acl-long.44/). Dataset commit: `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`. Any future redistribution of examples must preserve attribution and applicable license conditions.
- [SmolLM2-135M model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M), **Apache 2.0**. Model and tokenizer commit: `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`.

These are external works studied by Makata, not original Makata findings or institutional partnerships. Website teaching examples and tokenizer fixtures are unrelated to this isolated study environment.

## Milestone 3, Step 1: provisional Filipino data

**Current version: v2.** Use the revision commands below to avoid reopening benchmark examples. The original v1 instructions in this subsection are historical: the current script deliberately produces different counts. Original outputs/audits remain unchanged, and the exact earlier script is retained locally at `runs/aya-filipino-v2-review/before-prepare_dataset.py` as source evidence (not a directly runnable relocated project).

`prepare_dataset.py` prepares only the pinned Aya Filipino training file. It does not load a model, train, run benchmarks, or contact cloud services. See [the data audit](../docs/milestone-3-data-audit.md) for the measured counts, source hashes, filtering decisions, and remaining review requirements.

Use the existing Python 3.12 environment; no additional dependencies are required. The preparation uses Hugging Face Hub 0.33.4 and PyArrow 20.0.0 already in the CPU lock. It downloads only the source Parquet file and dataset card at commit `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`, verifies their SHA-256 hashes, and retains the originals in ignored `research/.cache/dataset-preparation/`.

From the repository root, provide the retained **Qwen** benchmark `samples.jsonl` whose SHA-256 is `e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512`. It is used only as an overlap-exclusion reference; scores, predicted answers, and failure categories are not consulted. The existing engineering fixtures are protected too. Missing or altered reference evidence stops preparation; the script never downloads benchmark examples.

```powershell
$benchmark = 'research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760/samples.jsonl'
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -p test_dataset_preparation.py -v
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --benchmark-records $benchmark --output research/runs/aya-filipino-new
```

Use a new output directory on every invocation; existing directories are never overwritten. The first command with data access populates the small source cache; later use `--offline` to prohibit Hub access. All real dataset files, review inputs, and outputs must remain under ignored `research/.cache/` or `research/runs/`. Tests use invented examples and never fetch benchmark data.

The delivered, agent-reviewed local preparation can be reproduced with its retained decisions:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --benchmark-records $benchmark --reviews research/runs/aya-filipino-v1/review-decisions.jsonl --output research/runs/aya-filipino-reproduce
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
```

Without `--reviews`, the script produces a different, purely screened candidate set. The local decisions are an input to reproduction, are hashed in the manifest, and are copied into each reviewed output directory. Do not assume those ignored decisions or benchmark references are available from a public checkout.

The flow is **verified source → validation → exact-pair deduplication → prompt groups → evaluation overlap screening → flags/review decisions → group-wise splits**. Exact-pair duplicate copies retain mappings to the lowest source ID. Repeated/near-identical prompts stay together, including when one member remains quarantined. The seed is 1234; approximately 10% of groups are assigned to validation by SHA-256, so record proportions can differ from exactly 90/10.

`train.jsonl` and `validation.jsonl` contain `id`, `group_id`, `prompt`, `response`, `content_sha256`, `assigned_split`, and `provenance`. These are plain prompt/response examples, not tokenized data or a chat-template commitment. `quarantine.jsonl` contains unresolved flags; `exclusions.jsonl` records discarded originals and duplicate mappings. `review.jsonl` records the seeded sample, flag coverage, and observations. `manifest.json` records completeness, source/review/script/environment hashes, rules, counts, and output hashes. The source card and `NOTICE.md` preserve attribution and licensing information.

Optional review inputs are UTF-8 JSONL objects containing `id`, `content_sha256`, `reviewer_type` (`agent` or `human`), `disposition` (`accept`, `reject`, `hold`), `rationale`, and `references` (a string list). IDs/hashes must match retained records. Agent acceptance never clears automatic flags. Human acceptance may clear heuristic flags, but cannot override exact benchmark overlap. A human label records a supplied decision; it is not an authentication system. Do not mark an agent observation as a human review.

**These exports are provisional and not approved for training.** The publisher declares Apache-2.0, but that declaration does not establish rights to every copied third-party passage. Native-speaker review, factual review, and third-party-content decisions remain unresolved. An independent untouched evaluation set remains required before adaptation; this data-preparation step does not create it or authorize GPU fine-tuning.

### Revision v2: grouping signals and quality holds

See [the revision audit](../docs/milestone-3-data-refinement.md). `answer_variants` and `near_duplicate_prompt` are now `grouping_signals`, preserving group IDs and split assignments without automatically quarantining records. Quarantine `flags` identify substantive concerns; explicit holds/rejections remain binding. Narrow contextual exceptions handle probability arithmetic, temporal words in illustrative prompts, and C++ syntax. No answers are edited.

The revised local export contains **951 training / 89 validation candidates, 184 quarantined records and 17 exclusions**. They remain provisional. The agent reviewed a deterministic sample expanded to whole groups; this was not an exhaustive native or legal review.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --previous-preparation research/runs/aya-filipino-v1 --reviews research/runs/aya-filipino-v2-review/revision-reviews.jsonl --output research/runs/aya-filipino-v2-reproduce
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/runs/aya-filipino-v2-review/verify_refinement.py
```

Use a new output directory. `--previous-preparation` accepts only the pinned audited v1 manifest and hash-verified outputs. It checks source/content hashes, unchanged groups, source revision and screening identity, and carries prior review holds/rejections forward. It **does not open or download benchmark examples**. A changed source, missing receipt, tampered artifact or attempted hold override fails closed. It cannot screen new or rewritten text. The alternative `--benchmark-records` remains available for explicitly authorized fresh screening; it was not used in this revision.

`dispositions.jsonl` gives every source ID its prior/new disposition, reason, grouping signals, substantive flags and applicable review rationale. The manifest hashes this ledger and both inherited and new review inputs. `prior-screening-manifest.json` identifies the reused coverage; no new contamination test is claimed. The separate review folder retains the deterministic selection, group observations and original source snapshots. All real data and review artifacts remain ignored. Run the original script only from a properly restored source checkout if historical v1 regeneration is required; the current implementation does not promise v1 output parity.

## Isolated QLoRA engineering smoke test

The [20-update smoke-test procedure](../docs/milestone-3-qlora-smoke.md) uses 16 content-pinned, provisional Aya v2 training records and a separate Colab dependency lock. It does not clear the full dataset or establish improved comprehension. See `qlora-smoke-plan.json` for the selection ledger and fixed configuration. Prepare private inputs with `qlora_smoke.py prepare`; upload them separately to `colab/makata-qlora-smoke.ipynb`. Full training still requires clearance, an untouched evaluation set, a frozen configuration, and approval. Do not rebuild the historical baseline notebook for this workflow.

## Aya-only approval packet

The [revised training-readiness report](../docs/milestone-3-training-readiness.md) proposes **363 quality-screened Aya examples, one epoch and 91 optimizer updates**, subject to approval. Of these, 80 have individual agent observations and 283 passed screening only; known defects, explicit holds and unresolved third-party concerns remain excluded. This is provisional internal experimental data, not native-speaker or legal clearance.

`aya-training-proposal.json` freezes the selection, review bases, configuration and hashes. `prepare_training_readiness.py` verifies source/smoke/review evidence and creates private approval materials; it has no training command. The local packet at `runs/aya-training-approval-v2-final/` includes all89 validation candidates (66 provisionally eligible,23 held),32 separate agent-authored evaluation tasks/rubrics, and121 pending human review entries. Review validation before loss monitoring and require independent human evaluation review before testing. Keep evaluation text/references out of training notebooks and bundles.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/prepare_training_readiness.py --source research/runs/aya-filipino-v2 --evaluation research/runs/aya-training-revision-v2/evaluation-reviewed-draft.jsonl --output research/runs/aya-training-approval-new
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
```

Use a new output directory. Reproduction requires the retained private Aya exports and hash-pinned risk/history files; those are intentionally absent from Git. The original24-example proposal and all smoke artifacts remain preserved locally. Full-run execution still requires approval and an execution change implementing the epoch/checkpoint/validation behavior without changing the verified historical smoke runner. No training is authorized by preparation.


## Authorized bounded Aya-only full run

Use `qlora_full.py` and the separate `colab/makata-qlora-full.ipynb` for the approved 363-record/91-update experiment. `qlora-full-authorization.json` records the user's bounded free-T4 authorization without editing the frozen proposal. The historical smoke runner/notebook remain immutable.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py prepare --source research/runs/aya-filipino-v2 --packet research/runs/aya-training-approval-v2-final --output research/runs/qlora-full-inputs-new
research/.venv/Scripts/python.exe -X utf8 research/colab/build_qlora_full_notebook.py
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py import --archive PATH_TO_DOWNLOADED_ZIP --output research/runs/qlora-full-import-new
```

Upload only `private-full-inputs.zip`: 363 selected training records, 66 provisional validation diagnostics and source attribution. Never upload the 32-task evaluation packet. AdamW accumulates per-example gradients over four examples, or three in the final window; no data is dropped. Checkpoints 50/91 include adapter, optimizer, scheduler, scaler, RNG and data position. Select final 91 only. Failures stay incomplete in separate directories; no automatic resume or protocol changes. Fresh-process reload and local checkpoint verification must pass before claiming completion. No evaluation, publication, paid compute or model release is authorized. See [the full-run execution report](../docs/milestone-3-qlora-full.md) for actual evidence.

This bounded run completed: 91 updates, both checkpoints locally verified, and a passing fresh-process final-adapter reload. Retained artifacts are in ignored `runs/qlora-full-import-v1/`. Recheck without training using `research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py verify --output research/runs/qlora-full-import-v1`. The separately authorized post-training evaluation is documented below; no public model release has occurred.

## Milestone 4: authorized final-checkpoint evaluation

The [post-training report](../docs/milestone-4-post-training.md) records a separate authorization for one complete FilBench Belebele evaluation of checkpoint91. `post_training.py` wraps only model loading in the unchanged evaluator: original FP32 base plus frozen FP32 LoRA, no quantization, prompt changes, retraining or checkpoint selection. `post-training-plan.json` pins source, adapter and original baseline evidence. The32 instruction-following tasks remain unscored.

Use `colab/makata-post-training.ipynb` and upload only the private adapter bundle produced by `post_training.py prepare`. The notebook has separate start and read-only monitor cells; do not start twice. After download, `post_training.py import` verifies900 records and `compare` requires identical per-question prompts/tokens before calculating paired changes and passage-cluster bootstrap uncertainty. Exact commands and retained paths are in the report. No paid compute or publication is authorized.

The single evaluation is complete and locally verified: checkpoint 91 scored **498/900 (55.33%)**, versus **483/900 (53.67%)** for the retained base. The measured change is +1.67 percentage points; the paired 95% passage-bootstrap interval is −1.45 to +4.80 points, so reliable improvement is not established. There were 108 newly correct and 93 newly wrong answers. Evidence remains ignored in `runs/post-training-import-v1/`. Recheck it without inference using `research/.venv/Scripts/python.exe -X utf8 research/post_training.py verify --output research/runs/post-training-import-v1`. Do not rerun or tune against this benchmark; the 32 instruction tasks remain unscored.

# Milestone 2: Tagalog comprehension baselines

**Status: COMPLETE — 2026-10-12. Two full 900-question baselines independently verified.**

Audited starting commit: `1c811c1b5a6b6208afb6448482c12ae54dbfe393`. The original CPU audit began with a clean working tree; the subsequent free-GPU setup preserved its uncommitted changes. That local resource blocker was resolved with a free Colab T4 allocation, unchanged model/data/scoring pins and float32 precision, and a separately frozen CUDA execution profile. Both candidate development pilots and both full baselines passed verification. No paid credits, training, publishing, or website changes were involved.

## Research question and scope

How accurately do a general multilingual base model and a Southeast Asian base model answer multiple-choice questions grounded in Tagalog translated passages under the same zero-shot FilBench protocol? The intended measurement is accuracy on the complete `facebook/belebele`, `tgl_Latn`, 900-question test split. It does not establish Taglish conversational quality, native cultural knowledge, generative reliability, or overall Filipino competence.

Baselines provide evidence for choosing a bounded future Filipino fine-tuning experiment. A comparison between these checkpoints is descriptive: their sizes, architectures, training data, and training histories differ. A regional model winning would not isolate the causal effect of regional training. A small base model can be a legitimate initial baseline without being the best eventual instruction-tuning candidate.

## Verified results

Both runs used all 900 questions, the official zero-shot `filbench|belebele_fil_mcf|0|0` task, CUDA float32, batch one, seed 1234, four CPU threads, no chat template or system prompt, and no quantization or truncation. The largest actual input was 711 tokens for each checkpoint, within both native context limits. Per-example predictions and accuracy were recomputed from four finite likelihoods and reconciled with the official aggregate.

| Checkpoint | Correct / total | Official accuracy | Official accuracy standard error | Run wall time | Inference time | Peak PyTorch allocation |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-1.7B-Base | 483 / 900 | 53.6667% | 1.6631 percentage points | 2,100.078 s (35.00 min) | 2,067.149676 s | 7,756,109,312 bytes (7.22 GiB) |
| Sailor2-1B | 222 / 900 | 24.6667% | 1.4377 percentage points | 1,141.737 s (19.03 min) | 1,113.361445 s | 4,826,461,184 bytes (4.50 GiB) |

Hardware: one Tesla T4 with 15,637,086,208 bytes VRAM, 13,605,830,656 bytes host RAM and two logical CPUs. PyTorch reserved peaks were 8,128,561,152 and 5,190,451,200 bytes respectively; these allocator measurements are not total system/GPU usage. Run wall times include initialization, loading, evaluation and artifact writing, but exclude notebook setup and earlier development pilots. The two runs consumed about 54 minutes combined. Software: isolated Python 3.12.13, torch 2.7.1+cu126, CUDA build 12.6, Transformers 4.53.3; TF32 disabled.

Qwen scored higher in this specific comparison. Sailor2's score is near the 25% expectation of uniform random guessing among four choices; this does not establish that it lacks all Tagalog ability or identify why it performed this way. The checkpoints differ in size and training history. No causal attribution, overall Filipino capability claim, or fine-tuning improvement follows from these two scores. Harness standard errors are retained as reported; they do not resolve shared-passage dependence, possible training contamination, or generalization beyond this test.

### Retained evidence and independent verification

The final downloaded archive is `makata-results-colab-1c92e225d7c2 (1).zip`, SHA-256 `f66674cc31417af054921e35cc5bd497e0f54e4a1ca09e89daee4baa64c202aa`. It was imported without CUDA on the Windows laptop; the importer exited **0** and wrote `research/runs/colab-import-7df37d1937bf/verification.json` with `status=complete`. All run artifacts remain local and Git-ignored.

- Qwen: `research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760/`; sample SHA-256 `e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512`.
- Sailor2: `research/runs/colab-import-7df37d1937bf/evaluate-20261012T095609Z-5a470bb9/`; sample SHA-256 `c064a3ca441abc5d0339d1d9b7201614e5f921c8b026d6d32ccd3b42cc51d3fe`.
- Frozen GPU profile SHA-256: `c14bc54e2d653bae3e4f8423cabbb1b5c8e1177462fae82f19a006e29ee8e98b`; its source/plan hashes match the local research snapshot. Each run embeds the same profile and hash.

The verifier checked 900 unique IDs per model, exact candidate configurations, data/plan/source/sample hashes, finite scores, gold/predicted indices, official accuracy, zero few-shot examples and zero truncation. Qualitative-review files remain empty; no human-validated failure categories are claimed. The initial Windows import without UTF-8 mode failed on Unicode punctuation and was marked incomplete; it did not change the archive or scores. The successful command was:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/colab/import_results.py "PATH_TO_DOWNLOADED_ARCHIVE.zip"
```

To reproduce inference, upload [`research/colab/makata-baselines.ipynb`](../research/colab/makata-baselines.ipynb) to Colab and follow the [guarded execution instructions](../research/colab/README.md). The notebook contains the exact checksummed local source, so it does not rely on the older GitHub commit. Free GPU availability remains provider-dependent; a different allocation must pass the same checks before a new run. The original CPU execution plan remains unchanged and is not a claim that this laptop can run the baselines.

## Frozen candidate selection

Model and tokenizer use the same repository and SHA for each row. Machine-readable configuration: [`research/baseline-plan.json`](../research/baseline-plan.json), frozen before any benchmark access.

| Role | Checkpoint | Model AND tokenizer SHA | Parameters | Native context |
| --- | --- | --- | --- | --- |
| General multilingual | `Qwen/Qwen3-1.7B-Base` | `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` | 1,720,574,976 | 32,768 |
| SEA-focused | `sail/Sailor2-1B` | `75c2856ffc7e6a6e64127f40c5f54a953deb682e` | 988,064,640 | 4,096 |

**Qwen:** a pretrained causal model with broad multilingual coverage; the authors explicitly list Tagalog among Qwen3's supported languages. Apache 2.0 permits research and adaptation subject to its terms. The base checkpoint avoids mixing this initial comparison with chat-template or reasoning-mode decisions. This is language-coverage evidence, not proof of strong Filipino accuracy. Sources: [pinned card](https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/README.md), [pinned license](https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/LICENSE), [author language list](https://qwenlm.github.io/blog/qwen3/), [technical report](https://arxiv.org/abs/2505.09388).

**Sailor2:** a Qwen2-family causal model expanded from Qwen2.5-0.5B and continued-pretrained for SEA languages, explicitly including Tagalog, Cebuano, Ilocano, and Waray. It is an existing regional research model, not a Makata creation. Its pinned card declares Apache 2.0; a standalone `LICENSE` file at this checkpoint returned HTTP 404, so the declaration is documented rather than inventing a license artifact. Sources: [pinned card](https://huggingface.co/sail/Sailor2-1B/blob/75c2856ffc7e6a6e64127f40c5f54a953deb682e/README.md), [official repository](https://github.com/sail-sg/sailor2), [technical report](https://arxiv.org/abs/2502.12982). The pinned card downloaded successfully with a direct Hub request even though the browser retrieval returned an internal error.

Both checkpoints were accessible without authentication or gated-license acceptance. Hub metadata, configurations, and locally instantiated architecture shapes agree on parameter counts. Transformers 4.53.3 recognizes `Qwen3ForCausalLM` and `Qwen2ForCausalLM` without remote code. During the initial CPU audit, both tokenizers encoded all 20 synthetic development questions and the official answer continuations: 80 requests per candidate, maximum input 128 tokens. A–D map to distinct single tokens. Those initial checks verified configuration/tokenizer compatibility without loading candidate weights. Subsequent Colab pilots verified actual pinned-weight inference before the full measurements above.

The size choice balances substantive multilingual/regional training with constrained free compute. Qwen3-4B-Base and Sailor2-3B were also inspected through metadata; their approximately 8.04 GB and 7.16 GB weight downloads, before float32 expansion, make them less suitable for this host. SEA-LION remains relevant regional research, but no third checkpoint is added to this focused first comparison. These selections do not limit future Makata research to small models.

## Fixed evaluation protocol and provenance

- Harness: FilBench Lighteval fork `7ad52795d7d218d4679f93a019b58dde4b749c5b`.
- Entry point: `community_tasks/filbench_evals.py`; selector `filbench|belebele_fil_mcf|0|0`.
- Dataset: `facebook/belebele`, revision `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, `tgl_Latn`, `test`, exactly 900 questions.
- Licensing/attribution: Belebele, Bandarkar et al., **CC BY-SA 4.0**. [Pinned dataset card](https://huggingface.co/datasets/facebook/belebele/blob/7899cdfa4e1e0d733fd77c848e2c273cb1d32be2/README.md), [ACL paper](https://aclanthology.org/2024.acl-long.44/), [FilBench paper](https://aclanthology.org/2025.emnlp-main.127/). Metadata/card inspection did not retrieve test examples.
- Zero-shot; no chat template, extra system prompt, example filtering, or adaptation. Float32, batch one, four threads, seed 1234. The original CPU plan is retained; the pre-benchmark CUDA amendment is separately frozen. No quantization or uploads.
- Native model context capacities are preserved. Every actual context-plus-continuation input is checked before scoring; overlength inputs abort rather than truncate.

Source audit confirmed the [official task](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/filbench/belebele.py) converts answer labels with `int(correct_answer_num) - 1`. The formatter produces localized `Tanong:` and `Sagot:` labels and continuations ` A`, ` B`, ` C`, ` D`. The backend sums next-token log probabilities for each continuation; highest likelihood wins. MCF selects **unnormalized accuracy**, despite other formulations in the same file using length-normalized metrics. Corpus accuracy is the mean of per-question correctness. Prompt, choices, and metric objects remain upstream originals.

Model and tokenizer revisions are independently verified. A local pinned tokenizer snapshot handles the old fork's single shared revision field; the model configuration and weights still receive the model SHA. The dataset adapter permits only the exact pinned dataset/subset, rejects filtering/remote dataset code, and requires 900 rows. Pilot mode permits only in-memory development fixtures and blocks external datasets.

## Original CPU audit fixes and verification

The original 15 tests passed in 31.4 seconds; the original CPU pilot then reproduced 20 complete synthetic examples in 116.767 seconds. These are engineering measurements, **not Tagalog baseline scores**.

The audit found two completeness/reporting gaps and added hardware/device checks:

1. A row count alone could accept duplicate saved results. Duplicate sample IDs now fail completion rather than counting toward 20 or 900.
2. `benchmark_accessed` was set before validating a dataset request. The callback now marks an attempted access only after the exact source/filter checks pass, immediately before the real loader call. Network failures after that boundary retain `true` because access was attempted.
3. RAM, free disk, CPU information, requested device, and available GPU details are saved before loading weights. A model-loading failure retains those observations.
4. The actual backend device must match the requested device; a substitution aborts before dataset access. Missing CUDA already failed explicitly.

After the original CPU audit, **19 tests passed**, including duplicate detection, access-flag timing, device mismatch, frozen configuration and memory accounting. Existing prompt/scoring parity, indexing, revision propagation, truncation, pilot isolation, artifact and failure tests continued to pass. The corrected evaluator's fresh pilot completed 20 unique synthetic questions in **98.306 seconds**; saved likelihoods, predictions, official aggregate, prompt/sample/source/plan hashes, revisions, zero-shot fields and no-truncation fields were independently inspected. CPU dependencies were unchanged; `uv pip check` verified all 125 installed packages. Upstream tracked source remains unmodified. The later Colab work extended the local suite to 27 tests.

## Original CPU hardware, memory, disk and runtime feasibility

Observed host: Windows 11, Intel Core i5-13420H, 8 physical cores / 12 logical processors, 16,890,322,944 bytes RAM (15.73 GiB), Intel UHD integrated graphics. No NVIDIA GPU was enumerated; `nvidia-smi` was unavailable. Installed PyTorch is `2.7.1+cpu`, with no CUDA build and `torch.cuda.is_available() == False`. Integrated graphics' reported adapter memory is not CUDA VRAM.

Available RAM fluctuated from approximately 0.46 to 1.83 GiB during checks; the initial candidate preflight observed **0.78 GiB**, and the final check observed **0.68 GiB** after checking both models. Free C: disk space was approximately **203.46 GiB**. Disk was sufficient; memory and execution time blocked local CPU inference. No usable external GPU allocation had been confirmed at that stage; the free Colab follow-up subsequently resolved execution.

| Candidate | Downloaded-weight size if run | Float32 weights alone | Conservative available-RAM budget at 2,048 tokens |
| --- | --- | --- | --- |
| Qwen3-1.7B-Base | 3,441,185,608 bytes / 3.20 GiB | 6.41 GiB | 17.14 GiB |
| Sailor2-1B | 1,976,194,640 bytes / 1.84 GiB | 3.68 GiB | 11.68 GiB |

**Planning assumptions:** batch one, float32 weights, one extra weight-sized loading/runtime allowance, 2 GiB other overhead, and two full sequence-by-vocabulary float32 arrays for logits/log-softmax. Formula: `2 × parameters × 4 + 2 × tokens × vocabulary × 4 + 2 GiB`. These are conservative screening budgets, not measured peaks or universal minimum requirements. A 2,048-token assumption is not a benchmark cap; actual maximum lengths remain unknown until dataset access. Full-native-context estimates are also saved in the preflight artifact. Even the weights-only lower bounds exceed current available RAM.

The reproduced pilot scored 80 likelihood requests averaging 115.75 input tokens, using a 134,515,008-parameter control. Scaling its 116.767-second wall time by sample count, parameters, and assumed average request lengths of 512–2,048 gives **about 83–330 hours for Qwen and 47–190 hours for Sailor2**. This is an explicitly rough extrapolation, not a measured candidate runtime: imports, memory bandwidth, paging, architecture, tokenizer lengths, attention complexity, and CPU kernels invalidate precise linear prediction. It was enough to reject an unbounded laptop run; no full CPU baseline was started.

The frozen CPU procedure would require a host with sufficient available RAM (a 32 GB host with ample free memory is a reasonable planning target) and acceptable measured runtime on synthetic development prompts. Closing applications alone was not evidence that days-long CPU evaluation would be practical. Instead, the Colab follow-up verified CUDA, memory, throughput and a frozen GPU profile before test-set access. AWS credits were not used.

## Reproduction and guarded execution

Use the existing Python 3.12.13 CPU environment and pinned dependencies from [`research/README.md`](../research/README.md). From the repository root:

```powershell
uv pip check --python research/.venv/Scripts/python.exe
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe research/evaluate.py pilot
research/.venv/Scripts/python.exe research/preflight.py
```

Preflight downloads only metadata/tokenizer files; it never runs benchmark mode. Exit **2** means a completed check with resource blockers, not a failed baseline. Inspect its ignored JSON report. Before using different hardware, repeat tests and pilot, record hardware, and measure candidate throughput on synthetic development prompts without examining benchmark examples. Architecture-only checks cannot promise that full inference will succeed.

Only after memory **and** runtime feasibility are established, use the frozen CPU settings below. These commands were reviewed but **not executed** in this pass:

```powershell
$plan = Get-Content -Raw research/baseline-plan.json | ConvertFrom-Json
research/.venv/Scripts/python.exe research/preflight.py
if ($LASTEXITCODE -ne 0) { throw 'Preflight blocked; do not download weights or evaluate.' }
foreach ($candidate in $plan.candidates) {
  research/.venv/Scripts/python.exe research/evaluate.py evaluate `
    --model $candidate.model --model-revision $candidate.model_revision `
    --tokenizer $candidate.tokenizer --tokenizer-revision $candidate.tokenizer_revision `
    --device $plan.execution.device --dtype $plan.execution.dtype --threads $plan.execution.threads
  if ($LASTEXITCODE -ne 0) { throw 'Evaluation incomplete; inspect its manifest before continuing.' }
}
```

A complete run must have `status=complete`, 900 unique saved samples, four finite likelihoods each, valid gold/predicted indices, zero few-shot examples and truncation, aggregate accuracy matching saved predictions, all exact revision pins, and matching source/sample hashes. Each run saves local `manifest.json`, `samples.jsonl`, `metrics.json`, and a separate empty `qualitative-review.json`. The manifest records the frozen plan hash. Failed/partial runs cannot substitute for full evidence; there is no resume support.

## Evidence and research limitations

- Original rerun: `research/runs/pilot-20261012T081617Z-b8c81682/` — 20 synthetic examples, complete, no benchmark access.
- Candidate check: `research/runs/preflight-20261012T082225423633Z/preflight.json` — both architectures/tokenizers verified; resource status blocked. This initial preflight predates the later addition of code/package hashes.
- Corrected pilot: `research/runs/pilot-20261012T082406Z-9f2dca0a/` — 20 unique verified development examples, 98.306 seconds, complete, no benchmark access. Sample SHA-256: `30fce5dbac0ae3700090754d6b27f7394f2909fb0ed36e550caec7210b11e385`.
- Final candidate check: `research/runs/preflight-20261012T082849756432Z/preflight.json` — exact pinned candidates, tokenizer file hashes, source/plan hashes and package versions verified; resource status blocked, exit 2. Cached snapshot inventories contain only configuration/tokenizer files, no selected-model weight files.
- Test logs: ignored `research/.cache/milestone2-tests-initial.log` and `milestone2-tests-final.log`.

These historical CPU artifacts are engineering evidence, not baseline measurements. The subsequent complete baseline counts and accuracy are reported above. No qualitative benchmark errors have been human-annotated. Synthetic-fixture errors do not establish a research weakness, and the tiny English-focused control is not a substitute baseline.

Public benchmark contamination cannot be ruled out. The frozen task tests label likelihood, not free-form answer generation, and checkpoint comparisons are prompt-sensitive. Once valid complete results exist, a separate qualitative review can examine explicit-detail retrieval, inference, negation, reference resolution and distractors without changing scores. These are potential human annotation categories, not existing benchmark labels or findings.

Future fine-tuning would be justified by reproducible deficiencies, a plausible data-based intervention supported by licensed/provenanced Filipino data, and controlled comparisons against the unchanged base checkpoint. Test-set mistakes must not become an iterative tuning loop. Before adaptation, establish a separately authored, untouched Filipino evaluation set and a distinct development set. No such dataset or training work is included in this milestone.

## Free Colab follow-up

The [Colab workflow](../research/colab/README.md) packages the current local research source rather than cloning the older published commit. Its final embedded source ZIP SHA-256 is `ac9949705cd1f5f5e6e9e266afb8b6f840c46ae7fab584ba6d8f34d236e05fde`. The runs used a free Colab allocation; no upgrade or paid provisioning was performed.

The Linux environment uses isolated Python 3.12.13 and `torch==2.7.1+cu126`. All 124 explicitly pinned CPU distributions are preserved except the torch CPU/CUDA build switch; 15 Linux/CUDA dependencies are added and pinned. The notebook's default Python/packages are not used for research execution. Both selected checkpoint architectures and actual CUDA inference were tested on 20 original development questions before test-set access. The CPU environment remains unchanged.

The initial notebook's three-hour planning screen estimated approximately 183 minutes for Qwen and 101 minutes for Sailor2. Before any benchmark access, the engineering execution budget was amended to four hours per subprocess, a new source snapshot/profile was frozen, and both candidate smoke tests were repeated. Neither model, prompt, score, dataset nor precision was tuned. The original smoke evidence is retained locally at `research/runs/colab-7f3a92de7c3f/`.

The final runtime session was retained locally; its source snapshot is identified by the hash above. The profile records explicit CUDA float32, TF32 disabled, batch one, four CPU threads, immutable source/plan hashes, and actual hardware/driver details. Candidate processes run sequentially. The evaluator now also records synchronized inference time and peak GPU allocation/reservation, while retaining the original scoring behavior.

The notebook executed the following calls in order after installing/checking the pinned environment and running the exported tests. Each `stage` dispatches the matching `research/colab/run.py` command through the isolated research interpreter, with the frozen session and explicit candidate index, capturing its log and exit status:

```python
stage('freeze')
stage('smoke', 0)
stage('smoke', 1)
stage('evaluate', 0)
stage('evaluate', 1)
```

Local verification passes **27 tests**, including notebook packaging, GPU safeguards, archive extraction safety and evidence completeness. The exported notebook passed 23 checks and skipped only the local notebook-packaging check. Both downloaded 900-question artifact sets passed `research/colab/import_results.py` with exit 0. The saved, output-free reproduction notebook is retained in the repository; private session links are omitted from release documentation. AWS credits remain unused. Milestone 2 is complete; no training or new research direction was started.

Final local suite command: `research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v` — 27 passed in 47.736 seconds, log at ignored `research/.cache/colab-tests-final.log`. `git diff --check` passed. The original and amended CPU development pilots remain engineering checks only. The completed Colab runtime is idle; its output notebook and verified local archive are retained. Colab's destructive runtime-reset action was not confirmed.

## File inventory

No files were deleted. Existing website files and the Windows CPU dependency lock were unchanged.

| File | Change and purpose |
| --- | --- |
| `docs/first-study.md` | Updated study protection, scope and verified status. |
| `docs/milestone-2-baselines.md` | Created this audit, selection, execution and evidence report. |
| `research/README.md` | Updated operating instructions and completed-study status. |
| `research/evaluate.py` | Audited completeness/access/device reporting; explicit CUDA safeguards, loading, timing and execution-profile evidence. |
| `research/protocol.py` | Audited artifact completeness and duplicate detection. |
| `research/preflight.py` | Created bounded model/tokenizer and local resource screening. |
| `research/baseline-plan.json` | Created immutable candidate pins and original CPU protocol. |
| `research/requirements-colab.txt` | Created separate pinned Linux/CUDA environment. |
| `research/colab/run.py` | Created GPU freeze, development smoke, guarded full-run and artifact checks. |
| `research/colab/build_notebook.py` | Created deterministic, allowlisted source packaging. |
| `research/colab/makata-baselines.ipynb` | Created the self-contained execution notebook. |
| `research/colab/import_results.py` | Created offline archive verification; explicit UTF-8 invocation guard on Windows. |
| `research/colab/README.md` | Created notebook, retention and local verification instructions. |
| `research/tests/test_evaluation.py` | Extended audit regression tests and CUDA mocks. |
| `research/tests/test_colab.py` | Created packaging, profile, GPU and evidence tests. |
| `research/tests/test_colab_import.py` | Created archive safety and incomplete-evidence tests. |

The separate landing-page-session prompt and completion screenshot are ignored supporting artifacts at `research/.cache/landing-page-session-prompt.txt` and `research/.cache/colab-baselines-complete.png`; they are not experiment inputs or public website changes.

# Milestone 4: final-checkpoint Tagalog comprehension evaluation

## Question and frozen comparison

Does the predetermined checkpoint 91 Aya-only adapter improve or regress relative to unchanged Qwen3-1.7B-Base on the exact FilBench Tagalog Belebele task? This is one narrow translated-passage, four-option reading-comprehension task, not a test of all Filipino abilities or conversational quality.

**Status: complete, locally verified October 13, 2026.** One authorized 900-question evaluation ran on a free Colab T4. Checkpoint 91 scored **498/900 (55.33%)**, versus the retained base's **483/900 (53.67%)**: **+1.67 percentage points**. The paired 95% passage-cluster bootstrap interval is **−1.45 to +4.80 percentage points**, including zero. This is a positive point estimate, not convincing evidence of a reliable gain on this task or broad Filipino improvement.

No retraining, adapter adjustment, paid resources, publication or test-guided optimization occurred. The 32 agent-authored instruction-following tasks remain separate and unscored pending independent review.

## Verified results

| Model | Correct / total | Accuracy | Official harness standard error | Recorded wall time | Inference time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unchanged Qwen3-1.7B-Base, retained Milestone 2 run | 483 / 900 | 53.6667% | 0.01663103346925096 | 2,100.078 s | 2,067.149676 s |
| Same FP32 base plus final checkpoint 91 adapter | 498 / 900 | 55.3333% | 0.016580794723924614 | 1,941.986 s | 1,884.626923 s |

Standard errors above are official harness outputs in accuracy units, not confidence intervals, passage-adjusted uncertainty, or a paired significance test. The base was not rerun. Runtime differences between free Colab sessions do not establish an efficiency improvement.

| Paired outcome | Questions |
| --- | ---: |
| Correct before and after | 390 |
| Wrong before, correct after | 108 |
| Correct before, wrong after | 93 |
| Wrong before and after | 309 |
| Total | 900 |

The adapter changed correctness on 201 questions, producing a net gain of 15. The bootstrap interval spans a modest regression through a modest improvement. Neither an absence of effect nor a dependable improvement is established by this single run. No semantic failure categories were inferred automatically; the separate qualitative annotation file remains empty.

Execution started `2026-10-12T18:22:26.722768+00:00` and finished `2026-10-12T18:54:48.708636+00:00` (October 13, 02:22–02:54 Philippine time). Wall time includes model loading, benchmark preparation, inference and result writing; notebook installation, upload, offline integration, download and local analysis are excluded. Inference was synchronized with CUDA. The process exited with code 0; there was no benchmark retry, OOM, nonfinite scoring failure or protocol change.

Hardware: one Tesla T4, 15,637,086,208 bytes reported VRAM, two logical host CPUs and 13,605,830,656 bytes host RAM. Peak PyTorch allocation was **7,825,839,616 bytes (7.288 GiB)**; peak reservation was **8,241,807,360 bytes (7.676 GiB)**. These allocator measurements are not whole-device usage. All 3,600 answer-choice likelihoods were finite. Maximum input length was 711 tokens against the unchanged 32,768-token model context limit; no question was truncated or supplied few-shot examples.

## Evidence and independent local checks

The GPU-side archive checksum matched the downloaded archive byte for byte. Local import verified the complete inventory, per-file hashes, source/configuration pins, adapter provenance, official aggregate and all 900 sample scores. Pairing then required exact prompt, choice, gold-answer, instruction, input-token and continuation-token equality for every question against the retained base run.

A second local calculation independently recomputed argmax predictions, finite scores, paired counts and the bootstrap interval using a loop and explicit percentile interpolation. It agreed with the production comparison. Comparing the recorded package inventories showed exactly one addition, PEFT 0.16.0; all prior package versions matched. This is integrity and analysis verification of Makata's retained evidence, not external replication or peer review.

Ignored local evidence directory: `research/runs/post-training-import-v1/`. It contains the original downloaded ZIP, profile, attempt receipt, adapter check, complete manifest, official metrics, per-question scores, evaluation log, empty qualitative-review file, archive hash inventory, local-verification receipt, paired-comparison report and independent-crosscheck receipt. The original training adapter, base predictions and baseline documents were not rewritten.

| Artifact | SHA-256 |
| --- | --- |
| Downloaded result archive, 1,063,685 bytes | `4d6735e268eff0be3b11e4089bb5d7fe04c1e4921a85bf4ce96605f349097bb2` |
| Adapted per-question scores | `90e13a458ef3e774e6b69b966ea73064bfeb8a08b6e425ee1d4cc113def46a24` |
| Retained base per-question scores | `e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512` |
| Paired comparison, including question hashes | `9d03ccd42619dae0c4aed26fedff61040809c4e7e65bc565bc748cb4d09e18b6` |
| Frozen post-training plan | `a53f12b373d186b616803b6642840a27f6a7c57c9ec989e56190b65c2b17b4c3` |

`research/post-training-plan.json` freezes the following before new benchmark access:

- Base/tokenizer: `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`.
- Adapter: predetermined final checkpoint 91, safetensors SHA-256 `f7605c629df52087d04da01fcf018368986570f64e3f864071eacb4a0ebdde2a`.
- Task: `filbench|belebele_fil_mcf|0|0`; custom entry point `community_tasks.filbench_evals`.
- FilBench revision: `7ad52795d7d218d4679f93a019b58dde4b749c5b`.
- Dataset: `facebook/belebele`, revision `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, complete 900-question `tgl_Latn` test split; CC BY-SA 4.0.
- CUDA float32, TF32 disabled, batch one, four CPU threads, seed 1234; no chat template, system prompt, quantization, filtering or silent truncation.
- Preserve the official prompt, one-based to zero-based gold conversion, answer-label likelihood requests and accuracy metric. No training completion prefix is added to evaluation prompts.

Original baseline evidence was reverified locally through `colab.import_results.verify_session`: Qwen 483/900 (53.6667%), Sailor2 222/900 (24.6667%). The paired comparator uses only the retained Qwen run at `research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760/`, samples SHA-256 `e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512`. Sailor2 is historical context, not the fine-tuning control.

Checkpoint91 and both checkpoints' optimizer states passed the existing deep full-run verifier. The original proposal, evaluation files, GPU locks, prior notebooks and all retained baseline/training evidence remain unchanged. The new plan pins baseline manifest/metrics/sample hashes and training manifest/local-verification hashes.

## Adapter-only evaluation extension

`research/post_training.py` calls the unchanged `evaluate.run` and official harness. A scoped model-loading wrapper loads the exact FP32 base using the original loader, then attaches checkpoint 91 using PEFT 0.16.0 with `is_trainable=False`, float32 adapter weights, evaluation mode and gradients disabled. The adapter remains unmerged. No tokenizer method, task construction, requests, scoring function or dataset loader is replaced.

QLoRA training stored the base in 4-bit NF4 with FP16 computation. Evaluation deliberately uses the original unquantized FP32 base: retaining 4-bit inference would confound the adapter comparison with quantization/precision changes. Thus this study measures applying the learned adapter to the original full-precision base, not the exact quantized training-time model. This distinction must remain visible in interpretation.

Before benchmark access, a fixed synthetic token sequence checks that disabling the attached adapter exactly reproduces pre-attachment base logits and that enabling it changes finite logits. Saved adapter tensors must equal their loaded counterparts. A tiny randomly initialized Qwen3 CPU integration independently checks the same mechanism without pretrained weights or benchmark examples. An attempt marker prevents a second benchmark invocation in the same frozen output directory; failures stay incomplete and are not automatically retried.

The separate Colab dependency file preserves every original evaluation dependency and adds only PEFT 0.16.0. Python 3.12.13, PyTorch 2.7.1+cu126, Transformers 4.53.3 and Accelerate 1.8.1 are unchanged. Neither the Windows evaluation environment nor the training lock is modified.

Data flow: verified checkpoint 91 → private adapter-only upload → original base loader with frozen adapter attached → unchanged official likelihood evaluation → local result archive → matched base/adapted predictions → passage-level uncertainty. The official harness creates four likelihood requests per question, sorts all 3,600 requests by length, and processes four request splits. A `900/900` inner progress bar is therefore one request split, not a complete benchmark result.

## Paired comparison and uncertainty

Pair all 900 questions by full-prompt SHA-256, independently rehash prompt text and require exact equality of prompts, choices, zero-based gold indices, input tokens, continuation tokens and instruction fields. Fail instead of comparing mismatched examples. Report both-correct, newly-correct, newly-wrong and both-wrong counts; the net accuracy difference is `(newly_correct-newly_wrong)/900`.

Belebele questions share passages. The retained official prompts identify 488 distinct passage clusters: 76 with one question and 412 with two. Use a paired passage-cluster percentile bootstrap with 10,000 replicates, seed 1234 and NumPy linear 2.5/97.5 percentiles. Resample 488 passages with replacement, retain every question belonging to each sampled passage, and recompute the difference divided by the sampled question count. Do not independently resample questions or subtract marginal confidence intervals.

This interval assumes passages are suitable sampling units and is conditional on this benchmark and one training realization. It does not represent uncertainty across training seeds, other Filipino tasks, contamination or dataset correctness. Official harness standard errors are retained as descriptive harness outputs, not substituted for paired uncertainty or treated as a causal test.

## Commands and retained materials

Executed locally before GPU evaluation:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/qlora_full.py verify --output research/runs/qlora-full-import-v1
research/.venv/Scripts/python.exe -X utf8 research/post_training.py prepare --training-run research/runs/qlora-full-import-v1 --baseline research/runs/colab-import-7df37d1937bf --output research/runs/post-training-inputs-v1
research/.cache/qlora-cpu-venv/Scripts/python.exe -X utf8 research/post_training.py integration --output research/runs/post-training-integration-v1
research/.venv/Scripts/python.exe -X utf8 research/colab/build_post_training_notebook.py
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
```

The ignored upload bundle contains only checkpoint 91 adapter weights/configuration and a provenance receipt; no Aya text, validation records, benchmark records or instruction-following tasks. Its SHA-256 is `a232f9ce61e11c99a548e016d1caedbdd3d4e1519e6d84cafaea1c9dbaed8039`. The output-free notebook embeds allowlisted source, checks hashes, freezes GPU/environment/configuration, starts one guarded evaluation process and provides a read-only monitor. Results are downloaded before disconnecting.

Executed after the single run, without rerunning inference:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/post_training.py import --archive "$env:USERPROFILE/Downloads/makata-post-training-results.zip" --output research/runs/post-training-import-v1
research/.venv/Scripts/python.exe -X utf8 research/post_training.py compare --output research/runs/post-training-import-v1 --baseline research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760 --destination research/runs/post-training-import-v1/paired-comparison.json
```

All uploaded inputs and downloaded results remain private and Git-ignored. No uploads to Hugging Face or model release are performed. No benchmark examples are reproduced in public documentation.

For a repeat local integrity check, run only:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/post_training.py verify --output research/runs/post-training-import-v1
```

Import and comparison refuse existing destinations; use new local paths if reproducing those analysis commands. Do not rerun the GPU benchmark or tune against its observed failures.

## Engineering verification and setup record

The complete local research suite passed **114 tests** in 39.693 seconds, including nine new post-training checks. The tiny CPU integration passed: disabled-adapter logits equaled the pre-attachment base bitwise and active adapter logits were finite and changed. The exported Colab checks also passed (only the notebook-file check is skipped when the notebook itself is absent from the source snapshot).

Frozen notebook source ZIP SHA-256: `d01c97b7d704371a87b1e6357aaf3f0ecfe1e3004c3171a2d7f22a7afb762924`. Uploaded adapter bundle size: 64,579,933 bytes. Colab initially rejected allocation because the old completed full-training session remained active. After explicit user confirmation, that old session was terminated; its locally verified artifacts were preserved. A new free T4 was allocated without a payment flow. Environment, upload hash, integration and profile freeze passed before starting the sole evaluation subprocess. The actual pretrained model's synthetic equivalence/activation check passed before the complete 900-question test split loaded.

## Interpretation boundaries

The adapter was trained once on 363 screened Aya examples, of which 283 lacked individual content review. Agent observations do not establish native-speaker quality or legal clearance. Known holds/defects remained excluded, but contributed third-party rights and unreviewed quality remain limitations. Aya instruction following is not matched passage-grounded comprehension training.

A lower training/provisional-validation loss does not establish improvement here. The 93 newly wrong answers demonstrate local regressions despite the positive aggregate change; task mismatch, forgetting or changed output preferences are possible explanations, not identified causes. These data do not diagnose overfitting: only one training realization and one narrow benchmark were evaluated, and no independently validated instruction-following set is available. The small screened Aya subset, unresolved contributor rights/quality, translated passages, multiple-choice formulation and possible pretraining contamination limit interpretation.

The honest finding is a +1.67-point measured change with considerable uncertainty and both improvements and regressions. It does not establish broad Filipino capability, cultural understanding, conversational quality or readiness to release Makata-v0.1. No additional training, checkpoint selection, prompt tuning or failure-driven dataset edits follow automatically from the result. No AWS resources, paid credits, new datasets or website changes were used. Evaluation and local verification are complete; further research or release requires separate authorization.

## Files

Created: `research/post_training.py`, `research/post-training-plan.json`, `research/requirements-post-training-colab.txt`, `research/tests/test_post_training.py`, `research/colab/build_post_training_notebook.py`, `research/colab/makata-post-training.ipynb`, and this report. Modified: `research/README.md` and `research/colab/README.md` to document this workflow and verified outcome. No files deleted. No historical source, website, benchmark, adapter or previous result was modified by this work; pre-existing working-tree changes were preserved.

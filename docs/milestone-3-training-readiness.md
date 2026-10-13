# Makata-v0.1: revised Aya-only training proposal

Recorded **October 13, 2026 (Asia/Manila)**. **Proposal ready for approval; training not authorized.** This supersedes the 24-example/six-update proposal. The original proposal, approval packets, raw Aya exports, reviews, baseline artifacts and successful 20-update smoke test remain preserved. No training, model inference, cloud provisioning, benchmark-example access or publication occurred in this revision.

## One proposed experiment

Train fresh QLoRA adapters on **363 unchanged Aya Filipino v2 training examples from 363 distinct prompt groups**, for **one epoch / 91 optimizer updates**. Compare the final adapter with the same quantized original base on a separately frozen, human-reviewed instruction-following evaluation. This tests exploratory instruction adaptation, not necessarily improved Tagalog passage comprehension. Historical FilBench results and scoring remain unchanged.

The authoritative [proposal JSON](../research/aya-training-proposal.json) pins every selected ID, content hash, group, review basis, tokenizer length and configuration. No validation examples enter training. Keep only one example per eligible prompt group to limit redundant templates; this does not prove semantic independence across groups.

## Selection, exclusions and uncertainty

Aya v2 contains 951 training candidates, 89 validation candidates, 184 quarantined records and 17 exclusions. Source revision remains `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`; original Parquet SHA-256 remains `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc`. The preparation verifies hashes of the unchanged v2 exports, source card, review evidence and historical smoke materials.

| Disposition of the 951 training candidates | Count |
| --- | ---: |
| Selected: current agent risk review | 43 |
| Selected: prior agent review | 37 |
| Selected: screening only, not individually reviewed | 283 |
| Excluded: frozen quality, rights or group concern | 436 |
| Omitted alternative within a selected group | 152 |
| **Total** | **951** |

No quarantined record is restored. Existing quality flags, explicit holds/rejections and newly discovered concerns propagate to the entire prompt group. Prefer reviewed representatives over screening-only alternatives. Record text is never corrected or rewritten. Selection categories are heuristic: quantitative 138, factual/cultural 135, programming 32, language 28, procedural 17 and grounded reasoning 13. These are screening strata, not validated task labels.

Screening conservatively excludes identified creative/third-party material, riddles with unresolved origins, extended quotations or code needing source review, news/celebrity-source concerns, health/safety or regulated/dynamic assertions, and documented language/correctness defects. Previously flagged groups remain excluded even if another answer looks acceptable. Length and tokenizer round-trip checks also apply. The frozen local risk ledger records all flags and each sampled observation; `selection-dispositions.jsonl` accounts for all 951 records.

**Risk-based sample:** deterministically select 12 previously unreviewed candidates from each of six heuristic strata using `SHA256("1234:risk-review-v2:" + id)`, supplement with the eight longest eligible records, and deduplicate IDs. Inspect the resulting **78 complete prompt/response pairs**: **43 provisional retentions, 35 holds**. Later family-level exclusions remove related concerns; the sample is not an unbiased population error estimate.

Examples held include record 406's invalid Python print statement, record 259's incorrect independence year, 411/1009's response mismatch with the requested word classification, and wording defects in 87/718/959. Other holds reflect uncertainty rather than established falsity: precise historical claims, food/medical advice, statutory benefits, idiom origins and an unattributed headline. No replacement answers were generated. Retentions include directly checked arithmetic and internally coherent language/programming examples; code was inspected, not systematically executed. Three prior observations (323, 491, 839) are recovered from the hash-pinned historical proposal rather than misrepresented as source-v2 review records.

**Review limits:** 80 selected records have individual agent observations; **283 do not**. Agent inspection is neither native-speaker verification nor legal review. Unidentified errors, factual inaccuracies, translation artifacts and copied material may remain. The user permits this disclosed screening uncertainty for a bounded internal experiment; there is no blanket requirement to approve each training record manually. Any subsequently identified defect or rights concern must be held, and changes require a new frozen selection before execution.

The retained publisher card declares **Apache-2.0**, and its attribution/NOTICE is copied into the packet. This is evidence of the publisher's declared terms, not confirmation of rights to every contribution. Known unresolved third-party material is excluded; the subset is **provisional, not comprehensively rights-cleared or publishable**. See the [original audit](milestone-3-data-audit.md) and [v2 refinement](milestone-3-data-refinement.md).

## Validation and separate evaluation review

All **89 original validation candidates** are packaged with unchanged text, IDs, hashes, flags and proposed dispositions. **66 have no detected remaining group concern; 23 stay held.** Review the 66 before using their losses. Held items must not enter validation monitoring merely to retain a count of 89. Review decisions that change eligibility must update hashes and freeze the revised proposal; do not move any validation group into training.

Proposed monitoring uses the eligible records before optimization and at epoch end, with the same completion format and response-only teacher-forced cross-entropy. Report mean per-example response-token loss. This checks fit to Aya answers, not comprehension benchmark performance. It must not select a best checkpoint: the final update remains the comparison checkpoint.

The **32 separately agent-authored tasks** remain untouched by model execution and human-unvalidated. Four tasks each cover extraction, classification, structured output, rewriting, ordering, arithmetic, insufficient information and summarization. Agent review checked references and constraints and clarified rubrics for items 015 (capitalization), 026 (equivalent missing-information explanations), 028 (case/punctuation equivalence), and 032 (15-word counting). Original authoring material remains preserved. No task is claimed independently authored by a human.

An independent Filipino-speaking reviewer must check all 32 prompts, references and rubrics for naturalness, correctness, answerability, ambiguity, acceptable alternatives and leakage before testing. Use a new copy of `human-review-template.jsonl`; it has **121 pending entries: 89 validation plus 32 evaluation**, not a mandatory per-record training approval list. Corrections create a new evaluation version, then freeze it before generating either system's answers.

The proposed rubric is **content 0–2**, **format 0–1**, and **language 0–1**. Strict pass requires all four points; report count/32, category counts/4, and dimensions separately. Content 2 satisfies all required facts without contradiction, 1 is partly correct, 0 incorrect/irrelevant. Format 1 satisfies all explicit constraints. Language 1 is intelligible Filipino without a material defect; requested code/JSON/numbers/names are not penalized for lacking prose. Accept valid equivalents unless literal form is required. One overall item changes accuracy by 3.125 percentage points; this small draft supports no broad or significance claim.

The draft passes lexical comparison against all 951 Aya training and 89 validation candidates and itself: normalized equality, shared 12-word spans, Jaccard similarity and character similarity. This does not establish semantic independence. The prior benchmark-screening receipt applies only to unchanged Aya text; **no Belebele examples were opened**.

After approval, training and human review, generate once per task from the original base and final adapter with identical NF4/FP16 loading, completion prefix, greedy decoding and max 256 new tokens. Flag cap hits; do not selectively rerun failures. Score anonymous A/B outputs with mapping retained separately; preferably two raters, otherwise disclose one-rater limits. Do not use this set to select checkpoints or tune the model. These conditions differ from the FP32 likelihood baseline: never merge the metrics or call an instruction-task change improved Belebele comprehension.

## Frozen configuration and compute estimate

Model/tokenizer: `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`. Initialize fresh adapters; do not continue from the smoke adapter.

| Setting | Proposed value |
| --- | --- |
| Duration | **One epoch, 363 examples, 91 optimizer updates** |
| Learning rate | **2e-4**, five warmup steps, constant thereafter |
| Batch / accumulation | **1 × 4**; seeded shuffle 1234; no dropped examples |
| LoRA | r16, alpha32, dropout0.05, no bias; Q/K/V/O and gate/up/down |
| Precision | NF4 double quantization; FP16 compute, FP32 adapters/AdamW states; BF16/TF32 off |
| Loss scaling | Initial1024, growth2, backoff0.5, interval2000 |
| Length / loss | Max512; no truncation/packing; prompt/padding labels -100, response/EOS supervised |
| Optimizer | AdamW, weight decay0, clipping1 |
| Memory | Gradient checkpointing, cache off |
| Checkpoints | Updates **50 and 91**, retain both; compare **final91** only |
| Contents | Adapter, optimizer, scheduler, RNG, data position and manifest |
| Failure / reload | Fail on skipped updates, nonfinite loss/gradients, OOM or changed inputs; no automatic retries/resume; fresh-process final reload checks |

The last accumulation contains **three examples**, not four: execute it with correct remainder normalization, without dropping or duplicating data. Under the smoke scheduler convention the first optimizer call has zero LR; 90 calls have nonzero LR. The fixed historical runner still permits only 20 updates; implementing the approved epoch/validation/checkpoint behavior is required before execution, while preserving that runner. This document does not claim the full-run executor is implemented or tested.

Retain Python3.12.13, PyTorch2.7.1+cu126, Transformers4.53.3, Accelerate1.8.1, TRL0.19.1, PEFT0.16.0 and bitsandbytes0.46.1 with the verified smoke lock. The cached frozen tokenizer measured **39,780 total tokens**, mean109.59, range24–373; provisional validation maximum306. No model weights or new dataset were downloaded.

The successful T4 smoke measured **57.935 seconds for 20 updates**, peak **3.195 GiB allocated / 3.479 GiB reserved**, at sequence lengths up to261. Linear update scaling gives ~264 seconds but ignores different lengths, validation and checkpoint costs. **Budget 10–30 minutes for training/validation/checkpoints and 15–45 minutes for setup/load**; these are unverified estimates. Plan 4–8 GiB allocated at the unchanged batch and <=512 limit; actual full-run peak remains unmeasured. Require a free single T4 with >=14 GiB physical and >=12 GiB free VRAM, >=6 GiB available host RAM and >=20 GiB disk. Never silently switch to CPU or paid compute.

There are 17,432,576 trainable adapter parameters. Adapter plus two FP32 optimizer moments is about **199.5 MiB per checkpoint**, before metadata/temporary files. Reserve **2 GiB** for both checkpoints, probes and logs. Base weights and environment use the separate disk allowance. Colab allocation/session duration is not guaranteed.

## Approval status and reproducibility

**One bounded proposal is ready for approval; execution remains blocked on user authorization, validation review before loss monitoring, independent human evaluation review before testing, and the subsequent approved full-run execution change.** Dataset uncertainty is disclosed rather than treated as resolved. No training or model-release claim is made.

Local ignored packet: `research/runs/aya-training-approval-v2-final/`:

- `train.jsonl`, `NOTICE.md`: 363 unchanged examples and attribution.
- `risk-review.json`, `selection-dispositions.jsonl`: sampled observations, all frozen risk flags and complete selection accounting.
- `validation-candidates.jsonl`, `validation-provisional.jsonl`, `validation-review.jsonl`, `validation-review-packet.md`: all89 original records, eligible66 and review holds.
- `evaluation-draft.jsonl`, `review-packet.md`, `human-review-template.jsonl`: 32 tasks/rubrics, readable training/evaluation texts and 121 pending human review entries.
- `manifest.json`: source/plan/script/output hashes and explicit false authorization/validation flags.

Historical approval materials and sources remain under `aya-training-readiness-v2/`, `aya-training-readiness-authoring-v1/` and `aya-training-revision-v2/previous-proposal/`. The current risk-authoring scripts and full review provenance are retained locally in `aya-training-revision-v2/`; a public checkout alone cannot reconstruct private texts or reviews.

Plan SHA-256: `9ab753aa10954de2832187df4486b95507dd33e4446cb9b6402c9ad9588e6ac8`.
Training SHA-256: `33a8edcaddee3c5b3fca12513b17ac906525b6d69745588b8a4c6cb848a071ac`.
Evaluation draft SHA-256: `e3d2c7c81d537428d4e2742b2cb47d30d4e961881bdac2add9fe050ea845a5a4`.

The preparer verified the frozen smoke files and source hashes, retained prompt-group isolation and rejected stale/missing review evidence. Two independent output directories were **byte-identical, including every manifest/output hash**. **96 research tests passed**, including17 planning tests for policy authorization, known concerns/holds, review hashes, partial accumulation counts, validation holds, pending human status, deterministic packaging and no training/benchmark entry point. Tests use synthetic records, not frozen benchmark examples.

```powershell
research/.venv/Scripts/python.exe -X utf8 research/prepare_training_readiness.py --source research/runs/aya-filipino-v2 --evaluation research/runs/aya-training-revision-v2/evaluation-reviewed-draft.jsonl --output research/runs/aya-training-approval-v2-final
research/.venv/Scripts/python.exe -X utf8 research/prepare_training_readiness.py --source research/runs/aya-filipino-v2 --evaluation research/runs/aya-training-revision-v2/evaluation-reviewed-draft.jsonl --output research/runs/aya-training-approval-v2-repeat
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
```

These output directories now exist: choose a new directory when reproducing; overwrites fail. Only the proposal, approval-material preparer, its tests, this report and research README changed. Existing data preparation, evaluation, smoke source/notebooks/dependencies and website were preserved. No training, paid resources, pushes or deployment.

### Local-only file inventory

The revision workspace contains `inspect_candidates.py`, `inspection.json`, `inspection-output.txt`, `review_candidates.py`, `risk-screen.json`, `risk-review-sample.txt`, `freeze_revision.py`, `risk-review.json`, and `evaluation-reviewed-draft.jsonl`. Its `previous-proposal/` preserves `aya-training-proposal.json`, `prepare_training_readiness.py`, `test_training_readiness.py`, `milestone-3-training-readiness.md`, `README.md` and `hashes.json`. These are private authoring/history materials, not an additional research subsystem.

The final and repeat packet directories each contain the eleven output files listed above plus `manifest.json`. An earlier intermediate `aya-training-approval-v2/` packet is retained for audit history and is superseded; use only `aya-training-approval-v2-final/` with the current frozen plan. Nothing was deleted. All these directories remain ignored.

# 0004 — Bounded Aya adaptation and final-checkpoint comparison

Recorded: October 13, 2026. Status: implemented; release restrictions remain.

**Retrospective documentation.** This record describes the retained proposal, separate execution authorization, and completed evidence. It is not public preregistration, external review, or proof of dataset rights.

## Context and problem

Makata had verified comprehension baselines and a successful 20-update QLoRA engineering test. The next question was whether one bounded Filipino instruction-tuning run changes performance under the unchanged Tagalog reading-comprehension protocol. Instruction following and passage comprehension are different objectives; transfer was a hypothesis, not established by the dataset choice.

## Criteria and chosen direction

Use the same Qwen3-1.7B-Base revision; select 363 screened Aya Filipino v2 records in distinct training groups; train one epoch on a free T4. Exclude known defects, explicit holds, and flagged unresolved third-party material. Preserve the 283 examples without individual content review as a disclosed limitation, not a claim of validation.

Keep the verified NF4/FP16 pipeline, response-only masking and initial AMP loss scale 1024. Freeze checkpoints 50 and 91, and compare the predetermined final checkpoint 91. Do not select using benchmark outcomes or provisional validation loss. Evaluate on the original FP32 base with unmerged FP32 adapters so precision and quantization do not differ from the baseline control.

## Documented alternatives and rationale

The earlier 24-example/six-update proposal was rejected as another engineering test after the successful smoke run. The revised proposal used a larger screened subset rather than discovering additional datasets. The prior FilQuAD investigation did not establish an accessible, cleared replacement. These are recorded developments; this record does not invent an exhaustive model or dataset search.

QLoRA fit the demonstrated free-T4 memory budget. One epoch bounded exposure and cost. This does not establish that the chosen data, schedule, or checkpoint was optimal.

## Constraints and tradeoffs

Only 80 selected records had individual agent observations; none had dataset-wide independent native-speaker/legal approval. The 66 provisional validation records were diagnostics. The separate 32 agent-authored tasks remained unscored pending independent review. The independently reviewed untouched evaluation requirement was therefore **not satisfied**. The explicit authorization permitted an exploratory internal experiment, not a validated model or unrestricted release. The frozen proposal's historical pending status was preserved and a separate authorization used.

## Supporting evidence

- Frozen proposal: `research/aya-training-proposal.json`, SHA-256 `9ab753aa10954de2832187df4486b95507dd33e4446cb9b6402c9ad9588e6ac8`.
- Execution authorization: `research/qlora-full-authorization.json`.
- Training procedure/evidence: `docs/milestone-3-qlora-full.md`; final adapter SHA-256 `f7605c629df52087d04da01fcf018368986570f64e3f864071eacb4a0ebdde2a`.
- Evaluation freeze: `research/post-training-plan.json`, SHA-256 `a53f12b373d186b616803b6642840a27f6a7c57c9ec989e56190b65c2b17b4c3`.
- Results/uncertainty: `docs/milestone-4-post-training.md` and Report 002's public evidence summary. Underlying per-example evidence remains private; public hashes do not grant access to it.

## Consequences and reconsideration

Training and adapter reload succeeded. The observed +1.67-point accuracy difference has a paired 95% passage-bootstrap interval of −1.45 to +4.80 points; a dependable gain is not established. Preserve regressions and negative evidence. Do not tune repeatedly against observed benchmark failures.

Revisit before further training or release if qualified review changes data eligibility, permissions are clarified, independent evaluation becomes available, or a new predeclared study warrants a different intervention. Do not reinterpret this retrospective record as prior approval of future experiments.

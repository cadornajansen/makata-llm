# 0003 — Preserve the official zero-shot likelihood protocol

**Recorded:** 2026-10-12. **Status:** adopted for Report 001. **Record type:** retrospective documentation.

## Context and problem

Changes to prompts, answer parsing, data versions, or truncation can change scores. The study requires a reproducible comparison and must prevent engineering tests from becoming benchmark measurements.

## Criteria and chosen direction

Use FilBench fork revision `7ad52795d7d218d4679f93a019b58dde4b749c5b`, custom entry `community_tasks/filbench_evals.py`, task `filbench|belebele_fil_mcf|0|0`, and Belebele revision `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`.

Preserve the official prompt, `int(correct_answer_num) - 1` conversion, and answer-label continuations. Sum continuation-token log probabilities and select the maximum; report unnormalized MCF accuracy. Use all 900 questions, zero few-shot demonstrations, no chat template or extra system prompt, and no silent context truncation. Freeze model and tokenizer revisions independently even where they are identical.

## Rationale and documented alternatives

The task source also defines other formulations. This study selected MCF; it does not merge their metrics or use generated-answer parsing. The earlier brief fixes the upstream protocol rather than comparing prompt variants. There is no documented prompt sweep to reconstruct.

CPU float32 with batch one was the original engineering configuration. After resource checks failed locally, explicit CUDA execution preserved float32 scoring, disabled TF32 and quantization, and kept batch one. This hardware amendment was frozen separately before benchmark access; the original CPU plan was retained. Numerical bit identity across devices is not promised.

## Constraints and tradeoffs

Float32 costs memory and time. Strict revision, device, memory, and context checks can abort a run rather than produce a partial score. Free GPU sessions are not guaranteed. A conservative runtime screen was amended from three to four hours before benchmark access after synthetic-pilot timing; this did not change models, scoring, or test examples.

## Supporting evidence and chronology

- [Official custom task entry](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/community_tasks/filbench_evals.py).
- [Official Belebele formulation](https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/filbench/belebele.py).
- [Committed protocol brief](https://github.com/cadornajansen/makata-llm/blob/1c811c1b5a6b6208afb6448482c12ae54dbfe393/docs/first-study.md).
- Frozen GPU profile SHA-256: `c14bc54e2d653bae3e4f8423cabbb1b5c8e1177462fae82f19a006e29ee8e98b`.
- Frozen source bundle SHA-256: `ac9949705cd1f5f5e6e9e266afb8b6f840c46ae7fab584ba6d8f34d236e05fde`.

The retained profile timestamp precedes both full runs and records no benchmark access at freeze. This retrospective record documents that local workflow; it is not an externally registered protocol.

## Consequences and revisit conditions

Failures and incomplete runs are not full baselines. Local verification checks all 900 unique IDs, finite per-choice scores, predictions, exact pins, source/profile hashes, zero truncation, and agreement with official metrics. Retain raw results privately rather than redistributing benchmark passages.

Revisit the protocol only through a new documented experiment or explicit correction. Future adaptation comparisons need identical evaluation conditions and a separate untouched evaluation set. Do not select prompts, checkpoints, or hyperparameters by repeatedly inspecting these test failures.

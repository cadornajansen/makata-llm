# 0001 — Begin with Tagalog reading comprehension

**Recorded:** 2026-10-12. **Status:** adopted for Report 001. **Record type:** retrospective documentation.

## Context and problem

Makata intends to investigate Filipino-language GPU fine-tuning. Before selecting an intervention, it needs a bounded, reproducible measurement of existing open-weight models. General claims about Filipino ability would exceed the evidence available from an initial small study.

## Selection criteria and chosen direction

Use an established task with explicit labels, a published evaluation implementation, a manageable complete test split, and documented provenance. The chosen scope is Tagalog reading comprehension on translated passages: all 900 questions in `facebook/belebele`, `tgl_Latn`, test split, evaluated through FilBench's zero-shot MCF task.

## Rationale and documented alternatives

The committed first-study brief identifies Taglish conversation, cultural knowledge, and open-ended generation as abilities this task does not measure. It names Batayan/SEA-HELM as possible later evaluation resources and rejects combining unrelated task scores into a custom metric. There is no contemporaneous record of a comprehensive benchmark-selection contest; this record does not invent one.

Established labels and an upstream protocol make the initial measurement inspectable without first asserting that Makata's own synthetic questions form a validated benchmark. The 20 original debugging questions remain development fixtures only.

## Constraints and tradeoffs

One translated multiple-choice benchmark cannot represent native-language use or all Philippine languages. Public test material may have appeared in model training. Questions share passages, limiting independence assumptions. The narrow task makes execution feasible while restricting conclusions.

## Supporting evidence and chronology

- [First-study brief at commit 1c811c1](https://github.com/cadornajansen/makata-llm/blob/1c811c1b5a6b6208afb6448482c12ae54dbfe393/docs/first-study.md), committed 2026-10-12T07:37:30Z, records the scope and evaluation protections before the retained runs.
- [FilBench](https://aclanthology.org/2025.emnlp-main.127/) and [Belebele](https://aclanthology.org/2024.acl-long.44/) establish the external task provenance.
- The public Report 001 evidence summary records the complete 900-question runs and their hashes.

This document was written after execution. The earlier commit supports the stated scope; it is not a formal public preregistration.

## Consequences and revisit conditions

Report findings only for this protocol. Do not use observed test failures as a repeated tuning loop. Before adaptation, establish separate development material and an independently authored, untouched Filipino evaluation set. Revisit task coverage when a specific adaptation hypothesis requires generation, code-switching, cultural knowledge, or another language; document each additional task separately.

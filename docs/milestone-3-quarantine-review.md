# Aya Filipino quarantine inspection

**October 12, 2026 — proposals only; no records restored.**

Inspected all **742** quarantine records for flags, prior decisions, grouping and provenance; read a **24-record diagnostic sample** in detail. Original text and content hashes were checked against the pinned Parquet for all 742. This is not a completed linguistic, factual or rights review of the entire quarantine.

Source: `CohereLabs/aya_collection_language_split`, revision `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`. Quarantine: `research/runs/aya-filipino-v1/quarantine.jsonl`, SHA-256 `5e18a703efbb9ede6934f5d78d940e321678f496e0293a6e6f3480c230cfcc4b`. The previous [data audit](milestone-3-data-audit.md) counted flags before review exclusions across 1,233 deduplicated records; the counts below refer **only to the current 742**.

## Reasons and counts

| Quarantine flag | Records carrying flag | Records with this flag alone |
| --- | ---: | ---: |
| `answer_variants` — different responses in a prompt group | 645 | 404 |
| `near_duplicate_prompt` — similar prompts | 201 | 16 |
| `time_sensitive_or_unsupported_claim` | 114 | 49 |
| `medical_or_health_claim` | 31 | 15 |
| `third_party_creative_text` | 11 | 5 |
| `sensitive_or_unsafe_content` | 7 | 3 |
| `suspicious_formatting` | 5 | 1 |

These categories **overlap**: 737 records carry 1,014 flag memberships. Five additional records have no automatic flags and remain quarantined by explicit agent review holds. There are 354 distinct quarantined prompt groups. No privacy, language-mismatch or benchmark-near-overlap flags occur here; that is not proof of their absence.

A mutually exclusive accounting is:

- **574:** grouping flags only, with no prior explicit hold.
- **5:** grouping flags only, plus an explicit quality hold (IDs 22, 201, 322, 927, 1044).
- **158:** at least one other content flag, possibly also grouping flags.
- **5:** explicit review holds only (IDs 44, 284, 642, 1146, 1178).

Total: **574 + 5 + 158 + 5 = 742**. Across the quarantine, 696 records have no previous decision, 30 have agent `accept` observations, and 16 have agent `hold` observations. Agent acceptance never cleared flags and does not represent human approval.

## Which rules over-trigger?

The principal issue in [prepare_dataset.py](../research/prepare_dataset.py) is that every flag triggers quarantine, including grouping signals that are not quality verdicts. **579 records (78.0%) have only grouping flags**, but five of those also have explicit unresolved quality holds. None of these counts is an estimate of recoverable examples.

| Rule | Evidence from the inspected sample | Assessment |
| --- | --- | --- |
| Different answer strings | 12/299 give equivalent divisibility answers; 19/513 both give 97; 31/42 both give 1/3. | Textual variation is not contradiction. Review related answers together. Conversely, 201/322 still have grammar problems. |
| Near prompts | 814/815 have equivalent seat-count prompts and identical answers; arithmetic is correct, but spelling needs review. | Grouping already keeps related records in the same split. Similarity alone should not imply unusability. |
| Time/claim keywords | 132 is probability arithmetic flagged by `%`; 127 uses `ngayon` in a language example. | These are not time-dependent factual claims. Technology descriptions such as 64 still need source/date checks. |
| Markup detection | All five formatting-flagged records contain C++ include/stream syntax matched by `<[^>]+>`. | Code syntax is being mistaken for suspicious markup. No compile or whole-group quality clearance follows from this finding. |
| Creative-text keywords | 184 explains a word; 499 mentions a song as a timer without reproducing lyrics. | Mention is not reproduction. Actual multi-line lyrics in 46 remain under an unresolved rights hold. |
| Health/safety keywords | 247 mentions medicine as a product in an economics explanation; 402/754 describe history/literature. | Topic words do not establish medical advice or harmful instructions. Accuracy and provenance still require review. |

**Recommended approach:** review grouping-only examples in their existing groups first, distinguishing equivalent answers from real errors. Preserve group IDs and split assignments, and retain substantive rights, factual, medical and language holds. Do not globally disable rules or lower thresholds based on this sample. No rule changes were made.

A missed flag is also informative: 44 is a health explanation with no automatic health flag; 1178 has an unresolved grammar concern with no automatic flags. Lexical screening cannot replace judgment.

## Review packet for approval

Local, Git-ignored files in `research/runs/aya-filipino-quarantine-review-v1/`:

- [review.md](../research/runs/aya-filipino-quarantine-review-v1/review.md): readable original instructions/responses, IDs, flags, related records, prior observations, proposals and remaining checks.
- [review.json](../research/runs/aya-filipino-quarantine-review-v1/review.json): exact original text, source and content hashes, all category membership IDs/combinations, and blank human-decision fields.
- [verify.py](../research/runs/aya-filipino-quarantine-review-v1/verify.py): read-only integrity check.

The fixed, purposive sample covers every observed flag plus explicit holds, with paired examples for the largest categories. It is **not random**, and cannot measure false-positive prevalence. It includes IDs 12, 299, 19, 513, 31, 42, 814, 815, 132, 127, 64, 189, 184, 46, 247, 499, 1018, 402, 754, 653, 1178, 44, 201 and 322.

**Eight proposals invite consideration after human review; sixteen propose continued holds. All 24 remain quarantined.** Acceptance candidates are 12, 299, 19, 513, 31, 42, 132 and 127. Their elementary numerical checks passed; native wording review remains necessary. The packet deliberately is not the pipeline's decision-input format and cannot silently apply these proposals.

Specific source checks reinforce caution: [CDC](https://www.cdc.gov/clean-hands/about/index.html) supports at least 20 seconds of scrubbing and specifies the birthday song twice; 499 omits the repetition and has repetitive wording. [AHA](https://www.heart.org/en/health-topics/cardiac-arrest/emergency-treatment-of-cardiac-arrest/cough-cpr) does not endorse cough CPR, but that does not validate the remaining emergency advice in 1018 or equate cardiac arrest with heart attack. Both remain held. These primary pages were read during this inspection; other sample claims are not represented as externally verified.

Publisher-declared Apache-2.0 provenance remains unchanged. This inspection grants no third-party permissions. Original lyric text is confined to the ignored review packet; it is not reproduced in this report or published.

## Verification and unchanged state

Run from the repository root:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/runs/aya-filipino-quarantine-review-v1/verify.py
```

The check validates original source text, counts, flag coverage, paired-group preservation, pending decisions, and recorded file hashes. All original prepared-output hashes, preparation/evaluation code, dependency lock, engineering fixture and two retained benchmark sample-file hashes remained unchanged. Benchmark files were hashed only; their questions, predictions and scores were not parsed for this inspection. No preparation rerun or inference was performed.

Only this report and the three local review files were created. Existing code, datasets, review decisions and prior documents were not modified. No files were deleted. No production code changed, so verification used artifact integrity checks rather than rerunning training/evaluation tests.

The existing state remains **437 training candidates, 49 validation candidates, 742 quarantined, 13 excluded, and zero cleared for training**. Your review of the packet is the next decision; nothing has been restored, trained, pushed or published.

# Aya Filipino preparation v2: grouping is not a quality verdict

**Recorded October 12, 2026. Preparation verified; candidates remain provisional, not cleared for training.**

This revision implements the [quarantine inspection](milestone-3-quarantine-review.md) without editing the original source, prior audits or v1 exports. It separates leakage-prevention groups from substantive quality concerns and records new agent-assisted review findings. No training, benchmark inference, cloud service or website change occurred.

## Original and revised counts

| Disposition | v1 | v2 |
| --- | ---: | ---: |
| Original Aya records | 1,241 | 1,241 |
| Provisional training candidates | 437 | **951** |
| Provisional validation candidates | 49 | **89** |
| Total provisional candidates | 486 | **1,040** |
| Quarantined | 742 | **184** |
| Exact duplicate copies excluded | 8 | 8 |
| Content-review exclusions | 5 | 9 |
| Total excluded | 13 | **17** |
| Cleared for training | 0 | **0** |

Accounting: **1,241 = 951 + 89 + 184 + 17**. All 486 previous candidates remain candidates. Of the 742 previously quarantined records, 554 become provisional candidates, 184 remain held and four are excluded for specific content defects.

The requested **579 records with grouping flags only** were reassessed: **545 provisional recoveries, 30 continued/new holds and four exclusions**. The five earlier explicit holds (22, 201, 322, 927, 1044) remain unchanged. Among the other 163 quarantine records, nine recoveries follow the narrowed quality rules; 154 remain quarantined. No blanket approval was applied to the quarantine.

Every original ID has a reason in the local `dispositions.jsonl`: 1,040 have no blocking quality flag/hold, 140 have unresolved quality flags, 44 have explicit review holds, nine have explicit review rejections, and eight are exact duplicate copies. Reasons and review rationales are retained per record, including unchanged dispositions.

## Pipeline changes

1. `group_prompts` still builds the same connected components, but exports `grouping_signals` separately from quarantine `flags`. Different answer strings and near prompts do not establish contradictions. They never independently trigger quarantine.
2. Existing normalization, deduplication, grouping thresholds and seed **1234** remain unchanged. All surviving records keep their original prompt, response, provenance, group ID and assigned split. There are still 842 source groups and 90 near-prompt edges. The candidate splits contain 661 training groups and 66 validation groups, with no shared group. Validation is 8.56% of candidate records and 9.08% of candidate groups; no seed search or rebalancing occurred.
3. Narrow contextual exceptions remove `%` as a quality trigger for probability-complement exercises; ignore `ngayon` in illustrative language/scenario prompts while retaining response-side and other claim triggers; and distinguish standard C++ includes/stream operators from suspicious markup. Other markup, URLs, privacy, creative-text, medical and safety screening remain active.
4. All inherited explicit holds/rejections are retained. This revision refuses attempts to override them. New agent `accept` observations do not clear substantive flags and never assert native-speaker, legal or training approval. New content-specific holds/rejections remain possible.
5. A disposition ledger records all 1,241 originals, prior/new status, signals, substantive flags and review rationale. No response was rewritten, repaired or replaced.

Eleven existing records were affected by the narrowed heuristics and inspected individually: **127, 132, 149, 189, 271, 400, 403, 488, 512, 603, 604**. Nine became provisional candidates. Record 403 remains held for an inference concern, and 189 for the earlier wording/code-review concern. Fixing a false flag is not automatically a whole-example approval.

Remaining quarantine flag memberships overlap: time-sensitive/unsupported claims **108**, medical/health **31**, third-party creative text **11**, sensitive/unsafe content **7**. Explicit holds can apply without a heuristic flag. All creative-text concerns remain quarantined; this revision does not establish permission for reproduced lyrics or quoted passages.

## Deterministic review and findings

Sampling was fixed before disposition decisions: sort the 574 grouping-only records without explicit holds by `SHA256("1234:recovery-review:" + id)`, take 60, then inspect every quarantined member of their groups. This produced **139 records in 56 groups**. Expansion captures alternatives but favors groups with more records; it is not a uniform group sample or a population false-positive estimate.

The 56 group observations distinguish:

| Agent observation | Groups |
| --- | ---: |
| Consistent variants on inspection | 41 |
| Consistent core with unresolved quality concerns | 11 |
| Different tasks legitimately sharing a lexical group | 1 |
| Shared factual error | 1 |
| Incomplete answer variant | 1 |
| Contradiction resolved by arithmetic | 1 |

Additional inspection covered the eleven heuristic exceptions and records 814/815 from the earlier spelling review, totaling **152 record observations**: 120 provisional `accept` observations, 28 holds and four rejections. These are agent assessments, not human approval. The deterministic sample is preserved in `selected-group-review.json`; findings are in `group-observations.json` and content-hashed `revision-reviews.jsonl`.

Concrete findings:

- **Valid alternatives:** 312/1078 both calculate 32/4 = 8; 372/724/1130 calculate 608/19 = 32; 1228/1231 agree on 1982 as MCMLXXXII. Concise versus expanded reasoning is not a contradiction.
- **Different tasks in one lexical group:** Java multiplication, Java addition and Python addition were connected by shared wording. Different answers are appropriate to their respective prompts. The conservative shared split is preserved.
- **Contradictory arithmetic:** 990 answers 8 incorrectly spelled words; 1087 correctly computes 15 − 8 = 7. Exclude 990; preserve 1087 as a candidate.
- **Shared wrong answer:** 214/273 call Filipino and English national languages. Article XIV sections 6–7 distinguish the national language from the official languages. Both unchanged answers are excluded. The [Supreme Court E-Library](https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/3/353) and [Official Gazette](https://officialgazette.gov.ph/constitutions/1987-constitution/) indexed primary text supports the distinction; initial direct fetches returned 502/403 before the indexed text was retrieved.
- **Incomplete instruction response:** 731 supplies only an `if` branch for an `if-else` request; exclude it. The companion 485 contains both branches.
- **Substantive holds:** vitamin-D and veterinary claims missed by coarse keywords; an unsupported idiom-origin explanation; a long quoted passage with unresolved provenance; strict yes/no responses containing extra prose; incomplete/version-sensitive setup instructions; and conspicuous language defects. Agreement between answers does not prove correctness or rights.

Numerical examples, palindrome strings, an anagram and leap-year branch outcomes were checked directly. Source-provided programs were not executed or compiled. Other historical, cultural, medical and linguistic assertions were not exhaustively independently verified. Minor language limitations are noted without silently rewriting examples.

Of the **554 recovered candidates, 134 have retained agent observations from this or the prior review; 420 have no individual content-review observation**. They satisfy the revised structural screening rules only. This explicit gap is a reason not to present the export as a verified clean training corpus.

## Benchmark protection without accessing test examples

The new `--previous-preparation` option reuses the audited v1 screening receipt only for unchanged source text. It verifies the pinned manifest SHA-256 `34497dae172bfab8770c5b2fff8c0c0aebed57bf6564dbe5e13388edb0ddc97f`, every referenced output hash, source/model-independent dataset identity, all deduplicated record hashes, and unchanged groups/splits. Inherited near-overlap holds remain binding. Unsupported receipts or exclusions without screened text hashes fail closed.

The original benchmark parser and exact/12-word overlap functions were not changed. The fresh-screening option remains available for separately authorized use, but **no retained Belebele example file was opened during this revision**. Tests use synthetic benchmark-shaped data. No new contamination screening or broader coverage is claimed; the earlier receipt covers only the frozen Tagalog Belebele and engineering fixtures. A changed/new text cannot inherit this receipt.

Aya remains pinned to `a3af2fde4b4cb5b2775830b11244a1a20b5f004f`, with Parquet SHA-256 `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc`. Publisher-declared Apache-2.0 and its third-party-rights limitations remain as documented in the [original audit](milestone-3-data-audit.md).

## Commands and verification

Executed from the repository root:

```powershell
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --previous-preparation research/runs/aya-filipino-v1 --reviews research/runs/aya-filipino-v2-review/revision-reviews.jsonl --output research/runs/aya-filipino-v2
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --previous-preparation research/runs/aya-filipino-v1 --reviews research/runs/aya-filipino-v2/review-decisions.jsonl --output research/runs/aya-filipino-v2-offline
research/.venv/Scripts/python.exe -X utf8 research/runs/aya-filipino-v2-review/verify_refinement.py
```

**64 tests passed**: 37 preparation tests plus 27 existing research tests. New coverage includes nonblocking grouping, retained substantive holds, targeted false positives, receipt authenticity/tampering, changed text/group refusal, inherited review protection, and execution without the benchmark loader. Existing synthetic prompt/likelihood/protocol tests still pass.

Both real offline runs completed with identical hashes for **all eleven deterministic outputs**. Integrity checks reconcile all original IDs, confirm train/validation group isolation, preserve all earlier holds/rejections and audit artifacts, and confirm real outputs remain Git-ignored. Only execution timestamps differ.

- Training SHA-256: `7468b67418756b738bc2bf4d5455316d87e116db242852738029f5dff4833ef2`
- Validation SHA-256: `cf006ddeffdbad609fb9d00cc7340b5465744a4e35b804461b7efcfa1866bd29`
- New review-input SHA-256: `be4d05c385da72380f25efb11bf29627135ae7eefe1fa21d5dc7251c925be361`

## Files and readiness

Modified: `research/prepare_dataset.py`, `research/tests/test_dataset_preparation.py`, `research/README.md`. Added: this report. No existing source, old audit or website file was deleted or modified outside those three listed files.

Each ignored `research/runs/aya-filipino-v2/` and `aya-filipino-v2-offline/` directory contains: `train.jsonl`, `validation.jsonl`, `quarantine.jsonl`, `exclusions.jsonl`, `review.jsonl`, `dispositions.jsonl`, `review-decisions.jsonl`, `prior-review-decisions.jsonl`, `prior-screening-manifest.json`, `source-card.md`, `NOTICE.md`, and `manifest.json`.

The ignored `aya-filipino-v2-review/` directory contains: `before-prepare_dataset.py`, `before-test_dataset_preparation.py`, `before-README.md`, `preserved-hashes.json`, `selected-group-review.json`, `group-observations.json`, `revision-reviews.jsonl`, and `verify_refinement.py`. Source snapshots preserve prior behavior as evidence; they are not executable relocated project installations. The old quarantine-review verifier intentionally checks the old script hash; use this revision's verifier for the revised script.

**Recommendation: do not start even the bounded fine-tuning run yet.** The preparation mechanics are verified, but content/rights review remains incomplete, 420 recoveries have no individual observation, repeated variants can overweight narrow tasks, and the independently authored untouched evaluation set is still outstanding. Resolve those explicit review requirements before proposing the bounded run. No improvement over the baseline is inferred from increased candidate count. Training remains a separate approved step.

# Milestone 3, Step 1: Aya Filipino data preparation

**Recorded: October 12, 2026. Preparation complete; dataset provisional and not cleared for training.**

This step prepares local instruction-response candidates for a proposed supervised fine-tuning experiment with `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`. It does not train a model or change the completed baseline experiment. Makata-v0.1 remains a proposed adaptation, not an existing checkpoint.

## Source and provenance

| Item | Verified value |
| --- | --- |
| Repository | [CohereLabs/aya_collection_language_split](https://huggingface.co/datasets/CohereLabs/aya_collection_language_split) |
| Immutable revision | `a3af2fde4b4cb5b2775830b11244a1a20b5f004f` |
| Selected file | `filipino/train-00000-of-00001.parquet` only |
| File size | 272,626 bytes |
| Parquet SHA-256 | `8140b6bbdfca748fab7203bfe094574fabe0a0527b256dff0d07170357e4f1bc` |
| Pinned repository-card SHA-256 | `453f2533dff0f575876bd5919e695db17f0b9c1d1b76b7d35e85ee0e9845bed1` |
| Original records | 1,241 |
| Language / source / split | Every record: `fil` / `Aya-Dataset` / `train` |
| Script | Every record: `Latn` |
| Unique source IDs | 1,241 |
| Distinct raw prompts | 939 |
| Distinct raw prompt-response pairs | 1,233 |

These counts were recomputed from the pinned Parquet bytes, independently of the preceding recommendation. The repository card's language table lists 220 Filipino records, which conflicts with the actual selected file. This preparation uses verified file contents, not that stale table. The script rejects a changed revision, changed bytes, source composition, schema, count, or duplicate source ID. Source text is preserved in the ignored cache; no other language subsets or Aya evaluation split were fetched.

[Aya's original dataset card](https://huggingface.co/datasets/CohereLabs/aya_dataset) and [Singh et al. (2024)](https://arxiv.org/abs/2402.06619) describe human-written original annotations and human edits of existing examples. The selected collection-format file labels all examples `Aya-Dataset`, but does not retain the original dataset's `annotation_type` field. Consequently, this audit cannot distinguish wholly original authorship from human-edited antecedents for each individual example. It makes no claim that every row is free of generated or translated ancestry.

## Filtering and grouping decisions

The implementation is [prepare_dataset.py](../research/prepare_dataset.py). It is separate from the frozen evaluation runner and uses only existing dependencies.

1. Validate schema, source identity, IDs, and nonempty string prompt/response fields. No invalid text rows occurred in this source. A malformed row's text is automatically excluded; structural/source mismatches stop the run.
2. Normalize output text to Unicode NFC, LF line endings, and outer trim only. Do not collapse internal paragraphs or rewrite, translate, or repair answers.
3. Remove exact pairs, retaining the lowest numeric source ID. Preserve duplicate source IDs in provenance and explicit duplicate mappings. Both raw and normalized exact-duplicate excess counts were **8**; normalization introduced no additional pair duplicates.
4. Group case-folded, punctuation-insensitive prompt keys. For prompts of at least five words, connect pairs with word-set Jaccard similarity at least 0.85, or character similarity at least 0.92 with a length ratio at least 0.85. Connected components preserve transitive relationships. Short prompts receive exact-key matching only.
5. Apply evaluation-overlap exclusions and conservative quality flags. Quarantine unresolved flagged examples. Different responses in one prompt group are **possible variants**, not proven contradictions.
6. Apply explicit, content-hashed review decisions without changing text. An agent acceptance never clears a heuristic flag. Human acceptance can clear heuristic flags but cannot override a confirmed evaluation overlap. This release deliberately never asserts training readiness automatically.
7. Assign whole groups by SHA-256 of seed **1234** and group ID: the lowest tenth of the first 64-bit hash range goes to validation. Grouping precedes quarantine/review, so reviewing an example does not reassign its group. No forced rebalancing or seed search occurred.

The source produced **842 prompt groups** and **90 near-prompt edges**. Near-duplicate grouping is a lexical safeguard, not a semantic equivalence detector. Negation and small factual differences can be important even when prompts look similar; those cases remain quarantined for judgment.

These filtering rules were developed during this data audit, including a health-content flag added after a source-data inspection exposed a medical factual error. They were not preregistered. No benchmark scores or benchmark failure cases informed those changes.

## Final local counts

| Classification | Records |
| --- | ---: |
| Original source | 1,241 |
| Excluded exact duplicate copies | 8 |
| Excluded after agent-assisted quality review | 5 |
| Excluded invalid text | 0 |
| Excluded detected evaluation overlap | 0 |
| Quarantined pending review | 742 |
| Provisional training candidates | 437 |
| Provisional validation candidates | 49 |
| Total provisional usable candidates | **486** |
| Records cleared for training by this step | **0** |

Accounting: **1,241 = 8 + 5 + 742 + 437 + 49**. Duplicate provenance may list multiple original IDs, but each original is classified once. The 486 candidate records occupy 486 groups; training and validation group IDs are disjoint. Validation comprises **10.08%** of retained records and groups. Quarantined records retain their assigned split for later review.

The purely screened preparation, before agent decisions, contained 443 training and 49 validation candidates. The final numbers above include the retained review input; reproducing them requires that input, not merely the source dataset. "Usable candidate" denotes structural eligibility after these rules, not established accuracy, native fluency, legal clearance, or training approval.

Flag counts below overlap and are measured before review dispositions, across 1,233 deduplicated records:

| Flag | Records |
| --- | ---: |
| Different answers within a prompt group | 648 |
| Near-duplicate prompts | 201 |
| Time-sensitive or potentially unsupported claims | 116 |
| Medical or health content | 32 |
| Possible third-party creative text | 11 |
| Sensitive or potentially unsafe content | 7 |
| Suspicious formatting | 5 |
| Possible personal information / language mismatch | 0 / 0 |

Zero flags do not establish absence. Language screening is a crude marker check; it cannot validate Filipino fluency or Taglish quality. Safety and personal-information rules are keyword/pattern checks, not comprehensive classifiers. No new classifier or paid service was used.

## Representative quality audit

The fixed-seed sample contains **60** deduplicated examples. Category coverage added two distinct examples; eight targeted follow-ups examined lyrics and grammar variants. All **70** received retained **agent-assisted observations**: 49 accept observations, 16 holds, and five rejections. Acceptance records inspection only; it is neither human approval nor a guarantee of factual accuracy. No native-speaker or legal reviewer has signed off. The sample is not a prevalence estimate or a full dataset review.

| Dimension | Finding and disposition |
| --- | --- |
| Filipino correctness | Several spelling/word-choice issues and a repeated `rin`/`din` explanation that confuses sentence endings with the preceding word. Grammar variants remain held; no text was repaired. |
| Instruction-response relevance | Many examples directly answer recipes, coding, arithmetic, pronoun-reference, and everyday questions. Their presence does not establish broad cultural or language coverage. |
| Factual accuracy | Reject `aya-fil-81`: conflates tenfold seismic amplitude with energy. [USGS](https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity) distinguishes amplitude x10 from approximately x32 energy per magnitude unit. |
| Health accuracy | Reject `aya-fil-119`: describes melatonin as the skin pigment. [Philippine FDA Advisory 2019-182](https://www.fda.gov.ph/wp-content/uploads/2019/07/FDA-Advisory-No.2019-182.pdf) identifies melanin. Other health claims remain flagged for qualified review. |
| Statistics and geography | Reject `aya-fil-293`: contains an undated over-86% Catholic population claim unsupported here; [PSA's 2020 household-population result](https://psa.gov.ph/content/religious-affiliation-philippines-2020-census-population-and-housing) is 78.8%. Reject `aya-fil-1225`: collapses the two Mindoro provinces; [DILG](https://mimaropa.dilg.gov.ph/about-us/dilg-mimaropa/) identifies five MIMAROPA provinces. |
| Misleading premise/history | Reject `aya-fil-693`: fails to clearly correct a misleading premise about Filipino lacking an alphabet and gives an oversimplified historical account. This is an agent quality judgment, not a verified historical correction. |
| Translation and framing | Perspective-dependent left/right geography, awkward wording, and literal framing warrant native review. This audit cannot infer the translation history of a particular row from wording alone. |
| Copyright/provenance | Five targeted retained examples reproduce multi-line song lyrics, including Christmas songs. Rights were not established; these examples remain quarantined. No lyrics are reproduced in this report. |
| Safety and usability | Sensitive historical descriptions and health content need context-sensitive review. Code examples may be illustrative rather than runnable; one file-reading example omits resource cleanup. |
| Duplicates and variants | Same-prompt answers can be concise versus expanded, or revised. The pipeline does not arbitrarily choose the longest answer or label every difference a contradiction. |

Direct checks confirmed the sampled lottery division, travel-time division, rain-measurement average, digit-nine count, simple ratio, palindrome, and Python even-number sequence. Other factual examples were not exhaustively verified. The [KWF orthography PDF](https://kwf.gov.ph/wp-content/uploads/Ortograpiyang_Pambansa_1.pdf) returned HTTP 403 during verification; no detailed grammar/historical correction is attributed to an unread document.

Conservative flags have false positives: a handwashing answer mentions a song as a timing aid without supplying lyrics, and C++ include syntax resembles markup. Both illustrate why flags are review requests, not automatic legal or linguistic judgments.

## Licensing and research integrity

The pinned repository card declares **Apache-2.0**. [Apache's terms](https://www.apache.org/licenses/LICENSE-2.0) require preserving the applicable license and notices when redistributing covered material and identifying modifications. The output keeps the source card, attribution, license link, and preparation changes in `NOTICE.md`. This task redistributes nothing.

The publisher's declaration is evidence of intended licensing, **not proof that contributors owned every embedded lyric, quotation, or other passage**. No row-level permission was located for the reproduced lyrics. Quarantining flagged material reduces an observed problem but does not clear the unflagged remainder. Further native review and third-party-content provenance decisions remain necessary; this audit does not certify a legally cleared corpus.

Overlap screening uses the retained Qwen 900-example file with SHA-256 `e44bd4942d65e8ea03e519416d79f1f54dd53d2e7cf584d2addf5dc5ecce4512`, the recorded official task identity, and the 20 existing engineering fixtures (SHA-256 `cf22ec6cc0043a53cc6564f05ab959c24874437cff6e353af6f32ebf09b1e24b`). The benchmark dataset remains pinned to `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`.

The guard parses prompt text into passage, question, and choices. It excludes exact normalized question/passage matches and shared 12-word spans, and flags near-identical questions. Short commonplace answer choices alone are not contamination. An initial diagnostic incorrectly treated those short choices as exact matches; that behavior was corrected, regression-tested, and the final source screening found **zero detected overlaps**. This is not proof of absence of paraphrased contamination, pretraining contamination, or overlap with other benchmarks.

Predictions, gold answers, likelihoods, and correctness fields are not used for screening or filtering. No benchmark data was downloaded, inference rerun, or retained result modified. The separate, independently authored untouched Filipino evaluation set required by the research protocol is still outstanding and was not created here.

## Local artifacts and reproduction

Final output: `research/runs/aya-filipino-v1/`. Offline verification output: `research/runs/aya-filipino-v1-offline/`. Both are ignored by Git, as are the source cache and review input. Intermediate audit directories remain local and are not the final preparation.

| File | Purpose |
| --- | --- |
| `train.jsonl`, `validation.jsonl` | Stable-ID-ordered provisional prompt/response examples with group IDs and provenance |
| `quarantine.jsonl` | Unresolved flags, assigned split, and any review decision |
| `exclusions.jsonl` | Every excluded original and its reason/duplicate mapping |
| `review.jsonl` | Representative selections and agent observations |
| `review-decisions.jsonl` | Exact local review input, preserved for replay |
| `source-card.md`, `NOTICE.md` | Original pinned card, attribution, licensing statement, and changes |
| `manifest.json` | Completeness, revisions, rules, seed, counts, environment, script/input/output hashes, and readiness |

Plain prompt/response output does not choose a future Qwen chat template, tokenizer truncation policy, or training configuration. No model weights or tokenizer were downloaded by this step.

Verified environment: Python **3.12.13**, Hugging Face Hub **0.33.4**, PyArrow **20.0.0**, Windows CPU. Existing dependency lock SHA-256: `e487546619e8b7749036d18d38fd3c2bcfdb53c232206b72e4ecae9db11c2dad`. No dependency was added. The final preparation took approximately **91 seconds**; this is CPU data-processing time, not training time.

Exact final execution commands from the repository root:

```powershell
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -p test_dataset_preparation.py -v
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --benchmark-records research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760/samples.jsonl --reviews research/.cache/aya-filipino-agent-reviews.jsonl --output research/runs/aya-filipino-v1
research/.venv/Scripts/python.exe -X utf8 -m unittest discover -s research/tests -v
research/.venv/Scripts/python.exe -X utf8 research/prepare_dataset.py --offline --benchmark-records research/runs/colab-import-7df37d1937bf/evaluate-20261012T092104Z-256a4760/samples.jsonl --reviews research/runs/aya-filipino-v1/review-decisions.jsonl --output research/runs/aya-filipino-v1-offline
```

The two source files were initially cached with `hf_hub_download` using the exact repository, dataset repository type, full revision, and individual allowlisted filenames. The source cache and local review decisions are retained inputs; a fresh public checkout does not contain them or the private benchmark records. Follow [research instructions](../research/README.md#milestone-3-step-1-provisional-filipino-data) for the initial online source fetch. Without reviews, output counts differ intentionally.

Reproduction anchors:

- Review input SHA-256: `de89200aa4f3990852993162a45583e706daa4a5f017c1f00df2d5d3fefdafef`.
- Preparation script SHA-256: `a800879ba33bb7c1983fb31d5696e3145bd93173f2254d600a3f240c2cf0d994`.
- Training JSONL SHA-256: `3004dea1e3ddc62383469c700bb6247771a3f707281f530475fcce31101eab8c`.
- Validation JSONL SHA-256: `4c1d4bedfe0e4e5ffacca3b0e621b48cae1f0a19660730ec54179ea5ee58c764`.

The manifest records every output hash. Execution timestamps differ between reproductions; deterministic content and output hashes must agree.

## Verification and readiness

The preparation suite passed **25 tests**. The complete research suite passed **52 tests**, including all 27 pre-existing evaluation/Colab tests. Coverage includes source schema/pins/checksums, exclusions, normalization, transitive grouping, short-prompt guards, review hashes, deterministic splits, output accounting, outcome-independent overlap checks, manifests, interruption handling, and overwrite refusal. Tests use synthetic data and do not fetch benchmark examples.

Final artifact verification checks every recorded output hash, parses all JSONL rows, reconciles original classifications, verifies train/validation prompt-group isolation, and compares both offline runs. Existing evaluation source, dependency lock, frozen notebook, and existing evaluation tests were checked against hashes recorded before implementation. Git ignore checks cover all real dataset artifacts.

**Readiness: preparation completed, training not approved.** There are 486 provisional candidates, 742 quarantined records, unresolved native/factual/rights reviews, and no new untouched evaluation set. Small size and broad mixed-task coverage do not establish that this data will improve Belebele accuracy, Taglish conversation, or cultural understanding. No GPU resources, paid services, training, dataset publication, push, or deployment were used. Any next training experiment remains a separate decision requiring approval.

## Files changed in this step

- Added `research/prepare_dataset.py` — isolated preparation pipeline.
- Added `research/tests/test_dataset_preparation.py` — offline preparation tests.
- Added `docs/milestone-3-data-audit.md` — this audit.
- Updated `research/README.md` — execution, review format, and readiness instructions.

No files were deleted. Existing ignore rules already cover all real inputs and outputs, so no ignore-rule change was needed. The website, frozen research implementation, prior results, and unrelated working-tree changes were preserved.

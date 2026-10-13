# Makata research roadmap

This roadmap translates the [project vision](project-vision.md) and [seven research directions](research-directions.md) into evidence gates. It commits to standards of inquiry, not dates, budgets, products, or guaranteed releases.

## Verified starting point

The [Milestone 2 report](milestone-2-baselines.md) records completion on **2026-10-12**: two full 900-question Tagalog reading-comprehension baselines, with per-example artifacts checked against the frozen protocol and official aggregate results. That historical report precedes the exploratory adaptation completed October 13, 2026.

The completed comparisons use existing [Qwen3-1.7B-Base](https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/README.md) and [Sailor2](https://github.com/sail-sg/sailor2) foundations; the exact Sailor2-1B checkpoint and both models' revisions are documented in the report. The task uses [FilBench](https://aclanthology.org/2025.emnlp-main.127/) with the `tgl_Latn` subset of [Belebele](https://aclanthology.org/2024.acl-long.44/). These models, benchmark, and evaluation framework belong to their respective creators.

This is artifact verification, not a claim of an independent experimental replication or peer review. The task measures multiple-choice comprehension of translated Tagalog passages. It does not establish Taglish conversational ability, cultural knowledge, generative reliability, or overall Filipino competence. Checkpoints differ in size and training history, so their comparison cannot isolate a causal benefit of regional training. Detailed scores and computing measurements remain in the report; unrelated benchmark scores are not combined here.

| Work | Status | Evidence or condition |
| --- | --- | --- |
| Research foundations and engineering pilot | Verified completed | Protocol, separate synthetic development fixtures, pinned evaluation integration, pilot and automated checks documented in the study reports |
| Initial Tagalog comprehension baselines | Verified completed | Two complete runs and artifact verification documented in the Milestone 2 report |
| Further baseline runs or human-reviewed error analysis | Not recorded as active | Require an explicit study update; the current report makes no human-validated failure-category claims |
| First bounded GPU adaptation and paired evaluation | Exploratory execution verified | [Milestone 3](milestone-3-qlora-full.md) and [Milestone 4](milestone-4-post-training.md); +1.67 points, paired 95% interval −1.45 to +4.80; no established gain |
| Cultural, broader-language, preservation, script, efficiency, and original-pretraining studies | Exploratory | Each requires its own question, prerequisites, and evidence gate |

One internal adapter is trained and verified, using provisional Aya data. No validated/released Makata model, original cultural benchmark, or fully cleared adaptation corpus is established. Institutional affiliation, funding, and partnership claims require separate evidence; this roadmap establishes none.

## Status and evidence rules

- **Verified completed** means the stated exit criteria and supporting report are available. The claim applies only to that bounded work.
- **Active** means a defined study is actually under way, with its protocol and current state recorded. A plan or an available notebook alone does not establish active execution.
- **Next proposed** identifies the immediate research intention, pending its entry requirements. **Exploratory** identifies a possibility without an approved experiment or release commitment.
- Partial, failed, or unverified runs remain incomplete. Resource checks, synthetic pilots, and live console output are not full benchmark results.

Use the latest verified study report when updating status. Record the evidence supporting a transition and revise public summaries consistently. Do not promote an active run to completed work based on elapsed time or expected results.

## Research foundations — completed

**Entry.** Define a narrow reading-comprehension question, attribute the external task and model foundations, and separate engineering development from held-out benchmark access.

**Exit and evidence.** The [first-study protocol](first-study.md) and [Milestone 2 report](milestone-2-baselines.md) document the pinned harness, isolated environment, original synthetic debugging questions, CPU pilot, automated checks, and reproducibility safeguards. These establish engineering readiness for that experiment, not a Filipino capability score or training result.

## Initial comprehension baselines — completed

**Entry.** Freeze candidate revisions, the official prompt and scoring method, and the execution configuration before test access. Verify licensing, environment compatibility, memory, and runtime feasibility using separate development material. Any hardware change requires its own documented feasibility evidence.

**Exit and evidence.** Each selected model must produce a complete valid run: all 900 unique examples, finite per-choice scores, correct label handling, official aggregate reconciled with saved predictions, matching model/tokenizer/data/source provenance, and no silent truncation or protocol substitution. Record hardware, precision, runtime, resource use, failures, and limitations. The Milestone 2 report records these criteria as satisfied for both baselines.

**Next decision.** Use the baseline evidence and a separate development set to justify a bounded intervention. Human-reviewed error analysis is still possible, but test-set mistakes must not become a repeated tuning loop. Public benchmark contamination remains an unresolved limitation.

## First GPU adaptation — exploratory cycle completed

One authorized 363-example Aya-only QLoRA epoch and final-checkpoint comparison are complete. The higher observed score is uncertain, with 108 improvements and 93 regressions. Data rights and independent evaluation review remain unresolved. The gates below remain standards for future validated studies; this exploratory run did **not** satisfy them all. In particular, 283 records lacked individual review and the separate 32 tasks lacked independent human validation. The retrospective [decision record 0004](research/decisions/0004-exploratory-aya-adaptation.md) discloses this exception rather than treating it as full readiness.

**Entry requirements.**

1. State a testable hypothesis and a specific target behavior supported by reproducible evidence and separate development analysis. Explain the choice of foundation and why the intervention is plausible.
2. Establish licensed or explicitly permitted Filipino training data with documented provenance, quality review, privacy safeguards, and permitted uses. Keep development material separate and check duplication and leakage across splits.
3. Establish an additional independently authored, untouched Filipino evaluation set with appropriate native review and documented coverage. Keep it outside training, prompt selection, and hyperparameter decisions. Freeze its evaluation protocol before comparing models; the already observed public benchmark alone is insufficient.
4. Document a reproducible training configuration: model/tokenizer/data revisions, method, seeds, dependencies, hardware, compute limits, and saved artifacts. Confirm feasible GPU access before starting; do not assume future free availability.
5. Define base-versus-adapted evaluation in advance, including the target task and explicit checks for regressions in retained language or general capabilities. Keep task scores distinct and document uncertainty and comparison limits.

**Exit criteria.** Complete the bounded training run with retained configuration and artifacts, reproducible instructions, and a like-for-like comparison against the unchanged base checkpoint. Report data coverage, sample counts, compute use and costs, improvements if observed, regressions, negative findings, failures, and limitations. Any changes to evaluation conditions must be disclosed rather than folded into an improvement claim.

A useful result may show no improvement or demonstrate that the intervention is unsuitable. An informative, reproducible experiment is the goal; a higher score is not guaranteed. Model release is a separate decision requiring compatible rights, attribution, privacy/community review where applicable, and documented readiness. No checkpoint name or release is promised.

## Exploratory branches

These branches may inform one another, but are not a mandatory chronological sequence. Completing adaptation does not automatically authorize expansion. Select one bounded study when its prerequisites, research value, and capacity are established.

| Direction | Entry requirements | Evidence required to close a bounded study |
| --- | --- | --- |
| Cultural intelligence | Review existing evaluations and licenses; define the construct, qualified reviewers, regional coverage, and treatment of uncertainty and plural perspectives | Documented methodology, a valid baseline or coverage analysis, reviewer agreement and limitations; propose new evaluation material only for a demonstrated gap |
| Broader language intelligence | A community-relevant question, evidence and expertise for the chosen language, suitable rights/resources, and independent evaluation | A reproducible comparison with native review, data and coverage limitations, regressions, and a justified decision about further work |
| Language preservation | Community-led objective, permission, privacy, attribution, governance, benefit sharing, and agreed access/release conditions | A community-reviewed deliverable and evidence of usefulness for the agreed need, including the option not to release materials |
| Writing systems | A defined script task, appropriate expertise, permitted validated source materials, and explicit orthographic conventions | A reproducible task-specific result with error analysis; distinguish transliteration, translation, and OCR claims |
| Datasets and evaluation | A documented coverage gap, source rights, representative sampling, native review, and contamination controls | Versioned resource or audit with provenance, quality checks, evaluation boundaries, limitations, and release restrictions |
| Efficient infrastructure | A measured constraint, compatible model rights, reference configuration, feasible compute, and predefined quality checks | Reproducible quality, memory, runtime, and cost comparison, with regressions and measurement boundaries reported |
| Original pretraining | Demonstrated expertise, suitable licensed corpora, independent evaluation, sustainable resources, and a hypothesis requiring training from scratch | A bounded reproducible feasibility or training study with fair reference comparisons, resource accounting, negative results, and a justified continue/stop decision |

Data rights, community participation, qualified review, compute availability, and research capacity can block or change a proposal. A well-supported decision to pause or reject a direction is a legitimate outcome. No branch establishes a partnership, funded program, or product commitment.

## Maintaining the roadmap

Keep detailed methods, immutable revisions, scores, and reproduction instructions in the relevant study report. Update this document with a concise status and evidence link after verification. Keep the [vision](project-vision.md) durable and the [directions](research-directions.md) explicit about maturity.

Use the charter's reporting standard for each new study. Keep educational library material separate from original findings, and update the README and homepage only with claims supported by verified reports. No future experiment is implemented or launched by this documentation.

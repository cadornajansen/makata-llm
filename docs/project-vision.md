# Makata project vision

**Toward intelligence we can call our own.**

Makata is an independent Philippine AI research initiative. Its mission is to advance the capacity to study, evaluate, adapt, and eventually create AI technologies that serve Philippine languages, knowledge, cultures, histories, and communities.

This is the enduring research charter. The [research directions](research-directions.md) describe the questions Makata hopes to investigate; the [research roadmap](research-roadmap.md) records demonstrated progress and the evidence required for further work. Specific study reports remain the source for experimental methods and results.

## Why Makata exists

The guiding ambition is greater Philippine participation in how AI is researched and built. That includes the ability to ask locally relevant questions, judge model behavior, develop suitable data, run reproducible experiments, and contribute findings that others can inspect and use.

Filipino and Taglish are the initial language priorities. Expansion to other Philippine languages depends on evidence, appropriate rights, resources, and collaboration with speakers and specialists. The Philippines' linguistic and cultural diversity requires research grounded in particular contexts; one model or evaluation cannot represent everyone.

Useful contributions can be modest: a well-documented baseline, a reproducible negative result, a dataset quality study, or an adaptation experiment that explains its tradeoffs. Their value comes from what they establish, rather than a model's size or a release name.

## Research philosophy

- **Evidence before claims.** State the question, test it under a documented method, and distinguish observations from hypotheses. Report uncertainty, failures, and regressions alongside successes.
- **Philippine-centered, globally informed.** Study and build upon international and regional open-weight models, methods, datasets, and software. Credit their creators and preserve their applicable terms.
- **Plural cultural perspectives.** Investigate history, knowledge, pragmatics, and regional contexts through qualified sources and reviewers. Acknowledge disagreement and uncertainty. Research must not require ideological conformity or claim authority over Philippine cultures.
- **Community responsibility.** Language and cultural materials require appropriate permission, privacy protections, attribution, governance, and benefit sharing. Technical accessibility alone does not justify collection, training, or publication.
- **Reproducibility and honest scope.** Preserve the information needed to inspect and repeat an experiment. A score on one task supports a claim about that task; it does not establish general intelligence, cultural understanding, or dependable deployment.
- **Collaboration through concrete work.** Learn from existing efforts, reproduce methods, improve documentation, and share useful findings where rights and community preferences permit.

## Independence and attribution

Independence means developing the expertise and practical capacity to make informed research choices and operate suitable systems. Accessible adaptation and inference can reduce dependence on any one hosted provider. They still rely on hardware, software, data, and model foundations whose provenance must remain visible.

Operational independence is different from original pretraining. A checkpoint adapted from an external model must be described as an adaptation and credit that foundation. Training a model from scratch is a separate, long-term research possibility, conditional on demonstrated expertise, suitable corpora, independent evaluation, sustainable resources, and a scientific hypothesis.

Makata's independent identity does not establish an institutional affiliation, funding arrangement, endorsement, or partnership. Such relationships should be stated only when they are confirmed and can be accurately described.

## Ambition and demonstrated capability

The first bounded cycle is complete: verified external baselines, provisional Aya preparation, one internal QLoRA adaptation, and a paired post-training evaluation. See the [baseline report](milestone-2-baselines.md), [training report](milestone-3-qlora-full.md), and [Milestone 4](milestone-4-post-training.md). The observed +1.67-point comprehension change is not statistically established; its paired 95% interval spans −1.45 to +4.80 points.

This demonstrates an experimental workflow, not a validated or released Philippine foundation model. Data-rights review, independent language review and untouched evaluation remain unresolved. Other long-term directions are research possibilities, not completed products.

The website's [Research & Learning library guide](research-library.md) describes educational explanations of external research and methods. Educational articles and teaching exercises are distinct from Makata's original experimental findings, which require their own study reports and evidence.

## Collaboration and intended contribution

Researchers, engineers, language specialists, historians, educators, and communities can help shape meaningful questions, review language and cultural coverage, assess data rights, and reproduce or challenge results. Community-led work should begin with speakers' identified needs and decision-making authority, including the ability to restrict access or decline participation. AI alone cannot reverse language loss.

Potential contributions include reusable methods, carefully governed resources, honest evaluations, and practical knowledge about adapting and operating models. Public release is appropriate only when licensing, privacy, community agreements, and research readiness allow it. Invitations to collaborate do not imply an existing relationship.

For a concrete research or collaboration inquiry: [jansencadorna5@gmail.com](mailto:jansencadorna5@gmail.com).

## Reporting standard

Each research report should disclose its question and hypothesis, relevant prior work, model and data provenance, rights and ethical considerations, method and configuration, metrics and sample counts, compute use and costs, results including negative findings, limitations, reproduction instructions, and contributor acknowledgments. Explain any information that cannot be shared and how that limits verification.

Preserve training, development, and evaluation boundaries. Do not train on evaluation items, present partial runs as complete, infer causal improvements from unrelated checkpoints, or combine unrelated benchmark scores. Claims and priorities should change when new evidence warrants it.

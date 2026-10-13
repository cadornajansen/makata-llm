# Makata research directions

These seven directions describe a long-term research agenda under the [project vision](project-vision.md). They are questions to investigate, not existing products or promised releases. The [research roadmap](research-roadmap.md) owns current status and entry/exit criteria; its current evidence includes baseline evaluation, an exploratory Aya-only QLoRA run, and an uncertain post-training comprehension change.

## 1. Philippine language intelligence

**Objective and questions.** Study comprehension and generation in Filipino and Taglish first. Where do existing models make linguistic errors? How does code-switching affect performance? Which data and adaptation methods help a defined task, and which capabilities regress?

**Possible contributions.** Controlled base-versus-adapted comparisons, human-reviewed error analyses, Filipino and Taglish evaluation protocols, and reproducible fine-tuning studies. Compare an intervention with its unchanged base model; comparisons between unrelated models remain descriptive.

**Prerequisites.** A bounded hypothesis, suitable licensed data, separate development material, native-language review, independently authored untouched evaluation, and demonstrated compute feasibility. Study existing international and regional foundations with attribution; the [baseline report](milestone-2-baselines.md) documents the selected models and their primary sources.

**Limitations.** Translated multiple-choice reading comprehension does not establish Taglish conversational quality, reliable generation, cultural knowledge, or general Filipino competence. Additional languages require evidence, rights, resources, and collaboration; dataset availability alone is insufficient.

**Maturity.** Initial Tagalog comprehension baselines are complete and artifact-verified. A first exploratory Aya-only adaptation and paired evaluation are complete; [Milestone 4](milestone-4-post-training.md) reports an uncertain change, not a proven gain. Taglish-specific and broader language studies remain proposed or exploratory.

## 2. Philippine cultural intelligence

**Objective and questions.** Investigate knowledge, history, regional contexts, communication practices, and uncertainty. Can models distinguish a supported fact from an interpretation? How do they handle pragmatics, regional variation, ambiguous social situations, and multiple legitimate perspectives?

**Possible contributions.** Coverage audits of existing evaluations, native-reviewed scenarios, evaluator-agreement studies, and carefully justified additions where existing methods leave a demonstrated gap. A new benchmark would be an optional research contribution requiring validation.

**Prerequisites.** Review relevant primary research and its licenses; establish a defined construct, qualified historical and cultural expertise, regional representation, provenance, and scoring methods that accommodate context and disagreement. Separate factual accuracy from subjective judgment.

**Limitations.** Culture is neither uniform nor static. A consensus label can hide minority perspectives; a factual score cannot establish cultural authority. Evaluations must not reward ideological conformity, stereotypes, or uncritical agreement with a government or interpretation of national identity.

**Maturity.** Exploratory. No original Makata cultural benchmark or validated cultural findings are established by the current study.

## 3. Philippine language preservation

**Objective and questions.** Support community-led documentation, learning, and language use. What do speakers want technology to help with? Which materials may be used, who decides, and how will benefits and responsibilities be shared?

**Possible contributions.** A bounded, community-approved documentation resource, learning aid, translation study, or speech study, selected for an identified need. Document useful failures as well as successful tools.

**Prerequisites.** Actual community participation, appropriate linguistic expertise, explicit permission, privacy safeguards, attribution, access rules, governance, and benefit-sharing arrangements. Agree on stewardship, retention, withdrawal where feasible, and release conditions before acquiring sensitive or community-held materials.

**Limitations.** Public availability is not permission for every use. Some resources should remain restricted or outside AI training. AI alone cannot reverse language loss, which also involves social, educational, and intergenerational conditions. A larger corpus is not itself evidence of benefit to speakers.

**Maturity.** Exploratory and dependent on community interest. No target community, language-preservation partnership, or deliverable is claimed.

## 4. Philippine writing systems

**Objective and questions.** Explore computational support for Philippine scripts, potentially Baybayin, with appropriate expertise. How should documented orthographic variants and ambiguities be represented? What prevents accurate digitization, rendering, search, or access?

**Possible contributions.** Validated script-aware text processing, transliteration studies, character recognition, optical character recognition (OCR), or documented digitization methods for a clearly defined source collection.

**Prerequisites.** Relevant scholarly and community expertise, permission to use source materials, documented orthographic conventions, reliable reference transcriptions, and a task-specific evaluation method.

**Limitations.** A writing system is not a language. Transliteration maps text between writing systems; translation conveys meaning between languages; OCR recognizes text in images. Each needs a different method and evaluation. Do not assume a single historically authoritative script rendering for every modern word or treat all Philippine scripts as interchangeable.

**Maturity.** Long-term exploratory work. No Baybayin tool, OCR system, or script dataset is claimed, and none is required for the initial adaptation experiment.

## 5. Datasets and evaluation

**Objective and questions.** Make model research interpretable through trustworthy data and measurement. Whose language use is represented? Are sources and permissions traceable? What do task scores actually measure? How can leakage, duplication, and possible benchmark contamination be detected and reported?

**Possible contributions.** Dataset discovery and quality audits, documented cleaning and deduplication, native-authored and native-reviewed evaluation sets, code-switching resources, coverage studies, and reproducible evaluation tooling. Study existing work before proposing a new resource. [FilBench](https://aclanthology.org/2025.emnlp-main.127/) and [Belebele](https://aclanthology.org/2024.acl-long.44/) are external research used in the first study, not Makata-created benchmarks.

**Prerequisites.** Provenance, licensing or permission, intended-use documentation, privacy safeguards, versioning, representative sampling, appropriate native review, and separate training/development/evaluation material. Freeze evaluation choices before use and record metrics, sample counts, revisions, exclusions, and uncertainty.

**Limitations.** Size does not establish quality or representativeness. Public benchmarks may already occur in model training data; contamination checks cannot prove their absence when training corpora are unknown. Unrelated benchmark scores must remain distinct.

**Maturity.** A reproducible external-task evaluation pipeline and verified baselines exist. Provisional Aya screening is documented, but independent evaluation review and complete data-rights clearance remain unresolved.

## 6. Efficient and independent infrastructure

**Objective and questions.** Study how useful adaptation and inference can run on accessible resources. What quality, memory, latency, and cost tradeoffs arise? Can another researcher reproduce the setup and operate the result under its license?

**Possible contributions.** Bounded studies of LoRA (training small low-rank adapters), QLoRA (adapters over a quantized base), quantization, tokenizer efficiency, compression, or local inference. Record actual hardware, software, precision, runtime, memory, and costs, including setup and failed attempts where measurable.

**Prerequisites.** A defined task and unchanged reference model, compatible licenses and tooling, realistic access to compute, reproducible configurations, and quality/regression checks. Select a method because it addresses a measured constraint, not because it is fashionable.

**Limitations.** Reduced memory or expense can trade off quality or speed. A free allocation is not guaranteed future capacity. Running an external open-weight model independently is operational independence, not original pretraining or ownership of its foundations.

**Maturity.** Baseline execution and resource reporting are demonstrated in the [Milestone 2 report](milestone-2-baselines.md). A bounded parameter-efficient run is now verified in [Milestone 3](milestone-3-qlora-full.md). Inference-efficiency comparisons remain proposed; the verified baseline and adapted evaluations did not use quantization.

## 7. Original model development

**Objective and questions.** Eventually investigate training a Philippine-centered model from scratch when evidence justifies it. What scientific hypothesis requires original pretraining rather than adaptation? Which corpus, tokenizer, architecture, and training objective would test that hypothesis?

**Possible contributions.** A bounded pretraining feasibility study, tokenizer or data-mixture experiment, reproducible small-scale training result, or a documented finding that adaptation is the more suitable approach.

**Prerequisites.** Demonstrated training and evaluation expertise, sufficient appropriately licensed corpora, independent evaluation, sustainable compute and research resources, and a clear hypothesis. Include training stability, optimization, safety, and fair comparisons with existing models in the study design.

**Limitations.** Training from scratch does not automatically provide better quality, cultural understanding, or independence. Model scale is not a scientific contribution by itself. Original pretraining is not required for Makata's first useful contributions and does not imply a frontier-scale commitment.

**Maturity.** Long-term exploratory work. No Makata-pretrained model, funded pretraining program, or release commitment is established.

## How the directions connect

Well-governed datasets support adaptation, while evaluation reveals whether it helps and where it fails. Language and cultural research can inform each other's questions, but require different evidence. Community-led preservation can identify useful tasks that broader benchmark work overlooks. Writing-system research may improve access to permitted materials without requiring a new language model.

Reproducible infrastructure supports all these studies. Experience from bounded adaptation may later inform a pretraining decision, but does not compel one. These connections are opportunities, not a mandatory sequence: choose the next small study according to evidence, community priorities, rights, expertise, and resources. The [roadmap](research-roadmap.md) defines the gates for doing so.

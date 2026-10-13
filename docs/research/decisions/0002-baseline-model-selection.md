# 0002 — Compare a multilingual and a Southeast Asian base checkpoint

**Recorded:** 2026-10-12. **Status:** adopted for Report 001. **Record type:** retrospective documentation.

## Context and problem

Makata needs useful baseline evidence while compute access is uncertain. A tiny English-focused engineering control tests code but cannot stand in for serious Tagalog baseline candidates. Regional research should inform the comparison alongside general multilingual models.

## Selection criteria

The earlier study brief records public checkpoint availability, appropriate licensing, Philippine/SEA language relevance, context and memory feasibility, supported architecture/tokenizer, immutable revisions, and suitability for future adaptation. The completed implementation additionally verifies compatibility with official answer-choice likelihood scoring.

## Chosen direction and rationale

- **Qwen/Qwen3-1.7B-Base:** general-purpose multilingual baseline. The authors explicitly list Tagalog in Qwen3's language coverage. Its pinned card and license identify Apache-2.0. Transformers supports its causal architecture without remote code.
- **sail/Sailor2-1B:** Southeast Asian-focused baseline. Its model card explicitly includes Tagalog and describes expansion from Qwen2.5-0.5B followed by regional continued pretraining. The pinned card declares Apache-2.0; no standalone LICENSE file at that revision was verified.

The base checkpoints are evaluated without chat templates. This removes instruction-template selection from this initial measurement but limits its applicability to conversational use. Their differing parameter counts mean the experiment is a descriptive checkpoint comparison, not a controlled test of regional training.

## Alternatives and constraints

SmolLM2-135M was retained only as the synthetic CPU engineering control. The later audit documents inspecting metadata for Qwen3-4B-Base and Sailor2-3B; this is a retrospective account rather than proof of a dated pre-evaluation shortlist. No systematic search for the strongest Filipino model is claimed.

Local CPU memory and estimated runtime were insufficient. A free Colab T4 subsequently passed development pilots. Resource feasibility constrained this first pair; neither architecture nor model size is a permanent Makata requirement.

## Supporting evidence and chronology

- [Earlier study criteria](https://github.com/cadornajansen/makata-llm/blob/1c811c1b5a6b6208afb6448482c12ae54dbfe393/docs/first-study.md).
- [Pinned Qwen card](https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/README.md), [Qwen language list](https://qwenlm.github.io/blog/qwen3/), and [Qwen3 report](https://arxiv.org/abs/2505.09388).
- [Pinned Sailor2 card](https://huggingface.co/sail/Sailor2-1B/blob/75c2856ffc7e6a6e64127f40c5f54a953deb682e/README.md) and [Sailor2 report](https://arxiv.org/abs/2502.12982).
- Candidate-plan SHA-256: `7363f35664b590690b4c7a5a39a70d1f8c48166b8cdc709a1385b01473b57b12`.
- GPU profile frozen at `2026-10-12T09:18:55.921885Z`, before the first benchmark start at `2026-10-12T09:21:04.135342Z`. Matching plan/source hashes are retained in the pilots and runs.

The exact candidate plan was local and uncommitted during execution. Its retained hashes support a local pre-execution freeze, not public preregistration. The documented rationale is availability, language relevance, compatibility, and resources; these records do not establish what benchmark scores the model developers or investigators may previously have seen.

## Consequences and revisit conditions

Keep checkpoint provenance explicit and avoid causal superiority claims. Revisit the foundation model for adaptation when licensed data, a target behavior, untouched evaluation material, and feasible compute are established. Baseline ranking alone does not prove which checkpoint will benefit most from fine-tuning.

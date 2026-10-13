export type StudySource = { title: string; attribution: string; url: string }

export const studySources: Record<string, StudySource> = {
  "aya-card": {
    title: "Aya Collection language split — pinned dataset card",
    attribution:
      "Cohere Labs / Aya contributors. Revision a3af2fde4b4cb5b2775830b11244a1a20b5f004f; declares Apache-2.0. Contributed third-party rights require separate consideration.",
    url: "https://huggingface.co/datasets/CohereLabs/aya_collection_language_split/blob/a3af2fde4b4cb5b2775830b11244a1a20b5f004f/README.md",
  },
  "aya-paper": {
    title:
      "Aya Dataset: An Open-Access Collection for Multilingual Instruction Tuning",
    attribution:
      "Singh et al., 2024. arXiv:2402.06619. External dataset research, not Makata-authored data.",
    url: "https://arxiv.org/abs/2402.06619",
  },
  lora: {
    title: "LoRA: Low-Rank Adaptation of Large Language Models",
    attribution: "Hu et al., 2021. arXiv:2106.09685.",
    url: "https://arxiv.org/abs/2106.09685",
  },
  qlora: {
    title: "QLoRA: Efficient Finetuning of Quantized LLMs",
    attribution:
      "Dettmers et al., 2023. arXiv:2305.14314. Our optimizer and execution choices are specified separately.",
    url: "https://arxiv.org/abs/2305.14314",
  },
  filbench: {
    title: "FilBench: Can LLMs Understand and Generate Filipino?",
    attribution:
      "Miranda, Aco, Manuel, Cruz & Imperial. EMNLP, 2025. DOI: 10.18653/v1/2025.emnlp-main.127.",
    url: "https://aclanthology.org/2025.emnlp-main.127/",
  },
  belebele: {
    title:
      "The Belebele Benchmark: a Parallel Reading Comprehension Dataset in 122 Language Variants",
    attribution:
      "Bandarkar et al. ACL, 2024. DOI: 10.18653/v1/2024.acl-long.44.",
    url: "https://aclanthology.org/2024.acl-long.44/",
  },
  qwen3: {
    title: "Qwen3 Technical Report",
    attribution: "Yang et al. / Qwen Team, 2025. arXiv:2505.09388.",
    url: "https://arxiv.org/abs/2505.09388",
  },
  sailor2: {
    title:
      "Sailor2: Sailing in South-East Asia with Inclusive Multilingual LLMs",
    attribution: "Dou et al., 2025. arXiv:2502.12982.",
    url: "https://arxiv.org/abs/2502.12982",
  },
  "qwen-card": {
    title: "Qwen3-1.7B-Base — pinned model card",
    attribution:
      "Qwen Team. Checkpoint ea980cb0a6c2ae4b936e82123acc929f1cec04c1.",
    url: "https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/README.md",
  },
  "qwen-license": {
    title: "Qwen3-1.7B-Base — Apache-2.0 license",
    attribution: "License file at the evaluated checkpoint revision.",
    url: "https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/ea980cb0a6c2ae4b936e82123acc929f1cec04c1/LICENSE",
  },
  "qwen-languages": {
    title: "Qwen3: Think Deeper, Act Faster",
    attribution:
      "Qwen Team, 2025. Author-reported language coverage; not evidence of this study's accuracy.",
    url: "https://qwenlm.github.io/blog/qwen3/",
  },
  "sailor-card": {
    title: "Sailor2-1B — pinned model card",
    attribution:
      "Sailor2 authors. Checkpoint 75c2856ffc7e6a6e64127f40c5f54a953deb682e; declares Apache-2.0.",
    url: "https://huggingface.co/sail/Sailor2-1B/blob/75c2856ffc7e6a6e64127f40c5f54a953deb682e/README.md",
  },
  "sailor-code": {
    title: "Sailor2 — original research repository",
    attribution:
      "Sailor2 authors. External model research and training implementation.",
    url: "https://github.com/sail-sg/sailor2",
  },
  "dataset-card": {
    title: "Belebele — pinned dataset card",
    attribution:
      "Belebele authors / Meta. Revision 7899cdfa4e1e0d733fd77c848e2c273cb1d32be2; CC BY-SA 4.0.",
    url: "https://huggingface.co/datasets/facebook/belebele/blob/7899cdfa4e1e0d733fd77c848e2c273cb1d32be2/README.md",
  },
  "filbench-entry": {
    title: "FilBench custom evaluation entry point",
    attribution:
      "FilBench authors. community_tasks/filbench_evals.py at 7ad52795d7d218d4679f93a019b58dde4b749c5b.",
    url: "https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/community_tasks/filbench_evals.py",
  },
  "filbench-task": {
    title: "FilBench Belebele task implementation",
    attribution:
      "FilBench authors. Official formatting, answer indexing, MCF formulation, and metric registration at the pinned revision.",
    url: "https://github.com/filbench/lighteval/blob/7ad52795d7d218d4679f93a019b58dde4b749c5b/filbench/belebele.py",
  },
  "original-brief": {
    title: "Makata first-study brief — earlier committed version",
    attribution:
      "Makata. Commit 1c811c1b5a6b6208afb6448482c12ae54dbfe393, October 12, 2026. This is the earlier brief, not the completed GPU source snapshot.",
    url: "https://github.com/cadornajansen/makata-llm/blob/1c811c1b5a6b6208afb6448482c12ae54dbfe393/docs/first-study.md",
  },
}

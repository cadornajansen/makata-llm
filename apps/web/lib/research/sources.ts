export type ResearchSource = {
  title: string
  url: string
  kind: "Paper" | "Documentation" | "Video & lessons" | "Project"
}

export const sources: Record<string, ResearchSource> = {
  mml: {
    title: "Mathematics for Machine Learning — Deisenroth, Faisal & Ong",
    url: "https://mml-book.github.io/",
    kind: "Documentation",
  },
  "3b1b-linear": {
    title: "3Blue1Brown — Essence of linear algebra",
    url: "https://www.3blue1brown.com/topics/linear-algebra",
    kind: "Video & lessons",
  },
  "3b1b-gradient": {
    title: "3Blue1Brown — Gradient descent",
    url: "https://www.3blue1brown.com/lessons/gradient-descent",
    kind: "Video & lessons",
  },
  "3b1b-backprop": {
    title: "3Blue1Brown — Backpropagation calculus",
    url: "https://www.3blue1brown.com/lessons/backpropagation-calculus",
    kind: "Video & lessons",
  },
  "3b1b-networks": {
    title: "3Blue1Brown — Neural networks",
    url: "https://www.3blue1brown.com/lessons/neural-networks",
    kind: "Video & lessons",
  },
  karpathy: {
    title: "Andrej Karpathy — Neural Networks: Zero to Hero",
    url: "https://karpathy.ai/zero-to-hero.html",
    kind: "Video & lessons",
  },
  "karpathy-gpt": {
    title: "Andrej Karpathy — Let's build GPT",
    url: "https://www.youtube.com/watch?v=kCc8FmEb1nY",
    kind: "Video & lessons",
  },
  "deep-learning": {
    title: "Deep Learning — Goodfellow, Bengio & Courville",
    url: "https://www.deeplearningbook.org/",
    kind: "Documentation",
  },
  "pytorch-basics": {
    title: "PyTorch — Learn the basics",
    url: "https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
    kind: "Documentation",
  },
  "pytorch-autograd": {
    title: "PyTorch — Automatic differentiation",
    url: "https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html",
    kind: "Documentation",
  },
  "pytorch-saving": {
    title: "PyTorch — Saving and loading models",
    url: "https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html",
    kind: "Documentation",
  },
  attention: {
    title: "Attention Is All You Need",
    url: "https://arxiv.org/abs/1706.03762",
    kind: "Paper",
  },
  "hf-course": {
    title: "Hugging Face — LLM Course",
    url: "https://huggingface.co/learn/llm-course/chapter1/1",
    kind: "Documentation",
  },
  "qwen-tokenizer": {
    title: "Qwen3-0.6B — model and tokenizer repository",
    url: "https://huggingface.co/Qwen/Qwen3-0.6B",
    kind: "Project",
  },
  lora: {
    title: "LoRA: Low-Rank Adaptation of Large Language Models",
    url: "https://arxiv.org/abs/2106.09685",
    kind: "Paper",
  },
  qlora: {
    title: "QLoRA: Efficient Finetuning of Quantized LLMs",
    url: "https://arxiv.org/abs/2305.14314",
    kind: "Paper",
  },
  chinchilla: {
    title: "Training Compute-Optimal Large Language Models",
    url: "https://arxiv.org/abs/2203.15556",
    kind: "Paper",
  },
  dpo: {
    title:
      "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
    url: "https://arxiv.org/abs/2305.18290",
    kind: "Paper",
  },
  "deepseek-r1": {
    title:
      "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
    url: "https://arxiv.org/abs/2501.12948",
    kind: "Paper",
  },
  peft: {
    title: "Hugging Face — PEFT",
    url: "https://huggingface.co/docs/peft/index",
    kind: "Documentation",
  },
  trl: {
    title: "Hugging Face — TRL",
    url: "https://huggingface.co/docs/trl/index",
    kind: "Documentation",
  },
  "hf-datasets": {
    title: "Hugging Face — Datasets",
    url: "https://huggingface.co/docs/datasets/index",
    kind: "Documentation",
  },
  datasheets: {
    title: "Datasheets for Datasets",
    url: "https://arxiv.org/abs/1803.09010",
    kind: "Paper",
  },
  itanong: {
    title: "DOST-ASTI — iTANONG",
    url: "https://asti.dost.gov.ph/projects/itanong/",
    kind: "Project",
  },
  filbench: {
    title: "FilBench: Can LLMs Understand and Generate Filipino?",
    url: "https://aclanthology.org/2025.emnlp-main.127/",
    kind: "Paper",
  },
  batayan: {
    title:
      "Batayan: A Filipino NLP benchmark for evaluating Large Language Models",
    url: "https://aclanthology.org/2025.acl-long.1509/",
    kind: "Paper",
  },
  "sea-helm": {
    title: "SEA-HELM: Southeast Asian Holistic Evaluation of Language Models",
    url: "https://arxiv.org/abs/2502.14301",
    kind: "Paper",
  },
  "sea-helm-code": {
    title: "AI Singapore — SEA-HELM evaluation code",
    url: "https://github.com/aisingapore/SEA-HELM",
    kind: "Project",
  },
  sealion: {
    title: "AI Singapore — SEA-LION",
    url: "https://sea-lion.ai/",
    kind: "Project",
  },
  "hf-evaluate": {
    title: "Hugging Face — Evaluate",
    url: "https://huggingface.co/docs/evaluate/index",
    kind: "Documentation",
  },
  "pytorch-amp": {
    title: "PyTorch — Automatic mixed precision",
    url: "https://docs.pytorch.org/docs/stable/amp.html",
    kind: "Documentation",
  },
  "pytorch-checkpoint": {
    title: "PyTorch — Activation checkpointing",
    url: "https://docs.pytorch.org/docs/stable/checkpoint.html",
    kind: "Documentation",
  },
  "pytorch-ddp": {
    title: "PyTorch — DistributedDataParallel",
    url: "https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html",
    kind: "Documentation",
  },
  cuda: {
    title: "NVIDIA — CUDA Programming Guide",
    url: "https://docs.nvidia.com/cuda/cuda-programming-guide/",
    kind: "Documentation",
  },
  coare: {
    title: "DOST-ASTI — COARE",
    url: "https://coare.asti.dost.gov.ph/",
    kind: "Project",
  },
}

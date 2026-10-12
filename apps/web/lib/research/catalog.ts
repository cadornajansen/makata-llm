export type ArticleSlug =
  | "mathematics-for-ml"
  | "neural-networks"
  | "pytorch"
  | "transformers"
  | "llm-training"
  | "dataset-engineering"
  | "evaluation"
  | "gpu-computing"

export type Article = {
  slug: ArticleSlug
  title: string
  shortTitle: string
  group: "Foundations" | "Models" | "Research practice"
  abstract: string
  prerequisites: readonly string[]
  objectives: readonly string[]
  related: readonly ArticleSlug[]
  sources: readonly string[]
}

export const articles: readonly Article[] = [
  {
    slug: "mathematics-for-ml",
    title: "Mathematics for Machine Learning",
    shortTitle: "Mathematics",
    group: "Foundations",
    abstract:
      "From a vector on a plane to a gradient through a model: build the mathematical language needed to understand what learning actually computes.",
    prerequisites: ["School algebra", "Comfort reading simple functions"],
    objectives: [
      "Track shapes through vector and matrix operations.",
      "Differentiate a loss through a sequence of computations.",
      "Connect probability, cross-entropy, and gradient descent.",
    ],
    related: ["neural-networks", "pytorch", "transformers"],
    sources: ["mml", "3b1b-linear", "3b1b-gradient", "3b1b-backprop"],
  },
  {
    slug: "neural-networks",
    title: "Neural Networks & Deep Learning",
    shortTitle: "Neural networks",
    group: "Foundations",
    abstract:
      "Understand a neural network as a composition of parameterized functions. Follow real values forward, gradients backward, and the evidence needed to call a model useful.",
    prerequisites: [
      "Vectors and matrix multiplication",
      "Derivatives and the chain rule",
    ],
    objectives: [
      "Calculate a small network's prediction and loss.",
      "Trace how a parameter affects the loss through backpropagation.",
      "Distinguish optimization, generalization, training, and inference.",
    ],
    related: ["mathematics-for-ml", "pytorch", "transformers"],
    sources: ["3b1b-networks", "3b1b-backprop", "karpathy", "deep-learning"],
  },
  {
    slug: "pytorch",
    title: "PyTorch & Practical Model Training",
    shortTitle: "PyTorch",
    group: "Foundations",
    abstract:
      "Turn the mathematics into an inspectable training loop. Learn how tensors, autograd, modules, batches, and checkpoints fit together in a reproducible CPU example.",
    prerequisites: [
      "Python functions and classes",
      "Neural networks",
      "Gradients",
    ],
    objectives: [
      "Build and debug a complete PyTorch training loop.",
      "Separate training from validation and control gradient tracking.",
      "Save and restore the state needed to continue an experiment.",
    ],
    related: ["neural-networks", "gpu-computing", "llm-training"],
    sources: [
      "pytorch-basics",
      "pytorch-autograd",
      "pytorch-saving",
      "karpathy",
    ],
  },
  {
    slug: "transformers",
    title: "Transformers & LLM Architecture",
    shortTitle: "Transformers",
    group: "Models",
    abstract:
      "Follow text through tokenization, embeddings, attention, and a decoder block. See how a distribution over the next token becomes a generated sequence.",
    prerequisites: [
      "Matrix multiplication",
      "Neural networks",
      "Softmax and probability",
    ],
    objectives: [
      "Compute a small attention operation with explicit dimensions.",
      "Explain causal masking, multiple heads, and positional information.",
      "Distinguish model probabilities from a sampling procedure.",
    ],
    related: ["mathematics-for-ml", "llm-training", "dataset-engineering"],
    sources: ["attention", "hf-course", "karpathy-gpt", "qwen-tokenizer"],
  },
  {
    slug: "llm-training",
    title: "LLM Training & Fine-Tuning",
    shortTitle: "Training & fine-tuning",
    group: "Models",
    abstract:
      "Compare pretraining, continued pretraining, supervised adaptation, and parameter-efficient methods. Make model provenance and experimental tradeoffs explicit before using compute.",
    prerequisites: [
      "A PyTorch training loop",
      "Decoder-only transformers",
      "Training and validation splits",
    ],
    objectives: [
      "Choose an adaptation method for a stated research question.",
      "Explain what LoRA, quantization, and distillation actually change.",
      "Plan a controlled Filipino-language adaptation experiment.",
    ],
    related: [
      "transformers",
      "dataset-engineering",
      "evaluation",
      "gpu-computing",
    ],
    sources: [
      "lora",
      "qlora",
      "chinchilla",
      "dpo",
      "deepseek-r1",
      "peft",
      "trl",
    ],
  },
  {
    slug: "dataset-engineering",
    title: "Dataset Engineering for LLMs",
    shortTitle: "Dataset engineering",
    group: "Research practice",
    abstract:
      "Treat a dataset as a documented set of decisions. Follow language data from collection and rights review through cleaning, partitioning, tokenization, and contamination checks.",
    prerequisites: [
      "Basic Python and text processing",
      "Training versus evaluation",
      "Tokenization",
    ],
    objectives: [
      "Document source provenance, permission, and transformations.",
      "Build splits that reduce leakage rather than merely shuffle rows.",
      "Assess Filipino and Taglish coverage without erasing linguistic variation.",
    ],
    related: ["transformers", "llm-training", "evaluation"],
    sources: [
      "hf-datasets",
      "hf-course",
      "datasheets",
      "qwen-tokenizer",
      "itanong",
    ],
  },
  {
    slug: "evaluation",
    title: "LLM Evaluation & Research Methodology",
    shortTitle: "Evaluation",
    group: "Research practice",
    abstract:
      "Ask what a score measures, how reliable it is, and what changed. Build an evaluation argument from baselines, controlled comparisons, uncertainty, and Philippine-language context.",
    prerequisites: [
      "Probability and statistics",
      "Training and test splits",
      "Language modeling",
    ],
    objectives: [
      "Calculate common metrics and recognize their limitations.",
      "Design controlled comparisons and reproducible ablations.",
      "Interpret FilBench, Batayan, and SEA-HELM without conflating their scope.",
    ],
    related: ["dataset-engineering", "llm-training", "mathematics-for-ml"],
    sources: [
      "filbench",
      "batayan",
      "sea-helm",
      "sea-helm-code",
      "sealion",
      "hf-evaluate",
    ],
  },
  {
    slug: "gpu-computing",
    title: "GPU Computing & Training Infrastructure",
    shortTitle: "GPU computing",
    group: "Research practice",
    abstract:
      "Understand where computation and memory go during training. Estimate costs with stated assumptions, then reason about precision, batching, checkpointing, and distributed execution.",
    prerequisites: [
      "A model training loop",
      "Tensor shapes",
      "Basic units of memory",
    ],
    objectives: [
      "Separate parameters, gradients, optimizer states, and activations.",
      "Explain accumulation, mixed precision, and checkpointing tradeoffs.",
      "Distinguish data, tensor, and pipeline parallelism.",
    ],
    related: ["pytorch", "llm-training", "evaluation"],
    sources: [
      "pytorch-amp",
      "pytorch-checkpoint",
      "pytorch-ddp",
      "cuda",
      "chinchilla",
      "coare",
    ],
  },
]

export const groups = ["Foundations", "Models", "Research practice"] as const

export function findArticle(slug: string): Article | undefined {
  return articles.find((article) => article.slug === slug)
}

export type OutlineItem = { id: string; title: string; level: 2 | 3 }

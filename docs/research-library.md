# Research library: coverage, authoring, and verification

The library is an educational collection of established methods, worked examples, and interactive explanations. It is not a record of completed Makata training experiments. Keep external research, synthetic teaching examples, and future Makata plans distinguishable in every contribution.

The section links below use the canonical host configured in `apps/web/lib/site.ts`. They describe the library's routes and anchors; this document does not assert deployment availability. During local review, replace the origin with `http://localhost:3000` or the port used by the production preview.

## How the content reaches the page

1. [`catalog.ts`](../apps/web/lib/research/catalog.ts) defines the eight article slugs, reading order, groups, abstracts, prerequisites, objectives, related articles, and source IDs. The index, navigation, static route parameters, and page metadata share this catalog.
2. [`content.ts`](../apps/web/lib/research/content.ts) is server-only. Its explicit loader map imports the requested local MDX article; navigation components do not import the article bodies.
3. [`next.config.ts`](../apps/web/next.config.ts) compiles MDX with GFM, mathematical notation, heading IDs, and KaTeX. Equations become HTML/MathML during compilation; the browser does not need to run a math parser.
4. [`outline.ts`](../apps/web/lib/research/outline.ts) extracts plain `##` and `###` headings, ignores fenced code, and uses GitHub-style slug generation. These IDs must agree with the headings rendered by `rehype-slug`.
5. The [`article route`](../apps/web/app/research/[slug]/page.tsx) combines the server-rendered article with prerequisites, objectives, navigation, a TOC, sources, related reading, and previous/next links. Unknown slugs are not generated.
6. [`mdx-components.tsx`](../apps/web/mdx-components.tsx) supplies consistent Tailwind typography, tables, callouts, anchors, and code-block presentation. Small Client Components provide copying, navigation, and interactive diagrams.
7. [`math.ts`](../apps/web/lib/research/math.ts) contains reusable numerical calculations. Diagram state selects their inputs; the resulting values drive the SVG and its textual or tabular equivalent.
8. [`sources.ts`](../apps/web/lib/research/sources.ts) maps stable source IDs to titles, authoritative URLs, and resource types. Catalog source IDs feed article further reading and citation metadata. Inline citations identify the claims supported in the article body.

The route catalog is also used by the sitemap and research metadata helpers. A new article therefore requires an explicit catalog entry and loader, not a runtime scan of arbitrary uploaded content.

The left sidebar and mobile navigation drawer list the eight main articles, grouped by subject. They do not contain nested article sections. Only **On this page** lists the current article's sections: it appears on the right at widths of 1280px and above, and as a collapsible TOC above the article from 1024px to 1279px. Below 1024px, a borderless floating rail on the right shows a scrollable window of nearby section links with fading ends. The current line and its neighbors are longer; swipe the rail to browse, then tap a line to navigate directly. The nearest section's label appears while browsing, hovering, or focusing the rail. It does not open a sidebar. Keep these two navigation purposes separate when adding or reorganizing content.

## Coverage checklist

Each row maps required subject matter to its actual section. Multiple concepts share a section where they belong to one explanation. This is a content map, not a claim that a link, browser interaction, or production build has passed a particular verification run.

### Mathematics for Machine Learning

| Required subject matter                                          | Article section                                                                                                                                   |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linear algebra fundamentals; scalars; vectors; matrices; tensors | [Scalars, vectors, matrices, and tensors](https://makata-llm.vercel.app/research/mathematics-for-ml#scalars-vectors-matrices-and-tensors)         |
| Vector operations                                                | [Vector operations and length](https://makata-llm.vercel.app/research/mathematics-for-ml#vector-operations-and-length)                            |
| Matrix multiplication; dot products                              | [Dot products and matrix multiplication](https://makata-llm.vercel.app/research/mathematics-for-ml#dot-products-and-matrix-multiplication)        |
| Matrix transformations                                           | [Matrices as transformations](https://makata-llm.vercel.app/research/mathematics-for-ml#matrices-as-transformations)                              |
| Vector spaces; eigenvalues; eigenvectors                         | [Vector spaces, bases, and eigenvectors](https://makata-llm.vercel.app/research/mathematics-for-ml#vector-spaces-bases-and-eigenvectors)          |
| Functions; calculus; derivatives                                 | [Functions, derivatives, and local change](https://makata-llm.vercel.app/research/mathematics-for-ml#functions-derivatives-and-local-change)      |
| Partial derivatives; gradients                                   | [Partial derivatives and gradients](https://makata-llm.vercel.app/research/mathematics-for-ml#partial-derivatives-and-gradients)                  |
| Chain rule                                                       | [The chain rule and computational graphs](https://makata-llm.vercel.app/research/mathematics-for-ml#the-chain-rule-and-computational-graphs)      |
| Probability; statistics; distributions; expected value; variance | [Probability distributions and uncertainty](https://makata-llm.vercel.app/research/mathematics-for-ml#probability-distributions-and-uncertainty)  |
| Conditional probability; Bayes' theorem                          | [Conditional probability and Bayes' theorem](https://makata-llm.vercel.app/research/mathematics-for-ml#conditional-probability-and-bayes-theorem) |
| Logarithms; exponentials                                         | [Logarithms, exponentials, and softmax](https://makata-llm.vercel.app/research/mathematics-for-ml#logarithms-exponentials-and-softmax)            |
| Loss functions                                                   | [Loss functions and what they reward](https://makata-llm.vercel.app/research/mathematics-for-ml#loss-functions-and-what-they-reward)              |
| Gradient descent; learning rates; optimization                   | [Gradient descent and optimization](https://makata-llm.vercel.app/research/mathematics-for-ml#gradient-descent-and-optimization)                  |

Interactive components: `VectorExplorer`, `MatrixExplorer`, `GradientDescent`, and `ChainRule` in `diagrams/mathematics.tsx`.

### Neural Networks and Deep Learning

| Required subject matter                                  | Article section                                                                                                                                   |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Biological inspiration versus artificial neural networks | [Biological inspiration and its limits](https://makata-llm.vercel.app/research/neural-networks#biological-inspiration-and-its-limits)             |
| Perceptrons; weights; biases                             | [Perceptrons, weights, and biases](https://makata-llm.vercel.app/research/neural-networks#perceptrons-weights-and-biases)                         |
| Activation functions                                     | [Activation functions](https://makata-llm.vercel.app/research/neural-networks#activation-functions)                                               |
| Forward propagation                                      | [Forward propagation through a small network](https://makata-llm.vercel.app/research/neural-networks#forward-propagation-through-a-small-network) |
| Loss calculation                                         | [Loss calculation](https://makata-llm.vercel.app/research/neural-networks#loss-calculation)                                                       |
| Backpropagation                                          | [Backpropagation and gradient flow](https://makata-llm.vercel.app/research/neural-networks#backpropagation-and-gradient-flow)                     |
| Optimizers                                               | [Optimizers and parameter updates](https://makata-llm.vercel.app/research/neural-networks#optimizers-and-parameter-updates)                       |
| Overfitting; generalization                              | [Overfitting and generalization](https://makata-llm.vercel.app/research/neural-networks#overfitting-and-generalization)                           |
| Training versus inference                                | [Training versus inference](https://makata-llm.vercel.app/research/neural-networks#training-versus-inference)                                     |

Interactive components: `NetworkExplorer` and `ActivationExplorer` in `diagrams/neural-networks.tsx`. The network connects editable parameters to forward values, loss, and backward derivatives.

### PyTorch and Practical Model Training

| Required subject matter                         | Article section                                                                                                                                                               |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tensors; tensor operations                      | [Tensors and tensor operations](https://makata-llm.vercel.app/research/pytorch#tensors-and-tensor-operations)                                                                 |
| Computational graphs; automatic differentiation | [Computational graphs and automatic differentiation](https://makata-llm.vercel.app/research/pytorch#computational-graphs-and-automatic-differentiation)                       |
| Model architecture with nn.Module               | [Defining architecture with nn.Module](https://makata-llm.vercel.app/research/pytorch#defining-architecture-with-nnmodule)                                                    |
| Optimizers; training loops                      | [Optimizers and the training loop](https://makata-llm.vercel.app/research/pytorch#optimizers-and-the-training-loop)                                                           |
| Batching                                        | [Batching with Dataset and DataLoader](https://makata-llm.vercel.app/research/pytorch#batching-with-dataset-and-dataloader)                                                   |
| Validation                                      | [Validation without parameter updates](https://makata-llm.vercel.app/research/pytorch#validation-without-parameter-updates)                                                   |
| Saving and loading checkpoints                  | [Saving and loading checkpoints](https://makata-llm.vercel.app/research/pytorch#saving-and-loading-checkpoints)                                                               |
| Debugging training failures                     | [Debugging training failures](https://makata-llm.vercel.app/research/pytorch#debugging-training-failures)                                                                     |
| Executable annotated example                    | [Running the example](https://makata-llm.vercel.app/research/pytorch#running-the-example) and [downloadable source](../apps/web/public/research/examples/train_regression.py) |

Interactive components: `AutogradExplorer` and `TrainingExplorer` in `diagrams/pytorch.tsx`. Browser calculations are teaching examples, separate from the downloadable script's run history.

### Transformers and LLM Architecture

| Required subject matter                 | Article section                                                                                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Language modeling                       | [Language modeling as conditional prediction](https://makata-llm.vercel.app/research/transformers#language-modeling-as-conditional-prediction)    |
| Tokenization                            | [Tokenization: text is not yet a tensor](https://makata-llm.vercel.app/research/transformers#tokenization-text-is-not-yet-a-tensor)               |
| Embeddings                              | [Embeddings: learned coordinates for token IDs](https://makata-llm.vercel.app/research/transformers#embeddings-learned-coordinates-for-token-ids) |
| Positional information                  | [Positional information](https://makata-llm.vercel.app/research/transformers#positional-information)                                              |
| Attention mechanisms                    | [Scaled dot-product attention](https://makata-llm.vercel.app/research/transformers#scaled-dot-product-attention)                                  |
| Queries; keys; values                   | [Queries, keys, and values](https://makata-llm.vercel.app/research/transformers#queries-keys-and-values)                                          |
| Self-attention                          | [Self-attention and causal masking](https://makata-llm.vercel.app/research/transformers#self-attention-and-causal-masking)                        |
| Multi-head attention                    | [Multi-head attention](https://makata-llm.vercel.app/research/transformers#multi-head-attention)                                                  |
| Feed-forward layers; transformer blocks | [Feed-forward layers and transformer blocks](https://makata-llm.vercel.app/research/transformers#feed-forward-layers-and-transformer-blocks)      |
| Decoder-only architectures              | [Decoder-only architectures](https://makata-llm.vercel.app/research/transformers#decoder-only-architectures)                                      |
| Autoregressive generation               | [Autoregressive generation](https://makata-llm.vercel.app/research/transformers#autoregressive-generation)                                        |
| Sampling; temperature                   | [Sampling, temperature, and decoding choices](https://makata-llm.vercel.app/research/transformers#sampling-temperature-and-decoding-choices)      |

Interactive components: `TokenizationExplorer`, `AttentionExplorer`, `TransformerExplorer`, and `SamplingExplorer` in `diagrams/transformers.tsx`. Explicit toy matrices and distributions must remain identified as such.

### LLM Training and Fine-Tuning

| Required subject matter                                                     | Article section                                                                                                                                                |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pretraining                                                                 | [Pretraining from an initial set of weights](https://makata-llm.vercel.app/research/llm-training#pretraining-from-an-initial-set-of-weights)                   |
| Continued pretraining                                                       | [Continued pretraining](https://makata-llm.vercel.app/research/llm-training#continued-pretraining)                                                             |
| Supervised fine-tuning; instruction tuning                                  | [Supervised fine-tuning and instruction tuning](https://makata-llm.vercel.app/research/llm-training#supervised-fine-tuning-and-instruction-tuning)             |
| Full fine-tuning versus parameter-efficient fine-tuning                     | [Full fine-tuning and parameter-efficient adaptation](https://makata-llm.vercel.app/research/llm-training#full-fine-tuning-and-parameter-efficient-adaptation) |
| LoRA                                                                        | [Low-rank adaptation](https://makata-llm.vercel.app/research/llm-training#low-rank-adaptation)                                                                 |
| QLoRA; quantization                                                         | [Quantization and QLoRA](https://makata-llm.vercel.app/research/llm-training#quantization-and-qlora)                                                           |
| Knowledge distillation                                                      | [Knowledge distillation](https://makata-llm.vercel.app/research/llm-training#knowledge-distillation)                                                           |
| Training hyperparameters                                                    | [Hyperparameters and controlled training](https://makata-llm.vercel.app/research/llm-training#hyperparameters-and-controlled-training)                         |
| Catastrophic forgetting                                                     | [Catastrophic forgetting and retained capabilities](https://makata-llm.vercel.app/research/llm-training#catastrophic-forgetting-and-retained-capabilities)     |
| Checkpoint management                                                       | [Checkpoints and reproducibility](https://makata-llm.vercel.app/research/llm-training#checkpoints-and-reproducibility)                                         |
| Planned Makata Filipino-language experiments; contextual DPO and R1 reading | [Beyond SFT and a Makata experiment proposal](https://makata-llm.vercel.app/research/llm-training#beyond-sft-and-a-makata-experiment-proposal)                 |

Interactive components: `ParameterExplorer`, `LoraExplorer`, and `DistillationExplorer` in `diagrams/llm-training.tsx`.

### Dataset Engineering for LLMs

| Required subject matter                                    | Article section                                                                                                                                 |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Corpus collection                                          | [Corpus collection starts with a question](https://makata-llm.vercel.app/research/dataset-engineering#corpus-collection-starts-with-a-question) |
| Dataset licensing; provenance                              | [Licensing, provenance, and privacy](https://makata-llm.vercel.app/research/dataset-engineering#licensing-provenance-and-privacy)               |
| Text cleaning                                              | [Text cleaning without erasing language](https://makata-llm.vercel.app/research/dataset-engineering#text-cleaning-without-erasing-language)     |
| Deduplication                                              | [Deduplication and document relationships](https://makata-llm.vercel.app/research/dataset-engineering#deduplication-and-document-relationships) |
| Dataset quality                                            | [Quality is multidimensional](https://makata-llm.vercel.app/research/dataset-engineering#quality-is-multidimensional)                           |
| Tokenization efficiency                                    | [Tokenization efficiency](https://makata-llm.vercel.app/research/dataset-engineering#tokenization-efficiency)                                   |
| Instruction-response formatting                            | [Instruction-response formatting](https://makata-llm.vercel.app/research/dataset-engineering#instruction-response-formatting)                   |
| Training, validation, and test splits                      | [Training, validation, and test splits](https://makata-llm.vercel.app/research/dataset-engineering#training-validation-and-test-splits)         |
| Data contamination                                         | [Contamination and data leakage](https://makata-llm.vercel.app/research/dataset-engineering#contamination-and-data-leakage)                     |
| Synthetic datasets                                         | [Synthetic data](https://makata-llm.vercel.app/research/dataset-engineering#synthetic-data)                                                     |
| Multilingual datasets; Filipino and Taglish code-switching | [Multilingual data and Taglish](https://makata-llm.vercel.app/research/dataset-engineering#multilingual-data-and-taglish)                       |
| Dataset bias; representativeness                           | [Bias and representativeness](https://makata-llm.vercel.app/research/dataset-engineering#bias-and-representativeness)                           |

Interactive components: `CleaningPipeline`, `DatasetSplitExplorer`, `TokenizationComparison`, and `ContaminationExplorer` in `diagrams/dataset-engineering.tsx`.

### LLM Evaluation and Research Methodology

| Required subject matter                                   | Article section                                                                                                                                                |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| What benchmarks measure                                   | [What benchmarks measure](https://makata-llm.vercel.app/research/evaluation#what-benchmarks-measure)                                                           |
| Accuracy                                                  | [Accuracy and the confusion matrix](https://makata-llm.vercel.app/research/evaluation#accuracy-and-the-confusion-matrix)                                       |
| Precision; recall; F1                                     | [Precision, recall, and F1](https://makata-llm.vercel.app/research/evaluation#precision-recall-and-f1)                                                         |
| Perplexity                                                | [Perplexity and language-model loss](https://makata-llm.vercel.app/research/evaluation#perplexity-and-language-model-loss)                                     |
| Generative evaluation                                     | [Generative evaluation](https://makata-llm.vercel.app/research/evaluation#generative-evaluation)                                                               |
| Human evaluation                                          | [Human evaluation and linguistic expertise](https://makata-llm.vercel.app/research/evaluation#human-evaluation-and-linguistic-expertise)                       |
| Baseline models; controlled experiments                   | [Baselines and controlled experiments](https://makata-llm.vercel.app/research/evaluation#baselines-and-controlled-experiments)                                 |
| Ablation studies                                          | [Ablation studies](https://makata-llm.vercel.app/research/evaluation#ablation-studies)                                                                         |
| Statistical uncertainty                                   | [Statistical uncertainty](https://makata-llm.vercel.app/research/evaluation#statistical-uncertainty)                                                           |
| Training versus validation curves                         | [Training curves and generalization](https://makata-llm.vercel.app/research/evaluation#training-curves-and-generalization)                                     |
| Reproducibility; data leakage; regression testing         | [Reproducibility, leakage, and regression testing](https://makata-llm.vercel.app/research/evaluation#reproducibility-leakage-and-regression-testing)           |
| Filipino-specific benchmarks; FilBench; Batayan; SEA-HELM | [Philippine-language benchmarks and external research](https://makata-llm.vercel.app/research/evaluation#philippine-language-benchmarks-and-external-research) |

Interactive components: `ConfusionMatrixExplorer` and `EvaluationExplorer` in `diagrams/evaluation.tsx`. No teaching chart is a Makata benchmark result.

### GPU Computing and Training Infrastructure

| Required subject matter                                    | Article section                                                                                                                               |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| CPU versus GPU                                             | [CPU versus GPU](https://makata-llm.vercel.app/research/gpu-computing#cpu-versus-gpu)                                                         |
| GPU parallelism; CUDA                                      | [GPU parallelism and CUDA](https://makata-llm.vercel.app/research/gpu-computing#gpu-parallelism-and-cuda)                                     |
| GPU memory; VRAM                                           | [VRAM and the memory hierarchy](https://makata-llm.vercel.app/research/gpu-computing#vram-and-the-memory-hierarchy)                           |
| Training precision: FP32, FP16, BF16                       | [FP32, FP16, and BF16](https://makata-llm.vercel.app/research/gpu-computing#fp32-fp16-and-bf16)                                               |
| Mixed precision                                            | [Mixed precision](https://makata-llm.vercel.app/research/gpu-computing#mixed-precision)                                                       |
| Batch sizes                                                | [Batch size and sequence length](https://makata-llm.vercel.app/research/gpu-computing#batch-size-and-sequence-length)                         |
| Gradient accumulation                                      | [Gradient accumulation](https://makata-llm.vercel.app/research/gpu-computing#gradient-accumulation)                                           |
| Gradient checkpointing                                     | [Gradient checkpointing](https://makata-llm.vercel.app/research/gpu-computing#gradient-checkpointing)                                         |
| Memory estimation; parameters, gradients, optimizer states | [Estimate persistent training memory](https://makata-llm.vercel.app/research/gpu-computing#estimate-persistent-training-memory)               |
| Model parallelism; distributed training fundamentals       | [Model parallelism and distributed training](https://makata-llm.vercel.app/research/gpu-computing#model-parallelism-and-distributed-training) |
| Training cost; efficiency                                  | [Training cost and efficiency](https://makata-llm.vercel.app/research/gpu-computing#training-cost-and-efficiency)                             |

Interactive components: `ParallelismExplorer`, `MemoryExplorer`, `BatchExplorer`, and `CheckpointExplorer` in `diagrams/gpu-computing.tsx`. Scheduling diagrams are conceptual; memory totals exclude categories explicitly identified in their assumptions.

## Authoring conventions

### Article structure and mathematics

- Edit local articles in `apps/web/content/research/`. Do not add an H1 or repeat the abstract, prerequisites, and objectives supplied by the article shell.
- Use plain `##` and `###` heading text. Avoid inline math, JSX, or Markdown formatting inside headings so rendered anchors and the extracted TOC agree. Renaming a heading changes its deep link; update this coverage map and any references to it.
- Use `$...$` for inline notation and `$$` blocks for display equations. Define symbols, units, dimensions, assumptions, and reductions before relying on them. KaTeX compilation rejects invalid notation rather than hiding the error.
- Explain a concept, then work a small numerical example, then connect it to LLM computation. State when a diagram and a worked example use different teaching inputs.
- Include misconceptions, `## Key takeaways`, and links to related library articles. Keep future work explicitly prospective.
- Use fenced code blocks with a language label. For the PyTorch example, the downloadable Python file is the executable source of truth; update article excerpts when changing it.
- Keep styling in Tailwind and the shared MDX mappings. KaTeX's vendor CSS is imported through the existing global stylesheet; do not add page-specific stylesheets or a browser math renderer.

### Sources and metadata

Add a verified authoritative source to `sources.ts`, then reference its ID in the appropriate catalog entry. Include inline links beside specific supported explanations. Preserve the source's identity and distinguish papers, documentation, videos, and external projects. Do not invent an author, publication date, benchmark score, endorsement, or institutional relationship.

Use `catalog.ts` for public article titles, abstracts, learning objectives, and related slugs. Keep IDs stable. The source registry and catalog are shared data, so test missing IDs and broken related links when editing them. Page metadata and social previews should describe educational content without implying original experimental findings.

### Interactive explanations

Use `apps/web/components/research/diagrams/shared.tsx` for the standard diagram frame, SVG scene, labeled sliders, choice controls, numerical values, tables, and playback. Use shadcn primitives for interactive controls.

Import article diagrams through `diagrams/lazy.tsx`. Its client `next/dynamic` boundaries split the eight topic implementations while retaining server-rendered initial figures. Importing every implementation directly from server-loaded MDX would eagerly bundle all topics together.

Desktop navigation lists articles on the left and sections in **On this page** on the right. Below 1280 px, the section list collapses. Below 1024 px, a floating rail on the right represents the main sections and highlights the current one; tapping it opens a labeled section Sheet. The separate **Browse topics** Sheet lists articles. The article reserves space for the rail so it does not cover the text.

- Put calculations in `math.ts` when they are shared or need numerical tests. Derive SVG geometry, displayed values, and accessible alternatives from the same state.
- Start playback paused. Provide Reset and manual Step; include Play/Pause only when a sequence explains a process.
- Use the shared approximately 300 ms transition and 800 ms teaching-step cadence. Keep axes and labels stable, and use color consistently without making it the only signal.
- Respect reduced motion by removing interpolation and automatic playback while retaining manual calculations. Pause when the diagram leaves the viewport or the document becomes hidden; clean up timers and observers.
- Give SVGs a meaningful title and description. Provide readable values or tables, keyboard-operable controls, and a static initial explanation.
- Add `data-lenis-prevent` to independently scrollable regions that must handle their own scrolling. Verify nested scrolling and page navigation with Lenis enabled.
- Label toy matrices, invented model comparisons, conceptual schedules, and theoretical memory estimates. Real tokenization fixtures must retain their actual model and revision metadata.

### Pinned tokenization fixture

[`tokenization.json`](../apps/web/lib/research/tokenization.json) records three fixed English, Filipino, and Taglish examples:

| Setting                  | Value                                              |
| ------------------------ | -------------------------------------------------- |
| Model tokenizer          | `Qwen/Qwen3-0.6B`                                  |
| Immutable revision       | `c1899de289a04d12100db370d81485cdf75e47ca`         |
| Python tokenizer package | `tokenizers==0.23.3`                               |
| Special tokens           | `add_special_tokens=False`                         |
| Stored information       | Original text, token IDs, and decoded token pieces |

[`verify-tokenization.py`](../apps/web/scripts/verify-tokenization.py) fetches only the pinned `tokenizer.json`, re-encodes each sentence, and compares IDs, decoded text, and pieces with the fixture. It does not download model weights or modify the fixture. These examples establish segmentation for the selected strings, not a general English/Filipino token-cost ratio or a measure of language-model quality.

## Verification procedure

Run the repository checks from the monorepo root with the pinned pnpm version and Node 24:

```powershell
pnpm lint
pnpm typecheck
pnpm --filter web test:research
pnpm build
pnpm --filter web start
```

Stop an existing server on the same port first, or use `pnpm --filter web start --port 3001`. A production build must exist before starting the production server.

The research tests cover catalog/reference relationships, heading extraction, article/diagram contracts, tokenizer-fixture structure, and numerical cases including gradients, attention, LoRA, classification metrics, split accounting, and memory estimates. They do not replace mathematical review, executing the Python example, external-source checks, or browser verification.

Use an isolated Python environment outside the website dependencies for the following checks. Install a compatible CPU PyTorch build using its official installation selector. Tokenizer reproduction additionally requires the fixture's pinned package version and network access:

```powershell
python -m pip install tokenizers==0.23.3
python apps/web/scripts/verify-tokenization.py
python apps/web/public/research/examples/train_regression.py --epochs 80 --output "$env:TEMP/makata-regression-check"
python apps/web/public/research/examples/train_regression.py --epochs 40 --output "$env:TEMP/makata-regression-partial"
python apps/web/public/research/examples/train_regression.py --epochs 80 --resume "$env:TEMP/makata-regression-partial/last.pt" --output "$env:TEMP/makata-regression-resumed"
```

Record interpreter/package versions and actual outputs. Inspect finite losses, held-out behavior, learned coefficients, checkpoint round-trip checks, and continuation behavior. These are synthetic regression results, not LLM benchmarks. Keep generated checkpoints and histories outside the source tree.

Browser review should cover:

- `/research` and all eight articles; an unknown article slug must return a real 404.
- 320, 393, 768, 1024, and 1440 px widths; readable equations/code, no page-level overflow, and the intended navigation/TOC breakpoint behavior.
- Keyboard traversal, drawer focus and Escape, slider keys, links to sections, back/forward navigation, and route changes during smooth scrolling.
- Initial, intermediate, and final diagram states; controls must change corresponding values correctly, Reset must restore the initial state, and labels/connections must remain unclipped.
- Reduced-motion mode, hidden-tab/offscreen playback, and JavaScript-disabled article reading.
- Server-rendered article text and equations, canonical/title/description metadata, social images, structured data, sitemap entries, and source links.
- The existing homepage, including its overview anchor, particle behavior, branding, and mobile layout.

Report the exact commands and browser scenarios executed, their outcomes, and unresolved limitations with the change. A checklist entry in this document is a requirement to verify, not a stored passing result.

## Files in this implementation

This inventory covers the research-library implementation: 9 modified files and 51 created files. No files were deleted. Pre-existing user-installed `.agents/` directories and `skills-lock.json` files are excluded, as are generated `.next/` artifacts.

### Existing files modified

| File | Purpose |
| --- | --- |
| [README.md](../README.md) | Describe the library, authoring guide, examples, and verification command. |
| [apps/web/app/page.tsx](../apps/web/app/page.tsx) | Link header/footer Research navigation to the library; retain the hero overview anchor. |
| [apps/web/app/sitemap.ts](../apps/web/app/sitemap.ts) | Include the research index and eight article URLs. |
| [apps/web/components/smooth-scroll.tsx](../apps/web/components/smooth-scroll.tsx) | Stop Lenis inertia during route navigation. |
| [apps/web/next.config.ts](../apps/web/next.config.ts) | Compile local MDX, GFM, heading anchors, and mathematical notation. |
| [apps/web/package.json](../apps/web/package.json) | Declare MDX/math dependencies and the research test command. |
| [packages/ui/package.json](../packages/ui/package.json) | Resolve KaTeX's stylesheet from the shared UI package. |
| [packages/ui/src/styles/globals.css](../packages/ui/src/styles/globals.css) | Import KaTeX vendor styles and include MDX in Tailwind source scanning. |
| [pnpm-lock.yaml](../pnpm-lock.yaml) | Record the resolved workspace dependency changes. |

### Research routes and presentation created

| File | Purpose |
| --- | --- |
| [apps/web/app/research/layout.tsx](../apps/web/app/research/layout.tsx) | Provide the research section's shared branded shell and navigation placement. |
| [apps/web/app/research/page.tsx](../apps/web/app/research/page.tsx) | Render the grouped library index and its page metadata. |
| [apps/web/app/research/opengraph-image.tsx](../apps/web/app/research/opengraph-image.tsx) | Generate the research index social preview. |
| [apps/web/app/research/[slug]/page.tsx](../apps/web/app/research/[slug]/page.tsx) | Statically compose articles, metadata, sources, TOC, and related reading. |
| [apps/web/app/research/[slug]/opengraph-image.tsx](../apps/web/app/research/[slug]/opengraph-image.tsx) | Generate article-specific social previews. |
| [apps/web/components/research/navigation.tsx](../apps/web/components/research/navigation.tsx) | Render article navigation, mobile controls, and the separate On this page TOC. |
| [apps/web/components/research/code-copy.tsx](../apps/web/components/research/code-copy.tsx) | Provide accessible code-copy interaction and feedback. |
| [apps/web/components/research/social-image.tsx](../apps/web/components/research/social-image.tsx) | Share the Makata research social-image composition. |
| [apps/web/mdx-components.tsx](../apps/web/mdx-components.tsx) | Map article markup to semantic, Tailwind-styled reading components. |

### Interactive diagram files created

| File | Purpose |
| --- | --- |
| [apps/web/components/research/diagrams/shared.tsx](../apps/web/components/research/diagrams/shared.tsx) | Share accessible controls, SVG frames, values, tables, and motion/playback behavior. |
| [apps/web/components/research/diagrams/lazy.tsx](../apps/web/components/research/diagrams/lazy.tsx) | Split topic implementations into dynamic chunks while retaining server-rendered initial diagrams. |
| [apps/web/components/research/diagrams/mathematics.tsx](../apps/web/components/research/diagrams/mathematics.tsx) | Explain vectors, matrix transformations, descent, and the chain rule. |
| [apps/web/components/research/diagrams/neural-networks.tsx](../apps/web/components/research/diagrams/neural-networks.tsx) | Explain editable network values, forward/backward flow, and activations. |
| [apps/web/components/research/diagrams/pytorch.tsx](../apps/web/components/research/diagrams/pytorch.tsx) | Explain autograd and computed training progress. |
| [apps/web/components/research/diagrams/transformers.tsx](../apps/web/components/research/diagrams/transformers.tsx) | Explain tokenization, attention, decoder stages, and sampling. |
| [apps/web/components/research/diagrams/llm-training.tsx](../apps/web/components/research/diagrams/llm-training.tsx) | Explain trainable parameters, low-rank updates, and distillation. |
| [apps/web/components/research/diagrams/dataset-engineering.tsx](../apps/web/components/research/diagrams/dataset-engineering.tsx) | Explain cleaning, splitting, tokenizer comparisons, and contamination. |
| [apps/web/components/research/diagrams/evaluation.tsx](../apps/web/components/research/diagrams/evaluation.tsx) | Explain confusion metrics, illustrative comparisons, and generalization curves. |
| [apps/web/components/research/diagrams/gpu-computing.tsx](../apps/web/components/research/diagrams/gpu-computing.tsx) | Explain parallel work, memory accounting, accumulation, and checkpointing. |

### Articles created

| File | Purpose |
| --- | --- |
| [apps/web/content/research/mathematics-for-ml.mdx](../apps/web/content/research/mathematics-for-ml.mdx) | Develop the mathematical foundations and their LLM applications. |
| [apps/web/content/research/neural-networks.mdx](../apps/web/content/research/neural-networks.mdx) | Develop forward computation, differentiation, optimization, and generalization. |
| [apps/web/content/research/pytorch.mdx](../apps/web/content/research/pytorch.mdx) | Explain an executable CPU training workflow and debugging methods. |
| [apps/web/content/research/transformers.mdx](../apps/web/content/research/transformers.mdx) | Trace text through tokenization, transformer computation, and generation. |
| [apps/web/content/research/llm-training.mdx](../apps/web/content/research/llm-training.mdx) | Compare training/adaptation methods and propose controlled future experiments. |
| [apps/web/content/research/dataset-engineering.mdx](../apps/web/content/research/dataset-engineering.mdx) | Explain provenance, responsible processing, linguistic coverage, and data independence. |
| [apps/web/content/research/evaluation.mdx](../apps/web/content/research/evaluation.mdx) | Explain metrics, experimental controls, uncertainty, and Philippine-language benchmarks. |
| [apps/web/content/research/gpu-computing.mdx](../apps/web/content/research/gpu-computing.mdx) | Explain execution, precision, memory, batching, distributed work, and measured cost. |

### Research data and server helpers created

| File | Purpose |
| --- | --- |
| [apps/web/lib/research/catalog.ts](../apps/web/lib/research/catalog.ts) | Define typed article metadata, groups, reading order, relationships, and source IDs. |
| [apps/web/lib/research/content.ts](../apps/web/lib/research/content.ts) | Load local articles and their outlines through a server-only boundary. |
| [apps/web/lib/research/math.ts](../apps/web/lib/research/math.ts) | Compute deterministic teaching models independently of SVG rendering. |
| [apps/web/lib/research/metadata.ts](../apps/web/lib/research/metadata.ts) | Construct consistent research canonical and social metadata. |
| [apps/web/lib/research/outline.ts](../apps/web/lib/research/outline.ts) | Extract heading text and stable IDs while ignoring fenced code. |
| [apps/web/lib/research/sources.ts](../apps/web/lib/research/sources.ts) | Centralize authoritative source identities and resource types. |
| [apps/web/lib/research/tokenization.json](../apps/web/lib/research/tokenization.json) | Store pinned, reproducible token IDs and pieces for three language examples. |

### Tests, reproducibility examples, and guide created

| File | Purpose |
| --- | --- |
| [apps/web/tests/research/content.test.mjs](../apps/web/tests/research/content.test.mjs) | Check the catalog, outlines, article/diagram contracts, and tokenizer-fixture structure. |
| [apps/web/tests/research/math.test.mjs](../apps/web/tests/research/math.test.mjs) | Check numerical results, gradient consistency, masking, metrics, and resource accounting. |
| [apps/web/public/research/examples/train_regression.py](../apps/web/public/research/examples/train_regression.py) | Supply the downloadable CPU training, validation, checkpoint, and resume example. |
| [apps/web/scripts/verify-tokenization.py](../apps/web/scripts/verify-tokenization.py) | Reproduce the committed tokenizer fixtures without model weights. |
| [docs/research-library.md](research-library.md) | Document topic coverage, authoring, verification, and this complete file inventory. |

### Shared shadcn primitives created

These files preserve the existing shared Base Nova component system; they do not introduce a second UI framework.

| File | Purpose |
| --- | --- |
| [packages/ui/src/components/alert.tsx](../packages/ui/src/components/alert.tsx) | Present article callouts. |
| [packages/ui/src/components/breadcrumb.tsx](../packages/ui/src/components/breadcrumb.tsx) | Present semantic article location trails. |
| [packages/ui/src/components/collapsible.tsx](../packages/ui/src/components/collapsible.tsx) | Support collapsible navigation/TOC regions. |
| [packages/ui/src/components/field.tsx](../packages/ui/src/components/field.tsx) | Group and label diagram controls. |
| [packages/ui/src/components/label.tsx](../packages/ui/src/components/label.tsx) | Supply the labeling primitive used by fields. |
| [packages/ui/src/components/separator.tsx](../packages/ui/src/components/separator.tsx) | Separate article content semantically. |
| [packages/ui/src/components/scroll-area.tsx](../packages/ui/src/components/scroll-area.tsx) | Provide the independently scrollable mobile section rail, with viewport props for section tracking. |
| [packages/ui/src/components/sheet.tsx](../packages/ui/src/components/sheet.tsx) | Provide the accessible mobile navigation drawer. |
| [packages/ui/src/components/slider.tsx](../packages/ui/src/components/slider.tsx) | Provide keyboard-operable numerical controls. |
| [packages/ui/src/components/table.tsx](../packages/ui/src/components/table.tsx) | Present article tables and diagram data alternatives. |
| [packages/ui/src/components/toggle-group.tsx](../packages/ui/src/components/toggle-group.tsx) | Group mutually selectable diagram modes. |
| [packages/ui/src/components/toggle.tsx](../packages/ui/src/components/toggle.tsx) | Supply shared toggle styling and behavior. |

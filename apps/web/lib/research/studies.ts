export type StudyStatus = "planned" | "in-progress" | "completed"
export type ReviewStatus = "not-peer-reviewed" | "peer-reviewed"

export type Study = {
  id: string
  slug: string
  title: string
  shortTitle: string
  subtitle: string
  abstract: string
  authors: readonly string[]
  completedOn?: string
  publishedOn?: string
  status: StudyStatus
  reviewStatus: ReviewStatus
  reviewEvidence?: string
  availability: "prepared-locally" | "published"
  category: string
  methods: readonly string[]
  models: readonly string[]
  datasets: readonly string[]
  sources: readonly string[]
  decisions: readonly { id: string; title: string; file: string }[]
  materials: readonly { file: string; title: string; description: string }[]
}

export const studies = [
  {
    id: "001",
    slug: "001-tagalog-comprehension",
    title:
      "Makata Research Report 001: Evaluating Open-Weight Language Models on Tagalog Reading Comprehension",
    shortTitle:
      "Evaluating open-weight models on Tagalog reading comprehension",
    subtitle:
      "A reproducible zero-shot evaluation of general multilingual and Southeast Asian-focused language models.",
    abstract:
      "We evaluate Qwen3-1.7B-Base and Sailor2-1B on the complete Tagalog Belebele reading-comprehension test through FilBench. The report documents likelihood-based scoring, frozen revisions, verified measurements, and the limits of this descriptive comparison before Filipino-language adaptation research.",
    authors: ["Makata"],
    completedOn: "2026-10-12",
    status: "completed",
    reviewStatus: "not-peer-reviewed",
    availability: "prepared-locally",
    category: "Language-model evaluation",
    methods: [
      "Zero-shot",
      "Multiple-choice likelihood",
      "Complete 900-question test",
    ],
    models: ["Qwen/Qwen3-1.7B-Base", "sail/Sailor2-1B"],
    datasets: ["facebook/belebele · tgl_Latn · test"],
    sources: [
      "filbench",
      "belebele",
      "qwen3",
      "sailor2",
      "qwen-card",
      "qwen-license",
      "qwen-languages",
      "sailor-card",
      "sailor-code",
      "dataset-card",
      "filbench-entry",
      "filbench-task",
      "original-brief",
    ],
    decisions: [
      {
        id: "0001",
        title: "Begin with Tagalog reading comprehension",
        file: "0001-tagalog-reading-comprehension.md",
      },
      {
        id: "0002",
        title: "Baseline model selection",
        file: "0002-baseline-model-selection.md",
      },
      {
        id: "0003",
        title: "Preserve the official evaluation protocol",
        file: "0003-evaluation-protocol.md",
      },
    ],
    materials: [
      {
        file: "makata-baselines.ipynb",
        title: "Frozen reproduction notebook",
        description:
          "Output-free notebook with the exact checksummed research source and pinned Linux/CUDA environment.",
      },
      {
        file: "source-snapshot.zip",
        title: "Exact embedded source snapshot",
        description:
          "The original source ZIP extracted byte-for-byte from the notebook; no model weights or benchmark data.",
      },
      {
        file: "evidence.json",
        title: "Public evidence summary",
        description:
          "Verified aggregates, revisions, runtime, environment, and hashes. Raw per-example records remain locally retained.",
      },
      {
        file: "reproduce.md",
        title: "Reproduction instructions",
        description:
          "Execution order, environment requirements, verification checks, and evidence-access limitations.",
      },
      {
        file: "checksums.json",
        title: "Download checksums",
        description:
          "SHA-256 checksums for every material and decision record in this release.",
      },
    ],
  },
  {
    id: "002",
    slug: "002-aya-qlora-evaluation",
    title:
      "Makata Research Report 002: Aya-Only QLoRA Adaptation and Tagalog Comprehension Evaluation",
    shortTitle:
      "An exploratory adaptation, with an uncertain comprehension change",
    subtitle:
      "Dataset screening, a bounded QLoRA run, and a paired evaluation of Makata-v0.1 checkpoint 91.",
    abstract:
      "We adapt Qwen3-1.7B-Base on 363 screened Aya Filipino examples. On the same 900-question Tagalog Belebele task, accuracy changes from 53.67% to 55.33% (+1.67 percentage points). The paired 95% passage-bootstrap interval spans −1.45 to +4.80 points: improvement is not statistically established. Data review and rights limitations remain unresolved; weights are not released.",
    authors: ["Makata"],
    completedOn: "2026-10-13",
    status: "completed",
    reviewStatus: "not-peer-reviewed",
    availability: "prepared-locally",
    category: "Exploratory model adaptation and evaluation",
    methods: [
      "Aya-only QLoRA",
      "One epoch · final checkpoint 91",
      "Paired passage-cluster bootstrap",
    ],
    models: [
      "Qwen/Qwen3-1.7B-Base",
      "Makata-v0.1 experimental adapter · checkpoint 91",
    ],
    datasets: [
      "Aya Filipino · 363 selected examples",
      "facebook/belebele · tgl_Latn · test",
    ],
    sources: [
      "filbench",
      "belebele",
      "qwen3",
      "qwen-card",
      "qwen-license",
      "dataset-card",
      "filbench-entry",
      "filbench-task",
      "aya-card",
      "aya-paper",
      "lora",
      "qlora",
    ],
    decisions: [
      {
        id: "0004",
        title: "Bounded exploratory adaptation and final-checkpoint comparison",
        file: "0004-exploratory-aya-adaptation.md",
      },
    ],
    materials: [
      {
        file: "evidence.json",
        title: "Verified public evidence summary",
        description:
          "Allowlisted aggregates, revisions, configurations, and retained artifact hashes. No private records or weights.",
      },
      {
        file: "makata-qlora-full.ipynb",
        title: "Frozen training notebook",
        description:
          "Output-free historical notebook. Execution requires the restricted, separately supplied training input bundle.",
      },
      {
        file: "training-source-snapshot.zip",
        title: "Exact training source snapshot",
        description:
          "Source extracted from the executed notebook, without Aya text, checkpoints, or unreviewed tasks.",
      },
      {
        file: "makata-post-training.ipynb",
        title: "Frozen evaluation notebook",
        description:
          "Output-free notebook. Requires the retained private adapter and original baseline evidence.",
      },
      {
        file: "evaluation-source-snapshot.zip",
        title: "Exact evaluation source snapshot",
        description:
          "Pinned evaluation implementation and dependency locks; no benchmark test records or weights.",
      },
      {
        file: "reproduce.md",
        title: "Reproduction and evidence-access instructions",
        description:
          "Exact commands, integrity checks, and a clear account of what cannot be reproduced from public downloads alone.",
      },
      {
        file: "checksums.json",
        title: "Download checksums",
        description: "SHA-256 inventory of this report's public materials.",
      },
    ],
  },
] as const satisfies readonly Study[]

export type StudySlug = (typeof studies)[number]["slug"]

export function findStudy(
  slug: string
): (Study & { slug: StudySlug }) | undefined {
  return studies.find((study) => study.slug === slug)
}

export function studyMaterialUrl(slug: string, file: string): string {
  return `/research-materials/${slug}/${file}`
}

export function studyStatusLabel(status: StudyStatus): string {
  return {
    planned: "Planned research",
    "in-progress": "In progress",
    completed: "Completed technical report",
  }[status]
}

export function studyReviewLabel(status: ReviewStatus): string {
  return status === "peer-reviewed"
    ? "Peer reviewed"
    : "Independent Technical Report — Not Peer Reviewed"
}

export function studyDate(date: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "long",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`))
}

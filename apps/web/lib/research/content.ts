import "server-only"
import { readFile } from "node:fs/promises"
import { join } from "node:path"
import { cache } from "react"
import type { ArticleSlug, OutlineItem } from "./catalog"
import { extractOutline } from "./outline"

export const articleLoaders = {
  "mathematics-for-ml": () =>
    import("@/content/research/mathematics-for-ml.mdx"),
  "neural-networks": () => import("@/content/research/neural-networks.mdx"),
  pytorch: () => import("@/content/research/pytorch.mdx"),
  transformers: () => import("@/content/research/transformers.mdx"),
  "llm-training": () => import("@/content/research/llm-training.mdx"),
  "dataset-engineering": () =>
    import("@/content/research/dataset-engineering.mdx"),
  evaluation: () => import("@/content/research/evaluation.mdx"),
  "gpu-computing": () => import("@/content/research/gpu-computing.mdx"),
} satisfies Record<ArticleSlug, () => Promise<{ default: React.ComponentType }>>

export const getOutline = cache(
  async (slug: ArticleSlug): Promise<OutlineItem[]> => {
    const source = await readFile(
      join(process.cwd(), "content", "research", `${slug}.mdx`),
      "utf8"
    )
    return extractOutline(source)
  }
)

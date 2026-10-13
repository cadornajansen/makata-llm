import "server-only"
import { readFile } from "node:fs/promises"
import { join } from "node:path"
import { cache } from "react"
import type { StudySlug } from "./studies"
import type { OutlineItem } from "./catalog"
import { extractOutline } from "./outline"

export const studyLoaders = {
  "001-tagalog-comprehension": () =>
    import("@/content/research/studies/001-tagalog-comprehension.mdx"),
  "002-aya-qlora-evaluation": () =>
    import("@/content/research/studies/002-aya-qlora-evaluation.mdx"),
} satisfies Record<StudySlug, () => Promise<{ default: React.ComponentType }>>

export const getStudyOutline = cache(
  async (slug: StudySlug): Promise<OutlineItem[]> => {
    const source = await readFile(
      join(process.cwd(), "content", "research", "studies", `${slug}.mdx`),
      "utf8"
    )
    return extractOutline(source)
  }
)

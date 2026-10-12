import GithubSlugger from "github-slugger"
import type { OutlineItem } from "./catalog"

// Article headings use plain Markdown. Ignore heading-like text inside code examples.
export function extractOutline(source: string): OutlineItem[] {
  const slugger = new GithubSlugger()
  const outline: OutlineItem[] = []
  let fence: string | null = null
  for (const line of source.split(/\r?\n/)) {
    const marker = line.match(/^\s*(`{3,}|~{3,})/)
    if (marker?.[1]) {
      if (!fence) fence = marker[1]
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length)
        fence = null
      continue
    }
    if (fence) continue
    const heading = line.match(/^(#{2,3}) (.+?)\s*#*$/)
    if (!heading?.[1] || !heading[2]) continue
    outline.push({
      id: slugger.slug(heading[2]),
      title: heading[2],
      level: heading[1].length as 2 | 3,
    })
  }
  return outline
}

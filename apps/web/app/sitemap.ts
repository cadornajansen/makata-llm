import type { MetadataRoute } from "next"
import { site } from "@/lib/site"
import { articles } from "@/lib/research/catalog"
import { studies } from "@/lib/research/studies"

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: site.url },
    { url: `${site.url}/research` },
    ...articles.map(({ slug }) => ({ url: `${site.url}/research/${slug}` })),
    { url: `${site.url}/research/studies` },
    ...studies.map(({ slug }) => ({
      url: `${site.url}/research/studies/${slug}`,
    })),
  ]
}

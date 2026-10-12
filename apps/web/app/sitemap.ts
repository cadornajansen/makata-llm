import type { MetadataRoute } from "next"
import { site } from "@/lib/site"
import { articles } from "@/lib/research/catalog"

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: site.url },
    { url: `${site.url}/research` },
    ...articles.map(({ slug }) => ({ url: `${site.url}/research/${slug}` })),
  ]
}

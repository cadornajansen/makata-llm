import type { Metadata } from "next"
import { site } from "@/lib/site"

export function researchMetadata(
  title: string,
  description: string,
  path: string,
  type: "website" | "article" = path === "/research" ? "website" : "article"
): Metadata {
  const fullTitle = `${title} — Makata`
  const image = `${path}/opengraph-image`
  return {
    title: fullTitle,
    description,
    alternates: { canonical: path },
    openGraph: {
      title: fullTitle,
      description,
      url: path,
      siteName: site.name,
      type,
      locale: "en_PH",
      images: [{ url: image, width: 1200, height: 630, alt: title }],
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      images: [image],
    },
  }
}

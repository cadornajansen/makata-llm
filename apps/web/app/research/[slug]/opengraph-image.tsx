import { notFound } from "next/navigation"
import { researchImage } from "@/components/research/social-image"
import { articles, findArticle } from "@/lib/research/catalog"
export const alt =
  "Makata Research & Learning — illustrated technical study notes"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const dynamic = "force-static"
export const dynamicParams = false
export function generateStaticParams(): { slug: string }[] {
  return articles.map(({ slug }) => ({ slug }))
}
export default async function Image({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Response> {
  const article = findArticle((await params).slug)
  if (!article) notFound()
  return researchImage(article.title, article.group)
}

import { notFound } from "next/navigation"
import { researchImage } from "@/components/research/social-image"
import { studies, findStudy } from "@/lib/research/studies"
export const alt =
  "Makata Research Report — independent technical report, not peer reviewed"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const dynamic = "force-static"
export const dynamicParams = false
export function generateStaticParams(): { slug: string }[] {
  return studies.map(({ slug }) => ({ slug }))
}
export default async function Image({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Response> {
  const study = findStudy((await params).slug)
  if (!study) notFound()
  return researchImage(
    study.shortTitle,
    `Report ${study.id} · Tagalog reading comprehension`,
    {
      section: "Research Studies",
      footer: "Independent technical report · Not peer reviewed",
    }
  )
}

import { researchImage } from "@/components/research/social-image"
export const alt =
  "Makata Research & Learning — understanding what we're building"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const dynamic = "force-static"
export default async function Image(): Promise<Response> {
  return researchImage(
    "Understanding what we’re building.",
    "Eight connected topics · Interactive explanations"
  )
}

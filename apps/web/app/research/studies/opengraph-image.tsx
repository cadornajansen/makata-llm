import { researchImage } from "@/components/research/social-image"
export const alt =
  "Makata Research Studies — methods, measurements, and limitations"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const dynamic = "force-static"
export default async function Image(): Promise<Response> {
  return researchImage(
    "Research, with the evidence attached.",
    "Original research · Independent technical reports",
    {
      section: "Research Studies",
      footer: "Methods. Measurements. Limitations. Reproduction.",
    }
  )
}

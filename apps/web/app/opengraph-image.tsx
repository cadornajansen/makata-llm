import { ImageResponse } from "next/og"
import { readFile } from "node:fs/promises"
import { join } from "node:path"

export const alt =
  "Makata — Building the foundations of Philippine intelligence. Independent research, foundational stage."
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const dynamic = "force-static"

export default async function OpenGraphImage(): Promise<ImageResponse> {
  const logo = await readFile(join(process.cwd(), "public/makata.svg"))
  // Google Sans's ligature tables are unsupported here; use the bundled sans font.
  return new ImageResponse(
    <div tw="relative flex h-full w-full flex-col overflow-hidden bg-[#f5f6f8] px-[76px] py-[58px] text-[#202328]">
      <div tw="flex items-center justify-between">
        <div tw="flex items-center">
          {/* ImageResponse embeds the SVG directly into the generated PNG. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/svg+xml;base64,${logo.toString("base64")}`}
            width={48}
            height={40}
            alt=""
          />
          <span tw="ml-[14px] text-[42px] tracking-[-2px]">makata</span>
        </div>
        <span tw="text-[18px] text-[#646b75]">Foundational stage</span>
      </div>
      <div tw="mt-[60px] flex flex-col">
        <span tw="text-[68px] leading-[76px] tracking-[-3px]">
          Building the foundations
        </span>
        <span tw="font-medium text-[68px] leading-[76px] tracking-[-3px]">
          of Philippine
        </span>
        <span tw="text-[68px] leading-[76px] tracking-[-3px]">
          intelligence.
        </span>
      </div>
      <div tw="mt-auto flex items-center justify-between">
        <span tw="text-[19px] text-[#646b75]">
          Filipino-first. Culturally-aware
        </span>
        <svg width="280" height="92" viewBox="0 0 280 92">
          {Array.from({ length: 8 }, (_, row) =>
            Array.from({ length: 25 }, (_, column) => (
              <circle
                key={`${row}-${column}`}
                cx={8 + column * 11}
                cy={24 + row * 6 + Math.sin(column * 0.25 + row * 0.28) * 14}
                r="1.7"
                fill={column > 16 ? "#ad778b" : "#7991ae"}
                opacity="0.65"
              />
            ))
          )}
        </svg>
      </div>
    </div>,
    size
  )
}

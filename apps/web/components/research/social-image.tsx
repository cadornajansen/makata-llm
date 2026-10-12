import { ImageResponse } from "next/og"
import { readFile } from "node:fs/promises"
import { join } from "node:path"
import { site } from "@/lib/site"

export async function researchImage(
  title: string,
  label: string
): Promise<ImageResponse> {
  const logo = await readFile(
    join(process.cwd(), "public/makata.svg"),
    "base64"
  )
  return new ImageResponse(
    <div tw="flex h-full w-full flex-col bg-[#f5f6f8] px-[76px] py-[60px] text-[#17191d]">
      <div tw="flex items-center justify-between">
        <div tw="flex items-center">
          {/* ImageResponse embeds this local asset into the final PNG. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`data:image/svg+xml;base64,${logo}`}
            width={48}
            height={40}
            alt=""
          />
          <span tw="ml-[14px] text-[38px] tracking-[-2px]">Makata</span>
        </div>
        <span tw="text-[20px] text-[#60656f]">Research & Learning</span>
      </div>
      <div tw="mt-[80px] flex flex-col">
        <span tw="mb-[22px] text-[20px] text-[#bc7c8f]">{label}</span>
        <span tw="text-[64px] leading-[74px] tracking-[-2px]">{title}</span>
      </div>
      <div tw="mt-auto flex items-center justify-between border-t border-[#dce0e6] pt-[24px]">
        <span tw="text-[21px] text-[#60656f]">
          Understand the mathematics. Examine the methods.
        </span>
        <span tw="text-[19px]">{new URL(site.url).hostname}</span>
      </div>
    </div>,
    { width: 1200, height: 630 }
  )
}

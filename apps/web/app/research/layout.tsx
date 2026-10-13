import type { ReactNode } from "react"
import Link from "next/link"
import Image from "next/image"
import { ArrowUpRight } from "lucide-react"

export default function ResearchLayout({
  children,
}: {
  children: ReactNode
}): React.ReactElement {
  return (
    <div className="min-h-dvh">
      <a
        href="#research-main"
        className="fixed top-3 left-3 z-50 -translate-y-24 rounded-lg bg-primary px-4 py-3 text-primary-foreground focus:translate-y-0"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b bg-background">
        <div className="mx-auto flex min-h-20 max-w-[1536px] items-center justify-between gap-4 px-5 sm:px-8 lg:px-10">
          <Link
            href="/"
            aria-label="Makata home"
            className="flex min-h-11 items-center gap-2.5 text-2xl font-semibold tracking-tight"
          >
            <Image
              src="/makata.svg"
              width={4000}
              height={3335}
              alt=""
              unoptimized
              className="h-auto w-8"
            />
            Makata
          </Link>
          <nav
            aria-label="Main navigation"
            className="flex items-center gap-3 text-sm sm:gap-8"
          >
            <Link
              href="/research"
              className="flex min-h-11 items-center font-medium"
            >
              Research<span className="hidden sm:inline">&nbsp;& Learning</span>
            </Link>
            <Link
              href="/research/studies"
              className="flex min-h-11 items-center font-medium"
            >
              Studies
            </Link>
            <a
              href="mailto:jansencadorna5@gmail.com"
              className="hidden min-h-11 items-center gap-2 text-muted-foreground hover:text-foreground sm:flex"
            >
              Get in touch
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
          </nav>
        </div>
      </header>
      {children}
      <footer className="mt-24 border-t">
        <div className="mx-auto flex max-w-[1536px] flex-col justify-between gap-5 px-5 py-10 text-sm text-muted-foreground sm:px-8 md:flex-row lg:px-10">
          <p className="max-w-xl leading-relaxed">
            Independent Philippine AI research. The learning library explains
            established methods; Research Studies documents our experiments and
            their limitations. An experimental adapter has been evaluated;
            weights remain private. Citations do not imply institutional
            partnerships.
          </p>
          <Link
            href="/"
            className="shrink-0 self-start py-2 hover:text-foreground"
          >
            Back to Makata ↗
          </Link>
        </div>
      </footer>
    </div>
  )
}

"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { ArrowUpRight, ChevronDown, List, Menu } from "lucide-react"
import { Button } from "@workspace/ui/components/button"
import { ScrollArea } from "@workspace/ui/components/scroll-area"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@workspace/ui/components/sheet"
import { cn } from "@workspace/ui/lib/utils"
import {
  articles,
  groups,
  type ArticleSlug,
  type OutlineItem,
} from "@/lib/research/catalog"

function TopicLinks({
  current,
  onNavigate,
}: {
  current: ArticleSlug
  onNavigate?: () => void
}): React.ReactElement {
  return (
    <nav aria-label="Research topics" className="flex flex-col gap-6">
      {groups.map((group) => (
        <Collapsible key={group} defaultOpen className="flex flex-col gap-2">
          <CollapsibleTrigger className="group flex min-h-10 items-center justify-between gap-3 text-xs font-medium tracking-wider text-muted-foreground uppercase">
            {group}
            <ChevronDown
              className="size-3.5 transition-transform group-data-[panel-open]:rotate-180"
              aria-hidden="true"
            />
          </CollapsibleTrigger>
          <CollapsibleContent className="flex flex-col gap-1">
            {articles
              .filter((article) => article.group === group)
              .map((article) => (
                <div key={article.slug}>
                  <Link
                    onClick={onNavigate}
                    href={`/research/${article.slug}`}
                    aria-current={article.slug === current ? "page" : undefined}
                    className={cn(
                      "flex min-h-10 items-center rounded-lg px-3 py-2 text-sm leading-snug transition-colors hover:bg-secondary",
                      article.slug === current
                        ? "bg-secondary font-medium text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {article.shortTitle}
                  </Link>
                </div>
              ))}
          </CollapsibleContent>
        </Collapsible>
      ))}
      <Link
        onClick={onNavigate}
        href="/research"
        className="flex min-h-10 items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        Library overview
        <ArrowUpRight className="size-3.5" aria-hidden="true" />
      </Link>
    </nav>
  )
}

export function ResearchNavigation({
  current,
}: {
  current: ArticleSlug
}): React.ReactElement {
  const [open, setOpen] = useState(false)
  return (
    <>
      <aside className="hidden min-w-0 lg:block">
        <div
          className="sticky top-28 max-h-[calc(100dvh-9rem)] overflow-y-auto overscroll-contain pr-4 pb-8 [scrollbar-width:thin]"
          data-lenis-prevent
        >
          <TopicLinks current={current} />
        </div>
      </aside>
      <div className="lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger
            render={<Button variant="outline" className="min-h-11" />}
          >
            <Menu data-icon="inline-start" aria-hidden="true" />
            Browse topics
          </SheetTrigger>
          <SheetContent side="left" className="w-[min(90vw,340px)]">
            <SheetHeader>
              <SheetTitle>Research & Learning</SheetTitle>
            </SheetHeader>
            <div
              className="min-h-0 overflow-y-auto overscroll-contain px-6 pb-8"
              data-lenis-prevent
            >
              <TopicLinks current={current} onNavigate={() => setOpen(false)} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  )
}

function MobileSectionRail({
  outline,
  active,
}: {
  outline: OutlineItem[]
  active: string
}): React.ReactElement {
  const viewport = useRef<HTMLDivElement>(null)
  const labelTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [nearestId, setNearestId] = useState<string | null>(null)
  const [browsing, setBrowsing] = useState(false)
  const activeIndex = Math.max(
    0,
    outline.findIndex(({ id }) => id === active)
  )
  const nearestIndex = Math.max(
    0,
    outline.findIndex(({ id }) => id === nearestId)
  )
  const label = outline[nearestIndex] ?? outline[activeIndex]

  useEffect(() => {
    // Scroll only this viewport; scrollIntoView could also move the article.
    viewport.current?.scrollTo({
      top: activeIndex * 44,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    })
  }, [activeIndex])

  useEffect(() => {
    return () => {
      if (labelTimeout.current) clearTimeout(labelTimeout.current)
    }
  }, [])

  return (
    <nav
      aria-label="Article sections"
      className="group/rail fixed top-1/2 right-0 z-40 -translate-y-1/2 lg:hidden"
      data-browsing={browsing}
    >
      <p
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 right-12 w-max max-w-[min(12rem,calc(100vw-5rem))] -translate-y-1/2 rounded-md bg-background/95 px-2 py-1.5 text-right text-xs leading-snug text-foreground opacity-0 shadow-sm group-focus-within/rail:opacity-100 group-hover/rail:opacity-100 group-data-[browsing=true]/rail:opacity-100 motion-safe:transition-opacity"
      >
        {label?.title}
      </p>
      <ScrollArea
        className="h-55 max-h-[50dvh] w-11 [mask-image:linear-gradient(to_bottom,transparent,black_24%,black_76%,transparent)] [&_[data-slot=scroll-area-scrollbar]]:hidden"
        data-lenis-prevent
        viewportProps={{
          ref: viewport,
          "aria-label": "Scroll to browse article sections",
          className: "overscroll-contain",
          onScroll: (event) => {
            const index = Math.min(
              outline.length - 1,
              Math.max(0, Math.round(event.currentTarget.scrollTop / 44))
            )
            setNearestId(outline[index]?.id ?? null)
            setBrowsing(true)
            if (labelTimeout.current) clearTimeout(labelTimeout.current)
            labelTimeout.current = setTimeout(() => setBrowsing(false), 1600)
          },
        }}
      >
        <div className="flex flex-col [padding-block:calc(min(110px,25dvh)-22px)]">
          {outline.map((section, index) => {
            const distance = Math.min(
              Math.abs(index - activeIndex),
              Math.abs(index - nearestIndex)
            )
            return (
              <Button
                key={section.id}
                variant="ghost"
                nativeButton={false}
                role="link"
                render={
                  <a
                    href={`#${section.id}`}
                    aria-label={section.title}
                    aria-current={
                      index === activeIndex ? "location" : undefined
                    }
                  />
                }
                className="size-11 rounded-none p-0"
                onFocus={() => viewport.current?.scrollTo({ top: index * 44 })}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "h-0.5 rounded-full motion-safe:transition-[width,background-color] motion-safe:duration-300 motion-safe:ease-[cubic-bezier(0.2,0,0,1)]",
                    index === activeIndex
                      ? "w-7 bg-primary"
                      : distance === 0
                        ? "w-6 bg-foreground/70"
                        : distance === 1
                          ? "w-5 bg-muted-foreground/60"
                          : distance === 2
                            ? "w-3 bg-muted-foreground/45"
                            : "w-2 bg-muted-foreground/30"
                  )}
                />
              </Button>
            )
          })}
        </div>
      </ScrollArea>
    </nav>
  )
}

export function TableOfContents({
  outline,
  compact = false,
  supplementalLinks = [
    { id: "sources", title: "Sources & further reading" },
    { id: "related-reading", title: "Related reading" },
  ],
}: {
  outline: OutlineItem[]
  compact?: boolean
  supplementalLinks?: readonly { id: string; title: string }[]
}): React.ReactElement {
  const [active, setActive] = useState("")
  useEffect(() => {
    const headings = outline.flatMap(({ id }) => {
      const element = document.getElementById(id)
      return element ? [element] : []
    })
    let frame = 0
    function updateActive(): void {
      frame = 0
      let current = headings[0]?.id ?? ""
      for (const heading of headings) {
        if (heading.getBoundingClientRect().top > 160) break
        current = heading.id
      }
      setActive(current)
    }
    function scheduleUpdate(): void {
      if (!frame) frame = requestAnimationFrame(updateActive)
    }
    // A jump can skip a heading entirely; track the last heading above the reading line.
    scheduleUpdate()
    window.addEventListener("scroll", scheduleUpdate, { passive: true })
    window.addEventListener("resize", scheduleUpdate)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener("scroll", scheduleUpdate)
      window.removeEventListener("resize", scheduleUpdate)
    }
  }, [outline])
  const links = (
    <nav aria-label="On this page" className="flex flex-col gap-1">
      {outline.map((section) => (
        <a
          key={section.id}
          href={`#${section.id}`}
          aria-current={active === section.id ? "location" : undefined}
          className={cn(
            "border-l py-1.5 pl-3 text-xs leading-relaxed transition-colors hover:text-primary",
            section.level === 3 && "ml-3",
            active === section.id
              ? "border-primary font-medium text-primary"
              : "border-transparent text-muted-foreground"
          )}
        >
          {section.title}
        </a>
      ))}
      {supplementalLinks.map((link) => (
        <a
          key={link.id}
          href={`#${link.id}`}
          className="py-1.5 pl-3 text-xs text-muted-foreground hover:text-primary"
        >
          {link.title}
        </a>
      ))}
    </nav>
  )
  return compact ? (
    <>
      <MobileSectionRail outline={outline} active={active} />
      <Collapsible className="hidden rounded-xl border p-4 lg:block">
        <CollapsibleTrigger className="group flex min-h-8 w-full items-center justify-between gap-3 text-sm font-medium">
          <span className="flex items-center gap-2">
            <List className="size-4" aria-hidden="true" />
            On this page
          </span>
          <ChevronDown
            className="size-4 transition-transform group-data-[panel-open]:rotate-180"
            aria-hidden="true"
          />
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-4">{links}</CollapsibleContent>
      </Collapsible>
    </>
  ) : (
    <div>
      <p className="mb-5 text-xs font-medium tracking-wider text-muted-foreground uppercase">
        On this page
      </p>
      {links}
    </div>
  )
}

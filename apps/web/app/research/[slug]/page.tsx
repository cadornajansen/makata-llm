import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, ArrowRight, ArrowUpRight } from "lucide-react"
import { articles, findArticle } from "@/lib/research/catalog"
import { articleLoaders, getOutline } from "@/lib/research/content"
import { sources } from "@/lib/research/sources"
import { researchMetadata } from "@/lib/research/metadata"
import { site } from "@/lib/site"
import {
  ResearchNavigation,
  TableOfContents,
} from "@/components/research/navigation"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@workspace/ui/components/breadcrumb"

type PageProps = { params: Promise<{ slug: string }> }
export const dynamicParams = false
export function generateStaticParams(): { slug: string }[] {
  return articles.map(({ slug }) => ({ slug }))
}
export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const article = findArticle((await params).slug)
  if (!article) notFound()
  return researchMetadata(
    article.title,
    article.abstract,
    `/research/${article.slug}`
  )
}

export default async function ResearchArticle({
  params,
}: PageProps): Promise<React.ReactElement> {
  const article = findArticle((await params).slug)
  if (!article) notFound()
  const [{ default: Content }, outline] = await Promise.all([
    articleLoaders[article.slug](),
    getOutline(article.slug),
  ])
  const position = articles.findIndex(({ slug }) => slug === article.slug)
  const previous = articles[position - 1]
  const next = articles[position + 1]
  const url = `${site.url}/research/${article.slug}`
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Article",
        "@id": `${url}#article`,
        headline: article.title,
        description: article.abstract,
        url,
        mainEntityOfPage: url,
        inLanguage: "en",
        author: { "@id": `${site.url}/#organization` },
        publisher: { "@id": `${site.url}/#organization` },
        image: `${url}/opengraph-image`,
        educationalUse: "self-study",
        citation: article.sources.map((id) => sources[id]?.url).filter(Boolean),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "Research & Learning",
            item: `${site.url}/research`,
          },
          { "@type": "ListItem", position: 2, name: article.title, item: url },
        ],
      },
    ],
  }
  return (
    <main
      id="research-main"
      tabIndex={-1}
      className="mx-auto max-w-[1536px] pt-8 pr-12 pl-5 outline-none sm:pr-14 sm:pl-8 lg:px-10"
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(data).replace(/</g, "\\u003c"),
        }}
      />
      <Breadcrumb className="mb-10">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink render={<Link href="/research" />}>
              Research & Learning
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{article.shortTitle}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="grid min-w-0 gap-8 lg:grid-cols-[200px_minmax(0,1fr)] xl:grid-cols-[200px_minmax(0,1fr)_180px] xl:gap-10 2xl:grid-cols-[220px_minmax(0,1fr)_200px]">
        <ResearchNavigation current={article.slug} />
        <article className="min-w-0">
          <header className="mx-auto max-w-[72ch]">
            <p className="mb-5 text-xs font-medium tracking-[.12em] text-muted-foreground uppercase">
              {article.group} · Study note{" "}
              {String(position + 1).padStart(2, "0")}
            </p>
            <h1 className="text-[clamp(34px,3.8vw,54px)] leading-[1.12] font-medium tracking-[-.045em] text-balance">
              {article.title}
            </h1>
            <p className="mt-6 text-lg leading-[1.75] text-muted-foreground sm:text-xl">
              {article.abstract}
            </p>
            <p className="mt-5 text-xs leading-relaxed text-muted-foreground">
              Makata learning library · Educational explanations of established
              methods
            </p>
            <div className="mt-10 grid gap-7 border-y py-7 sm:grid-cols-2">
              <div>
                <h2 className="mb-3 text-sm font-medium">Before you begin</h2>
                <ul className="flex flex-col gap-2 text-sm leading-relaxed text-muted-foreground">
                  {article.prerequisites.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h2 className="mb-3 text-sm font-medium">
                  What you’ll understand
                </h2>
                <ul className="flex flex-col gap-2 text-sm leading-relaxed text-muted-foreground">
                  {article.objectives.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </header>
          <div className="mx-auto mt-7 max-w-[72ch] xl:hidden">
            <TableOfContents outline={outline} compact />
          </div>
          <div className="mx-auto max-w-[72ch] min-w-0 text-[17px] leading-[1.85] [overflow-wrap:anywhere] text-foreground/85 [&_.katex]:text-[1.05em] [&_.katex-display]:my-7 [&_.katex-display]:overflow-x-auto [&_.katex-display]:overflow-y-hidden [&_.katex-display]:py-3">
            <Content />
          </div>
          <section
            id="sources"
            className="mx-auto mt-16 max-w-[72ch] scroll-mt-28 border-t pt-10"
          >
            <h2 className="text-2xl font-medium tracking-tight">
              Sources & further reading
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              External work informing these study notes. Inclusion does not
              imply authorship, affiliation, or endorsement.
            </p>
            <ul className="mt-6 flex flex-col gap-5">
              {article.sources.map((id) => {
                const source = sources[id]
                return source ? (
                  <li key={id}>
                    <p className="mb-1 text-xs text-muted-foreground">
                      {source.kind}
                    </p>
                    <a
                      href={source.url}
                      className="inline-flex items-start gap-2 text-sm leading-relaxed font-medium underline decoration-border underline-offset-4 hover:text-primary"
                    >
                      {source.title}
                      <ArrowUpRight
                        className="mt-1 size-3.5 shrink-0"
                        aria-hidden="true"
                      />
                    </a>
                  </li>
                ) : null
              })}
            </ul>
          </section>
          <section
            id="related-reading"
            className="mx-auto mt-12 max-w-[72ch] scroll-mt-28 border-t pt-8"
          >
            <h2 className="text-xl font-medium">Continue the connections</h2>
            <div className="mt-5 flex flex-wrap gap-3">
              {article.related.map((slug) => (
                <Link
                  key={slug}
                  href={`/research/${slug}`}
                  className="rounded-full border px-4 py-2.5 text-sm text-muted-foreground hover:border-primary hover:text-primary"
                >
                  {findArticle(slug)?.shortTitle} ↗
                </Link>
              ))}
            </div>
          </section>
          <nav
            aria-label="Reading order"
            className="mx-auto mt-12 grid max-w-[72ch] gap-4 border-t pt-7 sm:grid-cols-2"
          >
            {previous ? (
              <Link
                href={`/research/${previous.slug}`}
                className="flex items-center gap-3 py-3 text-sm"
              >
                <ArrowLeft className="size-4 shrink-0" aria-hidden="true" />
                <span>
                  <span className="mb-1 block text-xs text-muted-foreground">
                    Previous topic
                  </span>
                  {previous.shortTitle}
                </span>
              </Link>
            ) : (
              <span />
            )}
            {next && (
              <Link
                href={`/research/${next.slug}`}
                className="flex items-center justify-end gap-3 py-3 text-right text-sm"
              >
                <span>
                  <span className="mb-1 block text-xs text-muted-foreground">
                    Next topic
                  </span>
                  {next.shortTitle}
                </span>
                <ArrowRight className="size-4 shrink-0" aria-hidden="true" />
              </Link>
            )}
          </nav>
        </article>
        <aside className="hidden min-w-0 xl:block">
          <div
            className="sticky top-28 max-h-[calc(100dvh-9rem)] overflow-y-auto overscroll-contain pb-8 [scrollbar-width:thin]"
            data-lenis-prevent
          >
            <TableOfContents outline={outline} />
          </div>
        </aside>
      </div>
    </main>
  )
}

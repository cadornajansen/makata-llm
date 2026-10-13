import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@workspace/ui/components/breadcrumb"
import { TableOfContents } from "@/components/research/navigation"
import { StudyMetadata } from "@/components/research/study-elements"
import { studyLoaders, getStudyOutline } from "@/lib/research/study-content"
import { studies, findStudy, studyReviewLabel } from "@/lib/research/studies"
import { studySources } from "@/lib/research/study-sources"
import { researchMetadata } from "@/lib/research/metadata"
import { site } from "@/lib/site"

type PageProps = { params: Promise<{ slug: string }> }
export const dynamicParams = false
export function generateStaticParams(): { slug: string }[] {
  return studies.map(({ slug }) => ({ slug }))
}
export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const study = findStudy((await params).slug)
  if (!study) notFound()
  return researchMetadata(
    `Research Report ${study.id}: ${study.shortTitle}`,
    study.abstract,
    `/research/studies/${study.slug}`
  )
}

export default async function StudyPage({
  params,
}: PageProps): Promise<React.ReactElement> {
  const study = findStudy((await params).slug)
  if (!study) notFound()
  const [{ default: Content }, outline] = await Promise.all([
    studyLoaders[study.slug](),
    getStudyOutline(study.slug),
  ])
  const url = `${site.url}/research/studies/${study.slug}`
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Article",
        "@id": `${url}#article`,
        headline: study.title,
        description: study.abstract,
        url,
        mainEntityOfPage: url,
        inLanguage: "en",
        identifier: `Makata Research Report ${study.id}`,
        genre: studyReviewLabel(study.reviewStatus),
        isAccessibleForFree: true,
        author: {
          "@type": "Organization",
          "@id": `${site.url}/#organization`,
          name: "Makata",
        },
        publisher: { "@id": `${site.url}/#organization` },
        image: `${url}/opengraph-image`,
        ...(study.publishedOn ? { datePublished: study.publishedOn } : {}),
        citation: study.sources
          .map((id) => studySources[id]?.url)
          .filter(Boolean),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Makata", item: site.url },
          {
            "@type": "ListItem",
            position: 2,
            name: "Research & Learning",
            item: `${site.url}/research`,
          },
          {
            "@type": "ListItem",
            position: 3,
            name: "Research Studies",
            item: `${site.url}/research/studies`,
          },
          {
            "@type": "ListItem",
            position: 4,
            name: `Report ${study.id}`,
            item: url,
          },
        ],
      },
    ],
  }
  return (
    <main
      id="research-main"
      tabIndex={-1}
      className="mx-auto max-w-[1240px] pt-8 pr-12 pl-5 outline-none sm:pr-14 sm:pl-8 xl:px-10"
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
            <BreadcrumbLink render={<Link href="/research/studies" />}>
              Studies
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Report {study.id}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="grid min-w-0 gap-10 xl:grid-cols-[minmax(0,1fr)_190px]">
        <article className="mx-auto w-full max-w-[72ch] min-w-0">
          <header>
            <p className="mb-5 text-xs font-medium tracking-[.12em] text-muted-foreground uppercase">
              Original research · Report {study.id}
            </p>
            <h1 className="text-[clamp(30px,4.5vw,52px)] leading-[1.12] font-medium tracking-[-.04em] text-balance">
              {study.title}
            </h1>
            <p className="mt-6 text-lg leading-[1.75] text-muted-foreground sm:text-xl">
              {study.subtitle}
            </p>
            <StudyMetadata study={study} />
            <Alert>
              <AlertDescription>
                This is an independent technical research report. It has not
                undergone formal peer review. Measurements, interpretation, and
                proposed work are distinguished below. Model weights are not
                released with these reports.
              </AlertDescription>
            </Alert>
          </header>
          <div className="mt-7 xl:hidden">
            <TableOfContents outline={outline} compact supplementalLinks={[]} />
          </div>
          <div className="min-w-0 text-[17px] leading-[1.85] [overflow-wrap:anywhere] text-foreground/85 [&_.katex]:text-[1.05em] [&_.katex-display]:my-7 [&_.katex-display]:overflow-x-auto [&_.katex-display]:overflow-y-hidden [&_.katex-display]:py-3">
            <Content />
          </div>
          <nav
            aria-label="Study navigation"
            className="mt-12 border-t pt-6 text-sm"
          >
            <Link
              href="/research/studies"
              className="inline-flex min-h-11 items-center text-primary"
            >
              ← All research studies
            </Link>
          </nav>
        </article>
        <aside className="hidden min-w-0 xl:block">
          <div
            className="sticky top-28 max-h-[calc(100dvh-9rem)] overflow-y-auto overscroll-contain pr-3 pb-8 [scrollbar-width:thin]"
            data-lenis-prevent
          >
            <TableOfContents outline={outline} supplementalLinks={[]} />
          </div>
        </aside>
      </div>
    </main>
  )
}

import Link from "next/link"
import { ArrowUpRight } from "lucide-react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@workspace/ui/components/breadcrumb"
import {
  studies,
  studyDate,
  studyReviewLabel,
  studyStatusLabel,
} from "@/lib/research/studies"
import { researchMetadata } from "@/lib/research/metadata"
import { site } from "@/lib/site"

const description =
  "Original Makata research studies: transparent methods, verified measurements, limitations, research decisions, and reproducible technical reports."
export const metadata = researchMetadata(
  "Research Studies",
  description,
  "/research/studies",
  "website"
)

export default function StudiesIndex(): React.ReactElement {
  const data = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Makata Research Studies",
    description,
    url: `${site.url}/research/studies`,
    isPartOf: { "@id": `${site.url}/#website` },
    mainEntity: {
      "@type": "ItemList",
      itemListElement: studies.map((study, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: study.title,
        url: `${site.url}/research/studies/${study.slug}`,
      })),
    },
  }
  return (
    <main
      id="research-main"
      tabIndex={-1}
      className="mx-auto max-w-[1200px] px-5 pt-12 outline-none sm:px-8 sm:pt-20"
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
            <BreadcrumbPage>Studies</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <header className="max-w-3xl pb-12 sm:pb-16">
        <h1 className="text-[clamp(40px,6vw,72px)] leading-[1.08] font-medium tracking-[-.05em]">
          Research, with the evidence attached.
        </h1>
        <p className="mt-7 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          Technical reports documenting what we investigated, why we chose a
          method, what we measured, and what remains uncertain.
        </p>
      </header>
      <div className="divide-y border-y">
        {studies.map((study) => (
          <article
            key={study.id}
            className="grid gap-7 py-10 sm:py-14 lg:grid-cols-[200px_minmax(0,1fr)]"
          >
            <div className="flex flex-col gap-3 text-sm">
              <p className="font-mono text-xs text-muted-foreground">
                RESEARCH REPORT {study.id}
              </p>
              <p>{studyStatusLabel(study.status)}</p>
              <p className="leading-relaxed text-muted-foreground">
                {study.completedOn && (
                  <>
                    Completed{" "}
                    <time dateTime={study.completedOn}>
                      {studyDate(study.completedOn)}
                    </time>
                  </>
                )}
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {studyReviewLabel(study.reviewStatus)}
              </p>
            </div>
            <div className="min-w-0">
              <h2 className="text-2xl leading-tight font-medium tracking-tight sm:text-3xl">
                <Link
                  href={`/research/studies/${study.slug}`}
                  className="hover:text-primary"
                >
                  {study.shortTitle}
                </Link>
              </h2>
              <p className="mt-5 max-w-3xl leading-[1.85] text-muted-foreground">
                {study.abstract}
              </p>
              <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
                <div>
                  <dt className="mb-1 font-medium">Research area</dt>
                  <dd className="text-muted-foreground">{study.category}</dd>
                </div>
                <div>
                  <dt className="mb-1 font-medium">Methods</dt>
                  <dd className="leading-relaxed text-muted-foreground">
                    {study.methods.join(" · ")}
                  </dd>
                </div>
                <div>
                  <dt className="mb-1 font-medium">Checkpoints</dt>
                  <dd className="leading-relaxed text-muted-foreground">
                    {study.models.join("; ")}
                  </dd>
                </div>
                <div>
                  <dt className="mb-1 font-medium">Dataset</dt>
                  <dd className="text-muted-foreground">
                    {study.datasets.join("; ")}
                  </dd>
                </div>
              </dl>
              <Link
                href={`/research/studies/${study.slug}`}
                className="mt-6 inline-flex min-h-11 items-center gap-2 font-medium text-primary"
              >
                Read Report {study.id}
                <ArrowUpRight className="size-4" aria-hidden="true" />
              </Link>
            </div>
          </article>
        ))}
      </div>
      <section className="max-w-3xl pt-10">
        <h2 className="text-xl font-medium">How to read this archive</h2>
        <p className="mt-4 leading-relaxed text-muted-foreground">
          Planned research has a defined intention; in-progress work has not yet
          met its completion criteria. Completed technical reports document
          finished work. Peer review is a separate status requiring verifiable
          external review. Both reports are independent technical reports and
          have not undergone formal peer review.
        </p>
        <p className="mt-4 leading-relaxed text-muted-foreground">
          The{" "}
          <Link
            href="/research"
            className="font-medium text-primary underline underline-offset-4"
          >
            learning library
          </Link>{" "}
          explains established methods. This archive presents Makata's own
          experimental measurements. An internal QLoRA adapter has been trained
          and evaluated; a reliable comprehension gain is not established, and
          model weights have not been released.
        </p>
      </section>
    </main>
  )
}

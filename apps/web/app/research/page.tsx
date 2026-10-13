import Link from "next/link"
import { ArrowDown, ArrowUpRight, BookOpen } from "lucide-react"
import { buttonVariants } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import { articles, groups } from "@/lib/research/catalog"
import { researchMetadata } from "@/lib/research/metadata"
import { site } from "@/lib/site"

const description =
  "An open learning library on the mathematics, models, data, and methods behind Philippine-language AI research. Explore eight illustrated technical articles."
export const metadata = researchMetadata(
  "Research & Learning",
  description,
  "/research"
)

export default function ResearchIndex(): React.ReactElement {
  const data = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Makata Research & Learning",
    url: `${site.url}/research`,
    description,
    isPartOf: { "@id": `${site.url}/#website` },
    mainEntity: {
      "@type": "ItemList",
      itemListElement: articles.map((article, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: article.title,
        url: `${site.url}/research/${article.slug}`,
      })),
    },
  }
  return (
    <main
      id="research-main"
      tabIndex={-1}
      className="mx-auto max-w-[1200px] px-5 outline-none sm:px-8"
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(data).replace(/</g, "\\u003c"),
        }}
      />
      <section className="grid gap-10 pt-16 pb-14 sm:pt-24 sm:pb-20 lg:grid-cols-[1.6fr_1fr] lg:items-end">
        <div>
          <p className="mb-6 flex items-center gap-2.5 text-xs font-medium tracking-[.14em] text-muted-foreground uppercase">
            <BookOpen className="size-4" aria-hidden="true" />
            Research & Learning
          </p>
          <h1 className="max-w-3xl text-[clamp(42px,5.5vw,72px)] leading-[1.07] font-medium tracking-[-.05em]">
            Understanding
            <br />
            <span className="text-muted-foreground">what we’re building.</span>
          </h1>
        </div>
        <div className="max-w-lg">
          <p className="text-lg leading-relaxed text-muted-foreground">
            A growing body of study notes on the mathematics, models, and
            methods behind language AI. Start with an idea. Work through it. See
            it move.
          </p>
          <a
            href="#library"
            className={cn(
              buttonVariants({ variant: "outline" }),
              "mt-7 min-h-11 gap-3 rounded-full px-5"
            )}
          >
            Explore the library
            <ArrowDown data-icon="inline-end" aria-hidden="true" />
          </a>
        </div>
      </section>
      <div className="grid gap-6 border-y py-7 text-sm sm:grid-cols-3">
        <p>
          <span className="mb-2 block font-medium">Eight connected topics</span>
          <span className="text-muted-foreground">
            From mathematical foundations to a defensible experiment.
          </span>
        </p>
        <p>
          <span className="mb-2 block font-medium">
            Learn by changing things
          </span>
          <span className="text-muted-foreground">
            Worked examples, equations, and interactive SVG explanations.
          </span>
        </p>
        <p>
          <span className="mb-2 block font-medium">Evidence stays visible</span>
          <span className="text-muted-foreground">
            Primary sources and explicit assumptions throughout.
          </span>
        </p>
      </div>
      <div id="library" className="scroll-mt-28">
        {groups.map((group, groupIndex) => (
          <section
            key={group}
            className="grid gap-7 border-b py-12 sm:py-16 lg:grid-cols-[220px_1fr]"
          >
            <div>
              <p className="mb-3 text-xs text-muted-foreground">
                0{groupIndex + 1}
              </p>
              <h2 className="text-2xl font-medium tracking-tight">{group}</h2>
              <p className="mt-3 max-w-64 text-sm leading-relaxed text-muted-foreground">
                {group === "Foundations"
                  ? "Build the language of learning, then turn it into code."
                  : group === "Models"
                    ? "Understand the architecture and what adaptation changes."
                    : "Make data, evidence, and computing choices you can explain."}
              </p>
            </div>
            <div className="flex flex-col divide-y">
              {articles
                .filter((article) => article.group === group)
                .map((article) => (
                  <Link
                    key={article.slug}
                    href={`/research/${article.slug}`}
                    className="group flex items-start justify-between gap-6 rounded-sm py-7 first:pt-0 last:pb-0"
                  >
                    <div>
                      <h3 className="text-xl font-medium tracking-tight group-hover:text-primary sm:text-2xl">
                        {article.title}
                      </h3>
                      <p className="mt-3 max-w-2xl text-base leading-relaxed text-muted-foreground">
                        {article.abstract}
                      </p>
                      <p className="mt-4 text-xs text-muted-foreground">
                        Read, calculate, explore
                      </p>
                    </div>
                    <ArrowUpRight
                      className="mt-1 size-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 motion-reduce:transition-none"
                      aria-hidden="true"
                    />
                  </Link>
                ))}
            </div>
          </section>
        ))}
      </div>
      <section className="mt-12 grid gap-6 rounded-xl bg-secondary p-6 sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="max-w-2xl">
          <p className="mb-3 text-xs font-medium tracking-wider text-muted-foreground uppercase">
            Original Makata research
          </p>
          <h2 className="text-2xl font-medium tracking-tight">
            From learning the methods to documenting the evidence.
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Report 001 documents our Tagalog comprehension baselines. Report 002
            follows dataset screening, QLoRA training, and paired evaluation: an
            observed increase whose uncertainty includes no improvement. Both
            include methods, evidence, and limitations.
          </p>
        </div>
        <Link
          href="/research/studies"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "min-h-11 gap-2 self-start rounded-full"
          )}
        >
          Research Studies
          <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
        </Link>
      </section>
      <section className="max-w-2xl pt-12">
        <h2 className="text-xl font-medium">
          Study notes, with a research purpose.
        </h2>
        <p className="mt-4 leading-relaxed text-muted-foreground">
          These articles explain established ideas and external research as we
          build Makata’s foundations. Interactive examples are small teaching
          models, not benchmark results. Original measurements from Makata’s
          internal experimental adapter belong in Research Studies. Its weights
          remain private, and a reliable comprehension gain is not established.
        </p>
      </section>
    </main>
  )
}

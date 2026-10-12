import type { ReactElement } from "react"
import Image from "next/image"
import Link from "next/link"
import {
  ArrowDown,
  ArrowUpRight,
  Cpu,
  Database,
  Languages,
  Network,
  ScanLine,
  type LucideIcon,
} from "lucide-react"

import { buttonVariants } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import { ParticleWave } from "@/components/particle-wave"

const pageWidth =
  "mx-auto w-[calc(100%_-_96px)] max-w-[1200px] max-[1000px]:w-[calc(100%_-_64px)] max-[700px]:w-[calc(100%_-_40px)]"
const sectionSpacing = "py-[108px] max-[700px]:py-[72px]"
const eyebrow =
  "mb-6 text-xs leading-normal font-medium tracking-[.12em] text-muted-foreground uppercase max-[700px]:mb-[18px] max-[700px]:text-[11px]"
const sectionHeading =
  "text-[clamp(32px,3.15vw,44px)] leading-[1.16] font-medium tracking-[-.045em] text-balance max-[700px]:text-[35px] max-[380px]:text-[31px]"
const introCopy =
  "flex flex-col gap-5 pt-[42px] text-[17px] leading-[1.75] text-pretty text-muted-foreground max-[700px]:gap-[18px] max-[700px]:pt-0 max-[700px]:text-base"
const navLink =
  "inline-flex min-h-11 items-center text-sm text-muted-foreground hover:text-foreground"
const actionLink =
  "min-h-12 gap-3 rounded-full px-6 has-data-[icon=inline-end]:pe-6 max-[700px]:px-5 max-[700px]:has-data-[icon=inline-end]:pe-5"

type ResearchDirection = {
  title: string
  description: string
  icon: LucideIcon
}

const researchDirections: readonly ResearchDirection[] = [
  {
    title: "Philippine-language models",
    description:
      "Investigating how language models understand, generate, and reason in Filipino and Taglish, including the ways we move between languages.",
    icon: Languages,
  },
  {
    title: "Language datasets",
    description:
      "Exploring the collection, curation, and documentation of Philippine-language data, with careful attention to provenance, privacy, and licensing.",
    icon: Database,
  },
  {
    title: "Training & adaptation",
    description:
      "Studying open-weight models and controlled adaptation experiments, while building the knowledge needed for original model research.",
    icon: Network,
  },
  {
    title: "Independent evaluation",
    description:
      "Planning reproducible evaluations that make capabilities, limitations, and performance in Philippine contexts visible.",
    icon: ScanLine,
  },
  {
    title: "Efficient, local AI",
    description:
      "Investigating smaller models and efficient approaches that could run on accessible hardware and locally controlled infrastructure.",
    icon: Cpu,
  },
]

const principles = [
  {
    title: "Reproducible by design",
    description:
      "Document methods, configurations, and limitations so that others can understand and eventually repeat our experiments.",
  },
  {
    title: "Language in context",
    description:
      "Treat linguistic nuance, code-switching, and cultural knowledge as central research questions.",
  },
  {
    title: "Evidence before claims",
    description:
      "Evaluate against clear baselines. Report regressions alongside improvements, and distinguish plans from demonstrated results.",
  },
  {
    title: "Responsible foundations",
    description:
      "Respect data rights and privacy. Be explicit about model origins and the difference between adaptation and training from scratch.",
  },
] as const

function Wordmark(): ReactElement {
  return (
    <a
      className="inline-flex min-h-11 items-center gap-2.5 text-[27px] font-semibold tracking-[-1.3px] max-[700px]:text-[25px]"
      href="#top"
      aria-label="Makata home"
    >
      <Image
        src="/makata.svg"
        width={4000}
        height={3335}
        className="h-auto w-[34px] shrink-0"
        alt=""
        unoptimized
      />
      <span>Makata</span>
    </a>
  )
}

function SiteHeader(): ReactElement {
  return (
    <header
      className={cn(
        pageWidth,
        "relative z-2 flex min-h-[100px] items-center justify-between gap-6 max-[700px]:min-h-[120px] max-[700px]:flex-wrap max-[700px]:gap-x-5 max-[700px]:gap-y-2 max-[700px]:pt-4 max-[700px]:pb-2"
      )}
      id="top"
    >
      <Wordmark />
      <nav
        className="flex items-center gap-8 max-[1000px]:gap-5 max-[700px]:order-3 max-[700px]:w-full max-[700px]:justify-center max-[700px]:gap-[26px] max-[380px]:gap-[18px]"
        aria-label="Main navigation"
      >
        <Link className={cn(navLink, "max-[700px]:text-[13px]")} href="/research">
          Research
        </Link>
        <a className={cn(navLink, "max-[700px]:text-[13px]")} href="#approach">
          Our approach
        </a>
        <a className={cn(navLink, "max-[700px]:text-[13px]")} href="#status">
          Where we are
        </a>
      </nav>
      <a
        href="#collaboration"
        className={cn(
          buttonVariants({ variant: "outline" }),
          "min-h-[42px] gap-3 rounded-full px-5 has-data-[icon=inline-end]:pe-5 max-[700px]:min-h-10 max-[700px]:px-4 max-[700px]:has-data-[icon=inline-end]:pe-4"
        )}
      >
        Let&apos;s talk{" "}
        <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
      </a>
    </header>
  )
}

function Hero(): ReactElement {
  return (
    <section
      className="relative isolate flex min-h-[725px] items-center overflow-clip pt-[78px] pb-[135px] max-[1000px]:min-h-[665px] max-[1000px]:pt-[76px] max-[1000px]:pb-28 max-[700px]:min-h-[650px] max-[700px]:pt-[62px] max-[700px]:pb-[100px]"
      aria-labelledby="hero-heading"
    >
      <div
        className={cn(
          pageWidth,
          "relative z-1 text-center motion-safe:animate-in motion-safe:duration-700 motion-safe:ease-[cubic-bezier(.16,1,.3,1)] motion-safe:fade-in motion-safe:slide-in-from-bottom-3"
        )}
      >
        <h1
          className="mx-auto max-w-[1150px] text-[clamp(44px,5.25vw,76px)] leading-[1.08] font-medium tracking-[-.055em] text-balance max-[1000px]:text-[clamp(44px,6vw,64px)] max-[700px]:text-[clamp(34px,8.1vw,54px)] max-[700px]:leading-[1.1] max-[700px]:tracking-[-.05em]"
          id="hero-heading"
        >
          <span className="block">Building the foundations</span>
          <span className="block font-extralight text-muted-foreground">
            of Philippine intelligence.
          </span>
        </h1>
        <p className="mx-auto mt-7 max-w-[555px] text-lg leading-[1.65] text-pretty text-muted-foreground max-[700px]:mt-6 max-[700px]:max-w-[420px] max-[700px]:text-base max-[700px]:leading-[1.7]">
          Makata is an independent Filipino AI research initiative exploring
          language, local knowledge, and the foundations of intelligence we can
          help build ourselves.
        </p>
        <div className="mt-[30px] flex flex-wrap justify-center gap-3 max-[700px]:mt-[26px] max-[700px]:gap-2.5 max-[380px]:flex-col max-[380px]:items-center max-[380px]:[&_a]:w-full max-[380px]:[&_a]:max-w-60">
          <a
            href="#research"
            className={cn(buttonVariants({ size: "lg" }), actionLink)}
          >
            Explore our research{" "}
            <ArrowDown data-icon="inline-end" aria-hidden="true" />
          </a>
          <a
            href="#collaboration"
            className={cn(
              buttonVariants({ variant: "outline", size: "lg" }),
              actionLink
            )}
          >
            Connect with us{" "}
            <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
          </a>
        </div>
        <p className="mt-[26px] text-xs text-muted-foreground max-[700px]:mx-auto max-[700px]:max-w-60 max-[700px]:text-[11px] max-[700px]:leading-[1.6]">
          Filipino-first. Culturally-aware
        </p>
      </div>
    </section>
  )
}

function Purpose(): ReactElement {
  return (
    <section
      className={cn(pageWidth, sectionSpacing)}
      aria-labelledby="purpose-heading"
    >
      <div className="grid grid-cols-2 items-start gap-[90px] max-[1000px]:gap-[42px] max-[700px]:grid-cols-1 max-[700px]:gap-[30px]">
        <div>
          <p className={eyebrow}>Why Makata exists</p>
          <h2 className={sectionHeading} id="purpose-heading">
            A place for our languages.
            <br />A role in our own future.
          </h2>
        </div>
        <div className={introCopy}>
          <p>
            Language carries more than information. It carries how we think, the
            things we know, and the context that makes us understood. Philippine
            languages deserve a deeper place in AI research.
          </p>
          <p>
            We want to help the Philippines build the capability to create,
            study, and operate AI—not only use it. That begins with patient,
            independent work, informed by the wider research community.
          </p>
        </div>
      </div>
      <div className="mt-[68px] grid grid-cols-3 gap-12 border-t pt-[34px] max-[700px]:mt-9 max-[700px]:grid-cols-1 max-[700px]:gap-[26px] max-[700px]:pt-[30px] [&_h3]:mb-3 [&_h3]:text-[19px] [&_h3]:font-medium [&_h3]:tracking-[-.025em] max-[700px]:[&_h3]:mb-2 [&_p]:max-w-[340px] [&_p]:text-[15px] [&_p]:leading-[1.7] [&_p]:text-muted-foreground max-[700px]:[&_p]:max-w-none">
        <article>
          <h3>Representation</h3>
          <p>
            More room for Filipino, Taglish, and the language we use in everyday
            life.
          </p>
        </article>
        <article>
          <h3>Research capacity</h3>
          <p>
            Local knowledge and engineering skills to investigate the models
            behind the applications.
          </p>
        </article>
        <article>
          <h3>Greater independence</h3>
          <p>
            The long-term ability to make informed choices about our data,
            models, and infrastructure.
          </p>
        </article>
      </div>
    </section>
  )
}

function Research(): ReactElement {
  return (
    <section
      id="research"
      className={cn(sectionSpacing, "bg-secondary")}
      aria-labelledby="research-heading"
    >
      <div className={pageWidth}>
        <div className="mb-[54px] grid grid-cols-2 items-end gap-[90px] max-[1000px]:gap-[42px] max-[700px]:mb-8 max-[700px]:grid-cols-1 max-[700px]:gap-[30px]">
          <div>
            <p className={eyebrow}>Research directions</p>
            <h2 className={sectionHeading} id="research-heading">
              Small beginnings.
              <br />
              Foundational questions.
            </h2>
          </div>
          <p className={cn(introCopy, "pt-0")}>
            Our initial focus is Filipino and Taglish. These are the areas we
            intend to investigate as our research capabilities develop.
          </p>
        </div>
        <div>
          {researchDirections.map(({ title, description, icon: Icon }) => (
            <article
              className="grid grid-cols-2 items-start gap-[90px] border-t py-[29px] max-[1000px]:gap-[42px] max-[700px]:grid-cols-1 max-[700px]:gap-3.5 max-[700px]:py-[26px]"
              key={title}
            >
              <div className="flex items-center gap-[23px] pt-[3px] max-[700px]:gap-4">
                <Icon
                  className="shrink-0 text-muted-foreground"
                  size={23}
                  strokeWidth={1.4}
                  aria-hidden="true"
                />
                <h3 className="text-[23px] leading-[1.25] font-medium tracking-[-.025em] max-[700px]:text-[22px]">
                  {title}
                </h3>
              </div>
              <p className="max-w-[550px] text-base leading-[1.7] text-muted-foreground max-[700px]:text-[15px]">
                {description}
              </p>
            </article>
          ))}
        </div>
        <p className="mt-2.5 border-t pt-6 text-[13px] leading-[1.6] text-muted-foreground max-[700px]:text-xs">
          Other Philippine languages are a longer-term direction, guided by
          suitable datasets and language expertise.
        </p>
      </div>
    </section>
  )
}

function Approach(): ReactElement {
  return (
    <section
      id="approach"
      className={cn(
        pageWidth,
        sectionSpacing,
        "grid grid-cols-[.85fr_1.15fr] gap-28 max-[1000px]:gap-15 max-[700px]:grid-cols-1 max-[700px]:gap-[30px]"
      )}
      aria-labelledby="approach-heading"
    >
      <div>
        <p className={eyebrow}>Our approach</p>
        <h2 className={sectionHeading} id="approach-heading">
          Work that can
          <br />
          be examined.
        </h2>
        <p className="mt-6 max-w-[330px] text-[17px] leading-[1.7] text-pretty text-muted-foreground max-[700px]:max-w-[420px]">
          Credibility comes from how the research is done—and what we are
          willing to make clear.
        </p>
        <div className="mt-[52px] max-w-80 max-[700px]:mt-[30px]">
          <span
            className="block text-[50px] leading-[1.15] tracking-[-.05em] max-[700px]:text-[40px]"
            lang="fil"
          >
            makata
          </span>
          <span className="mt-[5px] block text-xs text-muted-foreground">
            Filipino noun · poet
          </span>
          <p className="mt-4 text-sm leading-[1.6] text-muted-foreground">
            A name rooted in language, expression, and the knowledge we carry.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-2 content-center gap-x-[42px] gap-y-[52px] max-[1000px]:gap-x-7 max-[1000px]:gap-y-9 max-[700px]:gap-x-6 max-[700px]:pt-[18px] max-[380px]:grid-cols-1">
        {principles.map(({ title, description }) => (
          <article key={title}>
            <span
              className="mb-[22px] block h-0.5 w-[26px] bg-primary"
              aria-hidden="true"
            />
            <h3 className="mb-[15px] text-[21px] leading-[1.3] font-medium tracking-[-.025em] max-[700px]:text-xl">
              {title}
            </h3>
            <p className="text-[15px] leading-[1.75] text-muted-foreground">
              {description}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}

function ResearchStatus(): ReactElement {
  return (
    <section id="status" className={pageWidth} aria-labelledby="status-heading">
      <div className="rounded-3xl bg-secondary p-[58px] max-[1000px]:p-10 max-[700px]:rounded-[20px] max-[700px]:px-6 max-[700px]:py-[30px]">
        <div className="grid grid-cols-2 gap-16 max-[1000px]:gap-10 max-[700px]:grid-cols-1 max-[700px]:gap-[30px]">
          <div>
            <p className={eyebrow}>Where we are</p>
            <h2
              className="text-[clamp(30px,2.8vw,38px)] leading-[1.16] font-medium tracking-[-.045em] text-balance"
              id="status-heading"
            >
              At the beginning,
              <br />
              with a clear direction.
            </h2>
          </div>
          <div className="flex flex-col gap-[18px] text-[15px] leading-[1.7] text-muted-foreground">
            <p className="flex items-center gap-2.5 font-medium text-foreground">
              <span
                className="size-[7px] rounded-full bg-primary"
                aria-hidden="true"
              />
              Foundational stage
            </p>
            <p>
              We are establishing Makata&apos;s research environment,
              documentation, and public identity.
            </p>
            <p>
              Next comes defining manageable baseline experiments, evaluating
              candidate open-weight models, and investigating appropriately
              sourced data.
            </p>
          </div>
        </div>
        <p className="mt-[38px] border-t pt-[26px] text-[13px] leading-[1.7] text-muted-foreground max-[700px]:mt-[26px] max-[700px]:pt-[22px]">
          <strong className="font-medium text-foreground">
            No Makata model has been trained or publicly released.
          </strong>{" "}
          Baseline evaluations and model adaptation are planned work.
        </p>
      </div>
    </section>
  )
}

function Collaboration(): ReactElement {
  return (
    <section
      id="collaboration"
      className={cn(
        pageWidth,
        "pt-32 pb-[118px] text-center max-[700px]:pt-[90px] max-[700px]:pb-[78px]"
      )}
      aria-labelledby="collaboration-heading"
    >
      <p className={eyebrow}>An open invitation</p>
      <h2
        className="text-[clamp(36px,4vw,56px)] leading-[1.16] font-medium tracking-[-.045em] text-balance max-[700px]:text-[38px]"
        id="collaboration-heading"
      >
        Good research begins
        <br />
        with a conversation.
      </h2>
      <p className="mx-auto mt-6 mb-[30px] max-w-[535px] text-[17px] leading-[1.7] text-pretty text-muted-foreground max-[700px]:text-base">
        Researchers, language specialists, engineers, universities, and
        institutions: if these questions matter to you, we&apos;d like to
        connect.
      </p>
      <a
        href="mailto:jansencadorna5@gmail.com"
        className={cn(buttonVariants({ size: "lg" }), actionLink)}
      >
        Explore a collaboration{" "}
        <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
      </a>
      <a
        className="mx-auto mt-5 block w-fit max-w-full py-2 text-[13px] wrap-anywhere text-muted-foreground hover:text-foreground"
        href="mailto:jansencadorna5@gmail.com"
      >
        jansencadorna5@gmail.com
      </a>
    </section>
  )
}

function SiteFooter(): ReactElement {
  return (
    <footer className={cn(pageWidth, "border-t pt-9 pb-7")}>
      <div className="flex items-center justify-between gap-[30px] max-[700px]:flex-col max-[700px]:items-start max-[700px]:gap-[22px]">
        <div>
          <Wordmark />
          <p className="mt-[9px] text-[13px] text-muted-foreground">
            Language. Knowledge. Possibility.
          </p>
        </div>
        <nav
          className="flex items-center gap-8 max-[700px]:gap-[26px]"
          aria-label="Footer navigation"
        >
          <Link className={navLink} href="/research">
            Research
          </Link>
          <a className={navLink} href="#approach">
            Our approach
          </a>
          <a className={navLink} href="#collaboration">
            Contact
          </a>
        </nav>
      </div>
      <div className="mt-[42px] flex justify-between gap-[30px] text-[11px] leading-[1.65] text-muted-foreground max-[700px]:mt-7 max-[700px]:flex-col max-[700px]:items-start max-[700px]:gap-[15px]">
        <p className="max-w-[640px]">
          Independent research in the Philippines. No institutional affiliation,
          funding, or endorsement is claimed.
        </p>
        <span className="shrink-0">© 2026 Makata</span>
      </div>
    </footer>
  )
}

export default function Page(): ReactElement {
  return (
    <div className="relative isolate">
      <ParticleWave />
      <a
        className="fixed top-3 left-3 z-10 -translate-y-[160%] rounded-lg bg-foreground px-5 py-3 text-background focus:translate-y-0"
        href="#main-content"
      >
        Skip to content
      </a>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        <Hero />
        <Purpose />
        <Research />
        <Approach />
        <ResearchStatus />
        <Collaboration />
      </main>
      <SiteFooter />
    </div>
  )
}

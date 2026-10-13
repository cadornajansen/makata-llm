import { Download, ArrowUpRight } from "lucide-react"
import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from "@workspace/ui/components/table"
import {
  studyDate,
  studyMaterialUrl,
  studyReviewLabel,
  studyStatusLabel,
  type Study,
} from "@/lib/research/studies"
import { studySources } from "@/lib/research/study-sources"

export function StudyMetadata({ study }: { study: Study }): React.ReactElement {
  return (
    <dl className="my-8 grid gap-5 border-y py-6 text-sm sm:grid-cols-2">
      {[
        ["Author", study.authors.join(", ")],
        ["Research status", studyStatusLabel(study.status)],
        [
          "Study completed",
          study.completedOn ? studyDate(study.completedOn) : "Not completed",
        ],
        ["Review classification", studyReviewLabel(study.reviewStatus)],
        ["Research area", study.category],
        [
          "Publication",
          study.publishedOn
            ? studyDate(study.publishedOn)
            : "Prepared for public release; publication date not assigned",
        ],
      ].map(([label, value]) => (
        <div key={label}>
          <dt className="mb-1 text-xs text-muted-foreground">{label}</dt>
          <dd className="leading-relaxed">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

type ComparisonResult = {
  model: string
  correct: number
  samples: number
  accuracy: number
  accuracy_standard_error: number
  wall_seconds: number
  inference_seconds: number
}

export function ResultComparison({
  results,
}: {
  results: readonly ComparisonResult[]
}): React.ReactElement {
  const plot = { left: 18, width: 520 }
  return (
    <figure className="my-8 min-w-0" aria-labelledby="result-caption">
      <svg
        viewBox="0 0 610 270"
        role="img"
        aria-labelledby="result-chart-title result-chart-description"
        className="h-auto w-full text-muted-foreground"
      >
        <title id="result-chart-title">
          Tagalog Belebele accuracy, complete 900-question test
        </title>
        <desc id="result-chart-description">
          {results
            .map(
              (result) =>
                `${result.model}: ${(result.accuracy * 100).toFixed(2)} percent, ${result.correct} of ${result.samples} correct.`
            )
            .join(" ")}{" "}
          The dashed reference at 25 percent is uniform random-choice
          expectation, not a significance test.
        </desc>
        {[0, 25, 50, 75, 100].map((tick) => (
          <g key={tick}>
            <line
              x1={plot.left + (plot.width * tick) / 100}
              x2={plot.left + (plot.width * tick) / 100}
              y1="32"
              y2="226"
              className={
                tick === 25 ? "stroke-muted-foreground" : "stroke-border"
              }
              strokeDasharray={tick === 25 ? "4 5" : undefined}
            />
            <text
              x={plot.left + (plot.width * tick) / 100}
              y="252"
              textAnchor="middle"
              className="fill-current text-[13px]"
            >
              {tick}%
            </text>
          </g>
        ))}
        {results.map((result, index) => {
          const y = 64 + index * 96
          return (
            <g key={result.model}>
              <text
                x={plot.left}
                y={y - 13}
                className="fill-foreground text-[15px]"
              >
                {result.model.split("/").at(-1)}
              </text>
              <rect
                x={plot.left}
                y={y}
                width={plot.width * result.accuracy}
                height="28"
                rx="3"
                className={
                  index === 0 ? "fill-primary" : "fill-muted-foreground"
                }
              />
              <text
                x={plot.left + plot.width * result.accuracy + 9}
                y={y + 19}
                className="fill-foreground text-[15px]"
              >
                {(result.accuracy * 100).toFixed(2)}%
              </text>
            </g>
          )
        })}
      </svg>
      <figcaption
        id="result-caption"
        className="mb-6 text-sm leading-relaxed text-muted-foreground"
      >
        Figure 1. Accuracy under the same zero-shot MCF protocol. The 25% line
        marks the expectation of uniformly choosing among four answers. It is
        not a statistical significance threshold.
      </figcaption>
      <div
        tabIndex={0}
        role="region"
        aria-label="Verified results table, scroll horizontally if needed"
        data-lenis-prevent
        className="min-w-0 overflow-x-auto rounded-lg border [&_[data-slot=table-container]]:overflow-visible"
      >
        <Table>
          <TableCaption>
            Verified original measurements. Standard errors are official harness
            outputs, in percentage points.
          </TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Checkpoint</TableHead>
              <TableHead scope="col">Correct</TableHead>
              <TableHead scope="col">Accuracy</TableHead>
              <TableHead scope="col">Standard error</TableHead>
              <TableHead scope="col">Wall time</TableHead>
              <TableHead scope="col">Inference</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {results.map((result) => (
              <TableRow key={result.model}>
                <TableHead scope="row">{result.model.split("/")[1]}</TableHead>
                <TableCell>
                  {result.correct}/{result.samples}
                </TableCell>
                <TableCell>{(result.accuracy * 100).toFixed(2)}%</TableCell>
                <TableCell>
                  {(result.accuracy_standard_error * 100).toFixed(4)} pp
                </TableCell>
                <TableCell>
                  {result.wall_seconds.toLocaleString("en", {
                    minimumFractionDigits: 3,
                    maximumFractionDigits: 3,
                  })}{" "}
                  s
                </TableCell>
                <TableCell>{result.inference_seconds.toFixed(6)} s</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </figure>
  )
}

export function StudyMaterials({
  study,
}: {
  study: Study
}): React.ReactElement {
  return (
    <ul className="my-7 flex list-none flex-col gap-5 p-0">
      {study.materials.map((material) => (
        <li key={material.file}>
          <a
            href={studyMaterialUrl(study.slug, material.file)}
            download
            className="inline-flex min-h-9 items-center gap-2 font-medium text-primary underline underline-offset-4"
          >
            <Download className="size-4 shrink-0" aria-hidden="true" />
            {material.title}
          </a>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            {material.description}
          </p>
        </li>
      ))}
    </ul>
  )
}

export function ResearchDecisions({
  study,
}: {
  study: Study
}): React.ReactElement {
  return (
    <div className="my-7">
      <Alert>
        <AlertDescription>
          These records were written retrospectively. They cite earlier recorded
          criteria and the retained local configuration freeze. The study was
          not publicly preregistered.
        </AlertDescription>
      </Alert>
      <ol className="mt-6 flex list-none flex-col gap-4 p-0">
        {study.decisions.map((decision) => (
          <li key={decision.id}>
            <a
              href={studyMaterialUrl(study.slug, decision.file)}
              className="flex min-h-11 items-center gap-3 font-medium text-primary underline underline-offset-4"
            >
              <span className="font-mono text-xs text-muted-foreground">
                {decision.id}
              </span>
              {decision.title}
              <ArrowUpRight className="size-4 shrink-0" aria-hidden="true" />
            </a>
          </li>
        ))}
      </ol>
    </div>
  )
}

export function StudyReferences({
  ids,
}: {
  ids: readonly string[]
}): React.ReactElement {
  return (
    <ol className="my-7 flex list-none flex-col gap-6 p-0">
      {ids.map((id, index) => {
        const source = studySources[id]
        if (!source) throw new Error(`Missing study source: ${id}`)
        return (
          <li id={`ref-${id}`} key={id} className="scroll-mt-28">
            <a
              href={source.url}
              className="font-medium text-primary underline underline-offset-4"
            >
              [{index + 1}] {source.title}
            </a>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {source.attribution}
            </p>
          </li>
        )
      })}
    </ol>
  )
}

import evidence from "@/content/research/studies/002-aya-qlora-evaluation.evidence.json"
import { ResultComparison } from "./study-elements"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@workspace/ui/components/table"

export function Report002Results(): React.ReactElement {
  return <ResultComparison results={evidence.models} />
}

export function Report002Uncertainty(): React.ReactElement {
  const { paired } = evidence
  const [low, high] = paired.uncertainty.difference_interval_percentage_points
  if (low === undefined || high === undefined)
    throw new Error("Missing paired interval")
  const x = (value: number): number => 50 + ((value + 5) / 11) * 510
  return (
    <figure className="my-8" aria-labelledby="paired-caption">
      <svg
        viewBox="0 0 610 180"
        role="img"
        aria-labelledby="paired-title paired-description"
        className="h-auto w-full"
      >
        <title id="paired-title">
          Paired accuracy difference with passage-bootstrap uncertainty
        </title>
        <desc id="paired-description">
          Observed difference {paired.difference_percentage_points.toFixed(2)}{" "}
          percentage points; paired 95 percent interval {low.toFixed(2)} to{" "}
          {high.toFixed(2)}. The interval includes zero; improvement is not
          statistically established.
        </desc>
        <line
          x1={x(0)}
          x2={x(0)}
          y1="25"
          y2="113"
          className="stroke-muted-foreground"
          strokeDasharray="4 5"
        />
        <line
          x1={x(low)}
          x2={x(high)}
          y1="70"
          y2="70"
          className="stroke-primary"
          strokeWidth="3"
        />
        {[low, high].map((value) => (
          <g key={value}>
            <line
              x1={x(value)}
              x2={x(value)}
              y1="60"
              y2="80"
              className="stroke-primary"
              strokeWidth="2"
            />
            <text
              x={x(value)}
              y="48"
              textAnchor="middle"
              className="fill-foreground text-[15px]"
            >
              {value.toFixed(2)}
            </text>
          </g>
        ))}
        <circle
          cx={x(paired.difference_percentage_points)}
          cy="70"
          r="6"
          className="fill-primary"
        />
        <text
          x={x(paired.difference_percentage_points)}
          y="104"
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          +{paired.difference_percentage_points.toFixed(2)}
        </text>
        {[-5, 0, 5].map((value) => (
          <text
            key={value}
            x={x(value)}
            y="140"
            textAnchor="middle"
            className="fill-muted-foreground text-[14px]"
          >
            {value > 0 ? "+" : ""}
            {value}
          </text>
        ))}
        <text
          x="305"
          y="169"
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          Accuracy difference, percentage points
        </text>
      </svg>
      <figcaption
        id="paired-caption"
        className="mt-3 text-sm leading-relaxed text-muted-foreground"
      >
        Figure 2. Paired 95% passage-cluster bootstrap interval,{" "}
        {paired.uncertainty.replicates.toLocaleString("en")} replicates, seed{" "}
        {paired.uncertainty.seed}. It spans zero. Conditional on this benchmark
        and one training run; it does not measure uncertainty across training
        seeds.
      </figcaption>
      <Table>
        <TableCaption>
          Paired correctness on the same {paired.sample_count} questions.
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Outcome</TableHead>
            <TableHead className="text-right">Questions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(paired.paired_counts).map(([key, count]) => (
            <TableRow key={key}>
              <TableCell>
                {{
                  both_correct: "Correct before and after",
                  improved: "Wrong before, correct after",
                  regressed: "Correct before, wrong after",
                  both_wrong: "Wrong before and after",
                }[key] ?? key}
              </TableCell>
              <TableCell className="text-right tabular-nums">{count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </figure>
  )
}

export function Report002Data(): React.ReactElement {
  const { aya } = evidence
  return (
    <Table>
      <TableCaption>
        Candidate preparation counts; candidates are not individually cleared
        training data.
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Disposition</TableHead>
          <TableHead className="text-right">Initial preparation</TableHead>
          <TableHead className="text-right">Revised v2</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {(
          [
            "original",
            "train",
            "validation",
            "quarantine",
            "exclusions",
          ] as const
        ).map((key) => (
          <TableRow key={key}>
            <TableCell className="capitalize">{key}</TableCell>
            <TableCell className="text-right tabular-nums">
              {aya.v1[key]}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {aya.v2[key]}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function Report002Training(): React.ReactElement {
  const { training } = evidence
  const rows = [
    [
      "Training examples / distinct groups",
      `${evidence.aya.selected_training} / ${evidence.aya.selected_groups}`,
    ],
    [
      "Individual agent observations / screening only",
      `${evidence.aya.individual_agent_observations} / ${evidence.aya.screening_only}`,
    ],
    ["Successful optimizer updates", training.metrics.optimizer_updates],
    [
      "First / final update training loss",
      `${training.metrics.initial_training_loss.toFixed(6)} / ${training.metrics.final_training_loss.toFixed(6)}`,
    ],
    [
      "Mean example loss during epoch",
      training.metrics.mean_training_loss.toFixed(6),
    ],
    [
      "Synchronized training runtime",
      `${training.metrics.training_seconds.toFixed(3)} s`,
    ],
    [
      "Peak allocated / reserved GPU memory",
      `${(training.metrics.peak_allocated_bytes / 2 ** 30).toFixed(3)} / ${(training.metrics.peak_reserved_bytes / 2 ** 30).toFixed(3)} GiB`,
    ],
    [
      "Trainable LoRA parameters",
      training.metrics.trainable_parameters.toLocaleString("en"),
    ],
    [
      "Fresh-process reload",
      `${training.reload.status}; equal tensors; max probe-logit error ${training.reload.maximum_absolute_logit_error}`,
    ],
  ]
  return (
    <Table>
      <TableCaption>
        Verified engineering measurements, not evidence of general language
        improvement.
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Measurement</TableHead>
          <TableHead>Observed value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map(([name, value]) => (
          <TableRow key={name}>
            <TableCell>{name}</TableCell>
            <TableCell className="tabular-nums">{value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function Report002Provenance(): React.ReactElement {
  const entries = [
    ["Base model revision", evidence.model.revision],
    ["Tokenizer revision", evidence.model.tokenizer_revision],
    ["Aya revision", evidence.aya.revision],
    ["Belebele revision", evidence.benchmark.revision],
    ["FilBench revision", evidence.protocol.filbench_revision],
    ["Aya original Parquet · SHA-256", evidence.aya.source_sha256],
    [
      "Selected training file · SHA-256 (private)",
      evidence.aya.selected_training_sha256,
    ],
    [
      "Final checkpoint 91 adapter · SHA-256 (private)",
      evidence.training.final_adapter_sha256,
    ],
    ...Object.entries(evidence.verification)
      .filter(([key]) => key.endsWith("sha256"))
      .map(([key, value]) => [key.replaceAll("_", " "), String(value)]),
  ]
  return (
    <dl className="my-7 flex flex-col gap-5 text-sm">
      {entries.map(([label, value]) => (
        <div key={label}>
          <dt className="mb-1 font-medium">{label}</dt>
          <dd className="font-mono text-xs leading-relaxed break-all text-muted-foreground">
            {value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

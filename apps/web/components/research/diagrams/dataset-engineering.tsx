"use client"

import { useState } from "react"
import { splitDataset } from "@/lib/research/math"
import fixtures from "@/lib/research/tokenization.json"
import {
  Choice,
  DataTable,
  Frame,
  number,
  Playback,
  Range,
  Reset,
  Scene,
  Stages,
  usePlayback,
  Values,
} from "./shared"

const documents = [
  { id: "A", permission: true, text: "  Magandang   umaga.  " },
  { id: "B", permission: true, text: "Magandang umaga." },
  {
    id: "C",
    permission: false,
    text: "Walang pahintulot para sa halimbawang ito.",
  },
  { id: "D", permission: true, text: "Nag-aaral ako ng AI." },
]

export function CleaningPipeline() {
  const playback = usePlayback(3)
  let records = documents
  if (playback.step >= 1)
    records = records.filter((record) => record.permission)
  if (playback.step >= 2)
    records = records.map((record) => ({
      ...record,
      text: record.text.trim().replace(/\s+/g, " "),
    }))
  if (playback.step >= 3)
    records = records.filter(
      (record, index, rows) =>
        rows.findIndex((other) => other.text === record.text) === index
    )
  return (
    <Frame
      containerRef={playback.ref}
      title="A traceable cleaning pipeline"
      description="Four handcrafted records illustrate source eligibility, whitespace normalization, and exact deduplication. The permission flags are hypothetical teaching metadata, not a licensing assessment of real sources."
    >
      <Stages
        active={playback.step}
        labels={[
          "Keep source records",
          "Check documented permission",
          "Normalize whitespace",
          "Deduplicate normalized text",
        ]}
        values={["4 records", "3 records", "3 records", "2 records"]}
      />
      <Playback playback={playback} />
      <DataTable
        caption="Records after the current cleaning stage"
        headers={["Source ID", "Eligible?", "Text (quoted)"]}
        rows={records.map((record) => [
          record.id,
          record.permission ? "yes" : "no",
          JSON.stringify(record.text),
        ])}
      />
      <Values
        rows={[
          ["Records remaining", records.length],
          [
            "Removed IDs",
            documents
              .filter(
                (record) =>
                  !records.some((remaining) => remaining.id === record.id)
              )
              .map((record) => record.id)
              .join(", ") || "none",
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Normalization makes A and B equal, so deduplication keeps A with its
        provenance. Real pipelines should retain a removal log and consider near
        duplicates; broad normalization can destroy meaningful code, formatting,
        or language distinctions.
      </p>
    </Frame>
  )
}

export function DatasetSplitExplorer() {
  const [train, setTrain] = useState(80)
  const [validation, setValidation] = useState(10)
  const counts = splitDataset(100, train, validation)
  return (
    <Frame
      title="Three splits, three different jobs"
      description="Allocate 100 illustrative document groups. Training updates weights; validation guides choices; test is held aside until the evaluation protocol is fixed. Each square represents one group."
    >
      <Scene
        title="Dataset partition allocation"
        description={`${counts.train} training, ${counts.validation} validation, ${counts.test} test groups.`}
        height={260}
      >
        {Array.from({ length: 100 }, (_, index) => (
          <rect
            key={index}
            x={70 + (index % 10) * 26}
            y={20 + Math.floor(index / 10) * 22}
            width={19}
            height={16}
            rx={3}
            className={
              index < counts.train
                ? "fill-blue-600"
                : index < counts.train + counts.validation
                  ? "fill-primary"
                  : "fill-muted-foreground"
            }
          />
        ))}
      </Scene>
      <div className="grid gap-5 sm:grid-cols-2">
        <Range
          label="Training percentage"
          value={train}
          min={50}
          max={90}
          onChange={(next) => {
            setTrain(next)
            setValidation((current) => Math.min(current, 95 - next))
          }}
        />
        <Range
          label="Validation percentage"
          value={validation}
          min={5}
          max={95 - train}
          onChange={setValidation}
        />
      </div>
      <Values
        rows={[
          ["Training · blue", counts.train],
          ["Validation · rose", counts.validation],
          ["Test · gray", counts.test],
          ["Total", counts.train + counts.validation + counts.test],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Ratios alone do not prevent leakage. Group related documents,
        conversations, authors, or time periods as required by your intended
        evaluation. Record the seed and split manifest.
      </p>
      <Reset
        onClick={() => {
          setTrain(80)
          setValidation(10)
        }}
      />
    </Frame>
  )
}

export function TokenizationComparison() {
  const [selected, setSelected] = useState(fixtures.examples[0]!.language)
  const example = fixtures.examples.find(
    (entry) => entry.language === selected
  )!
  const largest = Math.max(
    ...fixtures.examples.map((entry) => entry.ids.length)
  )
  return (
    <Frame
      title="Measure tokenization; do not assume equal cost"
      description="These fixed examples use the same verified tokenizer revision. Token counts vary with wording, script, vocabulary coverage, and normalization. A short example is not a language-wide efficiency benchmark."
    >
      <Scene
        title="Token counts by example"
        description={fixtures.examples
          .map((entry) => `${entry.language}: ${entry.ids.length} tokens`)
          .join("; ")}
        height={fixtures.examples.length * 64 + 30}
      >
        {fixtures.examples.map((entry, index) => (
          <g key={entry.language}>
            <text
              x={16}
              y={index * 64 + 22}
              className="fill-foreground text-[14px]"
            >
              {entry.language}
            </text>
            <rect
              x={16}
              y={index * 64 + 31}
              width={(entry.ids.length / largest) * 320}
              height={17}
              rx={4}
              className={
                entry.language === selected
                  ? "fill-primary"
                  : "fill-blue-600/60"
              }
            />
            <text
              x={350}
              y={index * 64 + 45}
              className="fill-foreground text-[14px]"
            >
              {entry.ids.length}
            </text>
          </g>
        ))}
      </Scene>
      <Choice
        label="Tokenization detail language"
        options={fixtures.examples.map((entry) => entry.language)}
        value={selected}
        onChange={setSelected}
      />
      <p className="m-0 rounded-xl bg-secondary p-3 text-sm">{example.text}</p>
      <div className="flex flex-wrap gap-1.5" aria-label="Token pieces">
        {example.pieces.map((piece, index) => (
          <span
            key={index}
            className="max-w-full rounded-md border border-border px-2 py-1 font-mono text-xs break-all"
          >
            {piece}
          </span>
        ))}
      </div>
      <Values
        rows={[
          ["Token count", example.ids.length],
          [
            "Whitespace-delimited words",
            example.text.trim().split(/\s+/).length,
          ],
          [
            "Tokens per whitespace word",
            number(
              example.ids.length / example.text.trim().split(/\s+/).length
            ),
          ],
        ]}
      />
      <p className="m-0 text-xs leading-relaxed break-all text-muted-foreground">
        {fixtures.model} · revision {fixtures.revision}. Whitespace words are a
        convenient denominator here, not a universal definition of a linguistic
        word.
      </p>
      <Reset onClick={() => setSelected(fixtures.examples[0]!.language)} />
    </Frame>
  )
}

export function ContaminationExplorer() {
  const [strategy, setStrategy] = useState("Random rows")
  const rows =
    strategy === "Source groups"
      ? [
          ["A", "Train", "Ang Maynila ay nasa Luzon."],
          ["A-copy", "Train", "Ang Maynila ay nasa Luzon."],
          ["A-paraphrase", "Train", "Nasa Luzon ang Maynila."],
          ["B", "Test", "Ang Cebu ay nasa Visayas."],
        ]
      : [
          ["A", "Train", "Ang Maynila ay nasa Luzon."],
          ...(strategy === "Exact deduplication"
            ? []
            : [["A-copy", "Test", "Ang Maynila ay nasa Luzon."]]),
          ["A-paraphrase", "Test", "Nasa Luzon ang Maynila."],
          ["B", "Test", "Ang Cebu ay nasa Visayas."],
        ]
  const leaked =
    strategy === "Source groups"
      ? 0
      : strategy === "Exact deduplication"
        ? 1
        : 2
  return (
    <Frame
      title="Leakage survives exact deduplication"
      description="A source family contains an original, an exact copy, and a paraphrase. Compare a hypothetical row split with deduplication and source-group splitting. This demonstrates overlap, not benchmark scores."
    >
      <Choice
        label="Split strategy"
        options={["Random rows", "Exact deduplication", "Source groups"]}
        value={strategy}
        onChange={setStrategy}
      />
      <Scene
        title="Cross-split source overlap"
        description={`${leaked} test records share the training source family.`}
        height={175}
      >
        <rect
          x={22}
          y={42}
          width={125}
          height={74}
          rx={10}
          className="fill-blue-600/15 stroke-blue-600"
        />
        <text
          x={84}
          y={74}
          textAnchor="middle"
          className="fill-foreground text-[16px]"
        >
          Train
        </text>
        <text
          x={84}
          y={98}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          family A
        </text>
        <path
          d="M155 80H245"
          strokeDasharray={leaked ? undefined : "5 5"}
          strokeWidth={3}
          className={leaked ? "stroke-primary" : "stroke-border"}
        />
        <text
          x={200}
          y={145}
          textAnchor="middle"
          className="fill-primary text-[14px]"
        >
          {leaked ? `${leaked} overlapping records` : "No shared source family"}
        </text>
        <rect
          x={254}
          y={42}
          width={125}
          height={74}
          rx={10}
          className="fill-secondary stroke-muted-foreground"
        />
        <text
          x={316}
          y={74}
          textAnchor="middle"
          className="fill-foreground text-[16px]"
        >
          Test
        </text>
        <text
          x={316}
          y={98}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          {leaked ? "families A + B" : "family B"}
        </text>
      </Scene>
      <DataTable
        caption="Illustrative document source and split manifest"
        headers={["Record", "Split", "Text"]}
        rows={rows}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Group splitting removes this known overlap, but does not prove a
        pretrained base model never saw the test content. Evaluate contamination
        at collection, split, pretraining, and benchmark levels.
      </p>
      <Reset onClick={() => setStrategy("Random rows")} />
    </Frame>
  )
}

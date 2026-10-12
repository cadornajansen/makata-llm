"use client"

import { useState } from "react"
import { motion } from "motion/react"
import { attention, attentionInputs, softmax } from "@/lib/research/math"
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
  useDiagramTransition,
  usePlayback,
  Values,
} from "./shared"

export function TokenizationExplorer() {
  const [exampleIndex, setExampleIndex] = useState(0)
  const example = fixtures.examples[exampleIndex]!
  const playback = usePlayback(example.ids.length)
  const vectors = [
    [0.2, -0.4],
    [0.8, 0.1],
    [-0.5, 0.6],
    [0.3, 0.9],
  ]
  return (
    <Frame
      containerRef={playback.ref}
      title="Text → token IDs → embedding lookup"
      description="The token IDs below come from the named tokenizer, not from splitting on spaces. The two-dimensional embedding vectors are explicit toy lookup entries, not extracted Qwen embeddings."
    >
      <Choice
        label="Example language"
        options={fixtures.examples.map((entry) => entry.language)}
        value={example.language}
        onChange={(language) => {
          setExampleIndex(
            fixtures.examples.findIndex((entry) => entry.language === language)
          )
          playback.reset()
        }}
      />
      <p className="m-0 rounded-xl bg-secondary p-4 text-base">
        {example.text}
      </p>
      <div className="flex flex-wrap gap-2" aria-label="Token pieces">
        {example.pieces.map((piece, index) => (
          <span
            key={index}
            className={`max-w-full rounded-md border px-2 py-1 font-mono text-sm break-all ${index < playback.step ? "border-primary bg-primary/10" : "border-border bg-secondary/50"}`}
          >
            {piece}
            <span className="sr-only">: token ID {example.ids[index]}</span>
          </span>
        ))}
      </div>
      <Playback playback={playback} />
      <DataTable
        headers={["Position", "Token ID", "Toy embedding"]}
        rows={example.ids.map((id, index) => [
          index,
          id,
          `[${vectors[index % 4]!.join(", ")}]`,
        ])}
        caption="Token positions, actual token IDs, and illustrative embedding entries"
      />
      <Scene
        title="Illustrative token embedding positions"
        description="Four toy embeddings on a two-dimensional coordinate plane. Real model embeddings have many more dimensions."
      >
        <path
          d="M55 130H360M200 220V20"
          className="fill-none stroke-muted-foreground"
        />
        {vectors.map(([x, y], index) => (
          <g key={index}>
            <circle
              cx={200 + x! * 140}
              cy={130 - y! * 100}
              r={5}
              className="fill-primary"
            />
            <text
              x={207 + x! * 140}
              y={125 - y! * 100}
              className="fill-foreground text-[15px]"
            >
              slot {index}
            </text>
          </g>
        ))}
        <text x={310} y={155} className="fill-muted-foreground text-[13px]">
          dimension 1
        </text>
        <text x={210} y={20} className="fill-muted-foreground text-[13px]">
          dimension 2
        </text>
      </Scene>
      <p className="m-0 text-xs leading-relaxed break-all text-muted-foreground">
        Tokenizer: {fixtures.model} · revision {fixtures.revision}. Repeated toy
        vectors here are a display simplification; production embedding tables
        have a learned row for each vocabulary ID.
      </p>
    </Frame>
  )
}

export function AttentionExplorer() {
  const [query, setQuery] = useState(2)
  const [causal, setCausal] = useState(true)
  const [head, setHead] = useState(0)
  const transition = useDiagramTransition()
  const result = attention(query, causal, head)
  const matrix = attentionInputs.tokens.map((_, index) =>
    attention(index, causal, head)
  )
  return (
    <Frame
      title="Attention is a calculated, normalized mixture"
      description="Choose a query token. Scores are q · k / √2; softmax turns them into nonnegative weights summing to 1. A causal mask excludes future positions. All Q, K, and V vectors here are small teaching examples."
    >
      <Choice
        label="Query token"
        options={attentionInputs.tokens}
        value={attentionInputs.tokens[query]!}
        onChange={(token) =>
          setQuery(
            attentionInputs.tokens.indexOf(
              token as (typeof attentionInputs.tokens)[number]
            )
          )
        }
      />
      <div className="grid gap-3">
        <Choice
          label="Attention masking"
          options={["Causal mask", "No mask"]}
          value={causal ? "Causal mask" : "No mask"}
          onChange={(next) => setCausal(next === "Causal mask")}
        />
        <Choice
          label="Attention head"
          options={["Head 1", "Head 2"]}
          value={head === 0 ? "Head 1" : "Head 2"}
          onChange={(next) => setHead(next === "Head 1" ? 0 : 1)}
        />
      </div>
      <Scene
        title="Attention matrix"
        description={`Rows are queries, columns are keys. Selected query: ${attentionInputs.tokens[query]}. Weights ${result.weights.map((value) => number(value)).join(", ")}.`}
        height={260}
      >
        {attentionInputs.tokens.map((token, index) => (
          <g key={token}>
            <text
              x={125 + index * 70}
              y={30}
              textAnchor="middle"
              className="fill-muted-foreground text-[12px]"
            >
              {token}
            </text>
            <text
              x={86}
              y={70 + index * 48}
              textAnchor="end"
              className="fill-muted-foreground text-[12px]"
            >
              {token}
            </text>
          </g>
        ))}
        {matrix.flatMap((row, i) =>
          row.weights.map((weight, j) => (
            <g key={`${i}-${j}`}>
              <motion.rect
                initial={false}
                animate={{ opacity: 0.08 + weight * 0.82 }}
                transition={transition}
                x={93 + j * 70}
                y={42 + i * 48}
                width={64}
                height={42}
                rx={5}
                className="fill-primary"
              />
              <text
                x={125 + j * 70}
                y={69 + i * 48}
                textAnchor="middle"
                className="fill-foreground text-[14px]"
              >
                {number(weight, 2)}
              </text>
            </g>
          ))
        )}
        <rect
          x={89}
          y={38 + query * 48}
          width={282}
          height={50}
          rx={6}
          className="fill-none stroke-foreground"
          strokeWidth={1.5}
        />
        <text
          x={230}
          y={252}
          textAnchor="middle"
          className="fill-muted-foreground text-[13px]"
        >
          Rows sum to 1; future masked cells are 0.
        </text>
      </Scene>
      <Scene
        title="Selected token relationships"
        description={`The selected query combines value vectors with weights ${result.weights.map((value) => number(value)).join(", ")}.`}
        height={170}
      >
        {result.weights.map((weight, index) => (
          <g key={index}>
            <motion.line
              initial={false}
              animate={{
                opacity: 0.15 + weight * 0.85,
                strokeWidth: 1 + weight * 9,
              }}
              transition={transition}
              x1={200}
              y1={130}
              x2={50 + index * 100}
              y2={45}
              className="stroke-primary"
            />
            <text
              x={50 + index * 100}
              y={24}
              textAnchor="middle"
              className="fill-foreground text-[13px]"
            >
              {attentionInputs.tokens[index]}
            </text>
            <circle
              cx={50 + index * 100}
              cy={45}
              r={5}
              className="fill-blue-600"
            />
          </g>
        ))}
        <circle cx={200} cy={130} r={7} className="fill-primary" />
        <text
          x={200}
          y={157}
          textAnchor="middle"
          className="fill-foreground text-[14px]"
        >
          query: {attentionInputs.tokens[query]}
        </text>
      </Scene>
      <DataTable
        headers={["Key", "K vector", "V vector", "Score", "Weight"]}
        rows={result.weights.map((weight, index) => [
          attentionInputs.tokens[index],
          attentionInputs.keys[index]!.join(", "),
          attentionInputs.values[index]!.join(", "),
          number(result.scores[index]!),
          number(weight),
        ])}
        caption="Exact attention inputs and calculated weights"
      />
      <Values
        rows={[
          [
            "Query vector (before head projection)",
            attentionInputs.queries[query]!.join(", "),
          ],
          [
            "Weighted value output",
            `[${result.output.map((value) => number(value)).join(", ")}]`,
          ],
          [
            "Sum of attention weights",
            number(result.weights.reduce((sum, value) => sum + value, 0)),
          ],
          [
            "Concatenate both head outputs",
            [
              ...attention(query, causal, 0).output,
              ...attention(query, causal, 1).output,
            ]
              .map((value) => number(value))
              .join(", "),
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Head 2 applies the toy query projection (q₁, q₂) → (q₂, −q₁). Real heads
        learn separate Q, K, and V projections. High attention weight is a
        mixing coefficient, not proof of linguistic importance.
      </p>
      <Reset
        onClick={() => {
          setQuery(2)
          setCausal(true)
          setHead(0)
        }}
      />
    </Frame>
  )
}

export function TransformerExplorer() {
  const playback = usePlayback(6)
  return (
    <Frame
      containerRef={playback.ref}
      title="Trace a decoder block without losing tensor shapes"
      description="A teaching decoder uses sequence length 4 and model width 8. This pre-norm diagram shows residual connections explicitly; an actual architecture may use different normalization, positional encodings, and feed-forward variants."
    >
      <Stages
        active={playback.step}
        labels={[
          "Token + position representation",
          "Normalize → causal attention",
          "Residual add: x + attention",
          "Normalize → feed-forward",
          "Residual add: x + feed-forward",
          "Final norm → vocabulary logits",
          "Sample → append → repeat",
        ]}
        values={[
          "4 × 8",
          "4 × 8",
          "4 × 8",
          "4 × 32 → 4 × 8",
          "4 × 8",
          "4 × |V|",
          "length becomes 5",
        ]}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Sequence axis", "4 token positions"],
          ["Residual stream width", "8 features per position"],
          ["Attention communication", "Across allowed token positions"],
          ["Feed-forward computation", "Independently at each position"],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Residual addition requires matching shapes. During autoregressive
        generation, use the final position’s logits for the next token; do not
        sample every position and overwrite the prompt.
      </p>
    </Frame>
  )
}

export function SamplingExplorer() {
  const [temperature, setTemperature] = useState(1)
  const playback = usePlayback(4)
  const vocabulary = ["wika", "agham", "modelo", "bansa"]
  const uniforms = [0.12, 0.68, 0.43, 0.89]
  const histories: string[] = []
  let logits = [2, 1, 0.2, -0.5]
  for (let step = 0; step < playback.step; step++) {
    const probabilities = softmax(logits, temperature)
    let cumulative = 0
    const selected = probabilities.findIndex((probability) => {
      cumulative += probability
      return uniforms[step]! < cumulative
    })
    histories.push(vocabulary[selected]!)
    logits = [0.5, 1.3, 0.2, -0.4].map(
      (value, index) => value + (index === (selected + 1) % 4 ? 1 : 0)
    )
  }
  const probabilities = softmax(logits, temperature)
  const transition = useDiagramTransition()
  return (
    <Frame
      containerRef={playback.ref}
      title="Temperature changes probabilities, not knowledge"
      description="A four-token toy vocabulary demonstrates normalized exp(logit / T). Step samples with fixed uniform draws for reproducibility, appends the token, and recalculates a simple illustrative conditional distribution. This is not an LLM output."
    >
      <Scene
        title="Next-token probabilities"
        description={vocabulary
          .map(
            (token, index) =>
              `${token}: ${number(probabilities[index]! * 100, 1)} percent`
          )
          .join("; ")}
      >
        {probabilities.map((probability, index) => (
          <g key={index}>
            <motion.rect
              initial={false}
              animate={{
                y: 190 - probability * 155,
                height: probability * 155,
              }}
              transition={transition}
              x={36 + index * 92}
              width={54}
              rx={4}
              className="fill-primary/70"
            />
            <text
              x={63 + index * 92}
              y={215}
              textAnchor="middle"
              className="fill-foreground text-[14px]"
            >
              {vocabulary[index]}
            </text>
            <text
              x={63 + index * 92}
              y={25}
              textAnchor="middle"
              className="fill-muted-foreground text-[14px]"
            >
              {number(probability * 100, 1)}%
            </text>
          </g>
        ))}
      </Scene>
      <Range
        label="Temperature T"
        value={temperature}
        min={0.1}
        max={2}
        step={0.1}
        onChange={(next) => {
          setTemperature(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          [
            "Generated toy continuation",
            histories.join(" → ") || "No tokens sampled yet",
          ],
          [
            "Logits for next position",
            logits.map((value) => number(value)).join(", "),
          ],
          [
            "Next fixed uniform draw",
            playback.step < 4 ? uniforms[playback.step] : "Sequence complete",
          ],
          [
            "Probability sum",
            number(probabilities.reduce((sum, value) => sum + value, 0)),
          ],
        ]}
      />
    </Frame>
  )
}

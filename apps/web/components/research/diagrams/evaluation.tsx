"use client"

import { useState } from "react"
import { metrics } from "@/lib/research/math"
import {
  DataTable,
  Frame,
  LineChart,
  number,
  Playback,
  Range,
  Reset,
  Scene,
  usePlayback,
  Values,
} from "./shared"

function percent(value: number | null): string {
  return value === null
    ? "undefined (zero denominator)"
    : `${number(value * 100, 1)}%`
}

export function ConfusionMatrixExplorer() {
  const [counts, setCounts] = useState([8, 2, 4, 6])
  const [tp, fp, fn, tn] = counts as [number, number, number, number]
  const result = metrics(tp, fp, fn, tn)
  const cells = [
    { label: "True positive", value: tp, x: 130, y: 72, correct: true },
    { label: "False negative", value: fn, x: 250, y: 72, correct: false },
    { label: "False positive", value: fp, x: 130, y: 165, correct: false },
    { label: "True negative", value: tn, x: 250, y: 165, correct: true },
  ]
  return (
    <Frame
      title="A confusion matrix explains the errors behind a score"
      description="Rows describe the true class; columns describe the predicted class. Counts are editable teaching values. Zero denominators remain undefined instead of silently becoming perfect scores."
    >
      <Scene
        title="Binary confusion matrix"
        description={`True positive ${tp}, false positive ${fp}, false negative ${fn}, true negative ${tn}.`}
        height={280}
      >
        <text
          x={183}
          y={30}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          Predicted +
        </text>
        <text
          x={303}
          y={30}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          Predicted −
        </text>
        <text
          x={111}
          y={117}
          textAnchor="end"
          className="fill-muted-foreground text-[14px]"
        >
          Actual +
        </text>
        <text
          x={111}
          y={210}
          textAnchor="end"
          className="fill-muted-foreground text-[14px]"
        >
          Actual −
        </text>
        {cells.map((cell) => (
          <g key={cell.label}>
            <rect
              x={cell.x}
              y={cell.y}
              width={108}
              height={78}
              rx={8}
              className={
                cell.correct
                  ? "fill-blue-600/15 stroke-blue-600"
                  : "fill-primary/10 stroke-primary"
              }
            />
            <text
              x={cell.x + 54}
              y={cell.y + 48}
              textAnchor="middle"
              className="fill-foreground text-[25px]"
            >
              {cell.value}
            </text>
          </g>
        ))}
      </Scene>
      <div className="grid gap-5 sm:grid-cols-2">
        {[
          "True positives",
          "False positives",
          "False negatives",
          "True negatives",
        ].map((label, index) => (
          <Range
            key={label}
            label={label}
            value={counts[index]!}
            min={0}
            max={30}
            onChange={(next) =>
              setCounts((current) =>
                current.map((value, position) =>
                  index === position ? next : value
                )
              )
            }
          />
        ))}
      </div>
      <Values
        rows={[
          ["Accuracy = (TP + TN) / N", percent(result.accuracy)],
          ["Precision = TP / (TP + FP)", percent(result.precision)],
          ["Recall = TP / (TP + FN)", percent(result.recall)],
          ["F1 = 2TP / (2TP + FP + FN)", percent(result.f1)],
        ]}
      />
      <Reset onClick={() => setCounts([8, 2, 4, 6])} />
    </Frame>
  )
}

const baselineScores = [
  0.8, 0.4, 0.7, 0.3, 0.9, 0.45, 0.6, 0.2, 0.4, 0.7, 0.1, 0.35,
]
const adaptedScores = [
  0.85, 0.6, 0.75, 0.4, 0.88, 0.55, 0.65, 0.25, 0.35, 0.45, 0.15, 0.3,
]

function evaluate(scores: readonly number[], threshold: number) {
  let tp = 0,
    fp = 0,
    fn = 0,
    tn = 0
  scores.forEach((score, index) => {
    if (index < 6) {
      if (score >= threshold) tp++
      else fn++
    } else {
      if (score >= threshold) fp++
      else tn++
    }
  })
  return metrics(tp, fp, fn, tn)
}

export function EvaluationExplorer() {
  const [threshold, setThreshold] = useState(0.5)
  const playback = usePlayback(20)
  const baseline = evaluate(baselineScores, 0.5)
  const adapted = evaluate(adaptedScores, threshold)
  const training = Array.from(
    { length: playback.step + 1 },
    (_, step) => Math.exp(-0.18 * step) + 0.1
  )
  const validation = Array.from(
    { length: playback.step + 1 },
    (_, step) =>
      Math.exp(-0.14 * step) + 0.2 + 0.025 * Math.max(0, step - 10) ** 1.5
  )
  return (
    <Frame
      containerRef={playback.ref}
      title="Compare like with like, then inspect generalization"
      description="All values here are explicitly illustrative. The first comparison uses twelve handcrafted classification scores, six positive and six negative. The learning curves below are analytic teaching curves, not measured results or Makata benchmarks."
    >
      <Range
        label="Adapted model decision threshold"
        value={threshold}
        min={0.1}
        max={0.9}
        step={0.05}
        onChange={setThreshold}
      />
      <Scene
        title="Illustrative baseline and adapted classification accuracy"
        description={`Baseline accuracy ${percent(baseline.accuracy)}; adapted accuracy ${percent(adapted.accuracy)}.`}
        height={190}
      >
        {[baseline, adapted].map((result, index) => (
          <g key={index}>
            <text
              x={20}
              y={36 + index * 82}
              className="fill-foreground text-[15px]"
            >
              {index === 0
                ? "Toy baseline · threshold 0.5"
                : `Toy adapted · threshold ${number(threshold)}`}
            </text>
            <rect
              x={20}
              y={48 + index * 82}
              width={(result.accuracy ?? 0) * 290}
              height={25}
              rx={4}
              className={index === 0 ? "fill-blue-600" : "fill-primary"}
            />
            <text
              x={325}
              y={67 + index * 82}
              className="fill-foreground text-[14px]"
            >
              {percent(result.accuracy)}
            </text>
          </g>
        ))}
      </Scene>
      <DataTable
        caption="Calculated metrics on handcrafted predictions"
        headers={["Metric", "Toy baseline", "Toy adapted"]}
        rows={(Object.keys(baseline) as (keyof typeof baseline)[]).map(
          (key) => [key, percent(baseline[key]), percent(adapted[key])]
        )}
      />
      <DataTable
        caption="Underlying illustrative classification scores"
        headers={["Item", "True class", "Baseline score", "Adapted score"]}
        rows={baselineScores.map((score, index) => [
          index + 1,
          index < 6 ? "positive" : "negative",
          score,
          adaptedScores[index],
        ])}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Choose thresholds on validation data, then freeze them before test
        evaluation. Changing the threshold after looking at test performance
        invalidates a clean comparison.
      </p>
      <LineChart
        series={[
          {
            name: "Illustrative training loss · rose",
            values: training,
            className: "stroke-primary",
          },
          {
            name: "Illustrative validation loss · blue",
            values: validation,
            className: "stroke-blue-600",
          },
        ]}
        labels={["Epoch", "Illustrative loss"]}
        maxY={1.3}
        maxX={20}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Training loss · rose", number(training.at(-1)!)],
          ["Validation loss · blue", number(validation.at(-1)!)],
          ["Generalization gap", number(validation.at(-1)! - training.at(-1)!)],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Teaching formulas: train(e) = exp(−0.18e) + 0.1; validation(e) =
        exp(−0.14e) + 0.2 + 0.025 max(0, e − 10)¹·⁵. The late rise illustrates
        why the final training checkpoint need not be the best validation
        checkpoint.
      </p>
      <Reset
        onClick={() => {
          setThreshold(0.5)
          playback.reset()
        }}
      />
    </Frame>
  )
}

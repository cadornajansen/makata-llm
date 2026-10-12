"use client"

import { useState } from "react"
import { motion } from "motion/react"
import { lora, multiply, softmax } from "@/lib/research/math"
import {
  Choice,
  DataTable,
  Frame,
  number,
  Playback,
  Range,
  Reset,
  Scene,
  useDiagramTransition,
  usePlayback,
  Values,
} from "./shared"

export function ParameterExplorer() {
  const [mode, setMode] = useState("LoRA")
  const full = mode === "Full fine-tuning"
  const inference = mode === "Inference"
  return (
    <Frame
      title="Which parameters receive updates?"
      description="Inspect a toy 4 × 4 linear layer. Full fine-tuning updates the base matrix. Rank-one LoRA freezes it and learns two small matrices with 4 + 4 parameters. Inference updates neither."
    >
      <Choice
        label="Parameter update method"
        options={["Full fine-tuning", "LoRA", "Inference"]}
        value={mode}
        onChange={setMode}
      />
      <Scene
        title="Frozen and trainable parameter map"
        description={`${full ? 16 : 0} base parameters and ${!full && !inference ? 8 : 0} adapter parameters are trainable.`}
      >
        <text
          x={110}
          y={29}
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          Base W: 4 × 4
        </text>
        {Array.from({ length: 16 }, (_, index) => (
          <rect
            key={index}
            x={40 + (index % 4) * 37}
            y={48 + Math.floor(index / 4) * 37}
            width={29}
            height={29}
            rx={5}
            className={
              full ? "fill-primary" : "fill-secondary stroke-muted-foreground"
            }
          />
        ))}
        <text
          x={297}
          y={29}
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          Adapter B × A
        </text>
        {Array.from({ length: 8 }, (_, index) => (
          <rect
            key={index}
            x={index < 4 ? 245 : 272 + (index - 4) * 25}
            y={index < 4 ? 60 + index * 30 : 99}
            width={20}
            height={20}
            rx={3}
            className={
              !full && !inference
                ? "fill-primary"
                : "fill-secondary stroke-border"
            }
          />
        ))}
        <text
          x={200}
          y={222}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          Rose = trainable · outlined = frozen or unused
        </text>
      </Scene>
      <Values
        rows={[
          ["Base weights", full ? "16 trainable" : "16 frozen"],
          ["Adapter weights", full || inference ? "not used" : "8 trainable"],
          ["Trainable parameters", full ? 16 : inference ? 0 : 8],
          ["Forward operation", full || inference ? "y = Wx" : "y = Wx + BAx"],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        A frozen weight still participates in the forward computation. LoRA
        reduces optimizer-state storage for trainable weights; it does not
        eliminate the base model or activation memory.
      </p>
      <Reset onClick={() => setMode("LoRA")} />
    </Frame>
  )
}

export function LoraExplorer() {
  const [rank, setRank] = useState(1)
  const [alpha, setAlpha] = useState(2)
  const result = lora(rank, alpha)
  const updateOutput = multiply(result.update, [[1], [2], [0]])
  return (
    <Frame
      title="Multiply the low-rank factors"
      description="For a 4 × 3 weight matrix, B is 4 × r and A is r × 3. The update is ΔW = (α/r)BA. Each displayed number is computed from the explicit matrices below."
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <Range label="Rank r" value={rank} min={1} max={3} onChange={setRank} />
        <Range
          label="Scale α"
          value={alpha}
          min={1}
          max={8}
          onChange={setAlpha}
        />
      </div>
      <Scene
        title="Low-rank matrix multiplication shapes"
        description={`B has shape 4 by ${rank}; A has shape ${rank} by 3; their product has shape 4 by 3.`}
        height={165}
      >
        <rect
          x={20}
          y={35}
          width={80}
          height={84}
          rx={7}
          className="fill-blue-600/20 stroke-blue-600"
        />
        <text
          x={60}
          y={69}
          textAnchor="middle"
          className="fill-foreground text-[18px]"
        >
          B
        </text>
        <text
          x={60}
          y={97}
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          4 × {rank}
        </text>
        <text x={119} y={84} className="fill-muted-foreground text-[22px]">
          ×
        </text>
        <rect
          x={147}
          y={35}
          width={80}
          height={84}
          rx={7}
          className="fill-primary/15 stroke-primary"
        />
        <text
          x={187}
          y={69}
          textAnchor="middle"
          className="fill-foreground text-[18px]"
        >
          A
        </text>
        <text
          x={187}
          y={97}
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          {rank} × 3
        </text>
        <text x={247} y={84} className="fill-muted-foreground text-[22px]">
          →
        </text>
        <rect
          x={280}
          y={35}
          width={100}
          height={84}
          rx={7}
          className="fill-secondary stroke-muted-foreground"
        />
        <text
          x={330}
          y={69}
          textAnchor="middle"
          className="fill-foreground text-[18px]"
        >
          ΔW
        </text>
        <text
          x={330}
          y={97}
          textAnchor="middle"
          className="fill-foreground text-[15px]"
        >
          4 × 3
        </text>
      </Scene>
      <DataTable
        caption="Matrix A"
        headers={["A row", "column 1", "column 2", "column 3"]}
        rows={result.a.map((row, index) => [
          index + 1,
          ...row.map((value) => number(value)),
        ])}
      />
      <DataTable
        caption="Matrix B"
        headers={[
          "B row",
          ...Array.from({ length: rank }, (_, index) => `column ${index + 1}`),
        ]}
        rows={result.b.map((row, index) => [
          index + 1,
          ...row.map((value) => number(value)),
        ])}
      />
      <DataTable
        caption="Calculated scaled LoRA update"
        headers={["ΔW row", "column 1", "column 2", "column 3"]}
        rows={result.update.map((row, index) => [
          index + 1,
          ...row.map((value) => number(value)),
        ])}
      />
      <Values
        rows={[
          ["Trainable adapter parameters r(4 + 3)", result.parameters],
          ["Full matrix parameters", result.fullParameters],
          [
            "ΔW × (1, 2, 0)",
            updateOutput.map((row) => number(row[0]!)).join(", "),
          ],
          ["Upper bound on update rank", rank],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        For this deliberately tiny matrix, r ≥ 2 uses more parameters than the
        full matrix. Savings require r(dᵢₙ + dₒᵤₜ) &lt; dᵢₙdₒᵤₜ. Production
        layers are much larger, with rank chosen far below their dimensions.
      </p>
      <Reset
        onClick={() => {
          setRank(1)
          setAlpha(2)
        }}
      />
    </Frame>
  )
}

export function DistillationExplorer() {
  const [temperature, setTemperature] = useState(2)
  const playback = usePlayback(12)
  const teacher = softmax([3, 1, 0], temperature)
  let logits = [0, 0, 0]
  for (let step = 0; step < playback.step; step++) {
    const student = softmax(logits, temperature)
    logits = logits.map(
      (logit, index) =>
        logit - 0.35 * temperature * (student[index]! - teacher[index]!)
    )
  }
  const student = softmax(logits, temperature)
  const divergence = teacher.reduce(
    (sum, probability, index) =>
      sum + probability * Math.log(probability / student[index]!),
    0
  )
  const transition = useDiagramTransition()
  return (
    <Frame
      containerRef={playback.ref}
      title="Learn from a teacher distribution"
      description="A toy teacher has logits [3, 1, 0]. A student starts at [0, 0, 0] and minimizes T² KL(teacher ∥ student) with learning rate 0.35. This demonstrates soft-target optimization, not measured model distillation."
    >
      <Scene
        title="Teacher and student probabilities"
        description={`Teacher probabilities: ${teacher.map((value) => number(value)).join(", ")}. Student: ${student.map((value) => number(value)).join(", ")}.`}
      >
        {teacher.map((probability, index) => (
          <g key={index}>
            <rect
              x={55 + index * 118}
              y={190 - probability * 155}
              height={probability * 155}
              width={28}
              rx={3}
              className="fill-blue-600"
            />
            <motion.rect
              initial={false}
              animate={{
                y: 190 - student[index]! * 155,
                height: student[index]! * 155,
              }}
              transition={transition}
              x={88 + index * 118}
              width={28}
              rx={3}
              className="fill-primary"
            />
            <text
              x={85 + index * 118}
              y={218}
              textAnchor="middle"
              className="fill-foreground text-[15px]"
            >
              token {index + 1}
            </text>
          </g>
        ))}
        <text
          x={200}
          y={22}
          textAnchor="middle"
          className="fill-muted-foreground text-[14px]"
        >
          Blue: teacher · Rose: student
        </text>
      </Scene>
      <Range
        label="Distillation temperature T"
        value={temperature}
        min={1}
        max={5}
        step={0.5}
        onChange={(next) => {
          setTemperature(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <DataTable
        caption="Teacher and student distribution"
        headers={["Token", "Teacher", "Student"]}
        rows={teacher.map((probability, index) => [
          index + 1,
          number(probability),
          number(student[index]!),
        ])}
      />
      <Values
        rows={[
          ["KL divergence", number(divergence, 6)],
          ["Scaled loss T² × KL", number(temperature ** 2 * divergence, 6)],
          ["Student logits", logits.map((value) => number(value)).join(", ")],
        ]}
      />
    </Frame>
  )
}

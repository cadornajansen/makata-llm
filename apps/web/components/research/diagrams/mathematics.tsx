"use client"

import { useState } from "react"
import { motion } from "motion/react"
import {
  descent,
  dot,
  gradient,
  loss,
  transform,
  type Matrix2,
  type Vector2,
} from "@/lib/research/math"
import {
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

function Plane({ children }: { children: React.ReactNode }) {
  return (
    <Scene
      title="Two-dimensional coordinate plane"
      description="The horizontal axis is x; the vertical axis is y. Exact coordinates are listed below."
      height={280}
    >
      {Array.from({ length: 9 }, (_, index) => index - 4).map((tick) => (
        <g key={tick}>
          <line
            x1={80 + (tick + 4) * 30}
            x2={80 + (tick + 4) * 30}
            y1={20}
            y2={260}
            className="stroke-border"
          />
          <line
            x1={80}
            x2={320}
            y1={20 + (tick + 4) * 30}
            y2={20 + (tick + 4) * 30}
            className="stroke-border"
          />
        </g>
      ))}
      <path d="M65 140H340M200 270V10" className="stroke-muted-foreground" />
      <text x={347} y={145} className="fill-muted-foreground text-[15px]">
        x
      </text>
      <text x={208} y={17} className="fill-muted-foreground text-[15px]">
        y
      </text>
      <text x={225} y={157} className="fill-muted-foreground text-[12px]">
        1
      </text>
      <text x={183} y={114} className="fill-muted-foreground text-[12px]">
        1
      </text>
      {children}
    </Scene>
  )
}

function Arrow({
  vector,
  origin = [0, 0],
  className,
  label,
  labelOffset = [7, -8],
}: {
  vector: Vector2
  origin?: Vector2
  className: string
  label: string
  labelOffset?: Vector2
}) {
  const transition = useDiagramTransition()
  const x = 200 + (origin[0] + vector[0]) * 30
  const y = 140 - (origin[1] + vector[1]) * 30
  return (
    <g>
      <motion.line
        initial={false}
        animate={{
          x1: 200 + origin[0] * 30,
          y1: 140 - origin[1] * 30,
          x2: x,
          y2: y,
        }}
        transition={transition}
        strokeWidth={3}
        className={className}
      />
      <motion.circle
        initial={false}
        animate={{ cx: x, cy: y }}
        transition={transition}
        r={4}
        className={className.replace("stroke-", "fill-")}
      />
      <text
        x={x + labelOffset[0]}
        y={y + labelOffset[1]}
        className="fill-foreground text-[15px]"
      >
        {label}
      </text>
    </g>
  )
}

export function VectorExplorer() {
  const [x, setX] = useState(2)
  const [y, setY] = useState(1)
  const u: Vector2 = [x, y]
  const v: Vector2 = [-1, 2]
  return (
    <Frame
      title="Vectors: direction, addition, and alignment"
      description="Move u. The blue vector v stays at (−1, 2). The rose vector is u + v, constructed by placing v at the tip of u."
    >
      <Plane>
        <Arrow
          vector={v}
          className="stroke-blue-600"
          label="v"
          labelOffset={[7, 18]}
        />
        <Arrow vector={u} className="stroke-foreground" label="u" />
        <Arrow vector={v} origin={u} className="stroke-blue-400" label="" />
        <Arrow
          vector={[x - 1, y + 2]}
          className="stroke-primary"
          label="u + v"
        />
      </Plane>
      <div className="grid gap-5 sm:grid-cols-2">
        <Range
          label="u horizontal component"
          value={x}
          min={-2}
          max={3}
          step={0.25}
          onChange={setX}
        />
        <Range
          label="u vertical component"
          value={y}
          min={-3}
          max={1.5}
          step={0.25}
          onChange={setY}
        />
      </div>
      <Values
        rows={[
          ["u + v", `(${number(x - 1)}, ${number(y + 2)})`],
          ["u · v = −x + 2y", number(dot(u, v))],
          ["Length ‖u‖", number(Math.hypot(x, y))],
          ["Projection coefficient (u · v)/(v · v)", number(dot(u, v) / 5)],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        A positive dot product means the vectors point partly in the same
        direction; zero means perpendicular (unless a vector is zero). Length
        and alignment are different properties.
      </p>
      <Reset
        onClick={() => {
          setX(2)
          setY(1)
        }}
      />
    </Frame>
  )
}

export function MatrixExplorer() {
  const [entries, setEntries] = useState([1, 0.5, 0, 1])
  const matrix: Matrix2 = [
    [entries[0]!, entries[1]!],
    [entries[2]!, entries[3]!],
  ]
  const transition = useDiagramTransition()
  const map = (vector: Vector2): string => {
    const result = transform(matrix, vector)
    return `${200 + result[0] * 30},${140 - result[1] * 30}`
  }
  const corner = [transform(matrix, [1, 0]), transform(matrix, [0, 1])]
  return (
    <Frame
      title="A matrix moves an entire coordinate system"
      description="The columns of A tell you where the unit basis vectors land. Change any entry to stretch, reflect, shear, or collapse the grid."
    >
      <Plane>
        {[-1, -0.5, 0, 0.5, 1].map((tick) => (
          <g key={tick}>
            <motion.path
              initial={false}
              animate={{ d: `M${map([tick, -1])}L${map([tick, 1])}` }}
              transition={transition}
              className="fill-none stroke-blue-500/50"
            />
            <motion.path
              initial={false}
              animate={{ d: `M${map([-1, tick])}L${map([1, tick])}` }}
              transition={transition}
              className="fill-none stroke-blue-500/50"
            />
          </g>
        ))}
        <Arrow vector={corner[0]!} className="stroke-primary" label="A e₁" />
        <Arrow
          vector={corner[1]!}
          className="stroke-blue-600"
          label="A e₂"
          labelOffset={[7, 18]}
        />
      </Plane>
      <div className="grid gap-5 sm:grid-cols-2">
        {entries.map((value, index) => (
          <Range
            key={index}
            label={`A${Math.floor(index / 2) + 1}${(index % 2) + 1}`}
            value={value}
            min={-1.5}
            max={1.5}
            step={0.25}
            onChange={(next) =>
              setEntries((current) =>
                current.map((entry, position) =>
                  index === position ? next : entry
                )
              )
            }
          />
        ))}
      </div>
      <Values
        rows={[
          [
            "First column / A e₁",
            `(${number(entries[0]!)}, ${number(entries[2]!)})`,
          ],
          [
            "Second column / A e₂",
            `(${number(entries[1]!)}, ${number(entries[3]!)})`,
          ],
          [
            "det(A) = ad − bc",
            number(entries[0]! * entries[3]! - entries[1]! * entries[2]!),
          ],
          [
            "A(1, 2)",
            transform(matrix, [1, 2])
              .map((value) => number(value))
              .join(", "),
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        The determinant is the signed area scale. At zero, the plane collapses
        onto a line or point and information is lost.
      </p>
      <Reset onClick={() => setEntries([1, 0.5, 0, 1])} />
    </Frame>
  )
}

export function GradientDescent() {
  const [rate, setRate] = useState(0.2)
  const playback = usePlayback(12)
  const transition = useDiagramTransition()
  const values = descent(-1, rate, playback.step)
  const weight = values.at(-1)!
  const outside = weight < -4 || weight > 10
  const x = (value: number): number =>
    36 + ((Math.max(-4, Math.min(10, value)) + 4) / 14) * 340
  const y = (value: number): number => 206 - (Math.min(49, value) / 49) * 170
  const curve = Array.from({ length: 71 }, (_, index) => -4 + index * 0.2)
    .map((value, index) => `${index ? "L" : "M"}${x(value)},${y(loss(value))}`)
    .join(" ")
  return (
    <Frame
      containerRef={playback.ref}
      title="Follow the gradient of L(w) = (w − 3)²"
      description="Start at w = −1. Each step subtracts η × 2(w − 3). A step size above 1 diverges; exactly 1 oscillates forever for this particular loss."
    >
      <Scene
        title="Gradient descent on a quadratic loss"
        description={`Step ${playback.step}: w = ${number(weight)}, loss = ${number(loss(weight))}. ${outside ? "The point is beyond the plotted range." : "The minimum is w = 3."}`}
      >
        <path
          d="M36 28V206H382"
          className="fill-none stroke-muted-foreground"
        />
        <path
          d={curve}
          className="fill-none stroke-blue-600"
          strokeWidth={2.5}
        />
        {values
          .slice(0, -1)
          .filter((value) => value >= -4 && value <= 10)
          .map((value, index) => (
            <circle
              key={index}
              cx={x(value)}
              cy={y(loss(value))}
              r={3}
              className="fill-primary/30"
            />
          ))}
        <motion.circle
          initial={false}
          animate={{ cx: x(weight), cy: y(loss(weight)) }}
          transition={transition}
          r={6}
          className="fill-primary stroke-background"
          strokeWidth={2}
        />
        <text x={40} y={19} className="fill-muted-foreground text-[14px]">
          Loss (0–49)
        </text>
        <text
          x={x(3)}
          y={227}
          textAnchor="middle"
          className="fill-foreground text-[14px]"
        >
          minimum: w = 3
        </text>
      </Scene>
      <Range
        label="Learning rate η"
        value={rate}
        min={0.05}
        max={1.2}
        step={0.05}
        onChange={(next) => {
          setRate(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Current weight w", number(weight)],
          ["Gradient 2(w − 3)", number(gradient(weight))],
          ["Loss L(w)", number(loss(weight))],
          ["Next weight", number(weight - rate * gradient(weight))],
        ]}
      />
      {outside && (
        <p role="status" className="m-0 text-sm font-medium text-primary">
          The iterate has left the plotted range. The numerical values show
          divergence; the dot is held at the chart boundary.
        </p>
      )}
    </Frame>
  )
}

export function ChainRule() {
  const [x, setX] = useState(2)
  const playback = usePlayback(3)
  const u = 3 * x + 1
  return (
    <Frame
      containerRef={playback.ref}
      title="The chain rule is multiplication along a path"
      description="For y = (3x + 1)², separate the affine operation u = 3x + 1 from the square y = u². Backward, multiply each local derivative."
    >
      <Stages
        active={playback.step}
        labels={[
          "Input x",
          "Forward: u = 3x + 1",
          "Forward: y = u²",
          "Backward: (2u) × 3",
        ]}
        values={[
          number(x),
          number(u),
          number(u ** 2),
          `dy/dx = ${number(6 * u)}`,
        ]}
      />
      <Range
        label="Input x"
        value={x}
        min={-2}
        max={3}
        step={0.25}
        onChange={(next) => {
          setX(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Local derivative du/dx", "3"],
          ["Local derivative dy/du", number(2 * u)],
          ["Chain rule dy/dx", `${number(2 * u)} × 3 = ${number(6 * u)}`],
        ]}
      />
    </Frame>
  )
}

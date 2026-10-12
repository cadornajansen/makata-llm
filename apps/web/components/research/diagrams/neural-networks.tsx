"use client"

import { useState } from "react"
import { motion } from "motion/react"
import { network } from "@/lib/research/math"
import {
  Choice,
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

export function NetworkExplorer() {
  const [weight, setWeight] = useState(0.6)
  const [bias, setBias] = useState(0.1)
  const playback = usePlayback(4)
  const transition = useDiagramTransition()
  const state = network(weight, bias)
  const labels = [
    "Inputs",
    "Hidden tanh activations",
    "Linear output",
    "Squared error",
    "Backward gradients",
  ]
  const nodes = [
    { x: 55, y: 80, value: 1, label: "x₁", phase: 0 },
    { x: 55, y: 190, value: 0.5, label: "x₂", phase: 0 },
    { x: 205, y: 80, value: state.hidden[0], label: "h₁", phase: 1 },
    { x: 205, y: 190, value: state.hidden[1], label: "h₂", phase: 1 },
    { x: 345, y: 135, value: state.output, label: "ŷ", phase: 2 },
  ]
  return (
    <Frame
      containerRef={playback.ref}
      title="A complete 2–2–1 network"
      description="Two inputs feed two tanh neurons, then a linear output. The target is 1 and the loss is ½(ŷ − 1)². Adjust the highlighted input weight and hidden bias; all displayed values are recalculated."
    >
      <Scene
        title="Neural network forward and backward pass"
        description={`${labels[playback.step]}. Output ${number(state.output)}, loss ${number(state.loss)}, selected weight gradient ${number(state.gradientWeight)}.`}
        height={280}
      >
        {[
          [0, 2],
          [0, 3],
          [1, 2],
          [1, 3],
          [2, 4],
          [3, 4],
        ].map(([from, to], index) => {
          const a = nodes[from!]!,
            b = nodes[to!]!
          return (
            <motion.line
              key={index}
              initial={false}
              animate={{ opacity: playback.step >= b.phase ? 1 : 0.2 }}
              transition={transition}
              x1={a.x + 24}
              y1={a.y}
              x2={b.x - 24}
              y2={b.y}
              strokeWidth={index === 0 ? 3 : 1.5}
              className={
                playback.step === 4
                  ? "stroke-primary"
                  : index === 0
                    ? "stroke-blue-600"
                    : "stroke-muted-foreground"
              }
            />
          )
        })}
        {nodes.map((node) => (
          <g key={node.label}>
            <motion.circle
              initial={false}
              animate={{ opacity: playback.step >= node.phase ? 1 : 0.3 }}
              transition={transition}
              cx={node.x}
              cy={node.y}
              r={27}
              className="fill-background stroke-blue-600"
              strokeWidth={2}
            />
            <text
              x={node.x}
              y={node.y + 5}
              textAnchor="middle"
              className="fill-foreground text-[13px]"
            >
              {number(node.value, 2)}
            </text>
            <text
              x={node.x}
              y={node.y - 37}
              textAnchor="middle"
              className="fill-muted-foreground text-[16px]"
            >
              {node.label}
            </text>
          </g>
        ))}
        <text x={113} y={67} className="fill-blue-700 text-[14px]">
          w = {number(weight)}
        </text>
        <text
          x={200}
          y={263}
          textAnchor="middle"
          className="fill-primary text-[15px]"
        >
          {labels[playback.step]}
        </text>
      </Scene>
      <div className="grid gap-5 sm:grid-cols-2">
        <Range
          label="Weight x₁ → h₁"
          value={weight}
          min={-2}
          max={2}
          step={0.1}
          onChange={(next) => {
            setWeight(next)
            playback.reset()
          }}
        />
        <Range
          label="Bias of h₁"
          value={bias}
          min={-1}
          max={1}
          step={0.1}
          onChange={(next) => {
            setBias(next)
            playback.reset()
          }}
        />
      </div>
      <Playback playback={playback} />
      <Values
        rows={[
          [
            "Hidden preactivations",
            state.preactivation.map((value) => number(value)).join(", "),
          ],
          ["Output 0.7h₁ − 0.5h₂ + 0.2", number(state.output)],
          ["Loss", number(state.loss)],
          [
            "∂L/∂w = (ŷ − 1) × 0.7 × (1 − h₁²) × x₁",
            number(state.gradientWeight),
          ],
          ["∂L/∂b₁", number(state.gradientBias)],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Other fixed weights: x₂→h₁ = −0.4, x₁→h₂ = −0.3, x₂→h₂ = 0.8; b₂ = −0.1.
        Backpropagation follows the same connections in reverse, multiplying
        local derivatives.
      </p>
      <Reset
        onClick={() => {
          setWeight(0.6)
          setBias(0.1)
          playback.reset()
        }}
      />
    </Frame>
  )
}

export function ActivationExplorer() {
  const [activation, setActivation] = useState("tanh")
  const [input, setInput] = useState(0.5)
  const transition = useDiagramTransition()
  function value(x: number): number {
    return activation === "ReLU"
      ? Math.max(0, x)
      : activation === "sigmoid"
        ? 1 / (1 + Math.exp(-x))
        : Math.tanh(x)
  }
  const output = value(input)
  const derivative =
    activation === "ReLU"
      ? input > 0
        ? 1
        : 0
      : activation === "sigmoid"
        ? output * (1 - output)
        : 1 - output ** 2
  const px = (x: number): number => 200 + x * 52
  const py = (y: number): number => 155 - y * 42
  const path = Array.from({ length: 61 }, (_, index) => -3 + index / 10)
    .map((x, index) => `${index ? "L" : "M"}${px(x)},${py(value(x))}`)
    .join(" ")
  return (
    <Frame
      title="An activation changes values and gradients"
      description="Inspect the output and local slope. Sigmoid and tanh flatten at large magnitudes; ReLU is linear above zero and zero below it."
    >
      <Choice
        label="Activation function"
        options={["tanh", "sigmoid", "ReLU"]}
        value={activation}
        onChange={setActivation}
      />
      <Scene
        title={`${activation} activation function`}
        description={`At x = ${number(input)}, output = ${number(output)}, local derivative = ${number(derivative)}.`}
      >
        <path
          d="M30 155H380M200 210V15"
          className="fill-none stroke-muted-foreground"
        />
        <motion.path
          initial={false}
          animate={{ d: path }}
          transition={transition}
          className="fill-none stroke-blue-600"
          strokeWidth={3}
        />
        <motion.circle
          initial={false}
          animate={{ cx: px(input), cy: py(output) }}
          transition={transition}
          r={6}
          className="fill-primary"
        />
        <text x={365} y={177} className="fill-muted-foreground text-[14px]">
          x
        </text>
        <text x={209} y={22} className="fill-muted-foreground text-[14px]">
          f(x)
        </text>
        <text x={39} y={178} className="fill-muted-foreground text-[14px]">
          −3
        </text>
        <text x={350} y={178} className="fill-muted-foreground text-[14px]">
          3
        </text>
      </Scene>
      <Range
        label="Input x"
        value={input}
        min={-3}
        max={3}
        step={0.1}
        onChange={setInput}
      />
      <Values
        rows={[
          ["Activation", number(output)],
          ["Local derivative", number(derivative)],
        ]}
      />
      {activation === "ReLU" && input === 0 && (
        <p className="m-0 text-sm text-muted-foreground">
          ReLU is not differentiable at zero. This teaching implementation uses
          the common autodiff convention of a zero gradient there.
        </p>
      )}
      <Reset
        onClick={() => {
          setActivation("tanh")
          setInput(0.5)
        }}
      />
    </Frame>
  )
}

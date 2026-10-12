"use client"

import { useState } from "react"
import { regressionTraining } from "@/lib/research/math"
import {
  Frame,
  LineChart,
  number,
  Playback,
  Range,
  Stages,
  usePlayback,
  Values,
} from "./shared"

export function AutogradExplorer() {
  const [weight, setWeight] = useState(0.5)
  const playback = usePlayback(5)
  const prediction = weight * 2 + 1
  const error = prediction - 4
  return (
    <Frame
      containerRef={playback.ref}
      title="Autograd records operations, then applies the chain rule"
      description="A scalar graph predicts ŷ = w × 2 + 1 for target 4. Each operation saves what its backward rule needs. There is no numerical differentiation in this example."
    >
      <Stages
        active={playback.step}
        labels={[
          "Leaf parameter w",
          "Multiply by input x = 2",
          "Add fixed bias b = 1",
          "Subtract target y = 4",
          "Square error: L = e²",
          "Backward: 2e × 1 × 2",
        ]}
        values={[
          number(weight),
          number(2 * weight),
          number(prediction),
          number(error),
          number(error ** 2),
          `∂L/∂w = ${number(4 * error)}`,
        ]}
      />
      <Range
        label="Leaf weight w"
        value={weight}
        min={-1}
        max={3}
        step={0.1}
        onChange={(next) => {
          setWeight(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Prediction", number(prediction)],
          ["Loss", number(error ** 2)],
          ["Gradient accumulated into w.grad", number(4 * error)],
          ["Gradient of input x if requested", number(2 * error * weight)],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        The optimizer changes the leaf parameter after backward. Calling
        backward again without clearing gradients accumulates another
        contribution; it does not replace the old gradient automatically.
      </p>
    </Frame>
  )
}

export function TrainingExplorer() {
  const [rate, setRate] = useState(0.2)
  const playback = usePlayback(25)
  const result = regressionTraining(rate, playback.step)
  const weight = result.weights.at(-1)!
  return (
    <Frame
      containerRef={playback.ref}
      title="A training curve computed from actual updates"
      description="Fit ŷ = wx to three points: (−1, −2), (0, 0), and (1, 2). Full-batch gradient descent minimizes mean squared error; the optimum is w = 2. These are teaching calculations, not Makata experiment results."
    >
      <LineChart
        series={[
          {
            name: "Computed training MSE",
            values: result.losses,
            className: "stroke-primary",
          },
        ]}
        labels={["Optimizer update", "Mean squared error"]}
        maxY={3}
        maxX={25}
        current={{ x: playback.step, y: result.losses.at(-1)! }}
      />
      <Range
        label="Learning rate"
        value={rate}
        min={0.02}
        max={0.7}
        step={0.02}
        onChange={(next) => {
          setRate(next)
          playback.reset()
        }}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Weight w", number(weight, 5)],
          ["Training MSE", number(result.losses.at(-1)!, 6)],
          ["Gradient (4/3)(w − 2)", number((4 / 3) * (weight - 2), 5)],
          ["Prediction for unseen x = 0.5", number(weight * 0.5, 5)],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        A falling training loss confirms optimization on these points. It does
        not, by itself, establish generalization on a real dataset. Use an
        independent validation split in the accompanying Python example.
      </p>
    </Frame>
  )
}

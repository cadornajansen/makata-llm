/** Small deterministic teaching models, not trained Makata models. */
export type Vector2 = readonly [number, number]
export type Matrix2 = readonly [Vector2, Vector2]

export function dot(a: readonly number[], b: readonly number[]): number {
  if (a.length !== b.length) throw new Error("Vector dimensions must match")
  return a.reduce((sum, value, index) => sum + value * b[index]!, 0)
}

export function transform(matrix: Matrix2, vector: Vector2): Vector2 {
  return [dot(matrix[0], vector), dot(matrix[1], vector)]
}

export function multiply(
  a: readonly (readonly number[])[],
  b: readonly (readonly number[])[]
): number[][] {
  if (
    !a.length ||
    !b.length ||
    !b[0]?.length ||
    a.some((row) => row.length !== b.length) ||
    b.some((row) => row.length !== b[0]!.length)
  ) {
    throw new Error("Matrix dimensions must be compatible")
  }
  return a.map((row) =>
    b[0]!.map((_, column) =>
      row.reduce((sum, value, index) => sum + value * b[index]![column]!, 0)
    )
  )
}

export function loss(weight: number): number {
  return (weight - 3) ** 2
}
export function gradient(weight: number): number {
  return 2 * (weight - 3)
}
export function descent(start: number, rate: number, steps: number): number[] {
  const values = [start]
  for (let i = 0; i < steps; i++)
    values.push(values[i]! - rate * gradient(values[i]!))
  return values
}

export function network(
  weight: number,
  bias: number
): {
  input: Vector2
  preactivation: Vector2
  hidden: Vector2
  output: number
  loss: number
  gradientWeight: number
  gradientBias: number
  hiddenGradient: Vector2
} {
  const input: Vector2 = [1, 0.5]
  const preactivation: Vector2 = [
    weight * input[0] - 0.4 * input[1] + bias,
    -0.3 * input[0] + 0.8 * input[1] - 0.1,
  ]
  const hidden: Vector2 = [
    Math.tanh(preactivation[0]),
    Math.tanh(preactivation[1]),
  ]
  const output = 0.7 * hidden[0] - 0.5 * hidden[1] + 0.2
  const error = output - 1
  const hiddenGradient: Vector2 = [
    error * 0.7 * (1 - hidden[0] ** 2),
    error * -0.5 * (1 - hidden[1] ** 2),
  ]
  return {
    input,
    preactivation,
    hidden,
    output,
    loss: 0.5 * error ** 2,
    gradientWeight: hiddenGradient[0] * input[0],
    gradientBias: hiddenGradient[0],
    hiddenGradient,
  }
}

export function softmax(values: readonly number[], temperature = 1): number[] {
  if (
    !values.length ||
    !(temperature > 0) ||
    values.every((value) => value === -Infinity)
  )
    throw new Error("Softmax needs values and a positive temperature")
  const maximum = Math.max(...values)
  const exponents = values.map((value) =>
    Math.exp((value - maximum) / temperature)
  )
  const sum = exponents.reduce((total, value) => total + value, 0)
  return exponents.map((value) => value / sum)
}

export const attentionInputs = {
  tokens: ["Ako", "ay", "nag-aaral", "."],
  queries: [
    [1, 0],
    [0, 1],
    [1, 1],
    [-1, 1],
  ],
  keys: [
    [1, 0],
    [0, 1],
    [1, 1],
    [-1, 0],
  ],
  values: [
    [1, 0],
    [0, 2],
    [1, 1],
    [-1, 0.5],
  ],
} as const

export function attention(
  queryIndex: number,
  causal: boolean,
  head = 0
): { scores: number[]; weights: number[]; output: Vector2 } {
  const query = attentionInputs.queries[queryIndex]
  if (!query) throw new Error("Unknown query token")
  const projected: Vector2 = head === 0 ? query : [query[1], -query[0]]
  const scores = attentionInputs.keys.map((key, index) =>
    causal && index > queryIndex
      ? -Infinity
      : dot(projected, key) / Math.sqrt(2)
  )
  const weights = softmax(scores)
  const weightedDimension = (dimension: 0 | 1): number =>
    weights.reduce(
      (sum, weight, index) =>
        sum + weight * attentionInputs.values[index]![dimension],
      0
    )
  const output: Vector2 = [weightedDimension(0), weightedDimension(1)]
  return { scores, weights, output }
}

export function lora(
  rank: number,
  scale = 1
): {
  a: number[][]
  b: number[][]
  update: number[][]
  parameters: number
  fullParameters: number
} {
  if (!Number.isInteger(rank) || rank < 1 || rank > 3)
    throw new Error("Teaching rank must be 1, 2, or 3")
  const a = [
    [0.2, -0.1, 0.3],
    [0.1, 0.4, -0.2],
    [-0.2, 0.1, 0.1],
  ].slice(0, rank)
  const b = [
    [0.3, -0.1, 0.2],
    [0.2, 0.4, 0.1],
    [-0.1, 0.2, 0.3],
    [0.4, -0.2, 0.1],
  ].map((row) => row.slice(0, rank))
  return {
    a,
    b,
    update: multiply(b, a).map((row) =>
      row.map((value) => (value * scale) / rank)
    ),
    parameters: rank * 7,
    fullParameters: 12,
  }
}

export function metrics(
  tp: number,
  fp: number,
  fn: number,
  tn: number
): {
  accuracy: number | null
  precision: number | null
  recall: number | null
  f1: number | null
} {
  const ratio = (numerator: number, denominator: number): number | null =>
    denominator === 0 ? null : numerator / denominator
  return {
    accuracy: ratio(tp + tn, tp + fp + fn + tn),
    precision: ratio(tp, tp + fp),
    recall: ratio(tp, tp + fn),
    f1: ratio(2 * tp, 2 * tp + fp + fn),
  }
}

export function splitDataset(
  total: number,
  trainPercent: number,
  validationPercent: number
): { train: number; validation: number; test: number } {
  if (
    !Number.isInteger(total) ||
    total < 0 ||
    trainPercent < 0 ||
    validationPercent < 0 ||
    trainPercent + validationPercent > 100
  )
    throw new Error("Invalid dataset split")
  const train = Math.floor((total * trainPercent) / 100)
  const validation = Math.floor((total * validationPercent) / 100)
  return { train, validation, test: total - train - validation }
}

export function memoryEstimate(
  parametersMillions: number,
  precision: "fp32" | "mixed" | "inference"
): {
  parameters: number
  gradients: number
  optimizer: number
  master: number
  total: number
} {
  const count = parametersMillions * 1_000_000
  const gib = 1024 ** 3
  const parameters = (count * (precision === "fp32" ? 4 : 2)) / gib
  const gradients =
    precision === "inference"
      ? 0
      : (count * (precision === "fp32" ? 4 : 2)) / gib
  const optimizer = precision === "inference" ? 0 : (count * 8) / gib
  const master = precision === "mixed" ? (count * 4) / gib : 0
  return {
    parameters,
    gradients,
    optimizer,
    master,
    total: parameters + gradients + optimizer + master,
  }
}

export function regressionTraining(
  rate: number,
  steps: number
): { weights: number[]; losses: number[] } {
  const x = [-1, 0, 1]
  const weights = [0]
  const losses = [8 / 3]
  for (let step = 0; step < steps; step++) {
    const weight = weights[step]!
    const grad = x.reduce(
      (sum, input) =>
        sum + (2 * (weight * input - 2 * input) * input) / x.length,
      0
    )
    const next = weight - rate * grad
    weights.push(next)
    losses.push(
      x.reduce(
        (sum, input) => sum + (next * input - 2 * input) ** 2 / x.length,
        0
      )
    )
  }
  return { weights, losses }
}

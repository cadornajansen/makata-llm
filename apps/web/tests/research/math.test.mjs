import assert from "node:assert/strict"
import test from "node:test"
import {
  attention,
  descent,
  dot,
  gradient,
  lora,
  loss,
  memoryEstimate,
  metrics,
  multiply,
  network,
  regressionTraining,
  softmax,
  splitDataset,
  transform,
} from "../../lib/research/math.ts"

const close = (actual, expected, tolerance = 1e-9) =>
  assert.ok(Math.abs(actual - expected) < tolerance, `${actual} ≈ ${expected}`)

test("dot products and matrix transformations have known numerical results", () => {
  assert.equal(dot([2, 3], [-1, 4]), 10)
  assert.deepEqual(
    transform(
      [
        [2, 1],
        [0, 1],
      ],
      [1, 2]
    ),
    [4, 2]
  )
  assert.deepEqual(
    multiply(
      [
        [1, 2],
        [3, 4],
      ],
      [[2], [1]]
    ),
    [[4], [10]]
  )
  assert.throws(() => multiply([[1]], [[2], [3]]))
})
test("analytical loss derivative matches central finite differences", () => {
  for (const weight of [-2, 0, 3, 7])
    close(
      gradient(weight),
      (loss(weight + 1e-5) - loss(weight - 1e-5)) / 2e-5,
      1e-7
    )
})
test("learning rate controls convergence, oscillation and divergence", () => {
  close(descent(-1, 0.5, 1)[1], 3)
  assert.deepEqual(descent(-1, 1, 2), [-1, 7, -1])
  assert.ok(loss(descent(-1, 1.1, 2)[2]) > loss(-1))
})
test("2–2–1 backpropagation matches finite differences", () => {
  const delta = 1e-5
  for (const weight of [-1, 0.6, 2]) {
    const state = network(weight, 0.1)
    close(
      state.gradientWeight,
      (network(weight + delta, 0.1).loss - network(weight - delta, 0.1).loss) /
        (2 * delta),
      1e-7
    )
    close(
      state.gradientBias,
      (network(weight, 0.1 + delta).loss - network(weight, 0.1 - delta).loss) /
        (2 * delta),
      1e-7
    )
  }
})
test("softmax is stable under large logits, normalized, and temperature sensitive", () => {
  const values = softmax([1000, 1001, 1002])
  close(
    values.reduce((a, b) => a + b),
    1
  )
  close(values[2], softmax([0, 1, 2])[2])
  assert.ok(softmax([0, 1, 2], 0.5)[2] > values[2])
  assert.throws(() => softmax([1], 0))
})
test("attention computes a weighted value mixture and masks future positions", () => {
  const first = attention(0, true)
  assert.deepEqual(first.weights, [1, 0, 0, 0])
  assert.deepEqual(first.output, [1, 0])
  const second = attention(1, true)
  close(
    second.weights.reduce((a, b) => a + b),
    1
  )
  assert.equal(second.weights[2], 0)
  close(second.output[0], second.weights[0])
  close(second.output[1], second.weights[1] * 2)
})
test("rank-one LoRA update is a scaled outer product", () => {
  const result = lora(1, 2)
  assert.equal(result.parameters, 7)
  close(result.update[0][0], 0.12)
  close(result.update[3][2], 0.24)
})
test("confusion metrics handle both real denominators and undefined cases", () => {
  const result = metrics(8, 2, 4, 6)
  close(result.accuracy, 0.7)
  close(result.precision, 0.8)
  close(result.recall, 2 / 3)
  close(result.f1, 8 / 11)
  assert.deepEqual(metrics(0, 0, 0, 0), {
    accuracy: null,
    precision: null,
    recall: null,
    f1: null,
  })
  assert.equal(metrics(0, 0, 2, 5).f1, 0)
})
test("dataset splits preserve every record and allocate rounding remainder to test", () => {
  assert.deepEqual(splitDataset(101, 80, 10), {
    train: 80,
    validation: 10,
    test: 11,
  })
  assert.throws(() => splitDataset(100, 90, 20))
})
test("memory accounting distinguishes persistent state from activations", () => {
  close(memoryEstimate(1000, "fp32").total * 1024 ** 3, 16_000_000_000)
  close(memoryEstimate(1000, "mixed").total * 1024 ** 3, 16_000_000_000)
  close(memoryEstimate(1000, "inference").total * 1024 ** 3, 2_000_000_000)
})
test("computed regression loss decreases for a stable learning rate", () => {
  const result = regressionTraining(0.2, 30)
  close(result.losses[0], 8 / 3)
  assert.ok(result.losses.at(-1) < 1e-7)
  close(result.weights.at(-1), 2, 0.001)
})

"use client"

import { useState } from "react"
import { memoryEstimate } from "@/lib/research/math"
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

export function ParallelismExplorer() {
  const playback = usePlayback(16)
  const serial = Math.min(16, playback.step)
  const parallel = Math.min(16, playback.step * 4)
  return (
    <Frame
      containerRef={playback.ref}
      title="Parallel work needs independent tasks"
      description="Sixteen identical, independent toy operations take one conceptual tick each. Compare one worker with four workers. Real CPUs and GPUs both have parallel hardware; this simplified schedule is not a hardware benchmark."
    >
      <Scene
        title="One worker versus four parallel workers"
        description={`After ${playback.step} conceptual ticks: one worker has finished ${serial} tasks; four workers have finished ${parallel}.`}
        height={270}
      >
        {[serial, parallel].map((completed, side) => (
          <g key={side}>
            <text
              x={side === 0 ? 102 : 300}
              y={27}
              textAnchor="middle"
              className="fill-foreground text-[16px]"
            >
              {side === 0 ? "One worker" : "Four workers"}
            </text>
            {Array.from({ length: 16 }, (_, index) => (
              <g key={index}>
                <rect
                  x={30 + side * 200 + (index % 4) * 35}
                  y={48 + Math.floor(index / 4) * 43}
                  width={28}
                  height={31}
                  rx={5}
                  className={
                    index < completed
                      ? side === 0
                        ? "fill-primary"
                        : "fill-blue-600"
                      : "fill-secondary stroke-border"
                  }
                />
                <text
                  x={44 + side * 200 + (index % 4) * 35}
                  y={69 + Math.floor(index / 4) * 43}
                  textAnchor="middle"
                  className={`${index < completed ? "fill-white" : "fill-muted-foreground"} text-[12px]`}
                >
                  {index + 1}
                </text>
              </g>
            ))}
            <text
              x={102 + side * 200}
              y={245}
              textAnchor="middle"
              className="fill-muted-foreground text-[14px]"
            >
              {completed}/16 complete
            </text>
          </g>
        ))}
      </Scene>
      <Playback playback={playback} />
      <Values
        rows={[
          ["Conceptual ticks elapsed", playback.step],
          ["One-worker completion time", "16 ticks"],
          ["Four-worker completion time", "4 ticks (idealized)"],
          ["Assumptions", "No transfer, launch, or synchronization costs"],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Matrix operations expose many independent multiply–accumulate
        operations. Small workloads, dependencies, and memory transfers can
        erase a parallelism benefit; do not read this idealized 4× schedule as a
        GPU speed claim.
      </p>
    </Frame>
  )
}

export function MemoryExplorer() {
  const [millions, setMillions] = useState(600)
  const [mode, setMode] = useState("FP32 training")
  const [capacity, setCapacity] = useState(24)
  const precision =
    mode === "FP32 training"
      ? "fp32"
      : mode === "Mixed training"
        ? "mixed"
        : "inference"
  const result = memoryEstimate(millions, precision)
  const parts = [
    {
      name: "Parameters",
      value: result.parameters,
      className: "fill-blue-600",
    },
    { name: "Gradients", value: result.gradients, className: "fill-primary" },
    {
      name: "Adam moments",
      value: result.optimizer,
      className: "fill-blue-400",
    },
    {
      name: "FP32 master",
      value: result.master,
      className: "fill-muted-foreground",
    },
  ]
  let offset = 0
  return (
    <Frame
      title="Count persistent memory before estimating the whole run"
      description="This calculator models dense parameters, gradients, and Adam's two FP32 moment buffers. Mixed training here explicitly means 16-bit parameters/gradients plus a separate FP32 master copy. Framework implementations differ."
    >
      <Choice
        label="Memory accounting mode"
        options={["FP32 training", "Mixed training", "16-bit inference"]}
        value={mode}
        onChange={setMode}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <Range
          label="Parameters (millions)"
          value={millions}
          min={100}
          max={10000}
          step={100}
          onChange={setMillions}
        />
        <Range
          label="GPU capacity (GiB)"
          value={capacity}
          min={8}
          max={80}
          step={8}
          onChange={setCapacity}
        />
      </div>
      <Scene
        title="Persistent model memory by category"
        description={`Estimated persistent state: ${number(result.total, 2)} GiB. Capacity comparison: ${capacity} GiB. Activations and runtime memory are excluded.`}
        height={120}
      >
        {parts.map((part) => {
          const start = offset
          offset += part.value
          return (
            <rect
              key={part.name}
              x={20 + (start / result.total) * 360}
              y={30}
              width={(part.value / result.total) * 360}
              height={32}
              className={part.className}
            />
          )
        })}
        <text
          x={200}
          y={92}
          textAnchor="middle"
          className="fill-foreground text-[17px]"
        >
          {number(result.total, 2)} GiB persistent state
        </text>
      </Scene>
      <DataTable
        caption="Persistent memory components in GiB"
        headers={["Component", "GiB"]}
        rows={parts.map((part) => [part.name, number(part.value, 3)])}
      />
      <Values
        rows={[
          [
            "Total persistent bytes per parameter",
            precision === "inference" ? 2 : 16,
          ],
          [
            "Capacity minus persistent state",
            `${number(capacity - result.total, 2)} GiB`,
          ],
          [
            "Feasibility",
            result.total >= capacity
              ? "Persistent state alone exceeds capacity"
              : "Undetermined until activations and overhead are included",
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        GiB = bytes / 2³⁰. Activations, temporary workspaces, allocator
        overhead, communication buffers, and inference KV cache are excluded.
        PyTorch autocast often keeps parameters and optimizer state in FP32; it
        is not identical to this explicit master-copy layout.
      </p>
      <Reset
        onClick={() => {
          setMillions(600)
          setMode("FP32 training")
          setCapacity(24)
        }}
      />
    </Frame>
  )
}

export function BatchExplorer() {
  const [microbatch, setMicrobatch] = useState(2)
  const [accumulation, setAccumulation] = useState(4)
  const [devices, setDevices] = useState(1)
  const playback = usePlayback(accumulation)
  const gradients = Array.from(
    { length: playback.step },
    (_, micro) =>
      Array.from(
        { length: devices },
        (_, rank) => 0.1 * (micro + rank + 1)
      ).reduce((sum, value) => sum + value, 0) / devices
  )
  const accumulated = gradients.reduce(
    (sum, value) => sum + value / accumulation,
    0
  )
  return (
    <Frame
      containerRef={playback.ref}
      title="Many microbatches can make one optimizer step"
      description="Effective batch size = microbatch × accumulation steps × data-parallel devices. Each toy gradient is averaged across devices and divided by the accumulation count before adding it to the buffer."
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <Range
          label="Examples per device microbatch"
          value={microbatch}
          min={1}
          max={8}
          onChange={(next) => {
            setMicrobatch(next)
            playback.reset()
          }}
        />
        <Range
          label="Accumulation steps"
          value={accumulation}
          min={1}
          max={8}
          onChange={(next) => {
            setAccumulation(next)
            playback.reset()
          }}
        />
      </div>
      <Choice
        label="Data parallel devices"
        options={["1 device", "2 devices", "4 devices"]}
        value={devices === 1 ? "1 device" : `${devices} devices`}
        onChange={(next) => {
          setDevices(Number.parseInt(next))
          playback.reset()
        }}
      />
      <Stages
        active={playback.step === accumulation ? 2 : playback.step > 0 ? 1 : 0}
        labels={[
          "Microbatch forward + backward",
          "Accumulate normalized gradients",
          "Optimizer update, then zero_grad",
        ]}
        values={[
          `${playback.step} / ${accumulation}`,
          number(accumulated, 4),
          playback.step === accumulation ? "1 update" : "not yet",
        ]}
      />
      <Playback playback={playback} />
      <Values
        rows={[
          ["Effective batch size", microbatch * accumulation * devices],
          ["Examples processed so far", microbatch * playback.step * devices],
          ["Accumulated scalar gradient", number(accumulated, 4)],
          [
            "Weight (starts at 1; learning rate 0.1)",
            playback.step === accumulation
              ? number(1 - 0.1 * accumulated, 4)
              : "1 (unchanged)",
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        Toy per-device gradient = 0.1 × (microbatch index + device index + 1),
        with zero-based indices. In real training the gradient comes from the
        examples. Accumulation is not perfectly interchangeable with a larger
        batch when batch-dependent layers, dropout, or uneven final batches
        matter.
      </p>
      <Reset
        onClick={() => {
          setMicrobatch(2)
          setAccumulation(4)
          setDevices(1)
          playback.reset()
        }}
      />
    </Frame>
  )
}

export function CheckpointExplorer() {
  const [mode, setMode] = useState("Store every activation")
  const playback = usePlayback(8)
  const checkpointed = mode === "Checkpoint segments"
  const retained = checkpointed
    ? [0, 4, 8]
    : Array.from({ length: 9 }, (_, index) => index)
  return (
    <Frame
      containerRef={playback.ref}
      title="Store less, recompute during backward"
      description="Eight toy layers each produce a 32 MiB activation. Compare retaining every boundary with checkpoint boundaries at 0, 4, and 8. Step through the forward pass; retained boundaries stay marked."
    >
      <Choice
        label="Activation retention strategy"
        options={["Store every activation", "Checkpoint segments"]}
        value={mode}
        onChange={(next) => {
          setMode(next)
          playback.reset()
        }}
      />
      <Scene
        title="Activation checkpoint boundaries"
        description={`${retained.filter((index) => index <= playback.step).length} boundaries retained after layer ${playback.step}.`}
        height={280}
      >
        {Array.from({ length: 9 }, (_, index) => (
          <g key={index}>
            <rect
              x={38 + (index % 3) * 120}
              y={25 + Math.floor(index / 3) * 76}
              width={84}
              height={48}
              rx={8}
              className={
                index <= playback.step && retained.includes(index)
                  ? "fill-blue-600/20 stroke-blue-600"
                  : index <= playback.step
                    ? "fill-primary/10 stroke-primary"
                    : "fill-secondary stroke-border"
              }
            />
            <text
              x={80 + (index % 3) * 120}
              y={55 + Math.floor(index / 3) * 76}
              textAnchor="middle"
              className="fill-foreground text-[15px]"
            >
              a{index}
            </text>
          </g>
        ))}
        <text
          x={200}
          y={268}
          textAnchor="middle"
          className="fill-muted-foreground text-[13px]"
        >
          Blue: retained · Rose: recomputed later
        </text>
      </Scene>
      <Playback playback={playback} />
      <Values
        rows={[
          [
            "Saved boundaries after this forward step",
            retained.filter((index) => index <= playback.step).join(", "),
          ],
          [
            "Saved boundary storage",
            `${retained.filter((index) => index <= playback.step).length * 32} MiB`,
          ],
          [
            "Saved boundaries at end",
            checkpointed ? "3 × 32 = 96 MiB" : "9 × 32 = 288 MiB",
          ],
          [
            "Backward requirement",
            checkpointed
              ? "Recompute intermediate activations within each segment"
              : "Read stored activations",
          ],
        ]}
      />
      <p className="m-0 text-sm text-muted-foreground">
        These figures count only saved boundary tensors, including the input.
        They are not peak VRAM: recomputation temporarily needs intermediate
        activations too. Checkpointing saves memory at the cost of extra forward
        computation and requires care with random state and side effects.
      </p>
    </Frame>
  )
}

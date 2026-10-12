"use client"

import {
  useEffect,
  useId,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
  type Ref,
} from "react"
import { motion, type Transition } from "motion/react"
import { Button } from "@workspace/ui/components/button"
import { Field, FieldLabel } from "@workspace/ui/components/field"
import { Slider } from "@workspace/ui/components/slider"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@workspace/ui/components/table"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@workspace/ui/components/toggle-group"

export function number(value: number, digits = 3): string {
  if (!Number.isFinite(value))
    return value === -Infinity ? "−∞" : "outside range"
  return Number(value.toFixed(digits)).toString()
}

const reducedMotionQuery = "(prefers-reduced-motion: reduce)"

function subscribeToMotionPreference(onChange: () => void): () => void {
  const preference = window.matchMedia(reducedMotionQuery)
  preference.addEventListener("change", onChange)
  return () => preference.removeEventListener("change", onChange)
}

function getReducedMotion(): boolean {
  return window.matchMedia(reducedMotionQuery).matches
}

function getServerReducedMotion(): boolean {
  return true
}

function useReducedMotion(): boolean {
  // Subscribe directly: the installed Motion hook only reads its initial preference.
  return useSyncExternalStore(
    subscribeToMotionPreference,
    getReducedMotion,
    getServerReducedMotion
  )
}

export function useDiagramTransition(): Transition {
  const reduced = useReducedMotion()
  return { duration: reduced ? 0 : 0.3, ease: [0.2, 0, 0, 1] }
}

export function Frame({
  title,
  description,
  children,
  containerRef,
}: {
  title: string
  description: string
  children: ReactNode
  containerRef?: Ref<HTMLDivElement>
}) {
  return (
    <div
      ref={containerRef}
      className="my-10 min-w-0 rounded-2xl border border-border bg-background p-4 sm:p-6"
      data-diagram={title}
    >
      <figure className="m-0 grid min-w-0 gap-5">
        <figcaption className="grid gap-2">
          <span className="text-base font-medium tracking-tight">{title}</span>
          <span className="text-sm leading-relaxed text-muted-foreground">
            {description}
          </span>
        </figcaption>
        {children}
      </figure>
    </div>
  )
}

export function Scene({
  title,
  description,
  children,
  height = 240,
}: {
  title: string
  description: string
  children: ReactNode
  height?: number
}) {
  const id = useId()
  return (
    <svg
      viewBox={`0 0 400 ${height}`}
      className="w-full overflow-visible rounded-xl bg-secondary/40 text-foreground"
      role="img"
      aria-labelledby={`${id}-title ${id}-description`}
    >
      <title id={`${id}-title`}>{title}</title>
      <desc id={`${id}-description`}>{description}</desc>
      {children}
    </svg>
  )
}

export function Range({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
}: {
  label: string
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  step?: number
}) {
  const id = useId()
  return (
    <Field className="gap-3">
      <FieldLabel
        id={`${id}-label`}
        className="flex w-full items-center justify-between gap-3 text-sm"
      >
        <span>{label}</span>
        <output className="font-mono text-muted-foreground">
          {number(value)}
        </output>
      </FieldLabel>
      <Slider
        aria-labelledby={`${id}-label`}
        value={[value]}
        min={min}
        max={max}
        step={step}
        onValueChange={(next) =>
          onChange(Array.isArray(next) ? next[0]! : next)
        }
      />
    </Field>
  )
}

export function Values({
  rows,
  caption = "Calculated values",
}: {
  rows: readonly (readonly [string, ReactNode])[]
  caption?: string
}) {
  return (
    <dl
      aria-label={caption}
      className="grid gap-2 rounded-xl border border-border bg-secondary/30 p-3 text-sm"
    >
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="flex flex-wrap justify-between gap-x-4 gap-y-1"
        >
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="m-0 font-mono break-words text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function DataTable({
  headers,
  rows,
  caption,
}: {
  headers: readonly string[]
  rows: readonly (readonly ReactNode[])[]
  caption: string
}) {
  return (
    <div
      data-lenis-prevent
      className="max-w-full overflow-x-auto rounded-xl border border-border text-sm"
      tabIndex={0}
      role="region"
      aria-label={caption}
    >
      <Table>
        <caption className="sr-only">{caption}</caption>
        <TableHeader>
          <TableRow>
            {headers.map((header) => (
              <TableHead key={header} scope="col">
                {header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={index}>
              {row.map((value, column) => (
                <TableCell key={column} className="font-mono">
                  {value}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function Reset({ onClick }: { onClick: () => void }) {
  return (
    <Button variant="outline" onClick={onClick} className="w-fit">
      Reset
    </Button>
  )
}

export function Choice({
  options,
  value,
  onChange,
  label,
}: {
  options: readonly string[]
  value: string
  onChange: (value: string) => void
  label: string
}) {
  return (
    <ToggleGroup
      aria-label={label}
      variant="outline"
      value={[value]}
      onValueChange={(next) => {
        if (typeof next[0] === "string") onChange(next[0])
      }}
      className="max-w-full flex-wrap"
    >
      {options.map((option) => (
        <ToggleGroupItem
          key={option}
          value={option}
          className="h-auto min-h-9 px-3 py-2 text-left whitespace-normal data-pressed:bg-primary data-pressed:text-primary-foreground"
        >
          {option}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}

export function usePlayback(lastStep: number) {
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) setPlaying(false)
      },
      { threshold: 0.05 }
    )
    if (ref.current) observer.observe(ref.current)
    const onVisibility = (): void => {
      if (document.hidden) setPlaying(false)
    }
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)")
    const onPreference = (): void => {
      if (preference.matches) setPlaying(false)
    }
    document.addEventListener("visibilitychange", onVisibility)
    preference.addEventListener("change", onPreference)
    return () => {
      observer.disconnect()
      document.removeEventListener("visibilitychange", onVisibility)
      preference.removeEventListener("change", onPreference)
    }
  }, [])
  useEffect(() => {
    if (!playing || reduced || step >= lastStep) return
    const timer = window.setTimeout(
      () => setStep((current) => Math.min(current + 1, lastStep)),
      800
    )
    return () => window.clearTimeout(timer)
  }, [playing, reduced, step, lastStep])
  function reset(): void {
    setPlaying(false)
    setStep(0)
  }
  function advance(): void {
    setPlaying(false)
    setStep((current) => Math.min(current + 1, lastStep))
  }
  function toggle(): void {
    if (step >= lastStep) {
      setStep(0)
      setPlaying(true)
    } else setPlaying((current) => !current)
  }
  return {
    step,
    ref,
    reset,
    advance,
    toggle,
    playing: playing && !reduced && step < lastStep,
    reduced: !!reduced,
    lastStep,
  }
}

export function Playback({
  playback,
}: {
  playback: ReturnType<typeof usePlayback>
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="outline"
        onClick={playback.advance}
        disabled={playback.step >= playback.lastStep}
      >
        Step
      </Button>
      <Button
        variant="outline"
        onClick={playback.toggle}
        disabled={playback.reduced}
      >
        {playback.playing ? "Pause" : "Play"}
      </Button>
      <Reset onClick={playback.reset} />
      <span className="text-xs text-muted-foreground" role="status">
        {playback.reduced
          ? "Reduced motion · manual steps"
          : `Step ${playback.step} / ${playback.lastStep}`}
      </span>
    </div>
  )
}

export function LineChart({
  series,
  labels,
  maxY,
  maxX,
  current,
}: {
  series: readonly {
    name: string
    values: readonly number[]
    className: string
  }[]
  labels: readonly [string, string]
  maxY: number
  maxX?: number
  current?: { x: number; y: number }
}) {
  const transition = useDiagramTransition()
  const xMax =
    maxX ?? Math.max(1, ...series.map((line) => line.values.length - 1))
  return (
    <Scene
      title={`${labels[1]} against ${labels[0]}`}
      description={series.map((line) => line.name).join(" and ")}
    >
      {[0, 0.5, 1].map((tick) => (
        <g key={tick}>
          <line
            x1={42}
            x2={378}
            y1={195 - tick * 158}
            y2={195 - tick * 158}
            className="stroke-border"
          />
          <text
            x={36}
            y={200 - tick * 158}
            textAnchor="end"
            className="fill-muted-foreground text-[13px]"
          >
            {number(tick * maxY, 1)}
          </text>
        </g>
      ))}
      <path d="M42 25V195H380" className="fill-none stroke-muted-foreground" />
      <text x={42} y={17} className="fill-muted-foreground text-[13px]">
        {labels[1]}
      </text>
      <text
        x={378}
        y={224}
        textAnchor="end"
        className="fill-muted-foreground text-[13px]"
      >
        {labels[0]} (0–{xMax})
      </text>
      {series.map((line) => (
        <motion.path
          key={line.name}
          initial={false}
          animate={{
            d: line.values
              .map(
                (value, index) =>
                  `${index ? "L" : "M"}${42 + (index / xMax) * 336},${195 - (Math.min(maxY, Math.max(0, value)) / maxY) * 158}`
              )
              .join(" "),
          }}
          transition={transition}
          strokeWidth={2.5}
          className={`fill-none ${line.className}`}
        />
      ))}
      {current && (
        <motion.circle
          initial={false}
          animate={{
            cx: 42 + (current.x / xMax) * 336,
            cy: 195 - (Math.min(maxY, Math.max(0, current.y)) / maxY) * 158,
          }}
          transition={transition}
          r={5}
          className="fill-primary stroke-background"
          strokeWidth={2}
        />
      )}
    </Scene>
  )
}

export function Stages({
  labels,
  active,
  values,
}: {
  labels: readonly string[]
  active: number
  values?: readonly string[]
}) {
  const transition = useDiagramTransition()
  const hasValues = values?.some((value) => value.length > 0) ?? false
  const rowHeight = hasValues ? 86 : 66
  const height = labels.length * rowHeight + 10
  return (
    <Scene
      title="Process stages"
      description={`Current stage: ${labels[Math.min(active, labels.length - 1)]}`}
      height={height}
    >
      {labels.map((label, index) => (
        <g key={label}>
          {index > 0 && (
            <path
              d={`M200 ${index * rowHeight - 2}v16m-4-5 4 5 4-5`}
              className="fill-none stroke-muted-foreground"
              strokeWidth={1.5}
            />
          )}
          <motion.rect
            initial={false}
            animate={{ opacity: index <= active ? 1 : 0.35 }}
            transition={transition}
            x={28}
            y={index * rowHeight + 14}
            width={344}
            height={hasValues ? 66 : 46}
            rx={9}
            className={
              index === active ? "fill-primary" : "fill-secondary stroke-border"
            }
          />
          <text
            x={44}
            y={index * rowHeight + (hasValues ? 38 : 42)}
            className={`${index === active ? "fill-primary-foreground" : "fill-foreground"} text-[15px]`}
          >
            {index + 1}. {label}
          </text>
          {values?.[index] && (
            <text
              x={44}
              y={index * rowHeight + 62}
              className={`${index === active ? "fill-primary-foreground" : "fill-muted-foreground"} font-mono text-[14px]`}
            >
              {values[index]}
            </text>
          )}
        </g>
      ))}
    </Scene>
  )
}

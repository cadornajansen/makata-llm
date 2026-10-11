"use client"

import {
  useEffect,
  useRef,
  useSyncExternalStore,
  type ReactElement,
} from "react"

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)"
const FRAME_INTERVAL = 1000 / 30
const RIBBON_COLORS = ["#6E86B2", "#BC7C8F"] as const

type Particle = {
  horizontal: number
  vertical: number
  radius: number
  opacity: number
  layer: number
}

function subscribeToMotionPreference(onChange: () => void): () => void {
  const preference = window.matchMedia(REDUCED_MOTION_QUERY)
  preference.addEventListener("change", onChange)
  return () => preference.removeEventListener("change", onChange)
}

function getReducedMotion(): boolean {
  return window.matchMedia(REDUCED_MOTION_QUERY).matches
}

function getServerReducedMotion(): boolean {
  return true
}

function seededValue(index: number): number {
  const value = Math.sin(index * 127.1 + 311.7) * 43758.5453
  return value - Math.floor(value)
}

function createParticles(mobile: boolean): Particle[] {
  return Array.from({ length: mobile ? 6000 : 18000 }, (_, index) => ({
    horizontal: seededValue(index * 7),
    // Three samples concentrate the dust near the ribbon's center without a grid.
    vertical:
      (seededValue(index * 7 + 1) +
        seededValue(index * 7 + 2) +
        seededValue(index * 7 + 3)) /
        1.5 -
      1,
    radius: 0.35 + seededValue(index * 7 + 4) * 0.5,
    opacity: 0.3 + seededValue(index * 7 + 5) * 0.65,
    layer: seededValue(index * 7 + 6),
  }))
}

function drawWave(
  context: CanvasRenderingContext2D,
  particles: Particle[],
  width: number,
  height: number,
  seconds: number,
  scrollProgress: number
): void {
  context.clearRect(0, 0, width, height)
  const phase = seconds * 0.13 + scrollProgress * 0.65
  const beyondHero = Math.min(scrollProgress, 1)

  for (const particle of particles) {
    const { horizontal, vertical, layer } = particle
    const curve = horizontal * Math.PI * 2 - phase
    const center = 0.78 - horizontal * 0.5 + Math.sin(curve) * 0.14
    const spread = 0.16 + Math.cos(curve + layer) * 0.025
    const fold = Math.sin(horizontal * 11 + vertical * 2.5 + phase) * 0.035
    const x = horizontal * (width + 100) - 50 + Math.sin(phase + layer * 2) * 18
    const y =
      (center + vertical * spread + fold + (layer - 0.5) * 0.025) * height
    const edgeFade = Math.pow(Math.max(0, 1 - Math.abs(vertical)), 0.5)

    // Leave the text clear, widening the quiet area once editorial content enters.
    const horizontalDistance =
      (x - width / 2) / (width * (0.35 + beyondHero * 0.15))
    const verticalDistance = (y - height * 0.46) / (height * 0.43)
    const textDistance =
      horizontalDistance ** 2 + verticalDistance ** 2 * (1 - beyondHero)
    const textFade = 0.015 + Math.min(1, textDistance ** 3) * 0.985
    context.globalAlpha =
      particle.opacity * edgeFade * textFade * (0.8 - beyondHero * 0.55)
    context.fillStyle = RIBBON_COLORS[horizontal < 0.52 ? 0 : 1]
    const diameter = particle.radius * 2
    context.fillRect(x, y, diameter, diameter)
  }
  context.globalAlpha = 1
}

export function ParticleWave(): ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const elapsedRef = useRef(0)
  const reducedMotion = useSyncExternalStore(
    subscribeToMotionPreference,
    getReducedMotion,
    getServerReducedMotion
  )

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext("2d")
    if (!canvas || !context) return

    let width = 0
    let height = 0
    let particles: Particle[] = []
    let frameId: number | null = null
    let lastPaint = 0
    let disposed = false
    let scrollTarget = window.scrollY / Math.max(window.innerHeight, 1)
    let scrollProgress = reducedMotion ? 0 : scrollTarget

    function paint(): void {
      if (!context) return
      drawWave(
        context,
        particles,
        width,
        height,
        reducedMotion ? 0 : elapsedRef.current / 1000,
        scrollProgress
      )
    }

    function stop(): void {
      if (frameId !== null) cancelAnimationFrame(frameId)
      frameId = null
      lastPaint = 0
    }

    function animate(now: number): void {
      if (disposed) return
      if (lastPaint === 0) lastPaint = now
      const delta = now - lastPaint
      if (delta >= FRAME_INTERVAL) {
        elapsedRef.current += Math.min(delta - (delta % FRAME_INTERVAL), 100)
        lastPaint = now - (delta % FRAME_INTERVAL)
        scrollProgress += (scrollTarget - scrollProgress) * 0.09
        paint()
      }
      frameId = requestAnimationFrame(animate)
    }

    function syncAnimation(): void {
      if (disposed) return
      if (document.hidden || reducedMotion) stop()
      else if (frameId === null) frameId = requestAnimationFrame(animate)
    }

    function onScroll(): void {
      scrollTarget = window.scrollY / Math.max(window.innerHeight, 1)
    }

    function resize(): void {
      if (disposed || !canvas || !context) return
      const bounds = canvas.getBoundingClientRect()
      width = bounds.width
      height = bounds.height
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5)
      canvas.width = Math.round(width * pixelRatio)
      canvas.height = Math.round(height * pixelRatio)
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
      particles = createParticles(width < 768)
      onScroll()
      paint()
    }

    const resizeObserver = new ResizeObserver(resize)
    resize()
    resizeObserver.observe(canvas)
    window.addEventListener("scroll", onScroll, { passive: true })
    document.addEventListener("visibilitychange", syncAnimation)
    syncAnimation()

    return () => {
      disposed = true
      stop()
      resizeObserver.disconnect()
      window.removeEventListener("scroll", onScroll)
      document.removeEventListener("visibilitychange", syncAnimation)
    }
  }, [reducedMotion])

  return (
    <div className="pointer-events-none fixed inset-0 -z-10" aria-hidden="true">
      <canvas ref={canvasRef} className="block size-full" />
    </div>
  )
}

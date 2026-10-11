"use client"

import { useEffect } from "react"
import Lenis from "lenis"

export function SmoothScroll(): null {
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)")
    let scrolling: Lenis | null = null

    function updatePreference(): void {
      scrolling?.destroy()
      scrolling = null

      if (!preference.matches) {
        scrolling = new Lenis({
          autoRaf: true,
          smoothWheel: true,
          syncTouch: false,
          anchors: true,
          lerp: 0.12,
        })
      }
    }

    updatePreference()
    preference.addEventListener("change", updatePreference)

    return () => {
      preference.removeEventListener("change", updatePreference)
      scrolling?.destroy()
    }
  }, [])

  return null
}

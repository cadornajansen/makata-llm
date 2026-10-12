"use client"

import { useEffect, useRef, useState } from "react"
import { Check, Copy } from "lucide-react"
import { Button } from "@workspace/ui/components/button"

export function CodeCopy({ text }: { text: string }): React.ReactElement {
  const [status, setStatus] = useState("Copy")
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current)
    },
    []
  )
  async function copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(text)
      setStatus("Copied")
    } catch {
      setStatus("Select code to copy")
    }
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setStatus("Copy"), 2500)
  }
  return (
    <Button variant="ghost" size="sm" onClick={copy} aria-label="Copy code">
      <span aria-live="polite">{status}</span>
      {status === "Copied" ? (
        <Check aria-hidden="true" data-icon="inline-end" />
      ) : (
        <Copy aria-hidden="true" data-icon="inline-end" />
      )}
    </Button>
  )
}

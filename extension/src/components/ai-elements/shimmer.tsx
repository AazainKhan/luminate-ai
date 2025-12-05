"use client"

import { cn } from "@/lib/utils"

interface ShimmerProps {
  className?: string
  lines?: number
  /** Width variants for more natural text-like appearance */
  variant?: "text" | "card" | "code" | "inline"
}

/**
 * Shimmer loading skeleton for AI response streaming
 * Creates a pulsing animation to indicate content is loading
 */
export function Shimmer({ className, lines = 3, variant = "text" }: ShimmerProps) {
  const lineWidths = {
    text: ["w-full", "w-[90%]", "w-[75%]", "w-[85%]", "w-[60%]"],
    card: ["w-full", "w-full", "w-full"],
    code: ["w-[80%]", "w-[65%]", "w-[90%]", "w-[50%]"],
    inline: ["w-24"],
  }

  const heights = {
    text: "h-4",
    card: "h-6",
    code: "h-3",
    inline: "h-4",
  }

  const widths = lineWidths[variant]
  const height = heights[variant]

  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]",
            height,
            widths[i % widths.length]
          )}
        />
      ))}
    </div>
  )
}

/**
 * Inline shimmer for text that is still loading
 */
export function ShimmerInline({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-block animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]",
        "h-4 w-20 align-middle",
        className
      )}
    />
  )
}

/**
 * Code block shimmer for loading code
 */
export function ShimmerCode({ className, lines = 4 }: { className?: string; lines?: number }) {
  return (
    <div className={cn("rounded-lg border border-border bg-muted/20 p-4 space-y-2", className)}>
      <div className="flex items-center gap-2 mb-3">
        <div className="h-3 w-16 animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]" />
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-3 animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]",
            i % 3 === 0 ? "w-[70%]" : i % 3 === 1 ? "w-[85%]" : "w-[50%]"
          )}
          style={{ animationDelay: `${i * 100}ms` }}
        />
      ))}
    </div>
  )
}

/**
 * Card shimmer for loading structured content
 */
export function ShimmerCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-lg border border-border bg-muted/10 p-4", className)}>
      <div className="flex items-center gap-3 mb-3">
        <div className="h-8 w-8 animate-shimmer rounded-full bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-32 animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]" />
          <div className="h-3 w-24 animate-shimmer rounded bg-gradient-to-r from-muted/30 via-muted/60 to-muted/30 bg-[length:400%_100%]" />
        </div>
      </div>
      <Shimmer lines={2} variant="text" />
    </div>
  )
}

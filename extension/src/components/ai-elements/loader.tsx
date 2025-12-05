"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface LoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Size of the loader in pixels */
  size?: number
  /** Variant style */
  variant?: "spinner" | "dots" | "pulse"
  /** Custom label for accessibility */
  label?: string
}

/**
 * Animated loader component for AI streaming states
 * 
 * Variants:
 * - spinner: Rotating circle (default)
 * - dots: Three bouncing dots
 * - pulse: Pulsing circle
 */
export function Loader({
  size = 20,
  variant = "spinner",
  label = "Loading...",
  className,
  ...props
}: LoaderProps) {
  if (variant === "dots") {
    return (
      <div
        role="status"
        aria-label={label}
        className={cn("flex items-center gap-1", className)}
        {...props}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="rounded-full bg-violet-400 animate-dot-pulse"
            style={{
              width: size / 3,
              height: size / 3,
              animationDelay: `${i * 0.16}s`,
            }}
          />
        ))}
        <span className="sr-only">{label}</span>
      </div>
    )
  }

  if (variant === "pulse") {
    return (
      <div
        role="status"
        aria-label={label}
        className={cn("relative", className)}
        style={{ width: size, height: size }}
        {...props}
      >
        <div
          className="absolute inset-0 rounded-full bg-violet-500/30 animate-ping"
          style={{ animationDuration: "1.5s" }}
        />
        <div className="absolute inset-1 rounded-full bg-violet-500" />
        <span className="sr-only">{label}</span>
      </div>
    )
  }

  // Default: spinner
  return (
    <div
      role="status"
      aria-label={label}
      className={cn("relative", className)}
      style={{ width: size, height: size }}
      {...props}
    >
      <svg
        className="animate-spinner"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  )
}

interface LoaderTextProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Text to display next to loader */
  children?: React.ReactNode
  /** Size of the loader icon */
  size?: number
  /** Loader variant */
  variant?: "spinner" | "dots" | "pulse"
}

/**
 * Loader with accompanying text label
 */
export function LoaderText({
  children = "Processing...",
  size = 16,
  variant = "spinner",
  className,
  ...props
}: LoaderTextProps) {
  return (
    <div
      className={cn("flex items-center gap-2 text-muted-foreground", className)}
      {...props}
    >
      <Loader size={size} variant={variant} />
      <span className="text-sm">{children}</span>
    </div>
  )
}

interface StreamingIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether currently streaming */
  isStreaming: boolean
  /** Label to show when streaming */
  streamingLabel?: string
  /** Label to show when complete */
  completeLabel?: string
  /** Duration in milliseconds (shown when streaming) */
  duration?: number
}

/**
 * Streaming status indicator with duration display
 * Shows animated indicator while streaming, then completion state
 */
export function StreamingIndicator({
  isStreaming,
  streamingLabel = "Thinking",
  completeLabel = "Complete",
  duration,
  className,
  ...props
}: StreamingIndicatorProps) {
  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <div
      className={cn(
        "flex items-center gap-2 text-xs font-medium transition-colors",
        isStreaming ? "text-violet-400" : "text-emerald-400",
        className
      )}
      {...props}
    >
      {isStreaming ? (
        <>
          <Loader size={14} variant="spinner" className="text-violet-400" />
          <span className="animate-processing">{streamingLabel}</span>
          {duration !== undefined && (
            <span className="text-muted-foreground font-mono">
              {formatDuration(duration)}
            </span>
          )}
        </>
      ) : (
        <>
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <span>{completeLabel}</span>
          {duration !== undefined && (
            <span className="text-muted-foreground font-mono">
              {formatDuration(duration)}
            </span>
          )}
        </>
      )}
    </div>
  )
}

export { Loader as default }

export type { LoaderProps }


"use client"

import { useState, useEffect, useCallback, useRef } from "react"

/**
 * Streaming state for agentic UI components
 * Coordinates expand/collapse animations with streaming status
 */
export interface StreamingState {
  /** Whether content is currently streaming */
  isStreaming: boolean
  /** Whether streaming has completed */
  isComplete: boolean
  /** Whether the component should be expanded */
  isExpanded: boolean
  /** Elapsed time since streaming started (ms) */
  duration: number
  /** Formatted duration string (e.g., "1.2s") */
  durationText: string
}

export interface UseStreamingStateOptions {
  /** Initial expanded state */
  defaultExpanded?: boolean
  /** Auto-collapse after completion (ms). Set to 0 to disable */
  collapseDelay?: number
  /** Auto-expand when streaming starts */
  expandOnStream?: boolean
  /** Callback when streaming completes */
  onComplete?: () => void
}

/**
 * Hook for managing streaming state with coordinated animations
 * 
 * Usage:
 * ```tsx
 * const { state, startStreaming, completeStreaming, toggle } = useStreamingState({
 *   collapseDelay: 1500,
 *   expandOnStream: true,
 * })
 * ```
 */
export function useStreamingState(options: UseStreamingStateOptions = {}) {
  const {
    defaultExpanded = true,
    collapseDelay = 1500,
    expandOnStream = true,
    onComplete,
  } = options

  const [isStreaming, setIsStreaming] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [duration, setDuration] = useState(0)
  
  const startTimeRef = useRef<number | null>(null)
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const collapseTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Format duration for display
  const formatDuration = useCallback((ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }, [])

  // Start streaming - auto-expand and start timer
  const startStreaming = useCallback(() => {
    setIsStreaming(true)
    setIsComplete(false)
    setDuration(0)
    startTimeRef.current = Date.now()

    // Auto-expand when streaming starts
    if (expandOnStream) {
      setIsExpanded(true)
    }

    // Start duration timer
    durationIntervalRef.current = setInterval(() => {
      if (startTimeRef.current) {
        setDuration(Date.now() - startTimeRef.current)
      }
    }, 100)
  }, [expandOnStream])

  // Complete streaming - stop timer and schedule auto-collapse
  const completeStreaming = useCallback(() => {
    setIsStreaming(false)
    setIsComplete(true)

    // Stop duration timer
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }

    // Final duration
    if (startTimeRef.current) {
      setDuration(Date.now() - startTimeRef.current)
    }

    // Notify completion
    onComplete?.()

    // Schedule auto-collapse
    if (collapseDelay > 0) {
      collapseTimeoutRef.current = setTimeout(() => {
        setIsExpanded(false)
      }, collapseDelay)
    }
  }, [collapseDelay, onComplete])

  // Toggle expanded state
  const toggle = useCallback(() => {
    // Cancel auto-collapse if user manually toggles
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setIsExpanded((prev) => !prev)
  }, [])

  // Expand
  const expand = useCallback(() => {
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setIsExpanded(true)
  }, [])

  // Collapse
  const collapse = useCallback(() => {
    setIsExpanded(false)
  }, [])

  // Reset state
  const reset = useCallback(() => {
    setIsStreaming(false)
    setIsComplete(false)
    setIsExpanded(defaultExpanded)
    setDuration(0)
    startTimeRef.current = null
    
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
  }, [defaultExpanded])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current)
      }
      if (collapseTimeoutRef.current) {
        clearTimeout(collapseTimeoutRef.current)
      }
    }
  }, [])

  const state: StreamingState = {
    isStreaming,
    isComplete,
    isExpanded,
    duration,
    durationText: formatDuration(duration),
  }

  return {
    state,
    startStreaming,
    completeStreaming,
    toggle,
    expand,
    collapse,
    reset,
  }
}

/**
 * Hook for staggered item animations in lists
 * Returns animation delay styles for each item
 */
export function useStaggerAnimation(itemCount: number, baseDelay: number = 50) {
  const getStaggerStyle = useCallback((index: number) => ({
    animationDelay: `${index * baseDelay}ms`,
  }), [baseDelay])

  const getStaggerClass = useCallback((index: number) => 
    `animate-stagger-in [animation-delay:${index * baseDelay}ms]`, 
  [baseDelay])

  return { getStaggerStyle, getStaggerClass }
}

/**
 * Hook for tracking elapsed time during streaming
 */
export function useElapsedTime(isActive: boolean) {
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    if (isActive) {
      startTimeRef.current = Date.now()
      const interval = setInterval(() => {
        if (startTimeRef.current) {
          setElapsed(Date.now() - startTimeRef.current)
        }
      }, 100)
      return () => clearInterval(interval)
    } else {
      // Keep final elapsed time when stopped
      if (startTimeRef.current) {
        setElapsed(Date.now() - startTimeRef.current)
      }
    }
  }, [isActive])

  const reset = useCallback(() => {
    setElapsed(0)
    startTimeRef.current = null
  }, [])

  const formatElapsed = useCallback((ms: number = elapsed): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }, [elapsed])

  return { elapsed, elapsedText: formatElapsed(), reset, formatElapsed }
}

export default useStreamingState



"use client"

import * as React from "react"
import { ChevronRight, Brain, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

// Context for sharing streaming state across components
interface ReasoningContextValue {
  isStreaming: boolean
  isComplete: boolean
  duration?: number
}

const ReasoningContext = React.createContext<ReasoningContextValue>({
  isStreaming: false,
  isComplete: false,
})

interface ReasoningProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.Root> {
  /** Whether content is currently streaming */
  isStreaming?: boolean
  /** Whether streaming is complete */
  isComplete?: boolean
  /** Duration in milliseconds since streaming started */
  duration?: number
  /** Auto-collapse after completion (ms). Set to 0 to disable */
  collapseDelay?: number
}

/**
 * Reasoning component for displaying AI thinking/chain-of-thought
 * 
 * Features:
 * - Auto-expands when streaming starts
 * - Shows duration while streaming
 * - Auto-collapses after completion with configurable delay
 * - Smooth expand/collapse animations
 * 
 * @example
 * ```tsx
 * <Reasoning isStreaming={isThinking} duration={elapsed}>
 *   <ReasoningTrigger />
 *   <ReasoningContent>{thinkingContent}</ReasoningContent>
 * </Reasoning>
 * ```
 */
const Reasoning = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.Root>,
  ReasoningProps
>(({ 
  isStreaming = false, 
  isComplete = false,
  duration, 
  collapseDelay = 1500,
  defaultOpen,
  open: controlledOpen,
  onOpenChange,
  children,
  ...props 
}, ref) => {
  const [internalOpen, setInternalOpen] = React.useState(defaultOpen ?? isStreaming)
  const collapseTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  // Use controlled or internal state
  const isOpen = controlledOpen ?? internalOpen
  const setOpen = onOpenChange ?? setInternalOpen

  // Auto-expand when streaming starts
  React.useEffect(() => {
    if (isStreaming && !isOpen) {
      setOpen(true)
    }
  }, [isStreaming, isOpen, setOpen])

  // Auto-collapse after completion
  React.useEffect(() => {
    if (isComplete && collapseDelay > 0) {
      collapseTimeoutRef.current = setTimeout(() => {
        setOpen(false)
      }, collapseDelay)
    }
    return () => {
      if (collapseTimeoutRef.current) {
        clearTimeout(collapseTimeoutRef.current)
      }
    }
  }, [isComplete, collapseDelay, setOpen])

  // Cancel auto-collapse on manual interaction
  const handleOpenChange = React.useCallback((open: boolean) => {
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setOpen(open)
  }, [setOpen])

  const contextValue = React.useMemo(() => ({
    isStreaming,
    isComplete,
    duration,
  }), [isStreaming, isComplete, duration])

  return (
    <ReasoningContext.Provider value={contextValue}>
      <CollapsiblePrimitive.Root 
        ref={ref} 
        open={isOpen}
        onOpenChange={handleOpenChange}
        {...props}
      >
        {children}
      </CollapsiblePrimitive.Root>
    </ReasoningContext.Provider>
  )
})
Reasoning.displayName = "Reasoning"

interface ReasoningTriggerProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger> {
  /** Override streaming state from context */
  isStreaming?: boolean
  /** Custom title when not streaming */
  title?: string
  /** Custom function to generate thinking message */
  getThinkingMessage?: (isStreaming: boolean, duration?: number) => React.ReactNode
  /** Show duration while streaming */
  showDuration?: boolean
}

const ReasoningTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  ReasoningTriggerProps
>(({ 
  className, 
  children, 
  isStreaming: isStreamingProp, 
  title = "Show reasoning",
  getThinkingMessage,
  showDuration = true,
  ...props 
}, ref) => {
  const context = React.useContext(ReasoningContext)
  const isStreaming = isStreamingProp ?? context.isStreaming
  const duration = context.duration

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const defaultThinkingMessage = (streaming: boolean, dur?: number) => {
    if (streaming) {
      return (
        <span className="flex items-center gap-1.5">
          <span className="animate-processing">Reasoning</span>
          {showDuration && dur !== undefined && (
            <span className="text-muted-foreground/70 font-mono text-[10px]">
              {formatDuration(dur)}
            </span>
          )}
        </span>
      )
    }
    return title
  }

  const message = getThinkingMessage 
    ? getThinkingMessage(isStreaming, duration)
    : defaultThinkingMessage(isStreaming, duration)

  return (
    <CollapsiblePrimitive.CollapsibleTrigger
      ref={ref}
      className={cn(
        "flex items-center gap-2 text-xs font-medium transition-colors group mb-2",
        isStreaming 
          ? "text-violet-400 hover:text-violet-300" 
          : "text-muted-foreground hover:text-foreground",
        className,
      )}
      {...props}
    >
      <ChevronRight className="h-3 w-3 transition-transform duration-200 group-data-[state=open]:rotate-90" />
      {isStreaming ? (
        <Loader2 className="h-3 w-3 animate-spin text-violet-400" />
      ) : (
        <Brain className="h-3 w-3" />
      )}
      {message}
      {children}
    </CollapsiblePrimitive.CollapsibleTrigger>
  )
})
ReasoningTrigger.displayName = "ReasoningTrigger"

interface ReasoningContentProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleContent> {
  /** Show streaming shimmer effect */
  showShimmer?: boolean
}

const ReasoningContent = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleContent>,
  ReasoningContentProps
>(({ className, children, showShimmer = false, ...props }, ref) => {
  const context = React.useContext(ReasoningContext)

  return (
    <CollapsiblePrimitive.CollapsibleContent
      ref={ref}
      className={cn(
        "overflow-hidden",
        "data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down",
        className,
      )}
      {...props}
    >
      <div 
        className={cn(
          "mt-1 rounded-lg border border-border/50 bg-muted/30 p-3 text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap",
          context.isStreaming && "border-violet-500/30 bg-violet-500/5",
          showShimmer && context.isStreaming && "animate-stream bg-gradient-to-r from-transparent via-violet-500/10 to-transparent bg-[length:200%_100%]"
        )}
      >
        {children}
      </div>
    </CollapsiblePrimitive.CollapsibleContent>
  )
})
ReasoningContent.displayName = "ReasoningContent"

export { 
  Reasoning, 
  ReasoningTrigger, 
  ReasoningContent,
  ReasoningContext,
  type ReasoningProps,
  type ReasoningTriggerProps,
  type ReasoningContentProps,
}

"use client"

import * as React from "react"
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle2,
  XCircle,
  Search,
  Shield,
  Brain,
  Sparkles,
  Terminal,
  FileText,
  Globe
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  Queue,
  QueueSection,
  QueueSectionTrigger,
  QueueSectionLabel,
  QueueSectionContent,
  QueueItem,
  QueueItemIndicator,
  QueueItemContent,
  type QueueItemStatus,
} from "@/components/ai-elements/queue"

// ============================================================================
// Types
// ============================================================================

export interface ThoughtStep {
  id: string
  type: "queue" | "tool" | "reasoning" | "search" | "result"
  name: string
  label?: string
  status: "pending" | "waiting" | "processing" | "in-progress" | "completed" | "complete" | "error"
  details?: string
  input?: Record<string, any>
  output?: any
  sources?: Array<{ title: string; url?: string }>
  timestamp?: number
}

// Icon mapping for different step types
const STEP_ICONS: Record<string, React.ReactNode> = {
  // Pipeline stages
  "policy-check": <Shield className="w-4 h-4" />,
  "reasoning": <Brain className="w-4 h-4" />,
  "intent-routing": <Sparkles className="w-4 h-4" />,
  "response-gen": <FileText className="w-4 h-4" />,
  "quality-check": <CheckCircle2 className="w-4 h-4" />,

  // Tool types  
  "retrieve_context": <Search className="w-4 h-4" />,
  "check_syllabus": <FileText className="w-4 h-4" />,
  "web_search": <Globe className="w-4 h-4" />,

  // Generic
  "tool": <Terminal className="w-4 h-4" />,
  "search": <Search className="w-4 h-4" />,
}

// ============================================================================
// ChainOfThought Component
// ============================================================================

interface ChainOfThoughtProps {
  steps: ThoughtStep[]
  isStreaming?: boolean
  defaultOpen?: boolean
  className?: string
  /** Auto-collapse after completion (ms). Set to 0 to disable */
  collapseDelay?: number
  /** Title to display */
  title?: string
}

/**
 * Unified Chain of Thought component using AI Elements Queue pattern
 * 
 * Features:
 * - Auto-expands when streaming starts
 * - Steps appear with staggered animation
 * - Auto-collapses after completion
 * - Shows processing status and duration
 */
export function ChainOfThought({
  steps,
  isStreaming = false,
  defaultOpen = true,
  collapseDelay = 1500,
  title = "Chain of Thought",
  className
}: ChainOfThoughtProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)
  const collapseTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  // Calculate stats
  const stats = React.useMemo(() => {
    const completed = steps.filter(s =>
      s.status === "completed" || s.status === "complete"
    ).length
    const hasError = steps.some(s => s.status === "error")
    const isProcessing = steps.some(s =>
      s.status === "processing" || s.status === "in-progress"
    )
    const currentStep = steps.find(s =>
      s.status === "processing" || s.status === "in-progress"
    )
    const isAllComplete = completed === steps.length && steps.length > 0
    return { completed, total: steps.length, hasError, isProcessing, currentStep, isAllComplete }
  }, [steps])

  // Dynamic title based on state
  const displayTitle = React.useMemo(() => {
    if (stats.hasError) return "Error"
    if (stats.isProcessing || isStreaming) return title || "Processing"
    if (stats.isAllComplete) return "Done"
    return title || "Processing"
  }, [stats.hasError, stats.isProcessing, stats.isAllComplete, isStreaming, title])

  // Auto-expand when streaming starts
  React.useEffect(() => {
    if (isStreaming && !isOpen) {
      setIsOpen(true)
    }
  }, [isStreaming, isOpen])

  // Auto-collapse when all done (with delay) - but KEEP visible, just collapsed
  // This allows users to still see "Done 5/5" and expand if they want
  React.useEffect(() => {
    if (!isStreaming && stats.completed === stats.total && stats.total > 0 && collapseDelay > 0) {
      // Only auto-collapse the content, not hide the entire component
      collapseTimeoutRef.current = setTimeout(() => setIsOpen(false), collapseDelay)
      return () => {
        if (collapseTimeoutRef.current) {
          clearTimeout(collapseTimeoutRef.current)
        }
      }
    }
  }, [isStreaming, stats.completed, stats.total, collapseDelay])

  // Cancel auto-collapse on manual interaction
  const handleOpenChange = React.useCallback((open: boolean) => {
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setIsOpen(open)
  }, [])

  // Don't render if no steps
  if (steps.length === 0) return null

  // Get icon for a step
  const getStepIcon = (step: ThoughtStep) => {
    if (STEP_ICONS[step.id]) return STEP_ICONS[step.id]
    if (STEP_ICONS[step.name]) return STEP_ICONS[step.name]
    if (step.type === "tool") return STEP_ICONS.tool
    if (step.type === "search") return STEP_ICONS.search
    if (step.type === "reasoning") return <Brain className="w-4 h-4" />
    return <Sparkles className="w-4 h-4" />
  }

  // Normalize status to QueueItemStatus
  const normalizeStatus = (status: ThoughtStep["status"]): QueueItemStatus => {
    if (status === "in-progress") return "processing"
    if (status === "complete") return "completed"
    if (status === "waiting") return "pending"
    return status as QueueItemStatus
  }

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={handleOpenChange}
      className={cn(
        "mb-3 rounded-lg border border-border/60 bg-card/40 backdrop-blur-sm overflow-hidden transition-colors duration-300",
        isStreaming && "border-violet-500/30",
        stats.isAllComplete && !isStreaming && "border-emerald-500/20",
        className
      )}
    >
      <CollapsibleTrigger className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors group">
        <div className="flex items-center gap-2.5">
          {stats.hasError ? (
            <XCircle className="h-4 w-4 text-red-500" />
          ) : stats.isProcessing || isStreaming ? (
            <Loader2 className="h-4 w-4 text-violet-500 animate-spin" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          )}

          <span className={cn(
            "text-sm font-medium transition-colors duration-300",
            stats.isAllComplete && !isStreaming ? "text-emerald-600 dark:text-emerald-400" : "text-foreground"
          )}>
            {displayTitle}
          </span>

          {/* Show current step when collapsed and processing */}
          {!isOpen && stats.currentStep && (stats.isProcessing || isStreaming) && (
            <span className="text-xs text-muted-foreground animate-processing ml-1">
              {stats.currentStep.label || stats.currentStep.name}...
            </span>
          )}

          {/* Show completion summary when collapsed and done */}
          {!isOpen && stats.isAllComplete && !isStreaming && (
            <span className="text-xs text-emerald-600/70 dark:text-emerald-400/70 ml-1">
              {stats.total} steps completed
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className={cn(
            "text-xs font-mono transition-colors duration-300",
            stats.isAllComplete && !isStreaming ? "text-emerald-600/70 dark:text-emerald-400/70" : "text-muted-foreground"
          )}>
            {stats.completed}/{stats.total}
          </span>
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
        <div className="px-3 pb-3 pt-1 space-y-1 border-t border-border/40">
          {steps.map((step, index) => (
            <ThoughtStepRow
              key={step.id}
              step={step}
              icon={getStepIcon(step)}
              status={normalizeStatus(step.status)}
              index={index}
              isLast={index === steps.length - 1}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

// ============================================================================
// ThoughtStepRow
// ============================================================================

interface ThoughtStepRowProps {
  step: ThoughtStep
  icon: React.ReactNode
  status: QueueItemStatus
  index: number
  isLast: boolean
}

function ThoughtStepRow({ step, icon, status, index, isLast }: ThoughtStepRowProps) {
  const [isExpanded, setIsExpanded] = React.useState(false)
  const [wasProcessing, setWasProcessing] = React.useState(false)
  const hasDetails = step.details || step.input || step.output || step.sources

  // Track status transitions for animation
  React.useEffect(() => {
    if (status === "processing") {
      setWasProcessing(true)
      setIsExpanded(true)
    } else if (status === "completed" && wasProcessing) {
      // Delay collapse after completion for visual feedback
      const timer = setTimeout(() => setIsExpanded(false), 800)
      return () => clearTimeout(timer)
    }
  }, [status, wasProcessing])

  const isActive = status === "processing"
  const isDone = status === "completed"
  const isPending = status === "pending"

  return (
    <div className={cn("relative", !isLast && "pb-1")}>
      {/* Connection line - animates when step completes */}
      {!isLast && (
        <div
          className={cn(
            "absolute left-[17px] top-7 w-0.5 h-[calc(100%-12px)] transition-colors duration-500",
            isDone ? "bg-emerald-500/40" : isActive ? "bg-violet-500/30" : "bg-border/50"
          )}
        />
      )}

      <div
        className={cn(
          "flex items-start gap-3 p-2 rounded-md transition-all duration-300",
          "animate-stagger-in",
          isActive && "bg-violet-500/10 border border-violet-500/30 shadow-sm shadow-violet-500/10",
          isDone && "opacity-80",
          isPending && "opacity-50",
          hasDetails && "cursor-pointer hover:bg-muted/30"
        )}
        style={{ animationDelay: `${index * 80}ms` }}
        onClick={() => hasDetails && setIsExpanded(!isExpanded)}
      >
        {/* Icon with status ring - pulses when active */}
        <div className={cn(
          "relative flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300",
          isActive && "bg-violet-500/20 text-violet-400 animate-pulse",
          isDone && "bg-emerald-500/15 text-emerald-500",
          isPending && "bg-muted/50 text-muted-foreground/50"
        )}>
          {icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pt-0.5">
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-sm font-medium transition-colors duration-300",
              isActive && "text-foreground",
              isDone && "text-muted-foreground",
              isPending && "text-muted-foreground/60"
            )}>
              {step.label || step.name}
            </span>
            <QueueItemIndicator status={status} />
          </div>

          {/* Inline preview for sources/results */}
          {step.sources && step.sources.length > 0 && !isExpanded && (
            <div className="flex items-center gap-1 mt-0.5 text-xs text-muted-foreground">
              <span>Found {step.sources.length} sources</span>
            </div>
          )}
        </div>

        {/* Expand indicator */}
        {hasDetails && (
          <div className="flex-shrink-0 pt-1">
            {isExpanded ? (
              <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            )}
          </div>
        )}
      </div>

      {/* Expanded details */}
      {isExpanded && hasDetails && (
        <div className="ml-10 mt-1 space-y-2 animate-fade-slide-in">
          {step.details && (
            <p className="text-xs text-muted-foreground leading-relaxed">
              {step.details}
            </p>
          )}

          {step.input && (
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Input</span>
              <pre className="text-xs bg-muted/50 p-2 rounded border border-border/50 overflow-x-auto whitespace-pre-wrap">
                {typeof step.input === 'string' ? step.input : JSON.stringify(step.input, null, 2)}
              </pre>
            </div>
          )}

          {step.output && (
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Output</span>
              <pre className="text-xs bg-muted/50 p-2 rounded border border-border/50 overflow-x-auto whitespace-pre-wrap max-h-32 overflow-y-auto">
                {typeof step.output === 'string' ? step.output : JSON.stringify(step.output, null, 2)}
              </pre>
            </div>
          )}

          {step.sources && step.sources.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Sources</span>
              <div className="flex flex-wrap gap-1">
                {step.sources.map((source, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-violet-500/10 text-violet-400 rounded-full text-xs"
                  >
                    <FileText className="w-3 h-3" />
                    {source.title}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Helper to convert existing queue/tool/thinking data to unified steps
 */
export function convertToThoughtSteps(data: {
  queue?: Array<{ id: string; name: string; label?: string; status: string }>
  tools?: Array<{ id?: string; name: string; args?: any; result?: any; status: string }>
  thinkingSteps?: Array<{ step: string; status: string; details?: string }>
  reasoning?: string
}): ThoughtStep[] {
  const steps: ThoughtStep[] = []

  // Convert queue items
  if (data.queue) {
    for (const q of data.queue) {
      steps.push({
        id: q.id,
        type: "queue",
        name: q.name,
        label: q.label,
        status: q.status as ThoughtStep["status"],
      })
    }
  }

  // Convert tools (insert at appropriate position based on when they were called)
  if (data.tools) {
    for (const t of data.tools) {
      steps.push({
        id: t.id || `tool-${t.name}`,
        type: "tool",
        name: t.name === "retrieve_context" ? "Searching course materials" : t.name,
        status: t.status as ThoughtStep["status"],
        input: t.args,
        output: t.result,
      })
    }
  }

  return steps
}

export default ChainOfThought

"use client"

import * as React from "react"
import { CheckCircle2, Circle, Loader2, Clock, XCircle, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"

// ============================================================================
// Types
// ============================================================================

export type QueueItemStatus = "pending" | "waiting" | "processing" | "completed" | "error"

export interface QueueItemData {
  id: string
  name: string
  label?: string
  status: QueueItemStatus
  description?: string
  startedAt?: number
  completedAt?: number
  error?: string
}

// ============================================================================
// Context
// ============================================================================

interface QueueContextValue {
  items: QueueItemData[]
  isProcessing: boolean
  isComplete: boolean
}

const QueueContext = React.createContext<QueueContextValue>({
  items: [],
  isProcessing: false,
  isComplete: false,
})

// ============================================================================
// Queue (Root)
// ============================================================================

interface QueueProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Queue items data */
  items?: QueueItemData[]
}

/**
 * Queue component root - container for pipeline/task display
 */
const Queue = React.forwardRef<HTMLDivElement, QueueProps>(
  ({ items = [], className, children, ...props }, ref) => {
    const isProcessing = items.some(i => i.status === "processing" || i.status === "waiting")
    const isComplete = items.length > 0 && items.every(i => i.status === "completed")

    const contextValue = React.useMemo(() => ({
      items,
      isProcessing,
      isComplete,
    }), [items, isProcessing, isComplete])

    return (
      <QueueContext.Provider value={contextValue}>
        <div ref={ref} className={cn("flex flex-col gap-1", className)} {...props}>
          {children}
        </div>
      </QueueContext.Provider>
    )
  }
)
Queue.displayName = "Queue"

// ============================================================================
// QueueSection (Collapsible Section)
// ============================================================================

interface QueueSectionProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.Root> {
  /** Auto-collapse after all items complete (ms). Set to 0 to disable */
  collapseDelay?: number
}

const QueueSection = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.Root>,
  QueueSectionProps
>(({ defaultOpen = true, collapseDelay = 1500, children, ...props }, ref) => {
  const context = React.useContext(QueueContext)
  const [isOpen, setIsOpen] = React.useState(defaultOpen)
  const collapseTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  // Auto-collapse when complete
  React.useEffect(() => {
    if (context.isComplete && collapseDelay > 0) {
      collapseTimeoutRef.current = setTimeout(() => {
        setIsOpen(false)
      }, collapseDelay)
    }
    return () => {
      if (collapseTimeoutRef.current) {
        clearTimeout(collapseTimeoutRef.current)
      }
    }
  }, [context.isComplete, collapseDelay])

  const handleOpenChange = React.useCallback((open: boolean) => {
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setIsOpen(open)
  }, [])

  return (
    <CollapsiblePrimitive.Root 
      ref={ref} 
      open={isOpen} 
      onOpenChange={handleOpenChange}
      {...props}
    >
      {children}
    </CollapsiblePrimitive.Root>
  )
})
QueueSection.displayName = "QueueSection"

// ============================================================================
// QueueSectionTrigger
// ============================================================================

interface QueueSectionTriggerProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger> {}

const QueueSectionTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  QueueSectionTriggerProps
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleTrigger
    ref={ref}
    className={cn(
      "w-full flex items-center justify-between px-3 py-2.5 rounded-t-lg",
      "bg-muted/30 hover:bg-muted/50 transition-colors text-left group",
      className
    )}
    {...props}
  >
    {children}
  </CollapsiblePrimitive.CollapsibleTrigger>
))
QueueSectionTrigger.displayName = "QueueSectionTrigger"

// ============================================================================
// QueueSectionLabel
// ============================================================================

interface QueueSectionLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Label text */
  label?: string
  /** Count to display */
  count?: number
  /** Total count */
  total?: number
  /** Icon to display */
  icon?: React.ReactNode
  /** Whether currently processing */
  isProcessing?: boolean
  /** Whether has error */
  hasError?: boolean
}

const QueueSectionLabel = React.forwardRef<HTMLDivElement, QueueSectionLabelProps>(
  ({ 
    label = "Processing", 
    count, 
    total,
    icon,
    isProcessing: isProcessingProp,
    hasError: hasErrorProp,
    className, 
    ...props 
  }, ref) => {
    const context = React.useContext(QueueContext)
    const isProcessing = isProcessingProp ?? context.isProcessing
    const completedCount = count ?? context.items.filter(i => i.status === "completed").length
    const totalCount = total ?? context.items.length
    const hasError = hasErrorProp ?? context.items.some(i => i.status === "error")

    return (
      <div ref={ref} className={cn("flex items-center gap-2.5", className)} {...props}>
        {/* Status Icon */}
        {hasError ? (
          <XCircle className="h-4 w-4 text-red-500" />
        ) : context.isComplete ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
        ) : isProcessing ? (
          <Loader2 className="h-4 w-4 text-violet-500 animate-spin" />
        ) : (
          icon || <Circle className="h-4 w-4 text-muted-foreground" />
        )}
        
        {/* Label */}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-foreground leading-none">{label}</span>
          {isProcessing && (
            <span className="text-xs text-muted-foreground mt-1 animate-processing">
              {context.items.find(i => i.status === "processing")?.label || 
               context.items.find(i => i.status === "processing")?.name}
            </span>
          )}
        </div>

        {/* Counter */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono">
            {completedCount}/{totalCount}
          </span>
          <ChevronDown className="h-4 w-4 text-muted-foreground group-data-[state=open]:hidden" />
          <ChevronUp className="h-4 w-4 text-muted-foreground hidden group-data-[state=open]:block" />
        </div>
      </div>
    )
  }
)
QueueSectionLabel.displayName = "QueueSectionLabel"

// ============================================================================
// QueueSectionContent
// ============================================================================

interface QueueSectionContentProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleContent> {}

const QueueSectionContent = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleContent>,
  QueueSectionContentProps
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleContent
    ref={ref}
    className={cn(
      "overflow-hidden",
      "data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down",
      className
    )}
    {...props}
  >
    <div className="p-2 space-y-1 border-t border-border/50 bg-background/30">
      {children}
    </div>
  </CollapsiblePrimitive.CollapsibleContent>
))
QueueSectionContent.displayName = "QueueSectionContent"

// ============================================================================
// QueueList
// ============================================================================

interface QueueListProps extends React.ComponentPropsWithoutRef<typeof ScrollArea> {
  /** Maximum height before scrolling */
  maxHeight?: string
}

const QueueList = React.forwardRef<
  React.ElementRef<typeof ScrollArea>,
  QueueListProps
>(({ maxHeight = "200px", className, children, ...props }, ref) => (
  <ScrollArea 
    ref={ref} 
    className={cn("", className)} 
    style={{ maxHeight }}
    {...props}
  >
    <ul className="space-y-1">{children}</ul>
  </ScrollArea>
))
QueueList.displayName = "QueueList"

// ============================================================================
// QueueItem
// ============================================================================

interface QueueItemProps extends React.LiHTMLAttributes<HTMLLIElement> {
  /** Item data */
  item?: QueueItemData
  /** Status (if not using item) */
  status?: QueueItemStatus
  /** Show timing info */
  showTiming?: boolean
  /** Index for stagger animation */
  index?: number
}

const QueueItem = React.forwardRef<HTMLLIElement, QueueItemProps>(
  ({ item, status: statusProp, showTiming = true, index = 0, className, children, ...props }, ref) => {
    const status = item?.status ?? statusProp ?? "pending"
    const [elapsedTime, setElapsedTime] = React.useState<number | null>(null)

    // Update elapsed time for processing items
    React.useEffect(() => {
      if (status === "processing" && item?.startedAt) {
        const interval = setInterval(() => {
          setElapsedTime(Date.now() - item.startedAt!)
        }, 100)
        return () => clearInterval(interval)
      } else if (status === "completed" && item?.startedAt && item?.completedAt) {
        setElapsedTime(item.completedAt - item.startedAt)
      } else {
        setElapsedTime(null)
      }
    }, [status, item?.startedAt, item?.completedAt])

    const formatTime = (ms: number) => {
      if (ms < 1000) return `${ms}ms`
      return `${(ms / 1000).toFixed(1)}s`
    }

    return (
      <li
        ref={ref}
        className={cn(
          "flex items-center gap-3 px-2 py-1.5 rounded-md transition-all",
          status === "processing" && "bg-violet-500/10",
          status === "completed" && "opacity-70",
          status === "error" && "bg-red-500/10",
          "animate-stagger-in",
          className
        )}
        style={{ animationDelay: `${index * 50}ms` }}
        {...props}
      >
        {/* Status Icon */}
        <QueueItemIndicator status={status} />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {children || (
            <>
              <QueueItemContent status={status}>
                {item?.label || item?.name}
              </QueueItemContent>
              {item?.description && (
                <QueueItemDescription>{item.description}</QueueItemDescription>
              )}
              {status === "error" && item?.error && (
                <div className="text-xs text-red-400 truncate">{item.error}</div>
              )}
            </>
          )}
        </div>

        {/* Timing */}
        {showTiming && elapsedTime !== null && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatTime(elapsedTime)}
          </div>
        )}
      </li>
    )
  }
)
QueueItem.displayName = "QueueItem"

// ============================================================================
// QueueItemIndicator
// ============================================================================

interface QueueItemIndicatorProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Status to display */
  status?: QueueItemStatus
  /** Whether completed */
  completed?: boolean
}

const QueueItemIndicator = React.forwardRef<HTMLSpanElement, QueueItemIndicatorProps>(
  ({ status = "pending", completed, className, ...props }, ref) => {
    const effectiveStatus = completed ? "completed" : status

    return (
      <span ref={ref} className={cn("flex-shrink-0", className)} {...props}>
        {effectiveStatus === "pending" || effectiveStatus === "waiting" ? (
          <Circle className="h-4 w-4 text-muted-foreground" />
        ) : effectiveStatus === "processing" ? (
          <Loader2 className="h-4 w-4 text-violet-500 animate-spin" />
        ) : effectiveStatus === "completed" ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500" />
        )}
      </span>
    )
  }
)
QueueItemIndicator.displayName = "QueueItemIndicator"

// ============================================================================
// QueueItemContent
// ============================================================================

interface QueueItemContentProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Status affects styling */
  status?: QueueItemStatus
  /** Whether completed */
  completed?: boolean
}

const QueueItemContent = React.forwardRef<HTMLSpanElement, QueueItemContentProps>(
  ({ status = "pending", completed, className, children, ...props }, ref) => {
    const isCompleted = completed || status === "completed"
    
    return (
      <span
        ref={ref}
        className={cn(
          "text-sm truncate block",
          isCompleted && "line-through opacity-70 text-muted-foreground",
          status === "processing" && "text-foreground font-medium",
          status === "error" && "text-red-400",
          !isCompleted && status !== "processing" && status !== "error" && "text-foreground",
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)
QueueItemContent.displayName = "QueueItemContent"

// ============================================================================
// QueueItemDescription
// ============================================================================

interface QueueItemDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {
  completed?: boolean
}

const QueueItemDescription = React.forwardRef<HTMLDivElement, QueueItemDescriptionProps>(
  ({ completed, className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "text-xs text-muted-foreground truncate",
        completed && "opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
QueueItemDescription.displayName = "QueueItemDescription"

// ============================================================================
// QueueItemActions
// ============================================================================

interface QueueItemActionsProps extends React.HTMLAttributes<HTMLDivElement> {}

const QueueItemActions = React.forwardRef<HTMLDivElement, QueueItemActionsProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity", className)}
      {...props}
    >
      {children}
    </div>
  )
)
QueueItemActions.displayName = "QueueItemActions"

// ============================================================================
// QueueItemAction
// ============================================================================

interface QueueItemActionProps extends Omit<React.ComponentPropsWithoutRef<typeof Button>, "variant" | "size"> {}

const QueueItemAction = React.forwardRef<
  React.ElementRef<typeof Button>,
  QueueItemActionProps
>(({ className, children, ...props }, ref) => (
  <Button
    ref={ref}
    variant="ghost"
    size="icon"
    className={cn("h-6 w-6", className)}
    {...props}
  >
    {children}
  </Button>
))
QueueItemAction.displayName = "QueueItemAction"

// ============================================================================
// QueueIndicator (Simple inline indicator)
// ============================================================================

interface QueueIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  current: number
  total: number
  label?: string
}

const QueueIndicator = React.forwardRef<HTMLDivElement, QueueIndicatorProps>(
  ({ current, total, label, className, ...props }, ref) => {
    const isComplete = current === total

    return (
      <div 
        ref={ref}
        className={cn("flex items-center gap-2 text-xs text-muted-foreground", className)} 
        {...props}
      >
        {isComplete ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <Loader2 className="h-3.5 w-3.5 text-violet-500 animate-spin" />
        )}
        <span>
          {label && `${label}: `}
          {current}/{total}
        </span>
      </div>
    )
  }
)
QueueIndicator.displayName = "QueueIndicator"

// ============================================================================
// Exports
// ============================================================================

export {
  Queue,
  QueueSection,
  QueueSectionTrigger,
  QueueSectionLabel,
  QueueSectionContent,
  QueueList,
  QueueItem,
  QueueItemIndicator,
  QueueItemContent,
  QueueItemDescription,
  QueueItemActions,
  QueueItemAction,
  QueueIndicator,
  QueueContext,
  type QueueProps,
  type QueueSectionProps,
  type QueueItemProps,
}

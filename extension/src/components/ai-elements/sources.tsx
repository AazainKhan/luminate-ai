"use client"

import * as React from "react"
import { ChevronRight, Link2, ExternalLink, FileText } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

// Context for sharing state across components
interface SourcesContextValue {
  count: number
  isNew: boolean
}

const SourcesContext = React.createContext<SourcesContextValue>({
  count: 0,
  isNew: false,
})

interface SourcesProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.Root> {
  /** Number of sources (passed to context) */
  count?: number
  /** Whether sources just arrived (triggers expand animation) */
  isNew?: boolean
  /** Auto-expand when sources arrive */
  autoExpand?: boolean
  /** Auto-collapse after delay (ms). Set to 0 to disable */
  collapseDelay?: number
}

/**
 * Sources component for displaying AI response citations
 * 
 * Features:
 * - Auto-expands when new sources arrive
 * - Auto-collapses after configurable delay
 * - Smooth expand/collapse animations
 * 
 * @example
 * ```tsx
 * <Sources count={sources.length}>
 *   <SourcesTrigger />
 *   <SourcesContent>
 *     {sources.map(s => <Source key={s.id} href={s.url} title={s.title} />)}
 *   </SourcesContent>
 * </Sources>
 * ```
 */
const Sources = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.Root>,
  SourcesProps
>(({ 
  count = 0,
  isNew = false,
  autoExpand = true,
  collapseDelay = 2000,
  defaultOpen,
  open: controlledOpen,
  onOpenChange,
  children,
  ...props 
}, ref) => {
  const [internalOpen, setInternalOpen] = React.useState(defaultOpen ?? false)
  const collapseTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)
  const prevCountRef = React.useRef(count)

  const isOpen = controlledOpen ?? internalOpen
  const setOpen = onOpenChange ?? setInternalOpen

  // Auto-expand when new sources arrive
  React.useEffect(() => {
    if (autoExpand && count > 0 && count > prevCountRef.current) {
      setOpen(true)
      
      // Schedule auto-collapse
      if (collapseDelay > 0) {
        if (collapseTimeoutRef.current) {
          clearTimeout(collapseTimeoutRef.current)
        }
        collapseTimeoutRef.current = setTimeout(() => {
          setOpen(false)
        }, collapseDelay)
      }
    }
    prevCountRef.current = count
  }, [count, autoExpand, collapseDelay, setOpen])

  // Cancel auto-collapse on manual interaction
  const handleOpenChange = React.useCallback((open: boolean) => {
    if (collapseTimeoutRef.current) {
      clearTimeout(collapseTimeoutRef.current)
      collapseTimeoutRef.current = null
    }
    setOpen(open)
  }, [setOpen])

  // Cleanup
  React.useEffect(() => {
    return () => {
      if (collapseTimeoutRef.current) {
        clearTimeout(collapseTimeoutRef.current)
      }
    }
  }, [])

  const contextValue = React.useMemo(() => ({
    count,
    isNew: count > prevCountRef.current,
  }), [count])

  return (
    <SourcesContext.Provider value={contextValue}>
      <CollapsiblePrimitive.Root 
        ref={ref}
        open={isOpen}
        onOpenChange={handleOpenChange}
        {...props}
      >
        {children}
      </CollapsiblePrimitive.Root>
    </SourcesContext.Provider>
  )
})
Sources.displayName = "Sources"

interface SourcesTriggerProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger> {
  /** Override count from context */
  count?: number
  /** Custom label format */
  label?: string | ((count: number) => string)
}

const SourcesTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  SourcesTriggerProps
>(({ className, children, count: countProp, label, ...props }, ref) => {
  const context = React.useContext(SourcesContext)
  const count = countProp ?? context.count

  const labelText = typeof label === 'function' 
    ? label(count) 
    : label ?? `Sources (${count})`

  return (
    <CollapsiblePrimitive.CollapsibleTrigger
      ref={ref}
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all group",
        "text-muted-foreground hover:text-foreground",
        "hover:bg-muted/50 border border-transparent hover:border-border/50",
        context.isNew && "animate-fade-slide-in",
        className,
      )}
      {...props}
    >
      <ChevronRight className="h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-90" />
      <Link2 className="h-4 w-4" />
      <span>{labelText}</span>
      {children}
    </CollapsiblePrimitive.CollapsibleTrigger>
  )
})
SourcesTrigger.displayName = "SourcesTrigger"

interface SourcesContentProps extends React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleContent> {}

const SourcesContent = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleContent>,
  SourcesContentProps
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleContent
    ref={ref}
    className={cn(
      "overflow-hidden",
      "data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down",
      "px-3 pb-2",
      className,
    )}
    {...props}
  >
    <div className="mt-1 space-y-2">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
))
SourcesContent.displayName = "SourcesContent"

interface SourceProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Source title (required) */
  title: string
  /** Source URL */
  href?: string
  /** Source description */
  description?: string
  /** Source file name */
  filename?: string
  /** Page number */
  page?: number | string
  /** Index for stagger animation */
  index?: number
}

/**
 * Individual source citation item
 */
const Source = React.forwardRef<HTMLAnchorElement, SourceProps>(
  ({ 
    className, 
    children, 
    title, 
    href, 
    description,
    filename,
    page,
    index = 0,
    ...props 
  }, ref) => {
    const hasLink = href && href !== '#'
    const Component = hasLink ? 'a' : 'div'
    
    return (
      <Component
        ref={hasLink ? ref : undefined}
        href={hasLink ? href : undefined}
        target={hasLink ? "_blank" : undefined}
        rel={hasLink ? "noopener noreferrer" : undefined}
        className={cn(
          "block rounded-md bg-card/50 p-3 transition-all border border-border/50",
          hasLink && "hover:bg-muted/50 hover:border-border cursor-pointer",
          "animate-stagger-in",
          className,
        )}
        style={{ animationDelay: `${index * 50}ms` }}
        {...props}
      >
        <div className="flex items-start gap-2">
          <FileText className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground truncate">
                {title}
              </span>
              {hasLink && (
                <ExternalLink className="w-3 h-3 text-muted-foreground shrink-0" />
              )}
            </div>
            {(filename || page) && (
              <div className="mt-0.5 text-xs text-muted-foreground truncate">
                {filename}
                {filename && page && " • "}
                {page && `Page ${page}`}
              </div>
            )}
            {description && (
              <div className="mt-1 text-xs text-muted-foreground/80 line-clamp-2">
                {description}
              </div>
            )}
          </div>
        </div>
        {children}
      </Component>
    )
  },
)
Source.displayName = "Source"

export { 
  Sources, 
  SourcesTrigger, 
  SourcesContent, 
  Source,
  SourcesContext,
  type SourcesProps,
  type SourcesTriggerProps,
  type SourcesContentProps,
  type SourceProps,
}

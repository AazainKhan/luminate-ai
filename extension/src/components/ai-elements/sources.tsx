"use client"

import * as React from "react"
import { ChevronRight, Link2, ExternalLink, FileText, Video, BookOpen, Globe, GraduationCap } from "lucide-react"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
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
  /** Loading state for skeleton */
  isLoading?: boolean
  /** Multi-collection fields (RAG v2) */
  sourceType?: "course" | "oer" | "embedded"
  linkType?: "blackboard" | "mediasite" | "generic_url"
  citationConfidence?: "high" | "medium" | "low"
}

/**
 * Individual source citation item with lazy-loaded contextual descriptions
 * Enhanced with multi-collection support (course, OER, embedded resources)
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
    isLoading = false,
    sourceType = "course",
    linkType,
    citationConfidence,
    ...props 
  }, ref) => {
    const hasLink = href && href !== '#'
    const Component = hasLink ? 'a' : 'div'
    
    // Icon selection based on source type and link type
    const Icon = linkType === "blackboard"
      ? GraduationCap
      : linkType === "mediasite" 
        ? Video 
        : sourceType === "oer" 
          ? BookOpen 
          : sourceType === "embedded" 
            ? Globe 
            : FileText
    
    // Safety check for Icon component
    if (!Icon) {
      console.warn('Source icon not found for:', { linkType, sourceType })
      return null
    }
    
    // Badge color based on source type
    const badgeVariant = sourceType === "course" 
      ? "default" 
      : sourceType === "oer" 
        ? "secondary" 
        : "outline"
    
    return (
      <Component
        ref={hasLink ? ref : undefined}
        href={hasLink ? href : undefined}
        target={hasLink ? "_blank" : undefined}
        rel={hasLink ? "noopener noreferrer" : undefined}
        className={cn(
          "block rounded-md bg-card/50 p-3 transition-all",
          "border border-transparent hover:border-blue-500/50",
          hasLink && "hover:bg-muted/50 cursor-pointer",
          "animate-stagger-in",
          className,
        )}
        style={{ animationDelay: `${index * 50}ms` }}
        {...props}
      >
        <div className="flex items-start gap-2">
          <Icon className={cn(
            "w-4 h-4 mt-0.5 shrink-0",
            linkType === "blackboard" ? "text-purple-500" : 
            linkType === "mediasite" ? "text-blue-500" : "text-muted-foreground"
          )} />
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-2 flex-wrap">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground line-clamp-1">
                    {title}
                  </span>
                  {hasLink && (
                    <ExternalLink className="w-3 h-3 text-muted-foreground shrink-0" />
                  )}
                </div>
                {filename && (
                  <div className="mt-0.5 text-xs text-muted-foreground/70 line-clamp-1">
                    {filename}
                    {page && ` • Page ${page}`}
                  </div>
                )}
              </div>
              {/* Badges */}
              <div className="flex items-center gap-1 shrink-0">
                {/* Blackboard/Course indicator */}
                {linkType === "blackboard" && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-purple-500 text-purple-500">
                    COURSE
                  </Badge>
                )}
                {/* Mediasite/Video indicator */}
                {linkType === "mediasite" && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-blue-500 text-blue-500">
                    VIDEO
                  </Badge>
                )}
                {/* Embedded indicator */}
                {linkType === "generic_url" && sourceType === "embedded" && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                    EMBEDDED
                  </Badge>
                )}
              </div>
            </div>
            {/* Description with fade-in animation */}
            {isLoading ? (
              <div className="mt-1 space-y-1.5">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
              </div>
            ) : description ? (
              <div className="mt-1 text-xs text-muted-foreground/80 line-clamp-2 animate-fade-in">
                {description}
              </div>
            ) : null}
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

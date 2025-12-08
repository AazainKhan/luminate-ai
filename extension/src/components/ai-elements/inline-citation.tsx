"use client"

import type React from "react"

import { ExternalLink, FileText, BookOpen, GraduationCap } from "lucide-react"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface InlineCitationProps {
  children: React.ReactNode
  className?: string
}

/**
 * InlineCitation - Root wrapper for content with embedded citation markers.
 * 
 * This component wraps content that contains [1], [2] style citations.
 * CRITICAL: Uses <span> not <div> to ensure citations flow inline with text.
 */
export function InlineCitation({ children, className }: InlineCitationProps) {
  return (
    <span className={cn("text-sm leading-relaxed text-foreground inline", className)}>
      {children}
    </span>
  )
}

interface InlineCitationTextProps {
  children: React.ReactNode
  className?: string
}

/**
 * InlineCitationText - Wrapper for text content between citation markers.
 * 
 * When children is a string, it preserves whitespace and allows markdown 
 * to be rendered by the parent. When children is a ReactNode (like Response),
 * it renders inline to flow naturally with citation markers.
 */
export function InlineCitationText({ children, className }: InlineCitationTextProps) {
  return (
    <span className={cn("inline", className)}>
      {children}
    </span>
  )
}

interface InlineCitationCardProps {
  children: React.ReactNode
}

export function InlineCitationCard({ children }: InlineCitationCardProps) {
  return <HoverCard openDelay={150} closeDelay={100}>{children}</HoverCard>
}

interface InlineCitationCardTriggerProps {
  number: string
  url?: string
  title?: string
  /** Optional source info for enhanced badge display */
  sourceInfo?: {
    module?: string
    week?: number
  }
  className?: string
}

export function InlineCitationCardTrigger({ number, url, title, sourceInfo, className }: InlineCitationCardTriggerProps) {
  // Handle local sources without real URLs
  const isLocalSource = !url || url.startsWith("#")

  return (
    <HoverCardTrigger asChild>
      <button 
        className={cn(
          "inline-flex items-center gap-1 px-1 py-0 rounded text-[10px] font-medium align-baseline",
          "bg-violet-500/10 text-violet-600 dark:text-violet-300 hover:bg-violet-500/20",
          "border border-violet-500/20 hover:border-violet-500/40",
          "transition-all duration-150 cursor-pointer select-none",
          "focus:outline-none focus:ring-2 focus:ring-violet-500/50",
          "relative -top-[0.15em] ml-0.5",
          className
        )}
        aria-label={`Citation ${number}${sourceInfo?.module ? ` from ${sourceInfo.module}` : ''}`}
      >
        {title ? (
          <span className="max-w-[150px] truncate">{title}</span>
        ) : (
          <span>[{number}]</span>
        )}
      </button>
    </HoverCardTrigger>
  )
}

interface InlineCitationCardBodyProps {
  children: React.ReactNode
}

export function InlineCitationCardBody({ children }: InlineCitationCardBodyProps) {
  return (
    <HoverCardContent 
      className="w-80 bg-card border-border shadow-lg p-4"
      sideOffset={8}
      align="start"
    >
      {children}
    </HoverCardContent>
  )
}

interface InlineCitationSourceProps {
  title: string
  url?: string
  description?: string
  sourceFile?: string
  /** Module name (e.g., "Module 4") */
  module?: string
  /** Week number (1-14) */
  week?: number
  /** Content snippet for preview */
  content?: string
}

export function InlineCitationSource({ 
  title, 
  url, 
  description
}: InlineCitationSourceProps) {
  // Handle local sources without real URLs
  const isLocalSource = !url || url.startsWith("#")
  
  return (
    <div className="space-y-2.5">
      {/* Title with icon */}
      <div className="flex items-start gap-2">
        <div className={cn(
          "flex items-center justify-center w-6 h-6 rounded shrink-0 mt-0.5",
          isLocalSource 
            ? "bg-violet-500/15 text-violet-400" 
            : "bg-blue-500/15 text-blue-400"
        )}>
          {isLocalSource ? (
            <BookOpen className="h-3 w-3" />
          ) : (
            <ExternalLink className="h-3 w-3" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          {isLocalSource ? (
            <h4 className="text-sm font-semibold text-foreground line-clamp-2 leading-snug">
              {title}
            </h4>
          ) : (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-foreground hover:text-blue-400 line-clamp-2 leading-snug transition-colors block"
            >
              {title}
            </a>
          )}
        </div>
      </div>
      
      {/* Description */}
      {description && (
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">
          {description}
        </p>
      )}
    </div>
  )
}

interface InlineCitationQuoteProps {
  children: React.ReactNode
}

export function InlineCitationQuote({ children }: InlineCitationQuoteProps) {
  return (
    <blockquote className="mt-3 pl-3 border-l-2 border-violet-500/50 text-xs italic text-muted-foreground bg-muted/30 py-2 pr-2 rounded-r">
      {children}
    </blockquote>
  )
}

// Re-export types for external use
export type { 
  InlineCitationProps,
  InlineCitationCardTriggerProps,
  InlineCitationSourceProps 
}

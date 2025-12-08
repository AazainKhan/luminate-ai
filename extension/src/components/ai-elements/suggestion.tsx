"use client"

import * as React from "react"
import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

// ============================================================================
// Suggestions Container (horizontal scrollable)
// ============================================================================

interface SuggestionsProps {
  children: React.ReactNode
  className?: string
}

export function Suggestions({ className, children }: SuggestionsProps) {
  return (
    <ScrollArea className="w-full overflow-x-auto whitespace-nowrap">
      <div className={cn("flex w-max flex-nowrap items-center gap-2 pb-2", className)}>
        {children}
      </div>
      <ScrollBar className="hidden" orientation="horizontal" />
    </ScrollArea>
  )
}

// ============================================================================
// Individual Suggestion Button
// ============================================================================

interface SuggestionProps extends Omit<React.ComponentProps<typeof Button>, 'onClick'> {
  suggestion: string
  onClick?: (suggestion: string) => void
  icon?: React.ReactNode
}

export function Suggestion({ 
  suggestion, 
  onClick, 
  icon,
  className, 
  variant = "outline",
  size = "sm",
  children,
  ...props 
}: SuggestionProps) {
  const handleClick = () => {
    onClick?.(suggestion)
  }

  return (
    <Button
      className={cn(
        "cursor-pointer rounded-full px-4 h-8",
        "bg-muted/50 border-border/50 hover:bg-muted hover:border-border",
        "text-foreground text-sm transition-all duration-200",
        "hover:shadow-sm",
        className
      )}
      onClick={handleClick}
      size={size}
      type="button"
      variant={variant}
      {...props}
    >
      {icon || <Sparkles className="h-3 w-3 mr-1.5 text-violet-400" />}
      {children || suggestion}
    </Button>
  )
}

// ============================================================================
// Smart Suggestions (context-aware suggestions for COMP 237)
// ============================================================================

interface SmartSuggestionsProps {
  onSelect: (suggestion: string) => void
  messageCount?: number
  className?: string
}

// Context-aware suggestions based on conversation state
const INITIAL_SUGGESTIONS = [
  "Explain backpropagation step by step",
  "What is gradient descent?",
  "How do neural networks learn?",
  "Compare supervised vs unsupervised learning",
]

const FOLLOW_UP_SUGGESTIONS = [
  "Can you give me an example?",
  "Explain this more simply",
  "How does this apply to the assignment?",
  "Quiz me on this topic",
]

export function SmartSuggestions({ onSelect, messageCount = 0, className }: SmartSuggestionsProps) {
  const suggestions = messageCount === 0 ? INITIAL_SUGGESTIONS : FOLLOW_UP_SUGGESTIONS
  
  return (
    <Suggestions className={className}>
      {suggestions.map((suggestion) => (
        <Suggestion
          key={suggestion}
          suggestion={suggestion}
          onClick={onSelect}
        />
      ))}
    </Suggestions>
  )
}

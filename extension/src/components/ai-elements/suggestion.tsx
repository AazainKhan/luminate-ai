"use client"

import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface SuggestionProps {
  text: string
  onSelect?: () => void
  className?: string
}

export function Suggestion({ text, onSelect, className }: SuggestionProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      className={cn(
        "bg-muted/50 border-border hover:bg-muted text-foreground text-sm h-auto py-2 px-3 transition-colors",
        className
      )}
      onClick={onSelect}
    >
      <Sparkles className="h-3 w-3 mr-1.5 text-violet-400" />
      {text}
    </Button>
  )
}

interface SuggestionListProps {
  suggestions: string[]
  onSelect?: (suggestion: string) => void
  className?: string
}

export function SuggestionList({ suggestions, onSelect, className }: SuggestionListProps) {
  if (!suggestions || suggestions.length === 0) return null
  
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {suggestions.map((suggestion, index) => (
        <Suggestion
          key={index}
          text={suggestion}
          onSelect={() => onSelect?.(suggestion)}
        />
      ))}
    </div>
  )
}

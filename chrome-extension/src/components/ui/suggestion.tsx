import * as React from "react"
import { cn } from "@/lib/utils"

export interface SuggestionProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline"
}

const Suggestion = React.forwardRef<HTMLButtonElement, SuggestionProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-3 py-1.5",
          "text-sm font-medium transition-all duration-200",
          "border border-border bg-background hover:bg-accent hover:border-primary/50",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:pointer-events-none disabled:opacity-50",
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Suggestion.displayName = "Suggestion"

const SuggestionGroup = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-wrap gap-2", className)}
    {...props}
  />
))
SuggestionGroup.displayName = "SuggestionGroup"

export { Suggestion, SuggestionGroup }

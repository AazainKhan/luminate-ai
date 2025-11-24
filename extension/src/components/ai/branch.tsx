/**
 * Branch component for AI response variations
 * Navigate between multiple AI-generated responses
 */

import * as React from "react"
import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface BranchProps extends React.HTMLAttributes<HTMLDivElement> {
  current?: number
  total?: number
  onNavigate?: (index: number) => void
  children?: React.ReactNode
}

export function Branch({
  current = 1,
  total = 1,
  onNavigate,
  className,
  children,
  ...props
}: BranchProps) {
  const handlePrevious = () => {
    if (onNavigate && current > 1) {
      onNavigate(current - 1)
    }
  }

  const handleNext = () => {
    if (onNavigate && current < total) {
      onNavigate(current + 1)
    }
  }

  if (total <= 1) return <>{children}</>

  return (
    <div className={cn("space-y-2", className)} {...props}>
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handlePrevious}
          disabled={current <= 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span>
          {current} / {total}
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleNext}
          disabled={current >= total}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      {children}
    </div>
  )
}

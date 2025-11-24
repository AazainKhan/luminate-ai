/**
 * Actions component for AI responses
 * Interactive buttons for message actions
 */

import * as React from "react"
import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Copy, ThumbsUp, ThumbsDown, RefreshCw, Check } from "lucide-react"

interface ActionsProps extends React.HTMLAttributes<HTMLDivElement> {
  onCopy?: () => void
  onThumbsUp?: () => void
  onThumbsDown?: () => void
  onRegenerate?: () => void
  children?: React.ReactNode
}

export function Actions({
  onCopy,
  onThumbsUp,
  onThumbsDown,
  onRegenerate,
  className,
  children,
  ...props
}: ActionsProps) {
  const [copied, setCopied] = React.useState(false)

  const handleCopy = () => {
    if (onCopy) {
      onCopy()
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div
      className={cn(
        "flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity",
        className
      )}
      {...props}
    >
      {onCopy && (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleCopy}
        >
          {copied ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
        </Button>
      )}
      {onThumbsUp && (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onThumbsUp}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </Button>
      )}
      {onThumbsDown && (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onThumbsDown}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </Button>
      )}
      {onRegenerate && (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onRegenerate}
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      )}
      {children}
    </div>
  )
}

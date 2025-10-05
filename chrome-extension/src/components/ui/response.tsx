import * as React from "react"
import { cn } from "@/lib/utils"

export interface ResponseProps extends React.HTMLAttributes<HTMLDivElement> {
  isStreaming?: boolean
}

const Response = React.forwardRef<HTMLDivElement, ResponseProps>(
  ({ className, isStreaming, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "prose prose-stone dark:prose-invert max-w-none",
          "prose-p:leading-7 prose-p:my-2",
          "prose-pre:bg-muted prose-pre:border prose-pre:border-border",
          "prose-code:text-sm prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded",
          "prose-strong:font-semibold prose-strong:text-foreground",
          "prose-a:text-primary prose-a:no-underline hover:prose-a:underline",
          "prose-headings:font-semibold prose-headings:tracking-tight",
          "prose-ul:my-2 prose-ol:my-2 prose-li:my-1",
          "text-foreground whitespace-pre-wrap break-words",
          isStreaming && "animate-pulse",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
Response.displayName = "Response"

export { Response }

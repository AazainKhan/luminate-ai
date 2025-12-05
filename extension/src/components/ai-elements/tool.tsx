"use client"

import { useState, useEffect } from "react"
import { Wrench, ChevronDown, ChevronUp, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ToolProps {
  name: string
  args?: Record<string, any>
  result?: any
  status: "pending" | "in-progress" | "completed" | "error"
}

export function Tool({ name, args, result, status }: ToolProps) {
  const [isOpen, setIsOpen] = useState(status === "in-progress")

  // Auto-open when in-progress, auto-close when completed
  useEffect(() => {
    if (status === "in-progress") {
      setIsOpen(true)
    } else if (status === "completed") {
      // Optional: Add a small delay before closing to let user see it finished
      const timer = setTimeout(() => setIsOpen(false), 1500)
      return () => clearTimeout(timer)
    }
  }, [status])

  // Helper to parse result if it's a stringified JSON
  const parsedResult = (() => {
    if (typeof result === 'string') {
      try {
        return JSON.parse(result)
      } catch (e) {
        return result
      }
    }
    return result
  })()

  // Helper to render result content nicely
  const renderResultContent = (content: any) => {
    if (Array.isArray(content)) {
      return (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground italic">Found {content.length} items</div>
          {content.map((item, i) => (
            <div key={i} className="bg-background/50 p-2 rounded border border-border/50 text-xs">
              {item.title && <div className="font-medium text-foreground mb-1">{item.title}</div>}
              {item.preview && <div className="text-muted-foreground line-clamp-2">{item.preview}</div>}
              {!item.title && !item.preview && <pre className="whitespace-pre-wrap">{JSON.stringify(item, null, 2)}</pre>}
            </div>
          ))}
        </div>
      )
    }
    return <pre className="text-xs bg-muted/50 p-2 rounded-md overflow-x-auto font-mono text-foreground/90 border border-border/50 whitespace-pre-wrap break-words max-w-full">{JSON.stringify(content, null, 2)}</pre>
  }

  return (
    <div className="my-2 rounded-lg border border-border bg-card/50 overflow-hidden transition-all w-full max-w-full">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/10 text-purple-400">
          <Wrench className="h-3.5 w-3.5" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">{name}</span>
            <span
              className={cn(
                "text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wider font-medium",
                status === "completed" && "bg-emerald-500/10 text-emerald-500",
                status === "error" && "bg-red-500/10 text-red-500",
                status === "in-progress" && "bg-blue-500/10 text-blue-500",
                status === "pending" && "bg-muted text-muted-foreground"
              )}
            >
              {status}
            </span>
          </div>
        </div>

        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {isOpen && (args || result) && (
        <div className="px-3 pb-3 pt-1 space-y-3 border-t border-border/50 bg-background/30">
          {args && (
            <div className="space-y-1.5 w-full min-w-0">
              <div className="text-xs font-medium text-muted-foreground">Input</div>
              <pre className="text-xs bg-muted/50 p-2 rounded-md overflow-x-auto font-mono text-foreground/90 border border-border/50 whitespace-pre-wrap break-words max-w-full">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}
          {result && (
            <div className="space-y-1.5 w-full min-w-0">
              <div className="text-xs font-medium text-muted-foreground">Output</div>
              {renderResultContent(parsedResult)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

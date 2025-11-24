"use client"

import * as React from "react"
import { ChevronRight, Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

const Reasoning = CollapsiblePrimitive.Root

const ReasoningTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger>
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleTrigger
    ref={ref}
    className={cn(
      "flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-300 transition-colors group mb-2",
      className,
    )}
    {...props}
  >
    <ChevronRight className="h-3 w-3 transition-transform group-data-[state=open]:rotate-90" />
    <Brain className="h-3 w-3" />
    Show reasoning
    {children}
  </CollapsiblePrimitive.CollapsibleTrigger>
))
ReasoningTrigger.displayName = "ReasoningTrigger"

const ReasoningContent = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleContent>,
  React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleContent>
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleContent
    ref={ref}
    className={cn(
      "overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down",
      className,
    )}
    {...props}
  >
    <div className="mt-1 rounded-lg border border-slate-800/60 bg-slate-900/80 p-2 text-xs text-slate-300 leading-relaxed">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
))
ReasoningContent.displayName = "ReasoningContent"

export { Reasoning, ReasoningTrigger, ReasoningContent }

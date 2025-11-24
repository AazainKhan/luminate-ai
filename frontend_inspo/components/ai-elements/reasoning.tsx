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
      "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-white/5 transition-colors group",
      className,
    )}
    {...props}
  >
    <ChevronRight className="h-4 w-4 transition-transform group-data-[state=open]:rotate-90" />
    <Brain className="h-4 w-4" />
    Reasoning
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
      "overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down px-3 pb-2",
      className,
    )}
    {...props}
  >
    <div className="mt-1 text-sm text-gray-400 leading-relaxed border-l-2 border-white/10 pl-4 py-1">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
))
ReasoningContent.displayName = "ReasoningContent"

export { Reasoning, ReasoningTrigger, ReasoningContent }

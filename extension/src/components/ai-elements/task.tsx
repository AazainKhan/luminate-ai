"use client"

import * as React from "react"
import { CheckCircle2, Circle, Loader2, ChevronRight, FileText } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

const Task = CollapsiblePrimitive.Root

const TaskTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger> & { title: string }
>(({ className, children, title, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleTrigger
    ref={ref}
    className={cn(
      "flex w-full items-center gap-2 rounded-lg bg-white/5 p-3 text-left text-sm font-medium hover:bg-white/10 transition-colors group",
      className,
    )}
    {...props}
  >
    <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-90" />
    {title}
    {children}
  </CollapsiblePrimitive.CollapsibleTrigger>
))
TaskTrigger.displayName = "TaskTrigger"

const TaskContent = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleContent>,
  React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleContent>
>(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleContent
    ref={ref}
    className={cn(
      "overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down pl-4 pr-2 pb-2 pt-0",
      className,
    )}
    {...props}
  >
    <div className="mt-2 flex flex-col gap-2 border-l border-white/10 pl-4">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
))
TaskContent.displayName = "TaskContent"

const TaskItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { status?: "pending" | "in-progress" | "completed" }
>(({ className, children, status = "pending", ...props }, ref) => (
  <div ref={ref} className={cn("flex items-start gap-3 text-sm text-gray-400", className)} {...props}>
    <div className="mt-0.5 shrink-0">
      {status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-400" />}
      {status === "in-progress" && <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />}
      {status === "pending" && <Circle className="h-4 w-4 text-gray-600" />}
    </div>
    <div className="flex-1">{children}</div>
  </div>
))
TaskItem.displayName = "TaskItem"

const TaskItemFile = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(
  ({ className, children, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium bg-white/10 text-gray-300 mx-1",
        className,
      )}
      {...props}
    >
      <FileText className="h-3 w-3" />
      {children}
    </span>
  ),
)
TaskItemFile.displayName = "TaskItemFile"

export { Task, TaskTrigger, TaskContent, TaskItem, TaskItemFile }

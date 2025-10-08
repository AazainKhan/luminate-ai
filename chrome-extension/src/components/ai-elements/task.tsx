"use client";

import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDownIcon, CheckCircle2Icon, CircleDashedIcon, FileIcon } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";
import { useState } from "react";

/**
 * Task - Container component managing collapsible state
 * Shows AI workflow progress with expandable details
 */
export type TaskProps = ComponentProps<typeof Collapsible> & {
  defaultOpen?: boolean;
  status?: "pending" | "in_progress" | "completed" | "error";
};

export const Task = ({
  className,
  defaultOpen = false,
  status = "in_progress",
  children,
  ...props
}: TaskProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn(
        "group rounded-lg border bg-card transition-all",
        status === "completed" && "border-green-500/20 bg-green-500/5",
        status === "error" && "border-destructive/20 bg-destructive/5",
        className
      )}
      {...props}
    >
      {children}
    </Collapsible>
  );
};

/**
 * TaskTrigger - Clickable header showing task title
 * Displays status icon and expand/collapse chevron
 */
export type TaskTriggerProps = ComponentProps<typeof CollapsibleTrigger> & {
  title: string;
  status?: "pending" | "in_progress" | "completed" | "error";
  subtitle?: string;
};

export const TaskTrigger = ({
  title,
  status = "in_progress",
  subtitle,
  className,
  ...props
}: TaskTriggerProps) => {
  const StatusIcon =
    status === "completed"
      ? CheckCircle2Icon
      : status === "error"
      ? CircleDashedIcon
      : CircleDashedIcon;

  return (
    <CollapsibleTrigger
      className={cn(
        "flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-all hover:bg-accent/50",
        "group-data-[state=open]:bg-accent/30",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <StatusIcon
          className={cn(
            "h-4 w-4 shrink-0",
            status === "completed" && "text-green-600 dark:text-green-400",
            status === "error" && "text-destructive",
            status === "in_progress" && "text-primary animate-pulse",
            status === "pending" && "text-muted-foreground"
          )}
        />
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-medium leading-tight truncate">{title}</h4>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-0.5 truncate">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      <ChevronDownIcon className="h-4 w-4 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180 text-muted-foreground" />
    </CollapsibleTrigger>
  );
};

/**
 * TaskContent - Container for task items with animations
 * Smoothly expands/collapses to show task details
 */
export type TaskContentProps = ComponentProps<typeof CollapsibleContent>;

export const TaskContent = ({
  className,
  children,
  ...props
}: TaskContentProps) => (
  <CollapsibleContent
    className={cn(
      "overflow-hidden transition-all data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  >
    <div className="border-t px-4 py-3 space-y-2">
      {children}
    </div>
  </CollapsibleContent>
);

/**
 * TaskItem - Individual task item with progress indicator
 * Shows a single step in the workflow
 */
export type TaskItemProps = ComponentProps<"div"> & {
  status?: "pending" | "in_progress" | "completed" | "error";
  icon?: ReactNode;
};

export const TaskItem = ({
  className,
  status = "completed",
  icon,
  children,
  ...props
}: TaskItemProps) => (
  <div
    className={cn(
      "flex items-start gap-2 text-sm leading-relaxed",
      status === "pending" && "text-muted-foreground",
      status === "completed" && "text-foreground",
      className
    )}
    {...props}
  >
    <div className="mt-0.5 shrink-0">
      {icon || (
        <div
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            status === "completed" && "bg-green-600 dark:bg-green-400",
            status === "in_progress" && "bg-primary animate-pulse",
            status === "pending" && "bg-muted-foreground/50",
            status === "error" && "bg-destructive"
          )}
        />
      )}
    </div>
    <div className="flex-1 min-w-0">{children}</div>
  </div>
);

/**
 * TaskItemFile - File reference badge with optional icon
 * Highlights file names in task items
 */
export type TaskItemFileProps = ComponentProps<"span"> & {
  icon?: ReactNode;
};

export const TaskItemFile = ({
  className,
  icon,
  children,
  ...props
}: TaskItemFileProps) => (
  <span
    className={cn(
      "inline-flex items-center gap-1.5 rounded-md bg-secondary px-2 py-0.5 font-mono text-xs",
      className
    )}
    {...props}
  >
    {icon || <FileIcon className="h-3 w-3 text-muted-foreground" />}
    <span>{children}</span>
  </span>
);

/**
 * TaskList - Container for multiple tasks
 * Stacks tasks with proper spacing
 */
export type TaskListProps = ComponentProps<"div">;

export const TaskList = ({ className, children, ...props }: TaskListProps) => (
  <div className={cn("space-y-3", className)} {...props}>
    {children}
  </div>
);

/**
 * TaskProgress - Progress indicator for task completion
 * Shows visual progress bar
 */
export type TaskProgressProps = ComponentProps<"div"> & {
  value: number; // 0-100
  max?: number;
};

export const TaskProgress = ({
  value,
  max = 100,
  className,
  ...props
}: TaskProgressProps) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("mt-2", className)} {...props}>
      <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
        <span>Progress</span>
        <span>{Math.round(percentage)}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};



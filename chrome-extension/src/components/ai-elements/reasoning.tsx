"use client";

import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDownIcon, BrainIcon } from "lucide-react";
import type { ComponentProps } from "react";
import { useState } from "react";

export type ReasoningProps = ComponentProps<typeof Collapsible> & {
  defaultOpen?: boolean;
  autoExpand?: boolean;
};

export const Reasoning = ({
  className,
  defaultOpen = false,
  autoExpand = false,
  children,
  ...props
}: ReasoningProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen || autoExpand);

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn("group", className)}
      {...props}
    >
      {children}
    </Collapsible>
  );
};

export type ReasoningTriggerProps = ComponentProps<typeof CollapsibleTrigger>;

export const ReasoningTrigger = ({
  className,
  children,
  ...props
}: ReasoningTriggerProps) => (
  <CollapsibleTrigger
    className={cn(
      "flex w-full items-center gap-2 rounded-lg border bg-secondary/50 px-3 py-2 text-sm font-medium transition-all hover:bg-secondary",
      "data-[state=open]:bg-secondary data-[state=open]:border-primary/20",
      className
    )}
    {...props}
  >
    <BrainIcon className="h-4 w-4 text-primary" />
    <span className="flex-1 text-left">
      {children ?? "View reasoning"}
    </span>
    <ChevronDownIcon className="h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
  </CollapsibleTrigger>
);

export type ReasoningContentProps = ComponentProps<typeof CollapsibleContent>;

export const ReasoningContent = ({
  className,
  children,
  ...props
}: ReasoningContentProps) => (
  <CollapsibleContent
    className={cn(
      "overflow-hidden transition-all data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
      className
    )}
    {...props}
  >
    <div className="mt-2 rounded-lg border border-dashed border-primary/20 bg-primary/5 p-4 text-sm text-muted-foreground">
      {children}
    </div>
  </CollapsibleContent>
);



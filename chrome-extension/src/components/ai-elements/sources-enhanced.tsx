"use client";

import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDownIcon, ExternalLinkIcon, FileTextIcon } from "lucide-react";
import type { ComponentProps } from "react";
import { useState } from "react";

export type SourcesEnhancedProps = ComponentProps<typeof Collapsible> & {
  defaultOpen?: boolean;
  sourceCount?: number;
};

export const SourcesEnhanced = ({
  className,
  defaultOpen = false,
  sourceCount,
  children,
  ...props
}: SourcesEnhancedProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

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

export type SourcesEnhancedTriggerProps = ComponentProps<typeof CollapsibleTrigger> & {
  count?: number;
};

export const SourcesEnhancedTrigger = ({
  className,
  count,
  children,
  ...props
}: SourcesEnhancedTriggerProps) => (
  <CollapsibleTrigger
    className={cn(
      "flex w-full items-center gap-2 rounded-lg border bg-secondary/30 px-3 py-2 text-sm font-medium transition-all hover:bg-secondary",
      "data-[state=open]:bg-secondary data-[state=open]:border-primary/20",
      className
    )}
    {...props}
  >
    <FileTextIcon className="h-4 w-4 text-primary" />
    <span className="flex-1 text-left">
      {children ?? `View sources${count ? ` (${count})` : ""}`}
    </span>
    <ChevronDownIcon className="h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
  </CollapsibleTrigger>
);

export type SourcesEnhancedContentProps = ComponentProps<typeof CollapsibleContent>;

export const SourcesEnhancedContent = ({
  className,
  children,
  ...props
}: SourcesEnhancedContentProps) => (
  <CollapsibleContent
    className={cn(
      "overflow-hidden transition-all data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
      className
    )}
    {...props}
  >
    <div className="mt-2 space-y-2">
      {children}
    </div>
  </CollapsibleContent>
);

export type SourceItemProps = {
  title: string;
  url?: string;
  description?: string;
  module?: string;
  className?: string;
};

export const SourceItem = ({
  title,
  url,
  description,
  module,
  className,
}: SourceItemProps) => (
  <a
    href={url || '#'}
    target="_blank"
    rel="noopener noreferrer"
    className={cn(
      "group block p-3 rounded-lg border bg-card hover:bg-accent transition-all hover:shadow-md hover:scale-[1.01] active:scale-[0.99]",
      className
    )}
  >
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 transition-colors group-hover:bg-primary/20">
        <FileTextIcon className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-sm font-medium leading-tight group-hover:text-primary transition-colors">
            {title}
          </h4>
          <ExternalLinkIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        {module && (
          <div className="mt-1">
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {module}
            </span>
          </div>
        )}
        {description && (
          <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
            {description}
          </p>
        )}
      </div>
    </div>
  </a>
);



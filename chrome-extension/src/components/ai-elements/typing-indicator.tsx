"use client";

import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export type TypingIndicatorProps = HTMLAttributes<HTMLDivElement>;

export const TypingIndicator = ({
  className,
  ...props
}: TypingIndicatorProps) => (
  <div
    className={cn("flex items-center gap-1", className)}
    role="status"
    aria-label="AI is typing"
    {...props}
  >
    <div className="flex gap-1">
      <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
    </div>
    <span className="ml-2 text-sm text-muted-foreground">
      Thinking...
    </span>
  </div>
);



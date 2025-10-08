"use client";

import { cn } from "@/lib/utils";
import { Button, type ButtonProps } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { ComponentProps, ReactNode } from "react";

/**
 * Actions - Container for grouping action buttons
 * Displays action buttons in a horizontal row with proper spacing
 */
export type ActionsProps = ComponentProps<"div">;

export const Actions = ({ className, children, ...props }: ActionsProps) => (
  <div
    className={cn("flex items-center gap-1 flex-wrap", className)}
    role="group"
    {...props}
  >
    {children}
  </div>
);

/**
 * Action - Individual action button with optional tooltip
 * Ghost variant by default for cleaner chat interfaces
 */
export type ActionProps = ButtonProps & {
  label: string;
  tooltip?: string;
};

export const Action = ({
  label,
  tooltip,
  variant = "ghost",
  size = "sm",
  className,
  children,
  disabled,
  ...props
}: ActionProps) => {
  const button = (
    <Button
      variant={variant}
      size={size}
      className={cn(
        "h-8 min-w-8 transition-all hover:scale-105 active:scale-95",
        className
      )}
      aria-label={label}
      disabled={disabled}
      {...props}
    >
      {children}
    </Button>
  );

  // If tooltip is provided, wrap in Tooltip
  if (tooltip || disabled) {
    return (
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent>
            <p className="text-xs">
              {disabled && tooltip ? tooltip : tooltip || label}
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return button;
};

/**
 * ActionGroup - Grouped actions with visual separator
 * Useful for organizing related actions together
 */
export type ActionGroupProps = ComponentProps<"div"> & {
  label?: string;
};

export const ActionGroup = ({
  label,
  className,
  children,
  ...props
}: ActionGroupProps) => (
  <div
    className={cn("flex items-center gap-1", className)}
    role="group"
    aria-label={label}
    {...props}
  >
    {children}
  </div>
);

/**
 * ActionSeparator - Visual separator between action groups
 */
export type ActionSeparatorProps = ComponentProps<"div">;

export const ActionSeparator = ({
  className,
  ...props
}: ActionSeparatorProps) => (
  <div
    className={cn("h-4 w-px bg-border mx-1", className)}
    role="separator"
    aria-orientation="vertical"
    {...props}
  />
);

/**
 * Utility: Copy text to clipboard with fallback
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers or non-HTTPS
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const success = document.execCommand("copy");
      textArea.remove();
      return success;
    }
  } catch (err) {
    console.error("Failed to copy:", err);
    return false;
  }
};



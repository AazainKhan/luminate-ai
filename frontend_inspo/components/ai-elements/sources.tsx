"use client"

import * as React from "react"
import { ChevronRight, Link2 } from "lucide-react"
import { cn } from "@/lib/utils"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

const Sources = CollapsiblePrimitive.Root

const SourcesTrigger = React.forwardRef<
  React.ElementRef<typeof CollapsiblePrimitive.CollapsibleTrigger>,
  React.ComponentPropsWithoutRef<typeof CollapsiblePrimitive.CollapsibleTrigger> & { count: number }
>(({ className, children, count, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleTrigger
    ref={ref}
    className={cn(
      "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-white/5 transition-colors group",
      className,
    )}
    {...props}
  >
    <ChevronRight className="h-4 w-4 transition-transform group-data-[state=open]:rotate-90" />
    <Link2 className="h-4 w-4" />
    Sources ({count}){children}
  </CollapsiblePrimitive.CollapsibleTrigger>
))
SourcesTrigger.displayName = "SourcesTrigger"

const SourcesContent = React.forwardRef<
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
    <div className="mt-1 space-y-2">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
))
SourcesContent.displayName = "SourcesContent"

const Source = React.forwardRef<HTMLAnchorElement, React.AnchorHTMLAttributes<HTMLAnchorElement> & { title: string }>(
  ({ className, children, title, href, ...props }, ref) => (
    <a
      ref={ref}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "block rounded-md bg-white/5 p-3 hover:bg-white/10 transition-colors border border-white/5",
        className,
      )}
      {...props}
    >
      <div className="text-sm font-medium text-gray-200 truncate">{title}</div>
      <div className="mt-0.5 text-xs text-muted-foreground truncate">{href}</div>
      {children}
    </a>
  ),
)
Source.displayName = "Source"

export { Sources, SourcesTrigger, SourcesContent, Source }

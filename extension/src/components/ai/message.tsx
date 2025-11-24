"use client"
import * as React from "react"
import { cn } from "~/lib/utils"

const Message = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    from: "user" | "assistant" | "system" | "tool"
  }
>(({ className, from, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex w-full gap-4 p-4 group transition-colors",
      from === "user" ? "flex-col items-end" : "hover:bg-white/[0.01]",
      className,
    )}
    {...props}
  />
))
Message.displayName = "Message"

const MessageContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("space-y-2 overflow-hidden max-w-[85%]", className)}
    {...props}
  />
))
MessageContent.displayName = "MessageContent"

export { Message, MessageContent }
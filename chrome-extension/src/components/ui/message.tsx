import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Bot, User } from "lucide-react"

const messageVariants = cva(
  "flex w-full gap-4 py-6 px-4 transition-colors group",
  {
    variants: {
      role: {
        user: "bg-transparent",
        assistant: "bg-muted/30 hover:bg-muted/40",
        system: "bg-accent/30 justify-center items-center",
      },
    },
    defaultVariants: {
      role: "assistant",
    },
  }
)

export interface MessageProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof messageVariants> {
  role?: "user" | "assistant" | "system"
}

const Message = React.forwardRef<HTMLDivElement, MessageProps>(
  ({ className, role, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(messageVariants({ role, className }))}
        {...props}
      >
        {/* Avatar */}
        <div className="flex-shrink-0">
          {role === "user" ? (
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="w-5 h-5 text-primary" />
            </div>
          ) : role === "assistant" ? (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
          ) : null}
        </div>
        
        {/* Content */}
        <div className="flex-1 space-y-3 min-w-0">
          {children}
        </div>
      </div>
    )
  }
)
Message.displayName = "Message"

const MessageContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("space-y-4", className)}
    {...props}
  />
))
MessageContent.displayName = "MessageContent"

const MessageHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center gap-2 text-sm font-semibold", className)}
    {...props}
  />
))
MessageHeader.displayName = "MessageHeader"

const MessageTimestamp = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement>
>(({ className, ...props }, ref) => (
  <span
    ref={ref}
    className={cn("text-xs text-muted-foreground font-normal ml-auto", className)}
    {...props}
  />
))
MessageTimestamp.displayName = "MessageTimestamp"

export { Message, MessageContent, MessageHeader, MessageTimestamp, messageVariants }

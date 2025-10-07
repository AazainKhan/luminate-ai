import * as React from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface ConversationProps extends React.HTMLAttributes<HTMLDivElement> {
  autoScroll?: boolean
}

const Conversation = React.forwardRef<HTMLDivElement, ConversationProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex flex-col h-full w-full", className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)
Conversation.displayName = "Conversation"

const ConversationHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "sticky top-0 z-10 flex items-center justify-between px-4 py-3",
      "border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
      className
    )}
    {...props}
  />
))
ConversationHeader.displayName = "ConversationHeader"

const ConversationContent = React.forwardRef<
  HTMLDivElement,
  ConversationProps & { autoScroll?: boolean }
>(({ className, autoScroll = true, children, ...props }, _ref) => {
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const contentRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [children, autoScroll])

  return (
    <ScrollArea className={cn("flex-1 bg-background", className)} ref={scrollRef}>
      <div ref={contentRef} className="max-w-4xl mx-auto" {...props}>
        {children}
      </div>
    </ScrollArea>
  )
})
ConversationContent.displayName = "ConversationContent"

const ConversationFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("sticky bottom-0 p-4 border-t bg-background/95 backdrop-blur", className)}
    {...props}
  />
))
ConversationFooter.displayName = "ConversationFooter"

export {
  Conversation,
  ConversationHeader,
  ConversationContent,
  ConversationFooter,
}

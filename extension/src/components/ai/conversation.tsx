"use client"
import * as React from "react"
import { cn } from "~/lib/utils"

const ConversationContext = React.createContext<{
  isStreaming: boolean
}>({
  isStreaming: false,
})

const Conversation = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    isStreaming?: boolean
  }
>(({ className, isStreaming = false, ...props }, ref) => (
  <ConversationContext.Provider value={{ isStreaming }}>
    <div ref={ref} className={cn("h-full overflow-y-auto", className)} {...props} />
  </ConversationContext.Provider>
))
Conversation.displayName = "Conversation"

const ConversationContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const { isStreaming } = React.useContext(ConversationContext)

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [props.children, isStreaming])

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto">
      <div
        ref={ref}
        className={cn("flex flex-col space-y-6 px-4 py-4", className)}
        {...props}
      />
    </div>
  )
})
ConversationContent.displayName = "ConversationContent"

export { Conversation, ConversationContent }
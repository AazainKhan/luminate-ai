"use client"

import * as React from "react"
import { ChevronDown } from "lucide-react"
import { Message } from "./Message"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Loader } from "@/components/ai-elements/loader"

// ============================================================================
// Context
// ============================================================================

interface ConversationContextValue {
  scrollToBottom: () => void
  isAtBottom: boolean
}

const ConversationContext = React.createContext<ConversationContextValue>({
  scrollToBottom: () => {},
  isAtBottom: true,
})

export const useConversation = () => React.useContext(ConversationContext)

// ============================================================================
// Conversation (Root)
// ============================================================================

interface ConversationProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Children to render (composable pattern) */
  children?: React.ReactNode
  /** Messages array (legacy pattern) */
  messages?: any[]
  /** Loading state (legacy pattern) */
  isLoading?: boolean
  /** Callback to regenerate a message */
  onRegenerate?: (messageId: string) => void
}

/**
 * Conversation wrapper component following AI Elements pattern
 * Supports both composable children and legacy messages prop
 */
const Conversation = React.forwardRef<HTMLDivElement, ConversationProps>(
  ({ className, children, messages, isLoading = false, onRegenerate, ...props }, ref) => {
    // Legacy mode: if messages array is provided, render legacy component
    if (messages !== undefined) {
      return <LegacyConversationInternal messages={messages} isLoading={isLoading} onRegenerate={onRegenerate} />
    }
    
    // Composable mode: render children with context
    const scrollRef = React.useRef<HTMLDivElement>(null)
    const [isAtBottom, setIsAtBottom] = React.useState(true)

    const scrollToBottom = React.useCallback(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight
      }
    }, [])

    // Check if at bottom on scroll
    const handleScroll = React.useCallback(() => {
      if (scrollRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
        const atBottom = scrollHeight - scrollTop - clientHeight < 50
        setIsAtBottom(atBottom)
      }
    }, [])

    const contextValue = React.useMemo(() => ({
      scrollToBottom,
      isAtBottom,
    }), [scrollToBottom, isAtBottom])

    return (
      <ConversationContext.Provider value={contextValue}>
        <div 
          ref={ref}
          className={cn("h-full relative", className)} 
          data-testid="conversation-container"
          {...props}
        >
          <Card className="h-full bg-card/80 border-border rounded-2xl shadow-lg mx-4 my-4 overflow-hidden">
            <ScrollArea className="h-full" onScroll={handleScroll}>
              <div ref={scrollRef} className="px-4 py-6">
                {children}
              </div>
            </ScrollArea>
          </Card>
        </div>
      </ConversationContext.Provider>
    )
  }
)
Conversation.displayName = "Conversation"

// ============================================================================
// ConversationContent
// ============================================================================

interface ConversationContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Auto-scroll when new content added */
  autoScroll?: boolean
}

/**
 * Content wrapper for conversation messages
 * Handles auto-scroll behavior and message layout
 */
const ConversationContent = React.forwardRef<HTMLDivElement, ConversationContentProps>(
  ({ autoScroll = true, className, children, ...props }, ref) => {
    const { scrollToBottom, isAtBottom } = useConversation()
    const childCount = React.Children.count(children)
    const prevChildCountRef = React.useRef(childCount)

    // Auto-scroll when new content is added (if at bottom)
    React.useEffect(() => {
      if (autoScroll && childCount > prevChildCountRef.current && isAtBottom) {
        scrollToBottom()
      }
      prevChildCountRef.current = childCount
    }, [childCount, autoScroll, isAtBottom, scrollToBottom])

    return (
      <div
        ref={ref}
        className={cn("space-y-6 max-w-3xl mx-auto pb-12", className)}
        data-testid="chat-messages"
        {...props}
      >
        {children}
      </div>
    )
  }
)
ConversationContent.displayName = "ConversationContent"

// ============================================================================
// ConversationEmptyState
// ============================================================================

interface ConversationEmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title text */
  title?: string
  /** Description text */
  description?: string
  /** Icon or avatar */
  icon?: React.ReactNode
}

/**
 * Empty state display for when there are no messages
 */
const ConversationEmptyState = React.forwardRef<HTMLDivElement, ConversationEmptyStateProps>(
  ({ title, description, icon, className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "h-full flex flex-col items-center justify-center p-8 pb-32 text-center",
        "animate-in fade-in slide-in-from-bottom-4 duration-700",
        className
      )}
      {...props}
    >
      {icon && (
        <div className="mb-4">{icon}</div>
      )}
      {title && (
        <h2 className="text-2xl font-semibold text-foreground mb-2 tracking-tight">
          {title}
        </h2>
      )}
      {description && (
        <p className="text-sm text-muted-foreground leading-relaxed max-w-md">
          {description}
        </p>
      )}
      {children}
    </div>
  )
)
ConversationEmptyState.displayName = "ConversationEmptyState"

// ============================================================================
// ConversationScrollButton
// ============================================================================

interface ConversationScrollButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Always show, regardless of scroll position */
  alwaysShow?: boolean
}

/**
 * Scroll to bottom button that appears when not at bottom
 */
const ConversationScrollButton = React.forwardRef<HTMLButtonElement, ConversationScrollButtonProps>(
  ({ alwaysShow = false, className, ...props }, ref) => {
    const { scrollToBottom, isAtBottom } = useConversation()

    if (!alwaysShow && isAtBottom) return null

    return (
      <Button
        ref={ref}
        variant="outline"
        size="icon"
        className={cn(
          "absolute bottom-20 right-8 z-10 rounded-full shadow-lg",
          "bg-background/80 backdrop-blur-sm border-border",
          "animate-fade-slide-in",
          className
        )}
        onClick={scrollToBottom}
        {...props}
      >
        <ChevronDown className="h-4 w-4" />
        <span className="sr-only">Scroll to bottom</span>
      </Button>
    )
  }
)
ConversationScrollButton.displayName = "ConversationScrollButton"

// ============================================================================
// ConversationLoader
// ============================================================================

interface ConversationLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Custom message */
  message?: string
}

/**
 * Loading indicator for when assistant is thinking
 */
const ConversationLoader = React.forwardRef<HTMLDivElement, ConversationLoaderProps>(
  ({ message = "Thinking...", className, ...props }, ref) => (
    <div 
      ref={ref}
      className={cn(
        "flex items-start gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300",
        className
      )}
      {...props}
    >
      <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30">
        <span className="text-xs font-bold">L</span>
      </div>
      <div className="flex-1 pt-1">
        <div className="inline-flex items-center gap-2 px-4 py-3 rounded-2xl bg-muted/50 border border-border text-muted-foreground">
          <Loader size={16} variant="dots" />
          <span className="text-xs font-medium">{message}</span>
        </div>
      </div>
    </div>
  )
)
ConversationLoader.displayName = "ConversationLoader"

// ============================================================================
// Legacy Conversation Export (for backwards compatibility)
// ============================================================================

interface LegacyConversationProps {
  messages: any[]
  isLoading: boolean
  onRegenerate?: (messageId: string) => void
}

/**
 * Internal legacy Conversation component for backwards compatibility
 */
function LegacyConversationInternal({ messages, isLoading, onRegenerate }: LegacyConversationProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  return (
    <div className="h-full relative" data-testid="conversation-container">
      <Card className="h-full bg-card/80 border-border rounded-2xl shadow-lg mx-4 my-4 overflow-hidden">
        <ScrollArea className="h-full">
          <div ref={scrollRef} className="px-4 py-6">
            <div className="space-y-6 max-w-3xl mx-auto pb-12" data-testid="chat-messages">
              {messages.map((message, index) => {
                // Pass isLoading to the last assistant message while streaming
                const isLastMessage = index === messages.length - 1
                const isAssistant = message.role === "assistant"
                const messageIsLoading = isLoading && isLastMessage && isAssistant
                
                return (
                  <Message 
                    key={message.id} 
                    message={message} 
                    isLoading={messageIsLoading}
                    onRegenerate={isAssistant && onRegenerate ? () => onRegenerate(message.id) : undefined}
                  />
                )
              })}
            </div>
          </div>
        </ScrollArea>
      </Card>
    </div>
  )
}

// ============================================================================
// Exports
// ============================================================================

// Alias for external use
const LegacyConversation = LegacyConversationInternal

export {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
  ConversationLoader,
  ConversationContext,
  LegacyConversation,
  // Default export is the unified Conversation component
  Conversation as default,
}

export type {
  ConversationProps,
  ConversationContentProps,
  ConversationEmptyStateProps,
  ConversationScrollButtonProps,
  ConversationLoaderProps,
}

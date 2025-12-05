"use client"

import * as React from "react"
import { Copy, RotateCcw, Check, ThumbsUp, ThumbsDown, MoreHorizontal, Flag, Volume2, Pencil } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sources, SourcesTrigger, SourcesContent, Source } from "@/components/ai-elements/sources"
import { Reasoning, ReasoningTrigger, ReasoningContent } from "@/components/ai-elements/reasoning"
import { Response } from "@/components/ai-elements/response"
import { cn } from "@/lib/utils"
import { CodeBlock, CodeBlockCopyButton } from "@/components/ai-elements/code-block"
import { AIImage } from "@/components/ai-elements/image"
import { Shimmer } from "@/components/ai-elements/shimmer"
import { Loader } from "@/components/ai-elements/loader"
import {
  InlineCitation,
  InlineCitationText,
  InlineCitationCard,
  InlineCitationCardTrigger,
  InlineCitationCardBody,
  InlineCitationSource,
  InlineCitationQuote,
} from "@/components/ai-elements/inline-citation"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { Message as MessageType, ThoughtStep } from "../../types"

import { ChainOfThought } from "./ChainOfThought"

// ============================================================================
// Context
// ============================================================================

interface MessageContextValue {
  from: "user" | "assistant"
  isLoading: boolean
}

const MessageContext = React.createContext<MessageContextValue>({
  from: "user",
  isLoading: false,
})

// ============================================================================
// Message (Root)
// ============================================================================

interface MessageProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Message data (legacy) */
  message?: MessageType
  /** Message sender */
  from?: "user" | "assistant"
  /** Whether message is loading/streaming */
  isLoading?: boolean
  /** Callback to regenerate this message */
  onRegenerate?: () => void
}

/**
 * Message component following AI Elements pattern
 * 
 * Supports both legacy single-prop pattern and composable sub-components
 * 
 * @example Legacy
 * ```tsx
 * <Message message={messageData} />
 * ```
 * 
 * @example Composable
 * ```tsx
 * <Message from="assistant">
 *   <MessageAvatar src="/ai.png" name="AI" />
 *   <MessageContent>Hello world</MessageContent>
 *   <MessageActions>...</MessageActions>
 * </Message>
 * ```
 */
const Message = React.forwardRef<HTMLDivElement, MessageProps>(
  ({ message, from: fromProp, isLoading = false, onRegenerate, className, children, ...props }, ref) => {
    const [copied, setCopied] = React.useState(false)
    
    // Determine if using legacy or composable pattern
    const isLegacy = !!message
    const from = fromProp ?? (message?.role === "user" ? "user" : "assistant")
    const isUser = from === "user"

    const handleCopy = React.useCallback(async () => {
      if (message?.content) {
        await navigator.clipboard.writeText(message.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    }, [message?.content])

    const contextValue = React.useMemo(() => ({
      from,
      isLoading,
    }), [from, isLoading])

    // Legacy rendering
    if (isLegacy && message) {
      return (
        <TooltipProvider>
          <MessageLegacyContent 
            message={message} 
            copied={copied} 
            handleCopy={handleCopy} 
            isUser={isUser} 
            isLoading={isLoading}
            onRegenerate={onRegenerate}
          />
        </TooltipProvider>
      )
    }

    // Composable rendering
    return (
      <MessageContext.Provider value={contextValue}>
        <div
          ref={ref}
          data-testid={`message-${from}`}
          data-role={from}
          className={cn(
            "flex w-full gap-2 sm:gap-4 group transition-colors",
            "animate-in fade-in slide-in-from-bottom-2 duration-300",
            isUser ? "flex-row-reverse" : "flex-row",
            className
          )}
          {...props}
        >
          {children}
        </div>
      </MessageContext.Provider>
    )
  }
)
Message.displayName = "Message"

// ============================================================================
// MessageAvatar
// ============================================================================

interface MessageAvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Avatar image source */
  src?: string
  /** Name for fallback */
  name?: string
  /** Fallback content */
  fallback?: React.ReactNode
}

const MessageAvatar = React.forwardRef<HTMLDivElement, MessageAvatarProps>(
  ({ src, name, fallback, className, ...props }, ref) => {
    const { from } = React.useContext(MessageContext)
    const isUser = from === "user"

    // Generate fallback from name
    const fallbackContent = fallback ?? (name ? name.charAt(0).toUpperCase() : (isUser ? "U" : "L"))

    if (isUser) return null // No avatar for user messages

    return (
      <div
        ref={ref}
        className={cn(
          "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full",
          "bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30",
          className
        )}
        {...props}
      >
        {src ? (
          <img src={src} alt={name ?? "Avatar"} className="h-full w-full rounded-full object-cover" />
        ) : (
          <span className="text-xs font-bold">{fallbackContent}</span>
        )}
      </div>
    )
  }
)
MessageAvatar.displayName = "MessageAvatar"

// ============================================================================
// MessageContent
// ============================================================================

interface MessageContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Content variant */
  variant?: "default" | "contained"
}

const MessageContent = React.forwardRef<HTMLDivElement, MessageContentProps>(
  ({ variant = "default", className, children, ...props }, ref) => {
    const { from, isLoading } = React.useContext(MessageContext)
    const isUser = from === "user"

    return (
      <div
        ref={ref}
        className={cn(
          "space-y-2 overflow-hidden",
          isUser 
            ? "flex flex-col items-end max-w-[90%] sm:max-w-[85%] md:max-w-[75%]" 
            : "flex-1 min-w-0",
          className
        )}
        {...props}
      >
        <div
          className={cn(
            "relative",
            isUser 
              ? "bg-violet-600 text-white px-3 py-2 sm:px-4 sm:py-3 rounded-2xl rounded-tr-sm shadow-md" 
              : "bg-muted/50 border border-border backdrop-blur-sm rounded-2xl rounded-tl-sm px-3 py-2 sm:px-4 sm:py-3 text-foreground shadow-sm w-full",
            isLoading && !isUser && "animate-processing",
          )}
        >
          {children}
        </div>
      </div>
    )
  }
)
MessageContent.displayName = "MessageContent"

// ============================================================================
// MessageActions
// ============================================================================

interface MessageActionsProps extends React.HTMLAttributes<HTMLDivElement> {}

const MessageActions = React.forwardRef<HTMLDivElement, MessageActionsProps>(
  ({ className, children, ...props }, ref) => {
    const { from } = React.useContext(MessageContext)
    const isUser = from === "user"

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center gap-1 pt-1 transition-opacity",
          isUser && "opacity-0 group-hover:opacity-100",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
MessageActions.displayName = "MessageActions"

// ============================================================================
// MessageAction
// ============================================================================

interface MessageActionProps extends React.ComponentPropsWithoutRef<typeof Button> {
  /** Tooltip text */
  tooltip?: string
}

const MessageAction = React.forwardRef<HTMLButtonElement, MessageActionProps>(
  ({ tooltip, className, children, ...props }, ref) => {
    const button = (
      <Button
        ref={ref}
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7 text-muted-foreground hover:text-foreground", className)}
        {...props}
      >
        {children}
      </Button>
    )

    if (tooltip) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent>{tooltip}</TooltipContent>
        </Tooltip>
      )
    }

    return button
  }
)
MessageAction.displayName = "MessageAction"

// ============================================================================
// Legacy Message Content (for backwards compatibility)
// ============================================================================

/**
 * Determines if chain of thought should be displayed.
 * For an educational AI tutor, we ALWAYS show chain of thought if steps exist.
 * This provides transparency and helps students understand the AI's reasoning process.
 */
function shouldShowChainOfThought(
  steps: ThoughtStep[] | undefined, 
  _isStreaming: boolean,
  _hasContent: boolean,
  _streamComplete?: boolean
): boolean {
  // Simple rule: if there are steps, show them
  // The ChainOfThought component handles auto-collapse after completion
  if (!steps || steps.length === 0) return false
  
  // Always show chain of thought when there are steps
  // The component itself will collapse after completion but remain visible
  return true
}

interface MessageLegacyContentProps {
  message: MessageType
  copied: boolean
  handleCopy: () => void
  isUser: boolean
  isLoading: boolean
  onRegenerate?: () => void
}

function MessageLegacyContent({ message, copied, handleCopy, isUser, isLoading, onRegenerate }: MessageLegacyContentProps) {
  const renderContentWithCitations = (content: string) => {
    if (!message.citations || message.citations.length === 0) {
      return content
    }
    const parts = content.split(/(\[\d+\])/)
    return (
      <InlineCitation>
        {parts.map((part, index) => {
          const match = part.match(/\[(\d+)\]/)
          if (match) {
            const citationNumber = match[1]
            const citation = message.citations?.find((c) => c.number === citationNumber)
            if (citation) {
              return (
                <InlineCitationCard key={index}>
                  <InlineCitationCardTrigger number={citation.number} url={citation.url} />
                  <InlineCitationCardBody>
                    <InlineCitationSource
                      title={citation.title}
                      url={citation.url}
                      description={citation.description}
                    />
                    {citation.quote && <InlineCitationQuote>{citation.quote}</InlineCitationQuote>}
                  </InlineCitationCardBody>
                </InlineCitationCard>
              )
            }
          }
          return <InlineCitationText key={index}>{part}</InlineCitationText>
        })}
      </InlineCitation>
    )
  }

  // Check if this is a loading message (empty content, assistant role)
  const showLoadingState = !isUser && isLoading && !message.content

  return (
    <div
      data-testid={`message-${isUser ? 'user' : 'assistant'}`}
      data-role={isUser ? 'user' : 'assistant'}
      className={cn(
        "flex w-full gap-2 sm:gap-4 group transition-colors",
        "animate-in fade-in slide-in-from-bottom-2 duration-300",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30">
          <span className="text-xs font-bold">L</span>
        </div>
      )}
      
      <div className={cn("space-y-2 overflow-hidden", isUser ? "flex flex-col items-end max-w-[90%] sm:max-w-[85%] md:max-w-[75%]" : "flex-1 min-w-0")}>
        <div
          className={cn(
            "relative",
            isUser 
              ? "bg-violet-600 text-white px-3 py-2 sm:px-4 sm:py-3 rounded-2xl rounded-tr-sm shadow-md" 
              : "bg-muted/50 border border-border backdrop-blur-sm rounded-2xl rounded-tl-sm px-3 py-2 sm:px-4 sm:py-3 text-foreground shadow-sm w-full",
          )}
        >
          {/* Reasoning - Model's internal thinking process */}
          {!isUser && message.reasoning && (
            <div className="mb-3" data-testid="message-reasoning">
              <Reasoning 
                isStreaming={isLoading && !message.streamComplete}
                isComplete={!!message.streamComplete}
                collapseDelay={3000}
                defaultOpen={true}
              >
                <ReasoningTrigger showDuration />
                <ReasoningContent>
                  {message.reasoning}
                </ReasoningContent>
              </Reasoning>
            </div>
          )}

          {/* Chain of Thought - Pipeline stages */}
          {!isUser && message.chainOfThought && message.chainOfThought.length > 0 && 
           shouldShowChainOfThought(message.chainOfThought, isLoading, !!message.content, message.streamComplete) && (
            <div className="mb-3" data-testid="chain-of-thought-container">
              <ChainOfThought 
                steps={message.chainOfThought}
                isStreaming={isLoading && !message.streamComplete}
                collapseDelay={3000}
                defaultOpen={true}
                title="Processing"
              />
            </div>
          )}

          {/* Loading state with shimmer - only show if NO chainOfThought steps */}
          {showLoadingState && !shouldShowChainOfThought(message.chainOfThought, isLoading, false, message.streamComplete) && (
            <div className="space-y-2" data-testid="message-loading">
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Loader size={16} variant="dots" className="text-violet-500" />
                <span className="animate-processing">Connecting...</span>
              </div>
              <Shimmer variant="text" className="w-full" />
              <Shimmer variant="text" className="w-3/4" />
            </div>
          )}

          {/* Main content - show as it streams */}
          {isUser ? (
            <p className="text-sm leading-snug whitespace-pre-wrap tracking-tight">
              {message.content}
            </p>
          ) : (
            message.content && (
              <Response>
                {message.citations ? String(renderContentWithCitations(message.content)) : message.content}
              </Response>
            )
          )}

          {/* Code blocks with syntax highlighting */}
          {!isUser && message.codeBlocks && message.codeBlocks.length > 0 && (
            <div className="space-y-3 mt-3">
              {message.codeBlocks.map((block, i) => (
                <CodeBlock key={block.id || i} code={block.code} language={block.language} showLineNumbers>
                  <CodeBlockCopyButton code={block.code} />
                </CodeBlock>
              ))}
            </div>
          )}

          {/* Images */}
          {!isUser && message.images && message.images.length > 0 && (
            <div className="space-y-3 mt-3">
              {message.images.map((img, i) => (
                <AIImage key={i} src={img.src} alt={img.alt} caption={img.caption} />
              ))}
            </div>
          )}

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {message.attachments.map((file, i) => (
                <div key={i} className="px-2 py-1 rounded bg-white/10 text-xs text-gray-300">
                  {file.name}
                </div>
              ))}
            </div>
          )}

          {/* Sources from RAG retrieval */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-3 pt-2 border-t border-border/30" data-testid="message-sources">
              <Sources count={message.sources.length} autoExpand collapseDelay={2000}>
                <SourcesTrigger />
                <SourcesContent>
                  {message.sources.map((source, i) => {
                    // Format source title to be more user-friendly with lecture/week context
                    const formatSourceTitle = (s: typeof source): string => {
                      // If we have a good title that's not a generic filename, use it
                      if (s.title && !s.title.match(/^res\d+\.dat$/i) && s.title.length > 3) {
                        return s.title
                      }
                      
                      const filename = (s.source_file || s.title || '').replace(/\.[^/.]+$/, '') // Remove extension
                      const lowerFilename = filename.toLowerCase()
                      
                      // Handle patterns like "res00224" -> try to extract topic from content
                      if (filename.match(/^res\d+$/i)) {
                        // Try to extract topic from description/content
                        const content = (s.description || s.content || '').toLowerCase()
                        
                        // ML/AI topic detection from content
                        const topicPatterns: [RegExp, string][] = [
                          [/neural network|hidden layer|perceptron/i, 'Neural Networks'],
                          [/gradient descent|learning rate/i, 'Gradient Descent'],
                          [/backpropagation|back.?prop/i, 'Backpropagation'],
                          [/decision tree/i, 'Decision Trees'],
                          [/support vector|svm/i, 'Support Vector Machines'],
                          [/k-?nearest|knn/i, 'K-Nearest Neighbors'],
                          [/naive bayes/i, 'Naive Bayes'],
                          [/regression|linear model/i, 'Regression'],
                          [/classification|classifier/i, 'Classification'],
                          [/clustering|k-?means/i, 'Clustering'],
                          [/overfitting|underfitting/i, 'Model Fitting'],
                          [/cross.?validation/i, 'Cross Validation'],
                          [/activation function/i, 'Activation Functions'],
                          [/loss function|cost function/i, 'Loss Functions'],
                        ]
                        
                        for (const [pattern, topic] of topicPatterns) {
                          if (pattern.test(content)) {
                            return topic
                          }
                        }
                        
                        return `Course Resource ${i + 1}`
                      }
                      
                      // Handle syllabus files
                      if (lowerFilename.includes('syllabus')) {
                        // Try to extract section info
                        const sectionMatch = lowerFilename.match(/section[_\-\s]?(\d+)/i)
                        if (sectionMatch) {
                          return `Syllabus - Section ${sectionMatch[1]}`
                        }
                        return 'Course Syllabus'
                      }
                      
                      // Handle syllabus map
                      if (lowerFilename.includes('syllabus_map')) {
                        return 'Course Structure'
                      }
                      
                      // Handle lecture files with week extraction
                      const weekMatch = lowerFilename.match(/week[_\-\s]?(\d+)/i)
                      const lectureMatch = lowerFilename.match(/lecture[_\-\s]?(\d+)/i)
                      const labMatch = lowerFilename.match(/lab[_\-\s]?(\d+)/i)
                      const assignmentMatch = lowerFilename.match(/(?:assignment|hw|homework)[_\-\s]?(\d+)/i)
                      
                      let parts: string[] = []
                      
                      if (weekMatch) {
                        parts.push(`Week ${weekMatch[1]}`)
                      }
                      if (lectureMatch) {
                        parts.push(`Lecture ${lectureMatch[1]}`)
                      }
                      if (labMatch) {
                        parts.push(`Lab ${labMatch[1]}`)
                      }
                      if (assignmentMatch) {
                        parts.push(`Assignment ${assignmentMatch[1]}`)
                      }
                      
                      if (parts.length > 0) {
                        // Try to extract topic from remaining filename
                        const cleanName = filename
                          .replace(/week[_\-\s]?\d+/gi, '')
                          .replace(/lecture[_\-\s]?\d+/gi, '')
                          .replace(/lab[_\-\s]?\d+/gi, '')
                          .replace(/(?:assignment|hw|homework)[_\-\s]?\d+/gi, '')
                          .replace(/[_\-]+/g, ' ')
                          .trim()
                        
                        if (cleanName.length > 2) {
                          // Capitalize each word
                          const topic = cleanName
                            .split(' ')
                            .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
                            .join(' ')
                          parts.push(`- ${topic}`)
                        }
                        
                        return parts.join(' ')
                      }
                      
                      // Default: clean up the filename
                      return filename
                        .replace(/[_\-]+/g, ' ')
                        .split(' ')
                        .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
                        .join(' ')
                    }
                    
                    // Extract page number if available
                    const pageInfo = source.page ? ` (p. ${source.page})` : ''
                    
                    return (
                      <Source 
                        key={source.id || i}
                        index={i}
                        title={formatSourceTitle(source) + pageInfo}
                        href={source.url || '#'} 
                        description={source.description || source.content?.substring(0, 150)}
                        filename={source.source_file}
                        page={source.page}
                      />
                    )
                  })}
                </SourcesContent>
              </Sources>
            </div>
          )}

          {/* Suggestions for follow-up */}
          {!isUser && message.suggestions && message.suggestions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <p className="text-xs text-muted-foreground mb-2">Suggested follow-ups:</p>
              <div className="flex flex-wrap gap-2">
                {message.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    className="text-xs px-2 py-1 rounded-full bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User message actions */}
        {isUser && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-foreground"
              onClick={handleCopy}
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground">
              <Pencil className="w-3 h-3" />
            </Button>
          </div>
        )}

        {/* Assistant message actions */}
        {!isUser && !showLoadingState && (
          <div className="flex items-center gap-1 pt-1 transition-opacity">
            {/* Feedback row */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Was this helpful?</span>
              <div className="flex gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-green-500 hover:bg-green-500/10"
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Good response</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Bad response</TooltipContent>
                </Tooltip>
              </div>
            </div>
            
            <div className="flex-1" />
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-foreground"
                  onClick={handleCopy}
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied!" : "Copy"}</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-7 w-7 text-muted-foreground hover:text-foreground"
                  onClick={onRegenerate}
                  disabled={!onRegenerate || isLoading}
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Regenerate</TooltipContent>
            </Tooltip>

            <DropdownMenu>
              <Tooltip>
                <TooltipTrigger asChild>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    >
                      <MoreHorizontal className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                </TooltipTrigger>
                <TooltipContent>More options</TooltipContent>
              </Tooltip>
              <DropdownMenuContent align="start" className="w-48 bg-popover border-border">
                <DropdownMenuItem className="cursor-pointer text-popover-foreground focus:bg-muted focus:text-foreground">
                  <Flag className="w-4 h-4 mr-2" />
                  Report Message
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer text-popover-foreground focus:bg-muted focus:text-foreground">
                  <Volume2 className="w-4 h-4 mr-2" />
                  Read Aloud
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// Exports
// ============================================================================

export {
  Message,
  MessageAvatar,
  MessageContent,
  MessageActions,
  MessageAction,
  MessageContext,
  type MessageProps,
  type MessageAvatarProps,
  type MessageContentProps,
  type MessageActionsProps,
  type MessageActionProps,
}

export { Message as default }

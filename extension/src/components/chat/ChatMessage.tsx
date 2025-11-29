import { User, Bot } from "lucide-react"
import { CodeBlock } from "./CodeBlock"
import { QuizCard } from "./QuizCard"
import { Visualizer } from "./Visualizer"
import { ThinkingAccordion } from "./ThinkingAccordion"
import { cn } from "@/lib/utils"

export interface Message {
  role: "user" | "assistant"
  content: string
  id: string
}

interface ChatMessageProps {
  message: Message
  thinkingSteps?: Array<{ step: string; status: "thinking" | "complete" | "error"; details?: string }>
}

export function ChatMessage({ message, thinkingSteps }: ChatMessageProps) {
  const isUser = message.role === "user"

  // Parse message content for special components
  const parseContent = (content: string) => {
    const parts: JSX.Element[] = []
    let currentIndex = 0

    // Look for code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    let match
    let lastIndex = 0

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {content.slice(lastIndex, match.index)}
          </span>
        )
      }

      // Add code block
      const language = match[1] || "python"
      const code = match[2]
      parts.push(
        <CodeBlock
          key={`code-${match.index}`}
          code={code}
          language={language}
          showRunButton={language === "python"}
        />
      )

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(<span key={`text-${lastIndex}`}>{content.slice(lastIndex)}</span>)
    }

    return parts.length > 0 ? parts : [<span key="content">{content}</span>]
  }

  return (
    <div
      className={cn(
        "flex gap-3 p-4 transition-colors",
        isUser ? "bg-muted/30" : "bg-background"
      )}
    >
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm",
          isUser ? "bg-primary/10 text-primary" : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-muted-foreground mb-1">
          {isUser ? "You" : "Course Marshal"}
        </div>
        {!isUser && thinkingSteps && thinkingSteps.length > 0 && (
          <div className="mb-3">
            <ThinkingAccordion steps={thinkingSteps} />
          </div>
        )}
        <div className="text-foreground whitespace-pre-wrap break-words space-y-3 leading-relaxed">
          {parseContent(message.content)}
        </div>
      </div>
    </div>
  )
}

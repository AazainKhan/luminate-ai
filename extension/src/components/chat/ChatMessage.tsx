import { User, Bot } from "lucide-react"
import { CodeBlock } from "./CodeBlock"
import { QuizCard } from "./QuizCard"
import { Visualizer } from "./Visualizer"
import { ThinkingAccordion } from "./ThinkingAccordion"

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
      className={`flex gap-3 p-4 ${
        isUser ? "bg-gray-50" : "bg-white"
      }`}
    >
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-blue-100" : "bg-purple-100"
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-blue-600" />
        ) : (
          <Bot className="w-4 h-4 text-purple-600" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-700 mb-1">
          {isUser ? "You" : "Course Marshal"}
        </div>
        {!isUser && thinkingSteps && thinkingSteps.length > 0 && (
          <div className="mb-3">
            <ThinkingAccordion steps={thinkingSteps} />
          </div>
        )}
        <div className="text-gray-900 whitespace-pre-wrap break-words space-y-3">
          {parseContent(message.content)}
        </div>
      </div>
    </div>
  )
}


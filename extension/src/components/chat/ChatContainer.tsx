import { useEffect, useRef } from "react"
import { ChatMessage as ChatMessageComponent } from "./ChatMessage"
import { ChatInput } from "./ChatInput"
import { useChat } from "~/hooks/use-chat"
import { useAuth } from "~/hooks/useAuth"

export function ChatContainer() {
  const { user } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, append, isLoading } = useChat()

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async (content: string) => {
    if (!content.trim() || isLoading) return
    await append({ role: "user", content })
  }

  if (!user) {
    return null
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center max-w-md">
              <h2 className="text-2xl font-bold mb-2">
                Welcome to Course Marshal
              </h2>
              <p className="text-gray-600">
                Ask me anything about COMP 237: Introduction to AI. I can help
                with concepts, assignments, and course logistics.
              </p>
            </div>
          </div>
        ) : (
          <div>
            {messages.map((message) => (
              <ChatMessageComponent key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}


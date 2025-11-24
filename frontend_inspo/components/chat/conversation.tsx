"use client"

import { useEffect, useRef } from "react"
import { Message } from "./message"
import { Loader2 } from "lucide-react"

interface ConversationProps {
  messages: any[]
  isLoading: boolean
}

export function Conversation({ messages, isLoading }: ConversationProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto px-4 py-4">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center px-6">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
            <span className="text-2xl font-bold text-primary">P</span>
          </div>
          <h2 className="text-lg font-semibold text-foreground mb-2">Welcome to Plasmo Assistant</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Ask me anything about Plasmo Framework, Itero, or Chrome extension development.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

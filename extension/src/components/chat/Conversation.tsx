"use client"

import { useEffect, useRef } from "react"
import { Message } from "./message"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

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
    <div className="h-full relative">
      <Card className="h-full bg-slate-900/80 border-slate-800 rounded-2xl shadow-lg mx-4 my-4 overflow-hidden">
        <ScrollArea className="h-full">
          <div 
            ref={scrollRef} 
            className="px-4 py-6"
          >
            <div className="space-y-6 max-w-3xl mx-auto pb-12">
              {messages.map((message) => (
                <Message key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex items-start gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-violet-500/30 text-violet-300">
                    <span className="text-xs font-bold">L</span>
                  </div>
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="flex items-center gap-2">
                      {/* Typing indicator with bouncing dots */}
                      <div className="flex gap-1">
                        <div className="h-2 w-2 bg-violet-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                        <div className="h-2 w-2 bg-violet-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                        <div className="h-2 w-2 bg-violet-400 rounded-full animate-bounce" />
                      </div>
                      <span className="text-xs text-slate-400">Luminate AI is thinking…</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </ScrollArea>
      </Card>
    </div>
  )
}

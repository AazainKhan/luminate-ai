import { useState, useCallback } from "react"
import { useAuth } from "./useAuth"
import type { Message } from "../types"
import type { Session } from "@supabase/supabase-js"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"
const isDevelopment = process.env.NODE_ENV !== "production"

export default function useChat(providedSession?: Session | null) {
  const { session: internalSession } = useAuth()
  const session = providedSession ?? internalSession
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const append = useCallback(async (message: { role: "user"; content: string; attachments?: File[] }) => {
    setIsLoading(true)
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: message.content,
      attachments: message.attachments
    }
    
    setMessages(prev => [...prev, userMessage])

    // Create placeholder assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      if (isDevelopment) {
        console.log("Sending chat request with token:", session?.access_token ? "Token present" : "No token")
      }
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: session?.access_token ? `Bearer ${session.access_token}` : "",
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({ role: m.role, content: m.content })),
          stream: true
        }),
      })

      if (response.status === 401) {
        throw new Error("Unauthorized: please ensure the backend SUPABASE_JWT_SECRET matches your project and that you are signed in.")
      }

      if (!response.ok) throw new Error("Network response was not ok")
      if (!response.body) throw new Error("No response body")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") continue // Handle standard OpenAI format if mixed
            
            try {
              const parsed = JSON.parse(data)
              
              setMessages(prev => prev.map(msg => {
                if (msg.id !== assistantMessageId) return msg

                const updatedMsg = { ...msg }
                
                if (parsed.type === "text-delta") {
                  updatedMsg.content += parsed.textDelta
                } else if (parsed.type === "reasoning-delta") {
                  updatedMsg.reasoning = (updatedMsg.reasoning || "") + parsed.reasoningDelta
                } else if (parsed.type === "sources") {
                  updatedMsg.sources = parsed.sources
                } else if (parsed.type === "tool-call") {
                  const toolCall = {
                    name: parsed.toolName,
                    args: parsed.toolInput,
                    status: "in-progress" as const
                  }
                  updatedMsg.tools = [...(updatedMsg.tools || []), toolCall]
                } else if (parsed.type === "tool-result") {
                  updatedMsg.tools = updatedMsg.tools?.map(t => 
                    t.name === parsed.toolName ? { ...t, result: parsed.toolOutput, status: "completed" } : t
                  )
                } else if (parsed.type === "finish") {
                   // Handle finish
                }
                
                return updatedMsg
              }))
            } catch (e) {
              console.error("Error parsing SSE data:", e)
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      // Handle error state
      setMessages(prev => {
        // Remove the loading assistant message if it exists and is empty
        const filtered = prev.filter(msg => msg.id !== assistantMessageId || msg.content !== "")
        
        // If we removed it, or if we want to show error in it
        // Actually better to just update the assistant message to show error
        return prev.map(msg => {
          if (msg.id === assistantMessageId) {
            return {
              ...msg,
              content: "I apologize, but I encountered an error while processing your request. Please try again later."
            }
          }
          return msg
        })
      })
    } finally {
      setIsLoading(false)
    }
  }, [messages, session])

  return {
    messages,
    append,
    isLoading,
    setMessages
  }
}

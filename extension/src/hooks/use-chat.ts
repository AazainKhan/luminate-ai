import { useState, useCallback, useEffect, useRef } from "react"
import { useAuth } from "./useAuth"
import type { Message, ThoughtStep } from "../types"
import type { Session } from "@supabase/supabase-js"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"
const isDevelopment = process.env.NODE_ENV !== "production"

// Generate or retrieve a persistent session ID for observability tracking
const getSessionId = (): string => {
  const STORAGE_KEY = "luminate_session_id"
  let sessionId = sessionStorage.getItem(STORAGE_KEY)
  
  if (!sessionId) {
    // Generate new session ID: timestamp + random string
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    sessionStorage.setItem(STORAGE_KEY, sessionId)
  }
  
  return sessionId
}

interface UseChatOptions {
  session?: Session | null
  chatId?: string
  onChatCreated?: (chatId: string) => void
  model?: string
}

interface UseChatReturn {
  messages: Message[]
  append: (message: { role: "user"; content: string; attachments?: File[] }) => Promise<void>
  isLoading: boolean
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  stop: () => void
  regenerate: (messageId?: string) => Promise<void>
  error: string | null
}

export default function useChat(options?: UseChatOptions): UseChatReturn {
  const { session: internalSession } = useAuth()
  const session = options?.session ?? internalSession
  const chatId = options?.chatId
  const onChatCreated = options?.onChatCreated
  const model = options?.model
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Track if we've already called onChatCreated to avoid duplicate calls
  const chatCreatedRef = useRef<string | null>(null)
  
  // AbortController for stopping generation
  const abortControllerRef = useRef<AbortController | null>(null)
  
  // Track the current streaming message ID
  const currentMessageIdRef = useRef<string | null>(null)

  // Fetch messages when chatId changes
  useEffect(() => {
    if (!chatId || !session?.access_token) {
      setMessages([])
      return
    }

    const fetchMessages = async () => {
      try {
        setIsLoading(true)
        const res = await fetch(`${API_BASE_URL}/api/history/messages/${chatId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        })
        if (res.ok) {
          const data = await res.json()
          // Restore chain of thought from message metadata
          const messagesWithChainOfThought = data.map((msg: any) => {
            if (msg.role === "assistant") {
              // Restore chain of thought from message metadata
              if (msg.metadata?.queue_steps) {
                // Convert saved queue_steps back to chainOfThought format
                const chainOfThought: ThoughtStep[] = msg.metadata.queue_steps.map((step: any) => ({
                  id: step.id,
                  type: "queue" as const,
                  name: step.label || step.name,
                  // All restored steps should show as completed since message is already done
                  status: "completed" as const,
                }))
                msg.chainOfThought = chainOfThought
              }

              // Restore sources from message metadata
              if (msg.metadata?.sources) {
                msg.sources = msg.metadata.sources
              }

              // Restore evaluation from message metadata
              if (msg.metadata?.evaluation) {
                msg.evaluation = msg.metadata.evaluation
              }
              
              // Mark as complete since it's from history
              msg.streamComplete = true
              msg.status = "complete"
            }
            return msg
          })
          setMessages(messagesWithChainOfThought)
        }
      } catch (e) {
        console.error("Error fetching messages:", e)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMessages()
  }, [chatId, session])

  /**
   * Stop the current generation
   */
  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    
    // Mark current message as stopped
    if (currentMessageIdRef.current) {
      setMessages(prev => prev.map(msg => {
        if (msg.id === currentMessageIdRef.current) {
          return {
            ...msg,
            content: msg.content || "(Generation stopped)",
            chainOfThought: msg.chainOfThought?.map(step => ({
              ...step,
              status: step.status === "processing" ? "completed" as const : step.status
            }))
          }
        }
        return msg
      }))
    }
    
    setIsLoading(false)
    currentMessageIdRef.current = null
  }, [])

  /**
   * Process SSE events from the stream
   */
  const processStreamEvent = useCallback((parsed: any, assistantMessageId: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id !== assistantMessageId) return msg

      const updatedMsg = { ...msg }

      // Text streaming
      if (parsed.type === "text-delta") {
        updatedMsg.rawContent = (updatedMsg.rawContent || updatedMsg.content) + parsed.textDelta

        let processedContent = updatedMsg.rawContent

        // Extract XML thinking tags
        const thinkingMatch = processedContent.match(/<thinking>([\s\S]*?)<\/thinking>/)
        const openThinkingMatch = processedContent.match(/<thinking>([\s\S]*)$/)

        if (thinkingMatch) {
          updatedMsg.reasoning = thinkingMatch[1]
          processedContent = processedContent.replace(/<thinking>[\s\S]*?<\/thinking>/, "")
        } else if (openThinkingMatch) {
          updatedMsg.reasoning = openThinkingMatch[1]
          processedContent = processedContent.replace(/<thinking>[\s\S]*$/, "")
        }

        // Clean up other tags
        processedContent = processedContent.replace(/<\/?follow_up>/g, "")

        // Strip reasoning JSON blocks (from reasoning node)
        processedContent = processedContent.replace(/```json\n?\s*\{[\s\S]*?"perception"[\s\S]*?\}\s*\n?```/gi, "")
        processedContent = processedContent.replace(/\{[\s\S]*?"perception"\s*:\s*\{[\s\S]*?"query_type"[\s\S]*?\}\s*\}/g, "")

        updatedMsg.content = processedContent

      // Reasoning/thinking delta
      } else if (parsed.type === "reasoning-delta") {
        updatedMsg.reasoning = (updatedMsg.reasoning || "") + parsed.reasoningDelta

      // Sources from RAG retrieval
      } else if (parsed.type === "sources") {
        updatedMsg.sources = parsed.sources?.map((s: any, idx: number) => ({
          id: s.id || `src-${idx}`,
          title: s.title || s.source_file || "Source",
          source_file: s.source_file,
          page: s.page,
          description: s.description || s.content?.substring(0, 100),
          content: s.content,
          url: s.url
        }))

        // Also add sources to the most recent search step in chain of thought
        if (updatedMsg.chainOfThought) {
          const searchStep = [...updatedMsg.chainOfThought].reverse().find(s =>
            s.type === "tool" && s.name.toLowerCase().includes("search")
          )
          if (searchStep) {
            searchStep.sources = updatedMsg.sources?.map(s => ({
              title: s.title,
              url: s.url
            }))
          }
        }

      // Tool call started - add to chain of thought
      } else if (parsed.type === "tool-call") {
        const toolStep: ThoughtStep = {
          id: parsed.toolId || `tool-${Date.now()}`,
          type: "tool",
          name: getToolDisplayName(parsed.toolName),
          status: "processing",
          input: parsed.toolInput,
          timestamp: parsed.timestamp || Date.now()
        }
        updatedMsg.chainOfThought = [...(updatedMsg.chainOfThought || []), toolStep]

      // Tool call completed - update in chain of thought
      } else if (parsed.type === "tool-result") {
        updatedMsg.chainOfThought = updatedMsg.chainOfThought?.map(step =>
          (step.id === parsed.toolId || step.name === getToolDisplayName(parsed.toolName))
            ? { ...step, output: parsed.toolOutput, status: "completed" as const }
            : step
        )

      // Queue initialization - add pipeline steps to chain of thought
      } else if (parsed.type === "queue-init") {
        const pipelineSteps: ThoughtStep[] = parsed.queue?.map((q: any) => ({
          id: q.id,
          type: "queue" as const,
          name: q.label || q.name,
          status: (q.status === "waiting" ? "pending" : q.status || "pending") as ThoughtStep["status"],
        })) || []
        updatedMsg.chainOfThought = pipelineSteps

      // Queue item updated - update in chain of thought
      } else if (parsed.type === "queue-update") {
        const newStatus = parsed.status === "waiting" ? "pending" : parsed.status
        updatedMsg.chainOfThought = updatedMsg.chainOfThought?.map(step =>
          step.id === parsed.queueItemId
            ? { ...step, status: newStatus as ThoughtStep["status"] }
            : step
        )

      // NEW: Chain-of-Thought reasoning steps from backend
      // Based on "Chain-of-Thought Prompting Elicits Reasoning" paper
      // This shows actual reasoning steps, not just status labels
      } else if (parsed.type === "chain-of-thought") {
        const thoughts = parsed.thoughts || []
        if (isDevelopment) {
          console.log("🧠 Received chain-of-thought:", thoughts.length, "steps")
        }
        // Add reasoning steps to chain of thought display
        const reasoningSteps: ThoughtStep[] = thoughts.map((t: any, index: number) => ({
          id: `thought-${t.step || index}`,
          type: "reasoning" as const,
          name: t.thought,
          details: t.detail || undefined,
          status: "completed" as const,
          timestamp: Date.now()
        }))
        // Append reasoning steps after queue steps
        updatedMsg.chainOfThought = [...(updatedMsg.chainOfThought || []), ...reasoningSteps]
        // Also store in thinkingSteps for compatibility
        updatedMsg.thinkingSteps = thoughts.map((t: any) => ({
          id: `thought-${t.step}`,
          step: t.thought,
          status: "complete" as const,
          details: t.detail
        }))

      // Concepts detected during reasoning
      } else if (parsed.type === "concepts-detected") {
        if (isDevelopment) {
          console.log("📚 Concepts detected:", parsed.concepts)
        }
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          detectedConcepts: parsed.concepts
        }

      // Queue item added (for dynamically added items)
      } else if (parsed.type === "queue-add") {
        const item = parsed.queueItem
        if (item) {
          const newStep: ThoughtStep = {
            id: item.id,
            type: "queue",
            name: item.label || item.name,
            status: (item.status === "waiting" ? "pending" : item.status || "pending") as ThoughtStep["status"],
          }
          updatedMsg.chainOfThought = [...(updatedMsg.chainOfThought || []), newStep]
        }

      // Status updates (rate limiting, retrying, etc.)
      } else if (parsed.type === "status") {
        // Add a status step to chain of thought
        if (parsed.status === "retrying") {
          const retryStep: ThoughtStep = {
            id: `retry-${Date.now()}`,
            type: "queue",
            name: `Retrying (${parsed.reason || "rate limited"})...`,
            status: "processing",
          }
          // Replace any existing retry step or add new
          const hasRetryStep = updatedMsg.chainOfThought?.some(s => s.id.startsWith("retry-"))
          if (!hasRetryStep) {
            updatedMsg.chainOfThought = [...(updatedMsg.chainOfThought || []), retryStep]
          }
        }

      // Evaluation scores (agent badge, concept, quality metrics)
      } else if (parsed.type === "evaluation") {
        if (isDevelopment) {
          console.log("📊 Received evaluation event:", {
            agent: parsed.evaluation?.agent_used,
            concept: parsed.evaluation?.detected_concept,
            confidence: parsed.evaluation?.confidence
          })
        }
        updatedMsg.evaluation = parsed.evaluation
        // Also update metadata for persistence
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          evaluation: parsed.evaluation
        }

      // Metadata on finish - mark stream as complete
      } else if (parsed.type === "finish") {
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          traceId: parsed.traceId,
          chatId: parsed.chatId
        }
        // Mark stream as complete for UI state management
        updatedMsg.streamComplete = true
        updatedMsg.status = "complete"
        // Mark any remaining steps as complete
        updatedMsg.chainOfThought = updatedMsg.chainOfThought?.map(step =>
          step.status === "processing" || step.status === "pending"
            ? { ...step, status: "completed" as const }
            : step
        )
      }

      return updatedMsg
    }))
  }, [])

  /**
   * Send a message and stream the response
   */
  const append = useCallback(async (message: { role: "user"; content: string; attachments?: File[] }) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController()
    
    setIsLoading(true)
    setError(null)

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
    currentMessageIdRef.current = assistantMessageId
    
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      rawContent: "",
      // Initialize unified chain of thought steps
      chainOfThought: [],
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
          stream: true,
          chat_id: chatId,
          session_id: getSessionId(), // Include session ID for observability tracking
          model: model || undefined
        }),
        signal: abortControllerRef.current.signal,
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
            if (data === "[DONE]") continue

            try {
              const parsed = JSON.parse(data)
              
              // Handle chat creation
              if (parsed.type === "finish" && parsed.chatId && !chatId && chatCreatedRef.current !== parsed.chatId) {
                chatCreatedRef.current = parsed.chatId
                onChatCreated?.(parsed.chatId)
              }
              
              processStreamEvent(parsed, assistantMessageId)
            } catch (e) {
              console.error("Error parsing SSE data:", e)
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log("Request aborted")
        return
      }
      
      console.error("Chat error:", error)
      setError(error.message || "An error occurred")
      
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId) {
          return {
            ...msg,
            content: msg.content || "I apologize, but I encountered an error while processing your request. Please try again later."
          }
        }
        return msg
      }))
    } finally {
      setIsLoading(false)
      currentMessageIdRef.current = null
      abortControllerRef.current = null
    }
  }, [messages, session, chatId, model, onChatCreated, processStreamEvent])

  /**
   * Regenerate the last assistant response (or a specific message)
   */
  const regenerate = useCallback(async (messageId?: string) => {
    // Find the message to regenerate
    const targetId = messageId || messages.filter(m => m.role === "assistant").pop()?.id
    if (!targetId) return

    // Find the index of the target message
    const targetIndex = messages.findIndex(m => m.id === targetId)
    if (targetIndex === -1) return

    // Find the preceding user message
    let userMessageIndex = targetIndex - 1
    while (userMessageIndex >= 0 && messages[userMessageIndex].role !== "user") {
      userMessageIndex--
    }
    if (userMessageIndex < 0) return

    const userMessage = messages[userMessageIndex]

    // Remove the assistant message and any messages after it
    setMessages(prev => prev.slice(0, targetIndex))

    // Re-send the user message
    await append({
      role: "user",
      content: userMessage.content,
      attachments: userMessage.attachments
    })
  }, [messages, append])

  return {
    messages,
    append,
    isLoading,
    setMessages,
    stop,
    regenerate,
    error
  }
}

/**
 * Convert tool name to user-friendly display name
 */
function getToolDisplayName(toolName: string): string {
  const displayNames: Record<string, string> = {
    "retrieve_context": "Searching course materials",
    "check_syllabus": "Checking syllabus",
    "web_search": "Searching the web",
  }
  return displayNames[toolName] || toolName
}

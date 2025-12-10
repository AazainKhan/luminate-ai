import { useState, useCallback, useEffect, useRef } from "react"
import { useAuth } from "./useAuth"
import { safeParsePartialJson } from "../lib/partial-json"
import type { Message, ThoughtStep, ThinkingStep, ThinkingStepType } from "../types"
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
  
  // Track if actively streaming to prevent refetch flash
  const isStreamingRef = useRef<boolean>(false)
  
  // Buffer for accumulated content during streaming (prevents race conditions)
  const streamBufferRef = useRef<{
    rawContent: string
    content: string
    reasoning?: string
    sources?: any[]
    citations?: any[]
    thinkingTrace?: ThinkingStep[]
    metadata?: Record<string, any>
    evaluation?: any
    structuredOutput?: any
    currentPhase?: "thinking" | "reasoning" | "response"
  }>({
    rawContent: "",
    content: "",
    currentPhase: "thinking"
  })

  // Fetch messages when chatId changes
  useEffect(() => {
    // Skip refetch if actively streaming to prevent flash
    if (isStreamingRef.current) {
      if (isDevelopment) {
        console.log("⏸️ Skipping history refetch - streaming in progress")
      }
      return
    }
    
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
          // Restore thinking trace, sources, and evaluation from message metadata
          const messagesWithMetadata = data.map((msg: any) => {
            if (msg.role === "assistant") {
              // Restore thinking trace from message metadata (new format)
              if (msg.metadata?.thinking_steps) {
                msg.thinkingTrace = msg.metadata.thinking_steps.map((step: any) => ({
                  step: step.step,
                  status: "completed" as const, // All restored steps are complete
                  message: step.message,
                  result: step.result
                }))
              }
              
              // Legacy: Restore chain of thought from queue_steps (backwards compat)
              if (msg.metadata?.queue_steps && !msg.thinkingTrace) {
                const chainOfThought: ThoughtStep[] = msg.metadata.queue_steps.map((step: any) => ({
                  id: step.id,
                  type: "queue" as const,
                  name: step.label || step.name,
                  status: "completed" as const,
                }))
                msg.chainOfThought = chainOfThought
              }

              // Restore sources from message metadata
              if (msg.metadata?.sources) {
                msg.sources = msg.metadata.sources
                // Also restore citations for inline [1], [2] references
                msg.citations = msg.metadata.sources.map((s: any, idx: number) => ({
                  id: `cite-${idx + 1}`,
                  number: String(idx + 1),
                  text: s.content?.substring(0, 150) || "",
                  title: s.title || s.source_file || "Source",
                  description: s.description || s.content?.substring(0, 100),
                  url: s.url || `#source-${idx + 1}`,
                  quote: s.content?.substring(0, 200),
                  source_file: s.source_file,
                  module: s.module,
                  week: s.week,
                  content: s.content?.substring(0, 150)
                }))
              }

              // Restore evaluation from message metadata
              if (msg.metadata?.evaluation) {
                msg.evaluation = msg.metadata.evaluation
              }
              
              // Restore reasoning (Gemini thought summaries) from message metadata
              if (msg.metadata?.reasoning) {
                msg.reasoning = msg.metadata.reasoning
              }
              
              // Restore currentPhase from metadata for correct accordion state
              if (msg.metadata?.currentPhase) {
                msg.metadata.currentPhase = msg.metadata.currentPhase
              }
              
              // Mark as complete since it's from history
              msg.streamComplete = true
              msg.status = "complete"
            }
            return msg
          })
          setMessages(messagesWithMetadata)
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
   * Uses streamBufferRef to accumulate content and prevent race conditions
   */
  const processStreamEvent = useCallback((parsed: any, assistantMessageId: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id !== assistantMessageId) return msg

      const updatedMsg = { ...msg }
      const buffer = streamBufferRef.current

      // Text streaming - accumulate in buffer to prevent race conditions
      if (parsed.type === "text-delta") {
        // Accumulate in buffer (source of truth during streaming)
        buffer.rawContent = (buffer.rawContent || "") + parsed.textDelta

        let processedContent = buffer.rawContent

        // Extract XML thinking tags
        const thinkingMatch = processedContent.match(/<thinking>([\s\S]*?)<\/thinking>/)
        const openThinkingMatch = processedContent.match(/<thinking>([\s\S]*)$/)

        if (thinkingMatch) {
          buffer.reasoning = thinkingMatch[1]
          processedContent = processedContent.replace(/<thinking>[\s\S]*?<\/thinking>/, "")
        } else if (openThinkingMatch) {
          buffer.reasoning = openThinkingMatch[1]
          processedContent = processedContent.replace(/<thinking>[\s\S]*$/, "")
        }

        // Clean up other tags
        processedContent = processedContent.replace(/<\/?follow_up>/g, "")

        // Strip reasoning JSON blocks (from reasoning node)
        processedContent = processedContent.replace(/```json\n?\s*\{[\s\S]*?"perception"[\s\S]*?\}\s*\n?```/gi, "")
        processedContent = processedContent.replace(/\{[\s\S]*?"perception"\s*:\s*\{[\s\S]*?"query_type"[\s\S]*?\}\s*\}/g, "")

        // Update buffer and message
        buffer.content = processedContent
        updatedMsg.rawContent = buffer.rawContent
        updatedMsg.content = buffer.content
        updatedMsg.reasoning = buffer.reasoning

        // Try to parse partial JSON for structured output (Manual Streaming)
        const partialJson = safeParsePartialJson(buffer.rawContent)
        if (partialJson && typeof partialJson === 'object') {
          buffer.structuredOutput = partialJson
          updatedMsg.structuredOutput = partialJson
        }

      // Reasoning/thinking delta
      } else if (parsed.type === "reasoning-delta") {
        buffer.reasoning = (buffer.reasoning || "") + parsed.reasoningDelta
        updatedMsg.reasoning = buffer.reasoning

      // Sources from RAG retrieval - store in buffer for persistence
      } else if (parsed.type === "sources") {
        const sources = parsed.sources?.map((s: any, idx: number) => ({
          id: s.id || `src-${idx}`,
          title: s.title || s.source_file || "Source",
          source_file: s.source_file,
          page: s.page,
          description: s.description || s.content?.substring(0, 100),
          content: s.content,
          url: s.url,
          module: s.module,
          week: s.week
        }))
        
        // Create numbered citations from sources for inline [1], [2] references
        const citations = parsed.sources?.map((s: any, idx: number) => ({
          id: `cite-${idx + 1}`,
          number: String(idx + 1),  // "1", "2", "3", etc.
          text: s.content?.substring(0, 150) || "",
          title: s.title || s.source_file || "Source",
          description: s.description || s.content?.substring(0, 100),
          url: s.url || `#source-${idx + 1}`,  // Fallback URL for local sources
          quote: s.content?.substring(0, 200),
          source_file: s.source_file,
          module: s.module,  // Pass module for badge display
          week: s.week,      // Pass week for badge display
          content: s.content?.substring(0, 150)  // Content preview
        }))
        
        // Store in buffer for finish handler
        buffer.sources = sources
        buffer.citations = citations
        
        updatedMsg.sources = sources
        updatedMsg.citations = citations

      // Citations event (separate from sources for inline citation badges)
      } else if (parsed.type === "citations") {
        buffer.citations = parsed.citations
        updatedMsg.citations = buffer.citations

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

      // Phase transition events (from backend orchestration)
      } else if (parsed.type === "phase-transition") {
        const fromPhase = parsed.from
        const toPhase = parsed.to
        
        if (isDevelopment) {
          console.log(`📍 Phase transition: ${fromPhase} → ${toPhase}`)
        }
        
        // Update phase in buffer and message
        buffer.currentPhase = toPhase
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          currentPhase: toPhase
        }
      
      // Structured thinking events from agent pipeline
      // Shows scope check, classification, escalation decisions, RAG retrieval
      } else if (parsed.type === "thinking") {
        const step = parsed.step as ThinkingStepType
        const status = parsed.status as ThinkingStep["status"]
        const message = parsed.message || ""
        const result = parsed.result || {}
        
        if (isDevelopment) {
          console.log("🧠 Thinking step:", step, status, message)
        }
        
        // Initialize thinkingTrace in buffer if not present
        if (!buffer.thinkingTrace) {
          buffer.thinkingTrace = []
        }
        if (!updatedMsg.thinkingTrace) {
          updatedMsg.thinkingTrace = []
        }
        
        // Find existing step or add new one
        const existingStepIndex = buffer.thinkingTrace.findIndex(s => s.step === step)
        if (existingStepIndex >= 0) {
          // Update existing step in buffer
          buffer.thinkingTrace = buffer.thinkingTrace.map((s, i) =>
            i === existingStepIndex 
              ? { ...s, status, result, message }
              : s
          )
        } else {
          // Add new step to buffer
          buffer.thinkingTrace = [
            ...buffer.thinkingTrace,
            { step, status, result, message }
          ]
        }
        // Sync to message
        updatedMsg.thinkingTrace = [...buffer.thinkingTrace]

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

      // Evaluation scores (agent badge, concept, quality metrics) - store in buffer
      } else if (parsed.type === "evaluation") {
        if (isDevelopment) {
          console.log("📊 Received evaluation event:", parsed.evaluation)
          console.log("📊 Evaluation keys:", parsed.evaluation ? Object.keys(parsed.evaluation) : "no evaluation")
        }
        // Store in buffer for finish handler
        buffer.evaluation = parsed.evaluation
        buffer.metadata = {
          ...buffer.metadata,
          evaluation: parsed.evaluation
        }
        
        updatedMsg.evaluation = parsed.evaluation
        // Also update metadata for persistence
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          evaluation: parsed.evaluation
        }

      // Metadata on finish - mark stream as complete and preserve buffer content
      } else if (parsed.type === "finish") {
        const buffer = streamBufferRef.current
        
        // CRITICAL: Ensure content from buffer is preserved in final message
        // This prevents the "disappearing content" issue
        if (buffer.content) {
          updatedMsg.content = buffer.content
          updatedMsg.rawContent = buffer.rawContent
        }
        if (buffer.reasoning) {
          updatedMsg.reasoning = buffer.reasoning
        }
        if (buffer.sources && buffer.sources.length > 0) {
          updatedMsg.sources = buffer.sources
        }
        if (buffer.citations && buffer.citations.length > 0) {
          updatedMsg.citations = buffer.citations
        }
        if (buffer.thinkingTrace && buffer.thinkingTrace.length > 0) {
          updatedMsg.thinkingTrace = buffer.thinkingTrace
        }
        if (buffer.evaluation) {
          updatedMsg.evaluation = buffer.evaluation
        }
        if (buffer.structuredOutput) {
          updatedMsg.structuredOutput = buffer.structuredOutput
        }
        
        // Ensure final phase is set to "response" for correct accordion state
        const finalPhase = parsed.finalPhase || "response"
        buffer.currentPhase = finalPhase
        
        updatedMsg.metadata = {
          ...updatedMsg.metadata,
          ...buffer.metadata,
          traceId: parsed.traceId,
          chatId: parsed.chatId,
          currentPhase: finalPhase
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
        // Mark thinkingTrace steps as complete
        updatedMsg.thinkingTrace = updatedMsg.thinkingTrace?.map(step =>
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
    
    // Mark as actively streaming to prevent refetch flash
    isStreamingRef.current = true
    
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

    // Reset stream buffer for new message (prevents stale data from previous stream)
    streamBufferRef.current = {
      rawContent: "",
      content: "",
      reasoning: undefined,
      sources: undefined,
      citations: undefined,
      thinkingTrace: undefined,
      metadata: undefined,
      evaluation: undefined,
      structuredOutput: undefined,
      currentPhase: "thinking"
    }

    // Create placeholder assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    currentMessageIdRef.current = assistantMessageId
    
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      rawContent: "",
      metadata: {
        currentPhase: "thinking"
      },
      // Initialize for structured thinking display
      thinkingTrace: [],
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
      
      // Clear streaming flag with delay to prevent immediate refetch
      setTimeout(() => {
        isStreamingRef.current = false
      }, 1000)
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

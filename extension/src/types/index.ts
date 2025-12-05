/**
 * Unified thought step for Chain of Thought display
 * Combines queue items, tool calls, and reasoning into a single type
 */
export interface ThoughtStep {
  id: string
  type: "queue" | "tool" | "reasoning" | "search" | "result"
  name: string
  status: "pending" | "waiting" | "processing" | "in-progress" | "completed" | "complete" | "error"
  details?: string
  input?: Record<string, any>
  output?: any
  sources?: Array<{ title: string; url?: string }>
  timestamp?: number
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  rawContent?: string
  reasoning?: string
  sources?: Array<{ 
    title: string
    url?: string
    description?: string 
    source_file?: string
    page?: number | string
    content?: string
  }>
  attachments?: File[]
  
  // NEW: Unified Chain of Thought (replaces separate queue/tools/tasks)
  chainOfThought?: ThoughtStep[]
  
  // Legacy: Task management (AI SDK task element) - kept for backwards compat
  tasks?: Array<{ 
    id: string
    title: string
    status: "pending" | "in-progress" | "completed" | "error"
    startedAt?: number
    completedAt?: number
    error?: string
  }>
  
  // Legacy: Tool execution (AI SDK tool element) - kept for backwards compat
  tools?: Array<{
    id?: string
    name: string
    args?: Record<string, any>
    result?: any
    status: "pending" | "in-progress" | "completed" | "error"
    startedAt?: number
    completedAt?: number
  }>
  
  // Legacy: Processing queue (AI SDK queue element) - kept for backwards compat
  queue?: Array<{
    id: string
    name: string
    status: "pending" | "processing" | "completed" | "error"
    description?: string
    startedAt?: number
    completedAt?: number
    error?: string
  }>
  
  // Code blocks with execution support
  codeBlocks?: Array<{ 
    id?: string
    language: string
    code: string 
    filename?: string
    executionResult?: string
  }>
  
  // Images with captions
  images?: Array<{ src: string; alt: string; caption?: string }>
  
  // Inline citations (AI SDK inline-citation element)
  citations?: Array<{
    id: string
    number: string
    text: string
    url?: string
    title: string
    description?: string
    quote?: string
    source_file?: string
  }>
  
  // Chain of thought / reasoning steps (AI SDK reasoning element)
  thinkingSteps?: Array<{
    id?: string
    step: string
    status: "thinking" | "complete" | "error"
    details?: string
    startedAt?: number
    completedAt?: number
  }>
  
  // Suggestions for follow-up
  suggestions?: string[]
  
  // Metadata for observability
  metadata?: {
    traceId?: string
    chatId?: string
    intent?: string
    model?: string
    scaffoldingLevel?: string
    executionTimeMs?: number
    evaluation?: {
      confidence: number
      passed: boolean
      feedback: string
      level: string
      quality_breakdown: Record<string, number>
      detected_concept?: string
      misconceptions?: Array<{ misconception_id: string; description: string; concept: string }>
      agent_used?: string
      scaffolding_level?: string
    }
  }
  
  // Evaluation scores (direct property for easier access)
  evaluation?: {
    confidence: number
    passed: boolean
    feedback: string
    level: string
    quality_breakdown: Record<string, number>
    detected_concept?: string
    misconceptions?: Array<{ misconception_id: string; description: string; concept: string }>
    agent_used?: string
    scaffolding_level?: string
  }
  
  // Status for streaming
  status?: "streaming" | "complete" | "error"
  
  // Flag to indicate stream has finished (for UI state management)
  streamComplete?: boolean
}

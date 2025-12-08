/**
 * Structured thinking step from agent execution
 * Matches backend ThinkingStep Pydantic schema
 * 
 * Step types:
 * - scope_check: Verifying question is within COMP237 scope
 * - integrity_check: Checking for academic integrity violations
 * - mastery_lookup: Fetching student's current mastery level
 * - escalation: Deciding scaffolding level (1-4)
 * - classification: Determining task type (explain/solve/code)
 * - rag_retrieval: Searching course materials
 * - strategy: Selecting teaching strategy
 * - concept_detection: Identifying AI/ML concept in response
 */
export type ThinkingStepType = 
  | "scope_check" 
  | "integrity_check"
  | "mastery_lookup"
  | "escalation"
  | "classification"
  | "rag_retrieval"
  | "strategy"
  | "concept_detection"

export interface ThinkingStep {
  step: ThinkingStepType
  status: "pending" | "processing" | "completed" | "error"
  result?: Record<string, any>
  message?: string
  duration_ms?: number
}

/**
 * Legacy ThoughtStep for backwards compatibility
 * Used by older queue-based UI components
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
    // Multi-collection support (from RAG v2)
    source_type?: "course" | "oer" | "embedded"
    citation_confidence?: "high" | "medium" | "low"
    link_type?: "blackboard" | "mediasite" | "generic_url"
  }>
  attachments?: File[]
  
  // Structured output parsed from partial JSON (for manual streaming)
  structuredOutput?: any

  // NEW: Structured thinking steps from agent (replaces chainOfThought)
  thinkingTrace?: ThinkingStep[]
  
  // Legacy: Unified Chain of Thought (for backwards compat)
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
    /** Module name (e.g., "Module 4") */
    module?: string
    /** Week number (1-14) */
    week?: number
    /** Content snippet for preview */
    content?: string
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
    detectedConcepts?: string[]
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

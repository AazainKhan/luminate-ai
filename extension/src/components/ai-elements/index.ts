/**
 * AI SDK Elements
 * 
 * Vercel AI SDK-style UI components for streaming AI responses.
 * These components are designed to display various types of AI-generated content
 * including reasoning, sources, tasks, tools, code, and more.
 * 
 * Components follow the AI Elements pattern with:
 * - Auto-expand/collapse animations during streaming
 * - Duration tracking for processing steps
 * - Staggered animations for list items
 * - Context-based state sharing
 */

// ============================================================================
// Loading States
// ============================================================================

export { 
  Shimmer, 
  ShimmerInline, 
  ShimmerCode, 
  ShimmerCard 
} from "./shimmer"

export { 
  Loader, 
  LoaderText, 
  StreamingIndicator,
  type LoaderProps,
} from "./loader"

// ============================================================================
// Reasoning / Chain of Thought
// ============================================================================

export { 
  Reasoning, 
  ReasoningTrigger, 
  ReasoningContent,
  ReasoningContext,
  type ReasoningProps,
  type ReasoningTriggerProps,
  type ReasoningContentProps,
} from "./reasoning"

// ============================================================================
// Thinking Trace (Structured Agent Decisions)
// ============================================================================

export {
  ThinkingTrace,
  type ThinkingStep,
  type ThinkingStepType,
} from "./thinking-trace"

// ============================================================================
// Source Citations
// ============================================================================

export { 
  Sources, 
  SourcesTrigger, 
  SourcesContent, 
  Source,
  SourcesContext,
  type SourcesProps,
  type SourcesTriggerProps,
  type SourcesContentProps,
  type SourceProps,
} from "./sources"

// ============================================================================
// Inline Citations
// ============================================================================

export {
  InlineCitation,
  InlineCitationText,
  InlineCitationCard,
  InlineCitationCardTrigger,
  InlineCitationCardBody,
  InlineCitationSource,
  InlineCitationQuote,
} from "./inline-citation"

// ============================================================================
// Task Progress
// ============================================================================

export { 
  Task, 
  TaskTrigger, 
  TaskContent, 
  TaskItem 
} from "./task"

// ============================================================================
// Tool Execution
// ============================================================================

export { Tool } from "./tool"

// ============================================================================
// Code Blocks
// ============================================================================

export { 
  CodeBlock, 
  CodeBlockCopyButton, 
  CodeBlockRunButton 
} from "./code-block"

// ============================================================================
// Response / Markdown Rendering
// ============================================================================

export { Response } from "./response"

// ============================================================================
// Images
// ============================================================================

export { AIImage } from "./image"

// ============================================================================
// Suggestions
// ============================================================================

export { 
  Suggestion, 
  SuggestionList 
} from "./suggestion"

// ============================================================================
// Evaluation
// ============================================================================

export { EvaluationCard } from "./evaluation-card"

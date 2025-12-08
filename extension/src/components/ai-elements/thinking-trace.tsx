"use client"

import * as React from "react"
import { 
  CheckCircle2, 
  Loader2, 
  AlertCircle,
  Shield,
  GraduationCap,
  Sparkles,
  Search,
  Target,
  BookOpen,
  ChevronDown,
  Brain
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ThinkingStep, ThinkingStepType } from "@/types"
import { Reasoning, ReasoningTrigger, ReasoningContent } from "./reasoning"

/**
 * Icon mapping for each thinking step type
 */
const STEP_ICONS: Record<ThinkingStepType, React.ElementType> = {
  scope_check: Shield,
  integrity_check: Shield,
  mastery_lookup: GraduationCap,
  escalation: Sparkles,
  classification: Target,
  rag_retrieval: Search,
  strategy: Brain,
  concept_detection: BookOpen,
}

/**
 * User-friendly labels for each step type
 */
const STEP_LABELS: Record<ThinkingStepType, string> = {
  scope_check: "Scope Check",
  integrity_check: "Integrity Check",
  mastery_lookup: "Mastery Lookup",
  escalation: "Scaffolding Level",
  classification: "Classification",
  rag_retrieval: "Course Materials",
  strategy: "Strategy",
  concept_detection: "Concept Detection",
}

interface ThinkingStepItemProps {
  step: ThinkingStep
  isLast?: boolean
}

/**
 * Single thinking step item with icon, status, and optional result
 */
function ThinkingStepItem({ step, isLast }: ThinkingStepItemProps) {
  const Icon = STEP_ICONS[step.step] || Brain
  const label = STEP_LABELS[step.step] || step.step
  
  return (
    <div className={cn(
      "flex items-start gap-2 relative",
      !isLast && "pb-2"
    )}>
      {/* Vertical line connecting steps */}
      {!isLast && (
        <div className="absolute left-[9px] top-5 bottom-0 w-px bg-border/50" />
      )}
      
      {/* Status indicator */}
      <div className={cn(
        "w-[18px] h-[18px] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
        step.status === "completed" && "bg-emerald-500/20 text-emerald-500",
        step.status === "processing" && "bg-violet-500/20 text-violet-400",
        step.status === "pending" && "bg-muted text-muted-foreground",
        step.status === "error" && "bg-red-500/20 text-red-500",
      )}>
        {step.status === "processing" ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : step.status === "completed" ? (
          <CheckCircle2 className="w-3 h-3" />
        ) : step.status === "error" ? (
          <AlertCircle className="w-3 h-3" />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-current" />
        )}
      </div>
      
      {/* Step content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3 h-3 text-muted-foreground" />
          <span className={cn(
            "text-xs font-medium",
            step.status === "processing" && "text-violet-400",
            step.status === "completed" && "text-foreground",
            step.status === "pending" && "text-muted-foreground",
            step.status === "error" && "text-red-500",
          )}>
            {label}
          </span>
        </div>
        
        {/* Step message */}
        {step.message && (
          <p className={cn(
            "text-[11px] mt-0.5 leading-snug",
            step.status === "completed" ? "text-muted-foreground" : "text-muted-foreground/70"
          )}>
            {step.message}
          </p>
        )}
      </div>
    </div>
  )
}

interface ThinkingTraceProps {
  /** Array of thinking steps from agent execution */
  steps: ThinkingStep[]
  /** Whether the agent is still processing */
  isStreaming?: boolean
  className?: string
}

/**
 * ThinkingTrace - Displays structured thinking steps from the agent
 * 
 * A sleek, Gemini-like accordion that shows the agent's decision-making process:
 * - Scope check (is question within COMP237?)
 * - Classification (explain/solve/code)
 * - Escalation (scaffolding level 1-4)
 * - RAG retrieval (finding course materials)
 * - Strategy selection (teaching approach)
 * 
 * @example
 * ```tsx
 * <ThinkingTrace 
 *   steps={message.thinkingTrace || []}
 *   isStreaming={isLoading}
 * />
 * ```
 */
export function ThinkingTrace({ 
  steps, 
  isStreaming = false,
  className 
}: ThinkingTraceProps) {
  // Don't render if no steps
  if (!steps || steps.length === 0) {
    return null
  }
  
  // Count completed steps for summary
  const completedCount = steps.filter(s => s.status === "completed").length
  const processingStep = steps.find(s => s.status === "processing")
  
  return (
    <Reasoning 
      isStreaming={isStreaming} 
      className={className}
    >
      <ReasoningTrigger>
        {isStreaming ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-violet-400" />
            <span className="animate-pulse text-violet-400 text-xs font-medium">
              {processingStep 
                ? STEP_LABELS[processingStep.step] || "Thinking..."
                : "Thinking..."}
            </span>
            <ChevronDown className="h-4 w-4 ml-auto transition-transform duration-200 group-data-[state=open]:rotate-180 text-muted-foreground" />
          </>
        ) : (
          <>
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium">
              {completedCount} step{completedCount !== 1 ? "s" : ""} completed
            </span>
            <ChevronDown className="h-4 w-4 ml-auto transition-transform duration-200 group-data-[state=open]:rotate-180 text-muted-foreground" />
          </>
        )}
      </ReasoningTrigger>
      
      <ReasoningContent>
        <div className="space-y-0">
          {steps.map((step, index) => (
            <ThinkingStepItem 
              key={step.step} 
              step={step} 
              isLast={index === steps.length - 1}
            />
          ))}
        </div>
      </ReasoningContent>
    </Reasoning>
  )
}

export { type ThinkingStep, type ThinkingStepType }

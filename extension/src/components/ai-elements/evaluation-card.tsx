import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Bot, Sparkles, Calculator, Code, BookOpen, Zap, Brain, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"

interface EvaluationData {
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

interface EvaluationCardProps {
  evaluation: EvaluationData
  defaultOpen?: boolean
}

/**
 * Rich evaluation display showing:
 * - Which agent handled the request
 * - Detected concept/topic
 * - Scaffolding level
 * - Quality confidence (expandable)
 * - Misconception alerts
 */
export function EvaluationCard({ evaluation, defaultOpen = false }: EvaluationCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultOpen)
  
  // Always show if we have any useful info
  if (!evaluation.agent_used && !evaluation.detected_concept) return null

  // Get agent display name and icon based on backend values
  const getAgentInfo = (agentName: string) => {
    const normalized = agentName.toLowerCase()
    
    if (normalized.includes("concept tutor") || normalized.includes("tutor") || normalized.includes("explainer")) {
      return { 
        name: normalized.includes("explainer") ? "Explainer" : "Concept Tutor", 
        icon: Sparkles, 
        color: "text-violet-500 border-violet-500/30 bg-violet-500/10" 
      }
    }
    if (normalized.includes("math") || normalized.includes("solver")) {
      return { 
        name: "Math Solver", 
        icon: Calculator, 
        color: "text-amber-500 border-amber-500/30 bg-amber-500/10" 
      }
    }
    if (normalized.includes("code") || normalized.includes("assistant") || normalized.includes("coder")) {
      return { 
        name: "Code Assistant", 
        icon: Code, 
        color: "text-blue-500 border-blue-500/30 bg-blue-500/10" 
      }
    }
    if (normalized.includes("course") || normalized.includes("syllabus") || normalized.includes("info")) {
      return { 
        name: "Course Info", 
        icon: BookOpen, 
        color: "text-emerald-500 border-emerald-500/30 bg-emerald-500/10" 
      }
    }
    if (normalized.includes("quick") || normalized.includes("fast")) {
      return { 
        name: "Quick Answer", 
        icon: Zap, 
        color: "text-cyan-500 border-cyan-500/30 bg-cyan-500/10" 
      }
    }
    if (normalized.includes("practice") || normalized.includes("problem") || normalized.includes("coach")) {
      return { 
        name: "Practice Coach", 
        icon: Bot, 
        color: "text-rose-500 border-rose-500/30 bg-rose-500/10" 
      }
    }
    
    return { 
      name: agentName, 
      icon: Bot, 
      color: "text-muted-foreground border-border bg-muted/50" 
    }
  }

  // Format concept name for display
  const formatConcept = (concept: string) => {
    return concept
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  // Get scaffolding level display
  const getScaffoldingInfo = (level: string | undefined) => {
    if (!level || level === 'none') return null
    
    const levelMap: Record<string, { label: string; color: string }> = {
      'hint': { label: 'Hint', color: 'text-sky-500' },
      'guided': { label: 'Guided', color: 'text-indigo-500' },
      'explained': { label: 'Explained', color: 'text-violet-500' },
      'demonstrated': { label: 'Demo', color: 'text-fuchsia-500' },
    }
    
    return levelMap[level] || { label: level, color: 'text-muted-foreground' }
  }

  const agentInfo = evaluation.agent_used ? getAgentInfo(evaluation.agent_used) : null
  const Icon = agentInfo?.icon || Bot
  const scaffoldingInfo = getScaffoldingInfo(evaluation.scaffolding_level)
  const hasMisconceptions = evaluation.misconceptions && evaluation.misconceptions.length > 0
  const hasDetails = evaluation.confidence > 0 || evaluation.quality_breakdown

  return (
    <div className="mt-2 pt-2 border-t border-border/30">
      {/* Primary row: Agent + Concept + Scaffolding */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Agent Badge */}
        {agentInfo && (
          <Badge 
            variant="outline" 
            className={cn(
              "text-xs font-normal gap-1.5 py-1",
              agentInfo.color
            )}
          >
            <Icon className="w-3 h-3" />
            {agentInfo.name}
          </Badge>
        )}

        {/* Concept Badge */}
        {evaluation.detected_concept && (
          <Badge 
            variant="outline" 
            className="text-xs font-normal gap-1.5 py-1 text-emerald-500 border-emerald-500/30 bg-emerald-500/10"
          >
            <Brain className="w-3 h-3" />
            {formatConcept(evaluation.detected_concept)}
          </Badge>
        )}

        {/* Scaffolding Badge */}
        {scaffoldingInfo && (
          <Badge 
            variant="outline" 
            className={cn(
              "text-xs font-normal py-1",
              scaffoldingInfo.color,
              `border-current/30 bg-current/10`
            )}
          >
            {scaffoldingInfo.label}
          </Badge>
        )}

        {/* Expand button for details */}
        {hasDetails && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="ml-auto flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <span className="opacity-60">
              {Math.round(evaluation.confidence * 100)}% confidence
            </span>
            {isExpanded ? (
              <ChevronUp className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
          </button>
        )}
      </div>

      {/* Misconception Alert */}
      {hasMisconceptions && (
        <div className="mt-2 p-2 rounded-md bg-amber-500/10 border border-amber-500/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-medium text-amber-500">Potential Misconception Detected</p>
              {evaluation.misconceptions!.map((m, i) => (
                <p key={i} className="text-xs text-muted-foreground mt-1">
                  {m.description}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Expanded Quality Details */}
      {isExpanded && hasDetails && (
        <div className="mt-2 p-2 rounded-md bg-muted/30 border border-border/50">
          <p className="text-xs text-muted-foreground mb-2">{evaluation.feedback}</p>
          
          {evaluation.quality_breakdown && Object.keys(evaluation.quality_breakdown).length > 0 && (
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              {Object.entries(evaluation.quality_breakdown).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full rounded-full transition-all",
                          value >= 0.7 ? "bg-emerald-500" : 
                          value >= 0.4 ? "bg-amber-500" : "bg-red-500"
                        )}
                        style={{ width: `${Math.round(value * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-8 text-right">
                      {Math.round(value * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

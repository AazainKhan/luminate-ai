import React from "react"
import { HelpCircle, Lightbulb, MapPin, BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface ScaffoldingCardProps {
  title: string
  icon: React.ElementType
  children: React.ReactNode
  className?: string
  variant?: "default" | "question" | "hint" | "orientation" | "example"
}

const variantStyles = {
  default: "bg-secondary/50 border-border",
  question: "bg-blue-500/10 border-blue-500/20 text-blue-900 dark:text-blue-100",
  hint: "bg-amber-500/10 border-amber-500/20 text-amber-900 dark:text-amber-100",
  orientation: "bg-emerald-500/10 border-emerald-500/20 text-emerald-900 dark:text-emerald-100",
  example: "bg-purple-500/10 border-purple-500/20 text-purple-900 dark:text-purple-100",
}

const iconStyles = {
  default: "text-foreground",
  question: "text-blue-700 dark:text-blue-400",
  hint: "text-amber-700 dark:text-amber-400",
  orientation: "text-emerald-600 dark:text-emerald-400",
  example: "text-purple-600 dark:text-purple-400",
}

export function ScaffoldingCard({ 
  title, 
  icon: Icon, 
  children, 
  className,
  variant = "default" 
}: ScaffoldingCardProps) {
  return (
    <div className={cn(
      "my-4 rounded-lg border p-4 text-sm",
      variantStyles[variant],
      className
    )}>
      <div className="flex items-start gap-3">
        <div className={cn("mt-0.5 shrink-0", iconStyles[variant])}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 space-y-1">
          <div className={cn("font-semibold", iconStyles[variant])}>
            {title}
          </div>
          <div className="leading-relaxed text-foreground">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

export function QuestionCard({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <ScaffoldingCard 
      title="Question" 
      icon={HelpCircle} 
      variant="question" 
      className={className}
    >
      {children}
    </ScaffoldingCard>
  )
}

export function HintCard({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <ScaffoldingCard 
      title="Hint" 
      icon={Lightbulb} 
      variant="hint" 
      className={className}
    >
      {children}
    </ScaffoldingCard>
  )
}

export function OrientationCard({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <ScaffoldingCard 
      title="Orientation" 
      icon={MapPin} 
      variant="orientation" 
      className={className}
    >
      {children}
    </ScaffoldingCard>
  )
}

export function ExampleCard({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <ScaffoldingCard 
      title="Example" 
      icon={BookOpen} 
      variant="example" 
      className={className}
    >
      {children}
    </ScaffoldingCard>
  )
}

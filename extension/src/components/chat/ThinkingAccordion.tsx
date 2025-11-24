import { useState } from "react"
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react"

interface ThinkingStep {
  step: string
  status: "thinking" | "complete" | "error"
  details?: string
}

interface ThinkingAccordionProps {
  steps: ThinkingStep[]
  isOpen?: boolean
}

export function ThinkingAccordion({ steps, isOpen: defaultOpen = false }: ThinkingAccordionProps) {
  const [open, setOpen] = useState(defaultOpen)

  if (steps.length === 0) {
    return null
  }

  return (
    <div className="border rounded-lg bg-gray-50">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
          <span className="text-sm font-medium text-gray-700">Agent Thinking Process</span>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-2">
          {steps.map((step, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-2 rounded bg-white"
            >
              <div className="flex-shrink-0 mt-0.5">
                {step.status === "thinking" && (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                )}
                {step.status === "complete" && (
                  <div className="w-4 h-4 rounded-full bg-green-500"></div>
                )}
                {step.status === "error" && (
                  <div className="w-4 h-4 rounded-full bg-red-500"></div>
                )}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{step.step}</div>
                {step.details && (
                  <div className="text-xs text-gray-600 mt-1">{step.details}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


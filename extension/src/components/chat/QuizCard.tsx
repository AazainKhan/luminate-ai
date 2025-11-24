import { useState } from "react"
import { CheckCircle2, XCircle } from "lucide-react"

interface QuizOption {
  id: string
  text: string
}

interface QuizCardProps {
  question: string
  options: QuizOption[]
  correctAnswerId: string
  onAnswer?: (selectedId: string, isCorrect: boolean) => void
}

export function QuizCard({ question, options, correctAnswerId, onAnswer }: QuizCardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)

  const handleSelect = (optionId: string) => {
    if (showResult) return // Don't allow changes after submission

    setSelectedId(optionId)
    const isCorrect = optionId === correctAnswerId
    setShowResult(true)

    if (onAnswer) {
      onAnswer(optionId, isCorrect)
    }
  }

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <h3 className="text-lg font-semibold mb-4">{question}</h3>
      <div className="space-y-2">
        {options.map((option) => {
          const isSelected = selectedId === option.id
          const isCorrect = option.id === correctAnswerId
          const showFeedback = showResult && isSelected

          return (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id)}
              disabled={showResult}
              className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all ${
                showFeedback
                  ? isCorrect
                    ? "border-green-500 bg-green-50"
                    : "border-red-500 bg-red-50"
                  : isSelected
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              } ${showResult ? "cursor-default" : "cursor-pointer"}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-gray-900">{option.text}</span>
                {showFeedback && (
                  <div className="flex-shrink-0 ml-2">
                    {isCorrect ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                )}
              </div>
            </button>
          )
        })}
      </div>
      {showResult && (
        <div
          className={`mt-4 p-3 rounded-lg ${
            selectedId === correctAnswerId
              ? "bg-green-50 text-green-800"
              : "bg-red-50 text-red-800"
          }`}
        >
          {selectedId === correctAnswerId ? (
            <p className="text-sm font-medium">Correct! Well done.</p>
          ) : (
            <p className="text-sm font-medium">
              Not quite. The correct answer is highlighted in green.
            </p>
          )}
        </div>
      )}
    </div>
  )
}


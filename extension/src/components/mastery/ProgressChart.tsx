import { BarChart3, TrendingUp } from "lucide-react"

interface ConceptMastery {
  concept_tag: string
  mastery_score: number
  last_interaction?: string
}

interface ProgressChartProps {
  mastery: ConceptMastery[]
}

export function ProgressChart({ mastery }: ProgressChartProps) {
  if (mastery.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-400" />
        <p>No mastery data yet. Start chatting to track your progress!</p>
      </div>
    )
  }

  // Sort by mastery score (lowest first)
  const sorted = [...mastery].sort((a, b) => a.mastery_score - b.mastery_score)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Mastery Progress</h3>
      </div>
      {sorted.map((item) => (
        <div key={item.concept_tag} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-gray-700 capitalize">
              {item.concept_tag.replace(/_/g, " ")}
            </span>
            <span className="text-gray-600 font-medium">
              {Math.round(item.mastery_score * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                item.mastery_score >= 0.7
                  ? "bg-green-500"
                  : item.mastery_score >= 0.4
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${item.mastery_score * 100}%` }}
            ></div>
          </div>
        </div>
      ))}
    </div>
  )
}


import { useState, useEffect } from "react"
import { ProgressChart } from "./ProgressChart"
import { apiRequest } from "~/lib/api"
import { BarChart3, AlertCircle } from "lucide-react"

interface ConceptMastery {
  concept_tag: string
  mastery_score: number
  last_interaction?: string
}

export function MasteryPanel() {
  const [mastery, setMastery] = useState<ConceptMastery[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMastery()
  }, [])

  const loadMastery = async () => {
    try {
      setLoading(true)
      const data = await apiRequest<{ mastery: ConceptMastery[] }>("/api/mastery")
      setMastery(data.mastery || [])
      setError(null)
    } catch (err: any) {
      setError(err.message || "Failed to load mastery data")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-600">
        Loading mastery data...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 text-red-600 mb-2">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <ProgressChart mastery={mastery} />
    </div>
  )
}


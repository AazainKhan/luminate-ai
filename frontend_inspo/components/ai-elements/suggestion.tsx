"use client"

import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SuggestionProps {
  text: string
  onSelect?: () => void
}

export function Suggestion({ text, onSelect }: SuggestionProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      className="bg-white/5 border-white/10 hover:bg-white/10 text-white text-sm h-auto py-2 px-3"
      onClick={onSelect}
    >
      <Sparkles className="h-3 w-3 mr-1.5 text-purple-400" />
      {text}
    </Button>
  )
}

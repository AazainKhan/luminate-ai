import { Loader2 } from "lucide-react"

export function Loader({ text }: { text?: string }) {
  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span className="text-sm">{text || "Loading..."}</span>
    </div>
  )
}
"use client"

import * as React from "react"
import { ChevronsUpDown, Zap, Brain, Cloud, HardDrive, Check } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { useAuth } from "@/hooks/useAuth"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"

export interface ModelInfo {
  id: string
  name: string
  provider: string
  description: string
  speed: "very_fast" | "fast" | "medium" | "slow"
  quality: "medium" | "high" | "very_high" | "excellent"
  cost: "free" | "low" | "medium" | "high"
  available: boolean
  default: boolean
  local: boolean
}

interface ModelSelectorProps {
  value?: string
  onValueChange?: (value: string) => void
  className?: string
  size?: "sm" | "default"
}

const speedColors: Record<string, string> = {
  very_fast: "text-emerald-400",
  fast: "text-green-400",
  medium: "text-yellow-400",
  slow: "text-orange-400",
}

const qualityColors: Record<string, string> = {
  excellent: "text-purple-400",
  very_high: "text-blue-400",
  high: "text-cyan-400",
  medium: "text-slate-400",
}

const providerIcons: Record<string, React.ReactNode> = {
  google: <Cloud className="w-3 h-3" />,
  github: <Brain className="w-3 h-3" />,
  groq: <Zap className="w-3 h-3" />,
  ollama: <HardDrive className="w-3 h-3" />,
}

export function ModelSelector({
  value,
  onValueChange,
  className,
  size = "sm",
}: ModelSelectorProps) {
  const { session } = useAuth()
  const [models, setModels] = React.useState<ModelInfo[]>([])
  const [loading, setLoading] = React.useState(true)
  const [internalValue, setInternalValue] = React.useState<string>("")

  // Fetch available models
  React.useEffect(() => {
    async function fetchModels() {
      if (!session?.access_token) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`${API_BASE_URL}/api/models/`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        })
        if (res.ok) {
          const data = await res.json()
          setModels(data)
          
          // Set default value if not provided
          if (!value) {
            // Default to "auto" if available, otherwise fallback to default model
            setInternalValue("auto")
            onValueChange?.("auto")
          }
        }
      } catch (e) {
        console.error("Failed to fetch models:", e)
      } finally {
        setLoading(false)
      }
    }

    fetchModels()
  }, [session])

  const currentValue = value ?? internalValue
  const selectedModel = currentValue === "auto" 
    ? { id: "auto", name: "Auto (Smart Router)", provider: "system", available: true, default: true, speed: "fast", quality: "high" } as ModelInfo
    : models.find((m) => m.id === currentValue)

  // Group models by provider
  const modelsByProvider = React.useMemo(() => {
    const grouped: Record<string, ModelInfo[]> = {}
    for (const model of models) {
      if (!grouped[model.provider]) {
        grouped[model.provider] = []
      }
      grouped[model.provider].push(model)
    }
    return grouped
  }, [models])

  const providerNames: Record<string, string> = {
    system: "System",
    google: "Google AI",
    github: "GitHub Models",
    groq: "Groq (Fast)",
    ollama: "Local (Ollama)",
  }
  
  const providerIcons: Record<string, React.ReactNode> = {
    system: <Brain className="w-3 h-3 text-violet-400" />,
    google: <Cloud className="w-3 h-3" />,
    github: <Brain className="w-3 h-3" />,
    groq: <Zap className="w-3 h-3" />,
    ollama: <HardDrive className="w-3 h-3" />,
  }

  const handleValueChange = (newValue: string) => {
    setInternalValue(newValue)
    onValueChange?.(newValue)
  }

  if (loading) {
    return (
      <div className={cn("h-8 w-[180px] animate-pulse bg-muted rounded-md", className)} />
    )
  }

  return (
    <Select value={currentValue} onValueChange={handleValueChange}>
      <SelectTrigger 
        size={size}
        className={cn(
          "w-[180px] bg-background/50 hover:bg-background/80 transition-colors",
          className
        )}
      >
        <SelectValue placeholder="Select model">
          {selectedModel && (
            <span className="flex items-center gap-2">
              <span className="opacity-70">{providerIcons[selectedModel.provider]}</span>
              <span className="truncate">{selectedModel.name}</span>
            </span>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="w-[280px]">
        {/* Auto Option */}
        <SelectGroup>
          <SelectLabel className="flex items-center gap-2">
            <Brain className="w-3 h-3 text-violet-400" />
            System
          </SelectLabel>
          <SelectItem value="auto" className="py-2">
            <div className="flex flex-col gap-0.5 w-full">
              <div className="flex items-center justify-between w-full">
                <span className="font-medium flex items-center gap-1.5">
                  Auto (Smart Router)
                  <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4 bg-violet-500/10 text-violet-400 hover:bg-violet-500/20">
                    recommended
                  </Badge>
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                <span className="text-violet-400">Dynamic</span>
                <span className="opacity-30">•</span>
                <span className="text-violet-400">Best for task</span>
              </div>
            </div>
          </SelectItem>
        </SelectGroup>
        <SelectSeparator />
        
        {Object.entries(modelsByProvider).map(([provider, providerModels], idx) => (
          <React.Fragment key={provider}>
            {idx > 0 && <SelectSeparator />}
            <SelectGroup>
              <SelectLabel className="flex items-center gap-2">
                {providerIcons[provider]}
                {providerNames[provider] || provider}
              </SelectLabel>
              {providerModels.map((model) => (
                <SelectItem
                  key={model.id}
                  value={model.id}
                  disabled={!model.available}
                  className="py-2"
                >
                  <div className="flex flex-col gap-0.5 w-full">
                    <div className="flex items-center justify-between w-full">
                      <span className="font-medium flex items-center gap-1.5">
                        {model.name}
                        {model.default && (
                          <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">
                            default
                          </Badge>
                        )}
                        {model.local && (
                          <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 text-emerald-400 border-emerald-400/30">
                            free
                          </Badge>
                        )}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                      <span className={speedColors[model.speed]}>
                        {model.speed.replace("_", " ")}
                      </span>
                      <span className="opacity-30">•</span>
                      <span className={qualityColors[model.quality]}>
                        {model.quality.replace("_", " ")} quality
                      </span>
                    </div>
                    {!model.available && (
                      <span className="text-[10px] text-destructive">
                        API key not configured
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectGroup>
          </React.Fragment>
        ))}
      </SelectContent>
    </Select>
  )
}

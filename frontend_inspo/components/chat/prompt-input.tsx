"use client"

import * as React from "react"
import { Mic, ChevronDown, SlidersHorizontal, Plus, AppWindow, Zap, Brain, Send, Square, Share } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

interface PromptInputProps {
  input: string
  setInput: (value: string) => void
  onSend: (content: string, attachments?: File[]) => void
  isLoading: boolean
  toggleHistory: () => void
}

export function PromptInput({ input, setInput, onSend, isLoading }: PromptInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const [modelMode, setModelMode] = React.useState<"auto" | "fast" | "thorough">("auto")
  const [mode, setMode] = React.useState<"quicknav" | "tutor" | null>("tutor") // Allow null (deselect)
  const [internetSearch, setInternetSearch] = React.useState(true)

  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (input.trim() && !isLoading) {
      onSend(input)
      setInput("")
    }
  }

  const handleModeToggle = (newMode: "quicknav" | "tutor") => {
    if (mode === newMode) {
      setMode(null)
    } else {
      setMode(newMode)
    }
  }

  const effectiveModelMode = mode === "quicknav" ? "auto" : modelMode
  const isQuickNavDisabled = modelMode === "thorough"

  return (
    <div className="p-4 pb-2 relative z-10">
      <div className="flex justify-end mb-2 px-2">
        <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-white">
          <Share className="w-4 h-4" />
        </Button>
      </div>
      <form
        onSubmit={handleSubmit}
        className="relative bg-[#1e1f2e] rounded-2xl border border-border/40 shadow-2xl overflow-hidden ring-1 ring-white/5"
      >
        {/* Toolbar */}
        <div className="flex items-center justify-between px-2 py-1.5 border-b border-border/30">
          <div className="flex items-center gap-1 w-full">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-2 text-xs font-medium text-gray-200 bg-white/5 hover:bg-white/10 rounded-lg border border-white/5 px-3"
                >
                  {effectiveModelMode === "auto" && <Zap className="w-3.5 h-3.5 text-yellow-400" />}
                  {effectiveModelMode === "fast" && <Zap className="w-3.5 h-3.5 text-yellow-400" />}
                  {effectiveModelMode === "thorough" && <Brain className="w-3.5 h-3.5 text-purple-400" />}
                  {effectiveModelMode === "auto" ? "Auto" : effectiveModelMode === "fast" ? "Fast" : "Thorough"}
                  <ChevronDown className="w-3 h-3 opacity-50" />
                </Button>
              </PopoverTrigger>
              {/* ... existing popover content ... */}
              <PopoverContent align="start" className="w-64 bg-[#1e1f2e] border-border/40 p-2">
                <div className="space-y-1">
                  <button
                    type="button"
                    onClick={() => setModelMode("auto")}
                    disabled={mode === "quicknav"}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left",
                      effectiveModelMode === "auto"
                        ? "bg-white/10 text-white"
                        : "text-gray-300 hover:bg-white/5 hover:text-white",
                      mode === "quicknav" && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">Auto</div>
                      <div className="text-xs text-muted-foreground">Best for task</div>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setModelMode("fast")}
                    disabled={mode === "quicknav"}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left",
                      modelMode === "fast" && mode !== "quicknav"
                        ? "bg-white/10 text-white"
                        : "text-gray-300 hover:bg-white/5 hover:text-white",
                      mode === "quicknav" && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">Fast</div>
                      <div className="text-xs text-muted-foreground">Llama 3.1 via Groq</div>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setModelMode("thorough")}
                    disabled={mode === "quicknav"}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left",
                      modelMode === "thorough" && mode !== "quicknav"
                        ? "bg-white/10 text-white"
                        : "text-gray-300 hover:bg-white/5 hover:text-white",
                      mode === "quicknav" && "opacity-50 cursor-not-allowed",
                    )}
                  >
                    <Brain className="w-4 h-4 text-purple-400" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">Thorough</div>
                      <div className="text-xs text-muted-foreground">Claude 3.5 Sonnet</div>
                    </div>
                  </button>
                </div>
              </PopoverContent>
            </Popover>
            <div className="h-4 w-[1px] bg-white/10 mx-1" />
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-white rounded-lg"
                >
                  <SlidersHorizontal className="w-4 h-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="start" side="top" className="w-72 bg-[#1e1f2e] border-border/40 p-4 mb-2">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-3">Capabilities</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="internet-search" className="text-sm text-gray-200">
                          Internet Search
                        </Label>
                        <Switch
                          id="internet-search"
                          checked={internetSearch}
                          onCheckedChange={setInternetSearch}
                          className="data-[state=checked]:bg-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-white rounded-lg"
              title="Add current tab to context"
            >
              <AppWindow className="w-4 h-4" />
            </Button>
            <div className="flex-1" /> {/* Spacer */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg ml-2"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Text Area */}
        <div className="px-3 py-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything, @ models, / prompts"
            className="min-h-[60px] w-full resize-none bg-transparent border-none p-0 text-sm text-gray-200 placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
          />
        </div>

        {/* Bottom Row */}
        <div className="px-3 pb-2 flex items-center justify-between border-t border-border/30 pt-2">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isQuickNavDisabled}
              onClick={() => handleModeToggle("quicknav")}
              className={cn(
                "h-7 rounded-full border text-xs px-3 gap-1.5",
                mode === "quicknav"
                  ? "bg-white/10 border-white/20 text-white"
                  : "bg-white/5 hover:bg-white/10 border-white/5 text-muted-foreground hover:text-white",
                isQuickNavDisabled && "opacity-40 cursor-not-allowed",
              )}
            >
              <Zap className="w-3 h-3" />
              Quick Nav
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleModeToggle("tutor")}
              className={cn(
                "h-7 rounded-full border text-xs px-3 gap-1.5",
                mode === "tutor"
                  ? "bg-white/10 border-white/20 text-white"
                  : "bg-white/5 hover:bg-white/10 border-white/5 text-muted-foreground hover:text-white",
              )}
            >
              <Brain className="w-3 h-3" />
              Tutor
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={!input.trim() && !isLoading}
              size="icon"
              className={cn(
                "h-8 w-8 rounded-full transition-all duration-200",
                isLoading
                  ? "bg-red-500 hover:bg-red-600 text-white"
                  : input.trim()
                    ? "bg-white text-black hover:bg-gray-200"
                    : "bg-white/5 text-muted-foreground hover:bg-white/10",
              )}
            >
              {isLoading ? <Square className="w-3 h-3 fill-current" /> : <Send className="w-4 h-4" />}
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-white"
            >
              <Mic className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}

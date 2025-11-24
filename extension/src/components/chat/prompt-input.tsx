"use client"

import * as React from "react"
import {
  Mic,
  ChevronDown,
  SlidersHorizontal,
  Plus,
  AppWindow,
  Zap,
  Brain,
  Send,
  Square,
  Share,
  Download,
  HelpCircle,
  Mailbox,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"

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
    <TooltipProvider>
      <div className="relative z-10 max-w-3xl mx-auto w-full">
        <form
          onSubmit={handleSubmit}
          className="relative bg-slate-900 rounded-2xl border border-slate-800 shadow-lg overflow-hidden"
        >
          {/* Header - Mode chips and tools */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/90">
            <div className="flex items-center gap-1.5 w-full">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 gap-2 text-xs font-medium text-slate-300 hover:text-slate-100 bg-slate-800/50 hover:bg-slate-800 rounded-full border border-slate-700 px-2.5"
                  >
                    {effectiveModelMode === "auto" && <Zap className="w-3 h-3 text-yellow-400" />}
                    {effectiveModelMode === "fast" && <Zap className="w-3 h-3 text-yellow-400" />}
                    {effectiveModelMode === "thorough" && <Brain className="w-3 h-3 text-purple-400" />}
                    {effectiveModelMode === "auto" ? "Auto" : effectiveModelMode === "fast" ? "Fast" : "Thorough"}
                    <ChevronDown className="w-3 h-3 opacity-60" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="start" sideOffset={10} className="w-64 bg-slate-900 border-slate-800 p-2 text-slate-100">
                  <div className="space-y-1">
                    <button
                      type="button"
                      onClick={() => setModelMode("auto")}
                      disabled={mode === "quicknav"}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                        effectiveModelMode === "auto"
                          ? "bg-slate-800 text-slate-100"
                          : "text-slate-300 hover:bg-slate-800/50 hover:text-slate-100",
                        mode === "quicknav" && "opacity-50 cursor-not-allowed",
                      )}
                    >
                      <Zap className="w-4 h-4 text-yellow-400" />
                      <div className="flex-1">
                        <div className="text-sm font-medium">Auto</div>
                        <div className="text-xs text-slate-400">Best for task</div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setModelMode("fast")}
                      disabled={mode === "quicknav"}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                        modelMode === "fast" && mode !== "quicknav"
                          ? "bg-slate-800 text-slate-100"
                          : "text-slate-300 hover:bg-slate-800/50 hover:text-slate-100",
                        mode === "quicknav" && "opacity-50 cursor-not-allowed",
                      )}
                    >
                      <Zap className="w-4 h-4 text-yellow-400" />
                      <div className="flex-1">
                        <div className="text-sm font-medium">Fast</div>
                        <div className="text-xs text-slate-400">Gemini 1.5 Flash</div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setModelMode("thorough")}
                      disabled={mode === "quicknav"}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                        modelMode === "thorough" && mode !== "quicknav"
                          ? "bg-slate-800 text-slate-100"
                          : "text-slate-300 hover:bg-slate-800/50 hover:text-slate-100",
                        mode === "quicknav" && "opacity-50 cursor-not-allowed",
                      )}
                    >
                      <Brain className="w-4 h-4 text-violet-400" />
                      <div className="flex-1">
                        <div className="text-sm font-medium">Thorough</div>
                        <div className="text-xs text-slate-400">Claude 3.5 Sonnet</div>
                      </div>
                    </button>
                  </div>
                </PopoverContent>
              </Popover>
              <div className="h-4 w-px bg-slate-700 mx-1" />
              <Popover>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <PopoverTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-slate-400 hover:text-slate-200 rounded-lg"
                      >
                        <SlidersHorizontal className="w-3.5 h-3.5" />
                      </Button>
                    </PopoverTrigger>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">Capabilities</TooltipContent>
                </Tooltip>
                <PopoverContent align="start" side="top" sideOffset={10} className="w-72 bg-slate-900 border-slate-800 p-4 mb-2">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-100 mb-3">Capabilities</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="internet-search" className="text-sm text-slate-200">
                            Internet Search
                          </Label>
                          <Switch
                            id="internet-search"
                            checked={internetSearch}
                            onCheckedChange={setInternetSearch}
                            className="data-[state=checked]:bg-violet-600"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-slate-400 hover:text-slate-200 rounded-lg"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Download context</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-slate-400 hover:text-slate-200 rounded-lg"
                    title="Add current tab to context"
                  >
                    <AppWindow className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Add current tab</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-slate-400 hover:text-slate-200 rounded-lg"
                  >
                    <Share className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Share chat</TooltipContent>
              </Tooltip>
              <div className="flex-1" />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 bg-violet-600 hover:bg-violet-500 text-white rounded-lg ml-2"
              >
                <Plus className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          {/* Body - Text Area */}
          <div className="px-3 py-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your courses…"
              className="min-h-[44px] max-h-[180px] w-full resize-none bg-transparent border-none p-0 text-sm text-slate-100 placeholder:text-slate-500 focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
            />
          </div>

          {/* Footer - Mode chips, helper text, and submit */}
          <div className="px-3 pb-3 flex flex-wrap items-center justify-between gap-y-2 border-t border-slate-800 pt-2">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="xs"
                disabled={isQuickNavDisabled}
                onClick={() => handleModeToggle("quicknav")}
                className={cn(
                  "h-6 rounded-full border text-xs px-3 gap-1.5 font-medium transition-all",
                  mode === "quicknav"
                    ? "bg-violet-500/10 border-violet-400/30 text-violet-300"
                    : "bg-transparent hover:bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200",
                  isQuickNavDisabled && "opacity-40 cursor-not-allowed",
                )}
              >
                <Zap className="w-3 h-3" />
                Quick Nav
              </Button>
              <Button
                type="button"
                variant="outline"
                size="xs"
                onClick={() => handleModeToggle("tutor")}
                className={cn(
                  "h-6 rounded-full border text-xs px-3 gap-1.5 font-medium transition-all",
                  mode === "tutor"
                    ? "bg-violet-500/10 border-violet-400/30 text-violet-300"
                    : "bg-transparent hover:bg-slate-800/50 border-slate-700 text-slate-400 hover:text-slate-200",
                )}
              >
                <Brain className="w-3 h-3" />
                Tutor
              </Button>
            </div>

            <div className="flex items-center gap-2.5">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={!input.trim() && !isLoading}
                size="sm"
                className={cn(
                  "h-8 px-4 rounded-full transition-all duration-200 gap-2",
                  isLoading
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : input.trim()
                      ? "bg-violet-600 text-white hover:bg-violet-500"
                      : "bg-slate-800 text-slate-500 cursor-not-allowed opacity-50",
                )}
              >
                {isLoading ? (
                  <>
                    <Square className="w-3 h-3 fill-current" />
                    Stop
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </TooltipProvider>
  )
}

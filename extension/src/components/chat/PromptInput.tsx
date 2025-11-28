"use client"

import * as React from "react"
import { 
  SlidersHorizontal, 
  Plus, 
  AppWindow, 
  Calendar, 
  GraduationCap, 
  Code2, 
  Send, 
  Square, 
  Share,
  BookOpen,
  FileText,
  Terminal
} from "lucide-react"
import { Button } from "~/components/ui/button"
import { Textarea } from "~/components/ui/textarea"
import { cn } from "~/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover"
import { Switch } from "~/components/ui/switch"
import { Label } from "~/components/ui/label"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "~/components/ui/tooltip"

interface PromptInputProps {
  input: string
  setInput: (value: string) => void
  onSend: (content: string, attachments?: File[]) => void
  isLoading: boolean
}

// Intent hints that map to system capabilities
type IntentHint = "course-info" | "study-help" | "code-help" | null

export function PromptInput({ input, setInput, onSend, isLoading }: PromptInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  
  // Intent hint - optional guidance for the AI (system auto-detects if null)
  const [intentHint, setIntentHint] = React.useState<IntentHint>(null)
  
  // Options that actually affect behavior
  const [showSources, setShowSources] = React.useState(true)
  const [enableCodeExecution, setEnableCodeExecution] = React.useState(true)

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

  const handleIntentToggle = (hint: IntentHint) => {
    // Toggle off if same, otherwise set new hint
    setIntentHint(intentHint === hint ? null : hint)
  }

  // Dynamic placeholder based on selected intent
  const getPlaceholder = () => {
    switch (intentHint) {
      case "course-info":
        return "Ask about syllabus, deadlines, policies..."
      case "study-help":
        return "Ask to explain a concept or help you understand..."
      case "code-help":
        return "Ask for help with code or run an example..."
      default:
        return "Ask anything about your courses..."
    }
  }

  return (
    <div className="p-2 pb-2 relative z-10 max-w-3xl mx-auto w-full">
      <form
        onSubmit={handleSubmit}
        className="relative bg-slate-950/40 backdrop-blur-md rounded-xl border border-white/10 shadow-2xl overflow-hidden ring-1 ring-white/5 transition-all duration-300"
      >
        {/* Toolbar - Simplified */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
          <div className="flex items-center gap-1.5 w-full">
            {/* Options Popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-white rounded-lg hover:bg-white/10"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="start" side="top" sideOffset={10} className="w-72 bg-slate-950/95 backdrop-blur-xl border-white/10 p-4 mb-2 shadow-2xl">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-3">Response Options</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-blue-400" />
                          <Label htmlFor="show-sources" className="text-sm text-gray-200">
                            Show Sources
                          </Label>
                        </div>
                        <Switch
                          id="show-sources"
                          checked={showSources}
                          onCheckedChange={setShowSources}
                          className="data-[state=checked]:bg-blue-500"
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground pl-5">
                        Display course materials used in answers
                      </p>
                      
                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-2">
                          <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                          <Label htmlFor="code-exec" className="text-sm text-gray-200">
                            Run Code
                          </Label>
                        </div>
                        <Switch
                          id="code-exec"
                          checked={enableCodeExecution}
                          onCheckedChange={setEnableCodeExecution}
                          className="data-[state=checked]:bg-emerald-500"
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground pl-5">
                        Execute Python code in secure sandbox
                      </p>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <div className="h-4 w-[1px] bg-white/10 mx-1" />

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-white rounded-lg hover:bg-white/10"
                  >
                    <AppWindow className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Add current tab to context</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-white rounded-lg hover:bg-white/10"
                  >
                    <Share className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export Chat</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <div className="flex-1" />

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg"
                >
                  <Plus className="w-3.5 h-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>New Chat</TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Text Area */}
        <div className="px-3 py-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={getPlaceholder()}
            className="min-h-[40px] w-full resize-none bg-transparent border-none p-0 text-sm text-gray-200 placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
          />
        </div>

        {/* Bottom Row - Intent Hints (Optional) */}
        <div className="px-3 pb-3 flex items-center justify-between pt-2">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-muted-foreground mr-1 hidden sm:inline">Help me with:</span>
            
            {/* Course Info - Syllabus, deadlines, policies */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleIntentToggle("course-info")}
              className={cn(
                "h-6 rounded-full text-[10px] font-medium px-2 gap-1 transition-all duration-200",
                intentHint === "course-info"
                  ? "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/50"
                  : "bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10",
              )}
            >
              <Calendar className="w-3 h-3" />
              <span className="hidden sm:inline">Course Info</span>
            </Button>

            {/* Study Help - Explanations, concepts */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleIntentToggle("study-help")}
              className={cn(
                "h-6 rounded-full text-[10px] font-medium px-2 gap-1 transition-all duration-200",
                intentHint === "study-help"
                  ? "bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/50"
                  : "bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10",
              )}
            >
              <GraduationCap className="w-3 h-3" />
              <span className="hidden sm:inline">Study Help</span>
            </Button>

            {/* Code Help - Programming assistance */}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleIntentToggle("code-help")}
              className={cn(
                "h-6 rounded-full text-[10px] font-medium px-2 gap-1 transition-all duration-200",
                intentHint === "code-help"
                  ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/50"
                  : "bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10",
              )}
            >
              <Code2 className="w-3 h-3" />
              <span className="hidden sm:inline">Code</span>
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={!input.trim() && !isLoading}
              size="icon"
              className={cn(
                "h-8 w-8 rounded-lg transition-all duration-200 shadow-lg",
                isLoading
                  ? "bg-red-500/80 hover:bg-red-500 text-white ring-1 ring-red-400/50"
                  : input.trim()
                    ? "bg-violet-600 hover:bg-violet-500 text-white ring-1 ring-violet-400/50"
                    : "bg-white/5 text-slate-500 hover:bg-white/10",
              )}
            >
              {isLoading ? <Square className="w-3 h-3 fill-current" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}



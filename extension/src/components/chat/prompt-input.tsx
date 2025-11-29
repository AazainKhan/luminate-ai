"use client"

import * as React from "react"
import {
  SlidersHorizontal,
  Plus,
  AppWindow,
  Send,
  Square,
  Share,
  FileText,
  Terminal,
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
  toggleHistory?: () => void
  onExport?: () => void
  hasMessages?: boolean
}

export function PromptInput({ input, setInput, onSend, isLoading, onExport, hasMessages }: PromptInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  
  // Options that actually affect behavior
  const [showSources, setShowSources] = React.useState(true)
  const [enableCodeExecution, setEnableCodeExecution] = React.useState(true)

  React.useEffect(() => {
    if (textareaRef.current) {
      // Reset height - important to shrink when deleting text
      textareaRef.current.style.height = "44px"
      // Set to scrollHeight but cap at max height
      const scrollHeight = textareaRef.current.scrollHeight
      if (input) {
        textareaRef.current.style.height = `${scrollHeight}px`
      }
    }
  }, [input])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (input.trim() && !isLoading) {
      onSend(input)
      setInput("")
    }
  }

  // Dynamic placeholder
  const getPlaceholder = () => {
    return "Ask anything about COMP 237..."
  }

  return (
    <TooltipProvider>
      <div className="relative z-10 max-w-3xl mx-auto w-full">
        <form
          onSubmit={handleSubmit}
          className="relative bg-card rounded-2xl border-0 shadow-lg overflow-hidden"
        >
          {/* Header - Simplified toolbar */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-border/50 bg-card/90">
            <div className="flex items-center gap-1.5 w-full">
              {/* Options Popover */}
              <Popover>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <PopoverTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg"
                      >
                        <SlidersHorizontal className="w-3.5 h-3.5" />
                      </Button>
                    </PopoverTrigger>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">Options</TooltipContent>
                </Tooltip>
                <PopoverContent align="start" side="top" sideOffset={10} className="w-72 bg-popover border-border p-4 mb-2">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-popover-foreground mb-3">Response Options</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="w-3.5 h-3.5 text-blue-400" />
                            <Label htmlFor="show-sources" className="text-sm text-popover-foreground">
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
                            <Label htmlFor="code-exec" className="text-sm text-popover-foreground">
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

              <div className="h-4 w-px bg-border mx-1" />

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg"
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
                    onClick={onExport}
                    disabled={!hasMessages}
                    className={cn(
                      "h-7 w-7 rounded-lg",
                      hasMessages 
                        ? "text-muted-foreground hover:text-foreground hover:bg-muted" 
                        : "text-muted-foreground/50 cursor-not-allowed"
                    )}
                  >
                    <Share className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Export chat as Markdown</TooltipContent>
              </Tooltip>

              <div className="flex-1" />

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">New chat</TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* Body - Text Area */}
          <div className="px-3 py-2 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={getPlaceholder()}
              className="min-h-[44px] max-h-[180px] w-full resize-none bg-transparent border-none p-0 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed pr-24"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
            />
            
            {/* Floating Send Button & Tags */}
            <div className="absolute bottom-2 right-2 flex items-center gap-2">
               {/* Auto-detect tags - faded until active or hover? For now just small text */}
               <div className="hidden sm:flex items-center gap-1.5 pointer-events-none opacity-50">
                  <span className="text-[10px] text-muted-foreground">
                    auto-detects
                  </span>
               </div>

              <Button
                type="button"
                onClick={handleSubmit}
                disabled={!input.trim() && !isLoading}
                size="sm"
                className={cn(
                  "h-8 w-8 p-0 rounded-full transition-all duration-200",
                  isLoading
                    ? "bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                    : input.trim()
                      ? "bg-primary text-primary-foreground hover:bg-primary/90"
                      : "bg-muted text-muted-foreground cursor-not-allowed opacity-50",
                )}
              >
                {isLoading ? (
                    <Square className="w-3 h-3 fill-current" />
                ) : (
                    <Send className="w-3.5 h-3.5 ml-0.5" />
                )}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </TooltipProvider>
  )
}

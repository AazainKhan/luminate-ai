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
  Paperclip,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { ModelSelector } from "./model-selector"

// ============================================================================
// Context
// ============================================================================

interface PromptInputContextValue {
  input: string
  setInput: (value: string) => void
  isLoading: boolean
  status: "ready" | "streaming" | "error" | "submitted"
  attachments: File[]
  addAttachment: (file: File) => void
  removeAttachment: (index: number) => void
}

const PromptInputContext = React.createContext<PromptInputContextValue>({
  input: "",
  setInput: () => {},
  isLoading: false,
  status: "ready",
  attachments: [],
  addAttachment: () => {},
  removeAttachment: () => {},
})

const usePromptInput = () => React.useContext(PromptInputContext)

// ============================================================================
// PromptInput (Root) - Composable Version
// ============================================================================

interface PromptInputRootProps extends React.FormHTMLAttributes<HTMLFormElement> {
  /** Accepted file types for attachments */
  accept?: string
  /** Allow multiple file attachments */
  multiple?: boolean
  /** Maximum number of files */
  maxFiles?: number
  /** Maximum file size in bytes */
  maxFileSize?: number
  /** Error handler */
  onError?: (error: Error) => void
  /** Submit handler */
  onSubmit?: (message: { text: string; files?: File[] }) => void | Promise<void>
  /** Current status */
  status?: "ready" | "streaming" | "error" | "submitted"
}

const PromptInputRoot = React.forwardRef<HTMLFormElement, PromptInputRootProps>(
  ({ 
    accept,
    multiple = true,
    maxFiles = 5,
    maxFileSize = 10 * 1024 * 1024,
    onError,
    onSubmit,
    status = "ready",
    className, 
    children, 
    ...props 
  }, ref) => {
    const [input, setInput] = React.useState("")
    const [attachments, setAttachments] = React.useState<File[]>([])
    const isLoading = status === "streaming" || status === "submitted"

    const addAttachment = React.useCallback((file: File) => {
      if (attachments.length >= maxFiles) {
        onError?.(new Error(`Maximum ${maxFiles} files allowed`))
        return
      }
      if (file.size > maxFileSize) {
        onError?.(new Error(`File size exceeds ${maxFileSize / 1024 / 1024}MB limit`))
        return
      }
      setAttachments(prev => [...prev, file])
    }, [attachments.length, maxFiles, maxFileSize, onError])

    const removeAttachment = React.useCallback((index: number) => {
      setAttachments(prev => prev.filter((_, i) => i !== index))
    }, [])

    const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
      e.preventDefault()
      if (!input.trim() && attachments.length === 0) return
      
      await onSubmit?.({ text: input, files: attachments.length > 0 ? attachments : undefined })
      setInput("")
      setAttachments([])
    }, [input, attachments, onSubmit])

    const contextValue = React.useMemo(() => ({
      input,
      setInput,
      isLoading,
      status,
      attachments,
      addAttachment,
      removeAttachment,
    }), [input, isLoading, status, attachments, addAttachment, removeAttachment])

    return (
      <PromptInputContext.Provider value={contextValue}>
        <form
          ref={ref}
          onSubmit={handleSubmit}
          className={cn(
            "relative bg-card rounded-2xl border-0 shadow-lg overflow-hidden",
            className
          )}
          {...props}
        >
          {children}
        </form>
      </PromptInputContext.Provider>
    )
  }
)
PromptInputRoot.displayName = "PromptInputRoot"

// ============================================================================
// PromptInputTextarea
// ============================================================================

interface PromptInputTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const PromptInputTextarea = React.forwardRef<HTMLTextAreaElement, PromptInputTextareaProps>(
  ({ className, placeholder = "Ask me anything...", ...props }, ref) => {
    const { input, setInput, isLoading } = usePromptInput()
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)
    const combinedRef = ref || textareaRef

    React.useEffect(() => {
      const textarea = typeof combinedRef === 'function' ? null : combinedRef.current
      if (textarea) {
        textarea.style.height = "44px"
        if (input) {
          textarea.style.height = `${textarea.scrollHeight}px`
        }
      }
    }, [input, combinedRef])

    return (
      <Textarea
        ref={combinedRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={placeholder}
        disabled={isLoading}
        data-testid="prompt-input"
        className={cn(
          "min-h-[44px] max-h-[180px] w-full resize-none bg-transparent border-none p-0",
          "text-sm text-foreground placeholder:text-muted-foreground",
          "focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed",
          className
        )}
        rows={1}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            e.currentTarget.form?.requestSubmit()
          }
        }}
        {...props}
      />
    )
  }
)
PromptInputTextarea.displayName = "PromptInputTextarea"

// ============================================================================
// PromptInputToolbar
// ============================================================================

interface PromptInputToolbarProps extends React.HTMLAttributes<HTMLDivElement> {}

const PromptInputToolbar = React.forwardRef<HTMLDivElement, PromptInputToolbarProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-center justify-between px-3 py-2 border-b border-border/50 bg-card/90",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
PromptInputToolbar.displayName = "PromptInputToolbar"

// ============================================================================
// PromptInputTools
// ============================================================================

interface PromptInputToolsProps extends React.HTMLAttributes<HTMLDivElement> {}

const PromptInputTools = React.forwardRef<HTMLDivElement, PromptInputToolsProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center gap-1.5", className)}
      {...props}
    >
      {children}
    </div>
  )
)
PromptInputTools.displayName = "PromptInputTools"

// ============================================================================
// PromptInputBody
// ============================================================================

interface PromptInputBodyProps extends React.HTMLAttributes<HTMLDivElement> {}

const PromptInputBody = React.forwardRef<HTMLDivElement, PromptInputBodyProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("px-3 py-2 relative", className)}
      {...props}
    >
      {children}
    </div>
  )
)
PromptInputBody.displayName = "PromptInputBody"

// ============================================================================
// PromptInputFooter
// ============================================================================

interface PromptInputFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

const PromptInputFooter = React.forwardRef<HTMLDivElement, PromptInputFooterProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("absolute bottom-2 right-2 flex items-center gap-2", className)}
      {...props}
    >
      {children}
    </div>
  )
)
PromptInputFooter.displayName = "PromptInputFooter"

// ============================================================================
// PromptInputButton
// ============================================================================

interface PromptInputButtonProps extends React.ComponentPropsWithoutRef<typeof Button> {
  /** Tooltip text */
  tooltip?: string
}

const PromptInputButton = React.forwardRef<HTMLButtonElement, PromptInputButtonProps>(
  ({ tooltip, className, children, ...props }, ref) => {
    const button = (
      <Button
        ref={ref}
        type="button"
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg", className)}
        {...props}
      >
        {children}
      </Button>
    )

    if (tooltip) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>{button}</TooltipTrigger>
          <TooltipContent side="bottom">{tooltip}</TooltipContent>
        </Tooltip>
      )
    }

    return button
  }
)
PromptInputButton.displayName = "PromptInputButton"

// ============================================================================
// PromptInputSubmit
// ============================================================================

interface PromptInputSubmitProps extends Omit<React.ComponentPropsWithoutRef<typeof Button>, "type"> {
  /** Override status */
  status?: "ready" | "streaming" | "error" | "submitted"
}

const PromptInputSubmit = React.forwardRef<HTMLButtonElement, PromptInputSubmitProps>(
  ({ status: statusProp, className, ...props }, ref) => {
    const { input, isLoading, status: contextStatus } = usePromptInput()
    const status = statusProp ?? contextStatus
    const isStreaming = status === "streaming"
    const hasContent = input.trim().length > 0

    return (
      <Button
        ref={ref}
        type={isStreaming ? "button" : "submit"}
        disabled={!hasContent && !isStreaming}
        size="sm"
        data-testid="send-button"
        className={cn(
          "h-8 w-8 p-0 rounded-full transition-all duration-200",
          isStreaming
            ? "bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            : hasContent
              ? "bg-primary text-primary-foreground hover:bg-primary/90"
              : "bg-muted text-muted-foreground cursor-not-allowed opacity-50",
          className
        )}
        {...props}
      >
        {isStreaming ? (
          <Square className="w-3 h-3 fill-current" />
        ) : (
          <Send className="w-3.5 h-3.5 ml-0.5" />
        )}
      </Button>
    )
  }
)
PromptInputSubmit.displayName = "PromptInputSubmit"

// ============================================================================
// PromptInputAttachments
// ============================================================================

interface PromptInputAttachmentsProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: (attachment: File, index: number) => React.ReactNode
}

const PromptInputAttachments = React.forwardRef<HTMLDivElement, PromptInputAttachmentsProps>(
  ({ children, className, ...props }, ref) => {
    const { attachments, removeAttachment } = usePromptInput()

    if (attachments.length === 0) return null

    return (
      <div
        ref={ref}
        className={cn("flex flex-wrap gap-2 px-3 py-2 border-b border-border/50", className)}
        {...props}
      >
        {attachments.map((file, index) => (
          children ? children(file, index) : (
            <div
              key={index}
              className="flex items-center gap-2 px-2 py-1 bg-muted rounded-lg text-sm"
            >
              <Paperclip className="w-3 h-3 text-muted-foreground" />
              <span className="truncate max-w-[150px]">{file.name}</span>
              <button
                type="button"
                onClick={() => removeAttachment(index)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )
        ))}
      </div>
    )
  }
)
PromptInputAttachments.displayName = "PromptInputAttachments"

// ============================================================================
// Legacy PromptInput (for backwards compatibility)
// ============================================================================

interface LegacyPromptInputProps {
  input: string
  setInput: (value: string) => void
  onSend: (content: string, attachments?: File[]) => void
  isLoading: boolean
  toggleHistory?: () => void
  onExport?: () => void
  onStop?: () => void
  hasMessages?: boolean
  model?: string
  onModelChange?: (model: string) => void
}

function PromptInput({ input, setInput, onSend, isLoading, onExport, onStop, hasMessages, model, onModelChange }: LegacyPromptInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  // Options that actually affect behavior
  const [showSources, setShowSources] = React.useState(true)
  const [enableCodeExecution, setEnableCodeExecution] = React.useState(true)

  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "44px"
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
              {/* Model Selector - Leftmost */}
              <ModelSelector 
                value={model}
                onValueChange={onModelChange}
                size="sm"
                className="h-7"
              />

              <div className="h-4 w-px bg-border mx-1" />

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
              data-testid="prompt-input"
              className="min-h-[44px] max-h-[180px] w-full resize-none bg-transparent border-none p-0 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:ring-offset-0 leading-relaxed pr-24"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
            />

            {/* Floating Send Button */}
            <div className="absolute bottom-2 right-2 flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-1.5 pointer-events-none opacity-50">
                <span className="text-[10px] text-muted-foreground">
                  auto-detects
                </span>
              </div>

              <Button
                type="button"
                onClick={isLoading ? onStop : handleSubmit}
                disabled={!input.trim() && !isLoading}
                size="sm"
                data-testid="send-button"
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

// ============================================================================
// Exports
// ============================================================================

export {
  // Composable components
  PromptInputRoot,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
  PromptInputBody,
  PromptInputFooter,
  PromptInputButton,
  PromptInputSubmit,
  PromptInputAttachments,
  PromptInputContext,
  usePromptInput,
  // Legacy
  PromptInput,
  // Re-export for convenience
  PromptInputRoot as Input,
}

export type {
  PromptInputRootProps,
  PromptInputTextareaProps,
  PromptInputButtonProps,
  PromptInputSubmitProps,
  LegacyPromptInputProps as PromptInputProps,
}

import * as React from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface PromptInputProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "onSubmit"> {
  onSubmit?: (value: string) => void | Promise<void>
  isLoading?: boolean
  submitLabel?: string
}

const PromptInput = React.forwardRef<HTMLTextAreaElement, PromptInputProps>(
  (
    {
      className,
      onSubmit,
      isLoading = false,
      submitLabel = "Send",
      value: controlledValue,
      onChange,
      ...props
    },
    ref
  ) => {
    const [value, setValue] = React.useState("")
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)
    const isControlled = controlledValue !== undefined

    const currentValue = isControlled ? controlledValue : value

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (!isControlled) {
        setValue(e.target.value)
      }
      onChange?.(e)

      // Auto-resize
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
      }
    }

    const handleSubmit = async () => {
      const valueToSubmit = String(currentValue).trim()
      if (!valueToSubmit || isLoading) return

      await onSubmit?.(valueToSubmit)

      if (!isControlled) {
        setValue("")
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto"
        }
      }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    }

    return (
      <div className="relative flex items-end gap-2 w-full">
        <textarea
          ref={(node) => {
            // Handle both refs
            if (typeof ref === "function") {
              ref(node)
            } else if (ref) {
              ref.current = node
            }
            // @ts-ignore
            textareaRef.current = node
          }}
          value={currentValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          className={cn(
            "flex min-h-[60px] max-h-[200px] w-full resize-none rounded-2xl",
            "border border-input bg-background px-4 py-3 pr-12",
            "text-sm placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "transition-all duration-200",
            className
          )}
          disabled={isLoading}
          {...props}
        />
        <Button
          type="button"
          size="icon"
          onClick={handleSubmit}
          disabled={!String(currentValue).trim() || isLoading}
          className={cn(
            "absolute right-2 bottom-2 h-8 w-8 rounded-lg shrink-0",
            "transition-all duration-200",
            String(currentValue).trim() && !isLoading
              ? "bg-primary text-primary-foreground hover:bg-primary/90" 
              : "bg-muted text-muted-foreground"
          )}
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">{submitLabel}</span>
        </Button>
      </div>
    )
  }
)
PromptInput.displayName = "PromptInput"

export { PromptInput }

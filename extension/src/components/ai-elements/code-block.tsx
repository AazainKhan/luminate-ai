"use client"

import type React from "react"

import { useState } from "react"
import { Check, Copy, Play, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface CodeBlockProps {
  code: string
  language: string
  showLineNumbers?: boolean
  children?: React.ReactNode
  className?: string
  filename?: string
}

export function CodeBlock({ code, language, showLineNumbers = false, children, className, filename }: CodeBlockProps) {
  const lines = code.split("\n")

  return (
    <div className={cn("relative rounded-lg overflow-hidden border border-border", className)}>
      <div className="flex items-center justify-between px-4 py-2 bg-muted/80 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono">{language}</span>
          {filename && (
            <span className="text-xs text-muted-foreground/60 font-mono">
              {filename}
            </span>
          )}
        </div>
        <div className="z-10 flex items-center gap-1">{children}</div>
      </div>
      <div className="bg-muted/50 overflow-x-auto">
        {showLineNumbers ? (
          <div className="p-4 m-0 text-sm font-mono leading-relaxed min-w-full w-max">
            <table className="border-collapse">
              <tbody>
                {lines.map((line, i) => (
                  <tr key={i}>
                    <td className="pr-4 text-right text-muted-foreground select-none w-8 align-top">{i + 1}</td>
                    <td className="text-foreground whitespace-pre">{line || "\n"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <pre className="p-4 m-0 text-sm font-mono leading-relaxed">
            <code className="text-foreground">{code}</code>
          </pre>
        )}
      </div>
    </div>
  )
}

interface CodeBlockCopyButtonProps {
  code: string
  onCopy?: () => void
  onError?: (error: Error) => void
  timeout?: number
}

export function CodeBlockCopyButton({ code, onCopy, onError, timeout = 2000 }: CodeBlockCopyButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      onCopy?.()
      setTimeout(() => setCopied(false), timeout)
    } catch (error) {
      onError?.(error as Error)
    }
  }

  return (
    <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hover:bg-muted" onClick={handleCopy}>
      {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
    </Button>
  )
}

interface CodeBlockRunButtonProps {
  code: string
  language: string
  onRun?: (code: string, language: string) => Promise<string>
  onResult?: (result: string) => void
  onError?: (error: Error) => void
}

export function CodeBlockRunButton({ code, language, onRun, onResult, onError }: CodeBlockRunButtonProps) {
  const [isRunning, setIsRunning] = useState(false)

  const handleRun = async () => {
    if (!onRun) return
    
    setIsRunning(true)
    try {
      const result = await onRun(code, language)
      onResult?.(result)
    } catch (error) {
      onError?.(error as Error)
    } finally {
      setIsRunning(false)
    }
  }

  // Only show run button for executable languages
  const executableLanguages = ["python", "javascript", "typescript", "js", "ts", "py"]
  if (!executableLanguages.includes(language.toLowerCase())) {
    return null
  }

  return (
    <Button 
      size="sm" 
      variant="ghost" 
      className="h-8 w-8 p-0 hover:bg-muted" 
      onClick={handleRun}
      disabled={isRunning || !onRun}
    >
      {isRunning ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Play className="h-4 w-4" />
      )}
    </Button>
  )
}










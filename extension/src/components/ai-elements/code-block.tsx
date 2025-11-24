"use client"

import type React from "react"

import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"

interface CodeBlockProps {
  code: string
  language: string
  showLineNumbers?: boolean
  children?: React.ReactNode
  className?: string
}

export function CodeBlock({ code, language, showLineNumbers = false, children, className }: CodeBlockProps) {
  const lines = code.split("\n")

  return (
    <div className={`relative rounded-lg overflow-hidden border border-white/10 ${className || ""}`}>
      <div className="flex items-center justify-between px-4 py-2 bg-[#0d0e15] border-b border-white/10">
        <span className="text-xs text-muted-foreground font-mono">{language}</span>
        <div className="z-10">{children}</div>
      </div>
      <div className="bg-[#0d0e15] overflow-x-auto">
        <pre className="p-4 m-0 text-sm font-mono leading-relaxed">
          <code className="text-gray-300">
            {showLineNumbers ? (
              <table className="w-full border-collapse">
                <tbody>
                  {lines.map((line, i) => (
                    <tr key={i}>
                      <td className="pr-4 text-right text-muted-foreground select-none w-8">{i + 1}</td>
                      <td className="text-gray-300">{line || "\n"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              code
            )}
          </code>
        </pre>
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
    <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hover:bg-white/10" onClick={handleCopy}>
      {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
    </Button>
  )
}

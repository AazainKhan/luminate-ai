"use client"
import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"
import { CodeBlock, CodeBlockCopyButton } from "@/components/ai-elements/code-block"

interface ResponseProps {
  children: string
  className?: string
}

export function Response({ children, className }: ResponseProps) {
  return (
    <div className={cn("prose prose-invert max-w-none text-sm leading-7 text-slate-100", className)}>
      <ReactMarkdown
        components={{
          code: ({ node, inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || "")
            const language = match ? match[1] : "text"
            const code = String(children).replace(/\n$/, "")

            if (!inline) {
              return (
                <CodeBlock code={code} language={language} showLineNumbers>
                  <CodeBlockCopyButton code={code} />
                </CodeBlock>
              )
            }

            return (
              <code className="px-1.5 py-0.5 rounded-md bg-slate-800/60 font-mono text-sm text-violet-300 ring-1 ring-slate-700/50" {...props}>
                {children}
              </code>
            )
          },
          a: ({ node, ...props }) => (
            <a {...props} className="text-violet-400 hover:text-violet-300 hover:underline transition-colors" target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

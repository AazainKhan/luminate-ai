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
    <div className={cn("prose prose-invert max-w-none text-sm leading-relaxed text-gray-300", className)}>
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
              <code className="px-1 py-0.5 rounded bg-white/10 font-mono text-xs text-pink-300" {...props}>
                {children}
              </code>
            )
          },
          a: ({ node, ...props }) => (
            <a {...props} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

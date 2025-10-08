"use client"

import * as React from "react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { CodeBlock } from '@/components/ui/code-block'
import { cn } from "@/lib/utils"
import 'katex/dist/katex.min.css'

export interface ResponseProps extends React.HTMLAttributes<HTMLDivElement> {
  content: string
  isStreaming?: boolean
}

const Response = React.forwardRef<HTMLDivElement, ResponseProps>(
  ({ className, content, isStreaming, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "prose prose-stone dark:prose-invert max-w-none",
          "prose-p:leading-7 prose-p:my-2",
          "prose-pre:bg-muted prose-pre:border prose-pre:border-border",
          "prose-code:text-sm prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded",
          "prose-strong:font-semibold prose-strong:text-foreground",
          "prose-a:text-primary prose-a:no-underline hover:prose-a:underline",
          "prose-headings:font-semibold prose-headings:tracking-tight",
          "prose-ul:my-2 prose-ol:my-2 prose-li:my-1",
          "text-foreground break-words",
          isStreaming && "animate-pulse",
          className
        )}
        {...props}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            code({ className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '')
              const isInline = !match
              
              return !isInline && match ? (
                <CodeBlock
                  language={match[1]}
                  code={String(children).replace(/\n$/, '')}
                />
              ) : (
                <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              )
            },
            p: ({ children }) => <p className="mb-4 leading-7">{children}</p>,
            h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6">{children}</h1>,
            h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 mt-5">{children}</h2>,
            h3: ({ children }) => <h3 className="text-lg font-semibold mb-2 mt-4">{children}</h3>,
            ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-primary pl-4 italic my-4">{children}</blockquote>
            ),
            a: ({ children, href }) => (
              <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    )
  }
)
Response.displayName = "Response"

export { Response }

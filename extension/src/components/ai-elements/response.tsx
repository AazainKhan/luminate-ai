"use client"
import React, { Component } from "react"
import type { ErrorInfo, ReactNode } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { cn } from "@/lib/utils"
import { CodeBlock, CodeBlockCopyButton } from "@/components/ai-elements/code-block"

interface ResponseProps {
  children: string
  className?: string
}

/**
 * Strip problematic content from LLM responses.
 * Removes internal reasoning blocks, malformed HTML-like tags, and JSON analysis blocks.
 * Also fixes incomplete markdown that can crash the parser.
 */
function sanitizeContent(text: string): string {
  if (!text) return ''
  
  let cleaned = text
  
  // Remove <thinking>...</thinking> blocks including content
  cleaned = cleaned.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
  
  // Remove any standalone <thinking> or </thinking> tags
  cleaned = cleaned.replace(/<\/?thinking>/gi, '')
  
  // Remove reasoning JSON blocks that leaked from the reasoning node
  // Pattern: ```json\n{"perception": ... }``` or raw {"perception": ...}
  cleaned = cleaned.replace(/```json\s*\{[\s\S]*?"perception"[\s\S]*?"decision"[\s\S]*?\}\s*```/gi, '')
  cleaned = cleaned.replace(/\{[\s\S]*?"perception"[\s\S]*?"analysis"[\s\S]*?"planning"[\s\S]*?"decision"[\s\S]*?\}/gi, '')
  
  // Remove other potentially problematic XML-like tags that aren't standard Markdown
  // but preserve valid HTML tags like <br>, <hr>, etc.
  cleaned = cleaned.replace(/<\/?(?:quiz|example|step|hint|activation|exploration|guidance|challenge)[^>]*>/gi, '')
  
  // Remove any unclosed or malformed angle bracket sequences that could break the parser
  // This handles cases like "< thinking" or "< /thinking" with spaces
  cleaned = cleaned.replace(/<\s*\/?\s*thinking\s*>/gi, '')
  
  // Fix incomplete markdown that can crash the parser:
  
  // 1. Close any unclosed code blocks (odd number of ```)
  const codeBlockMatches = cleaned.match(/```/g)
  if (codeBlockMatches && codeBlockMatches.length % 2 !== 0) {
    cleaned = cleaned + '\n```'
  }
  
  // 2. Close any unclosed inline code (odd number of single backticks not in code blocks)
  // This is tricky - we'll just escape trailing backticks that seem unclosed
  const lines = cleaned.split('\n')
  cleaned = lines.map(line => {
    // Skip code block markers
    if (line.trim().startsWith('```')) return line
    // Count backticks in line
    const backticks = (line.match(/`/g) || []).length
    if (backticks % 2 !== 0) {
      // Odd number - add closing backtick
      return line + '`'
    }
    return line
  }).join('\n')
  
  // 3. Fix incomplete bold/italic markers at end of text
  // Remove trailing ** or * that aren't closed
  cleaned = cleaned.replace(/\*{1,2}$/, '')
  cleaned = cleaned.replace(/_{1,2}$/, '')
  
  // 4. Fix incomplete links at end of text  
  // Remove incomplete link syntax like [text or [text](url
  cleaned = cleaned.replace(/\[[^\]]*$/, '')
  cleaned = cleaned.replace(/\]\([^)]*$/, '')
  
  // 5. Fix incomplete list items that are just numbers or bullets
  cleaned = cleaned.replace(/\n\d+\.\s*$/, '\n')
  cleaned = cleaned.replace(/\n[-*+]\s*$/, '\n')
  
  return cleaned.trim()
}

/**
 * Error boundary to catch ReactMarkdown parsing errors
 */
interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

class MarkdownErrorBoundary extends Component<{ children: ReactNode; fallback: string }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode; fallback: string }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('Markdown parsing error:', error.message)
  }
  
  componentDidUpdate(prevProps: { children: ReactNode; fallback: string }) {
    // Reset error state when content changes (streaming updates)
    if (prevProps.fallback !== this.props.fallback && this.state.hasError) {
      this.setState({ hasError: false, error: undefined })
    }
  }

  render() {
    if (this.state.hasError) {
      // Fallback: render as plain text with basic formatting
      return (
        <div className="prose dark:prose-invert max-w-none text-sm leading-7 text-foreground break-words w-full whitespace-pre-wrap">
          {this.props.fallback}
        </div>
      )
    }
    return this.props.children
  }
}

export function Response({ children, className }: ResponseProps) {
  // Clean the content before rendering
  const cleanedContent = sanitizeContent(children || '')
  
  // Don't render if empty after cleaning
  if (!cleanedContent) {
    return null
  }
  
  return (
    <div className={cn("prose dark:prose-invert max-w-none text-sm leading-7 text-foreground break-words w-full", className)}>
      <MarkdownErrorBoundary fallback={cleanedContent}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Handle code blocks at the pre level to avoid div-in-p nesting issues
            // ReactMarkdown renders fenced code as <pre><code>...</code></pre>
            // By handling pre, we can return our CodeBlock (which contains divs) directly
            pre: ({ node, children, ...props }: any) => {
              // Extract the code element from children
              const codeChild = React.Children.toArray(children).find(
                (child): child is React.ReactElement => 
                  React.isValidElement(child) && child.type === 'code'
              )
              
              if (codeChild) {
                const codeClassName = codeChild.props.className || ""
                const match = /language-(\w+)/.exec(codeClassName)
                const language = match ? match[1] : "text"
                const code = String(codeChild.props.children || "").replace(/\n$/, "")
                
                if (code) {
                  return (
                    <CodeBlock code={code} language={language} showLineNumbers>
                      <CodeBlockCopyButton code={code} />
                    </CodeBlock>
                  )
                }
              }
              
              // Fallback for non-code pre elements
              return <pre {...props}>{children}</pre>
            },
            // Handle inline code only (not fenced code blocks)
            code: ({ node, inline, className: codeClassName, children, ...props }: any) => {
              // If this is a fenced code block (inside pre), it's handled by pre component
              // This handler is only for inline code like `code`
              if (inline) {
                return (
                  <code className="px-1.5 py-0.5 rounded-md bg-slate-800/60 font-mono text-sm text-violet-300 ring-1 ring-slate-700/50" {...props}>
                    {children}
                  </code>
                )
              }
              
              // For any other non-inline code not wrapped in pre (shouldn't happen normally)
              return (
                <code className="px-1.5 py-0.5 rounded-md bg-slate-800/60 font-mono text-sm text-violet-300 ring-1 ring-slate-700/50" {...props}>
                  {children}
                </code>
              )
            },
            a: ({ node, ...props }) => (
              <a {...props} className="text-violet-400 hover:text-violet-300 hover:underline transition-colors" target="_blank" rel="noopener noreferrer" />
            ),
            // Use div for paragraphs when they contain block elements (like code blocks)
            // This prevents the div-in-p nesting issue
            p: ({ node, children, ...props }) => {
              // Check if children contain any block-level elements
              const hasBlockChild = React.Children.toArray(children).some(
                (child) => React.isValidElement(child) && 
                  (child.type === CodeBlock || child.type === 'div' || child.type === 'pre')
              )
              
              if (hasBlockChild) {
                return <div className="mb-4" {...props}>{children}</div>
              }
              
              return <p {...props}>{children}</p>
            },
          }}
        >
          {cleanedContent}
        </ReactMarkdown>
      </MarkdownErrorBoundary>
    </div>
  )
}










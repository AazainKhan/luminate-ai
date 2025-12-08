"use client"
import React, { Component, useMemo } from "react"
import type { ErrorInfo, ReactNode } from "react"
import { marked } from "marked"
import katex from "katex"
import "katex/dist/katex.min.css"
import { cn } from "@/lib/utils"
import { CodeBlock, CodeBlockCopyButton } from "@/components/ai-elements/code-block"
import { QuestionCard, HintCard, OrientationCard, ExampleCard } from "@/components/ai-elements/scaffolding-card"

interface ResponseProps {
  children: string
  className?: string
}

/**
 * Pre-render LaTeX math with KaTeX before passing to ReactMarkdown.
 * We then allow raw HTML with rehypeRaw so KaTeX output renders correctly.
 */
function renderMathWithKatex(text: string): string {
  if (!text) return ""

  // Protect code blocks from math processing
  const codeBlocks: string[] = []
  let processed = text.replace(/```[\s\S]*?```/g, (match) => {
    codeBlocks.push(match)
    return `__CODEBLOCK_${codeBlocks.length - 1}__`
  })

  // Protect inline code from math processing
  const inlineCodes: string[] = []
  processed = processed.replace(/`[^`]+`/g, (match) => {
    inlineCodes.push(match)
    return `__INLINECODE_${inlineCodes.length - 1}__`
  })

  // Block math $$...$$
  processed = processed.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
    try {
      const html = katex.renderToString(math.trim(), {
        throwOnError: false,
        strict: false,
        displayMode: true,
        trust: true,
        output: "html"
      })
      return `<div class="katex-display my-4">${html}</div>`
    } catch (e) {
      console.warn("KaTeX block error:", e)
      return `$$${math}$$`
    }
  })

  // Inline math $...$ (avoid currency by requiring non-space content)
  processed = processed.replace(/\$([^\s$][^$]*?[^\s$])\$/g, (_, math) => {
    try {
      const html = katex.renderToString(math.trim(), {
        throwOnError: false,
        strict: false,
        displayMode: false,
        trust: true,
        output: "html"
      })
      return `<span class="katex-inline">${html}</span>`
    } catch (e) {
      console.warn("KaTeX inline error:", e)
      return `$${math}$`
    }
  })

  // Single-character math like $x$
  processed = processed.replace(/\$([^\s$])\$/g, (_, math) => {
    try {
      const html = katex.renderToString(math.trim(), {
        throwOnError: false,
        strict: false,
        displayMode: false,
        trust: true,
        output: "html"
      })
      return `<span class="katex-inline">${html}</span>`
    } catch (e) {
      console.warn("KaTeX single char error:", e)
      return `$${math}$`
    }
  })

  // Restore inline code
  processed = processed.replace(/__INLINECODE_(\d+)__/g, (_, index) => inlineCodes[parseInt(index)])

  // Restore code blocks
  processed = processed.replace(/__CODEBLOCK_(\d+)__/g, (_, index) => codeBlocks[parseInt(index)])

  return processed
}

/**
 * Loosely format common scaffolding markers so the UI doesn't render as a single wall of text.
 */
function addScaffoldingSpacing(text: string): string {
  return text
    .replace(/\s*\*\*Orientation:\*\*/gi, "\n\n**Orientation:**")
    .replace(/\s*\*\*Brief Orientation:\*\*/gi, "\n\n**Brief Orientation:**")
    .replace(/\s*\*\*Brief Explanation:\*\*/gi, "\n\n**Brief Explanation:**")
    .replace(/\s*\*\*Example:\*\*/gi, "\n\n**Example:**")
    .replace(/\s*\*\*Worked Example:\*\*/gi, "\n\n**Worked Example:**")
    .replace(/\s*\*\*Question:\*\*/gi, "\n\n**Question:**")
    .replace(/\s*\*\*Hints?:\*\*/gi, "\n\n**Hint:**")
    .replace(/\s*\*\*Self-Check:\*\*/gi, "\n\n**Self-Check:**")
    .replace(/\s*\*\*Step \d+:\*\*/gi, (match) => `\n\n${match.trim()}`)
}

/**
 * Intelligent parsing for streaming markdown.
 */
function parseIncompleteMarkdown(markdown: string): string {
  if (!markdown) return ""

  // 1. Sanitize problematic content first
  let processed = markdown
    .replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
    .replace(/<\/?thinking>/gi, '')
    .replace(/```json\s*\{[\s\S]*?"perception"[\s\S]*?"decision"[\s\S]*?\}\s*```/gi, '')
    .replace(/\{[\s\S]*?"perception"[\s\S]*?"analysis"[\s\S]*?"planning"[\s\S]*?"decision"[\s\S]*?\}/gi, '')
    .replace(/<\/?(?:quiz|example|step|hint|activation|exploration|guidance|challenge)[^>]*>/gi, '')
    .replace(/<\s*\/?\s*thinking\s*>/gi, '')

  // 2. Handle code blocks (protect content inside them)
  const codeBlockRegex = /```[\s\S]*?```/g
  const codeBlocks: string[] = []
  let placeholderIndex = 0
  
  processed = processed.replace(codeBlockRegex, (match) => {
    const placeholder = `__CODE_BLOCK_${placeholderIndex++}__`
    codeBlocks.push(match)
    return placeholder
  })

  const incompleteCodeBlockMatch = processed.match(/```[\s\S]*$/)
  if (incompleteCodeBlockMatch) {
    const incompleteBlock = incompleteCodeBlockMatch[0]
    processed = processed.substring(0, incompleteCodeBlockMatch.index) + `__CODE_BLOCK_${placeholderIndex}__`
    codeBlocks.push(incompleteBlock + "\n```")
  }

  // 3. Auto-complete formatting tokens
  const boldCount = (processed.match(/\*\*/g) || []).length
  if (boldCount % 2 !== 0) {
    processed += "**"
  }

  const backtickCount = (processed.match(/`/g) || []).length
  if (backtickCount % 2 !== 0) {
    processed += "`"
  }

  const strikeCount = (processed.match(/~~/g) || []).length
  if (strikeCount % 2 !== 0) {
    processed += "~~"
  }

  // 4. Hide incomplete links/images
  processed = processed.replace(/!\[[^\]]*$/, '')
  processed = processed.replace(/\[[^\]]*$/, '')
  processed = processed.replace(/\]\([^\)]*$/, '')

  // 5. Remove trailing period after citations
  processed = processed.replace(/(\[\d+\])\s*\./g, '$1')

  // 6. Restore code blocks
  processed = processed.replace(/__CODE_BLOCK_(\d+)__/g, (_, index) => {
    return codeBlocks[parseInt(index)]
  })

  // 7. Apply scaffolding spacing
  processed = addScaffoldingSpacing(processed)

  return processed
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
    if (prevProps.fallback !== this.props.fallback && this.state.hasError) {
      this.setState({ hasError: false, error: undefined })
    }
  }

  render() {
    if (this.state.hasError) {
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
  // Handle JSX children (from citations) - pass through without processing
  if (typeof children !== 'string') {
    return (
      <div className={cn("max-w-none text-sm leading-7 break-words w-full", className)}>
        {children}
      </div>
    )
  }
  
  // Process content: parse incomplete markdown, then pre-render math to HTML
  const parsedContent = useMemo(() => {
    const cleaned = parseIncompleteMarkdown(children || "")
    return renderMathWithKatex(cleaned)
  }, [children])

  const htmlContent = useMemo(() => {
    // marked parses markdown to HTML; GFM enabled by default in marked v12+
    return marked.parse(parsedContent, { breaks: true }) as string
  }, [parsedContent])
  
  if (!parsedContent) {
    return null
  }
  
  return (
    <div className={cn("max-w-none text-sm leading-7 break-words w-full", className)}>
      <MarkdownErrorBoundary fallback={parsedContent}>
        <div
          className="prose dark:prose-invert max-w-none text-sm leading-7 text-foreground break-words w-full"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      </MarkdownErrorBoundary>
    </div>
  )
}










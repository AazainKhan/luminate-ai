/**
 * Utilities for safely handling Markdown content from LLM responses
 */

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * Sanitize content before passing to ReactMarkdown.
 * Removes problematic patterns that can crash the parser.
 */
export function sanitizeMarkdownContent(text: string | null | undefined): string {
  if (!text) return ''
  
  let cleaned = text
  
  // Remove <thinking>...</thinking> blocks including content
  cleaned = cleaned.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
  
  // Remove any standalone <thinking> or </thinking> tags
  cleaned = cleaned.replace(/<\/?thinking>/gi, '')
  
  // Remove <thinking with spaces or malformed versions
  cleaned = cleaned.replace(/<\s*\/?\s*thinking\s*>/gi, '')
  
  // Remove other potentially problematic XML-like tags that aren't standard HTML
  // These are custom tags that may appear in LLM output
  const customTags = ['example', 'step', 'hint', 'activation', 'exploration', 'guidance', 'challenge', 'answer', 'solution']
  for (const tag of customTags) {
    // Keep the content but remove the tags themselves for proper display
    cleaned = cleaned.replace(new RegExp(`<${tag}[^>]*>`, 'gi'), '')
    cleaned = cleaned.replace(new RegExp(`</${tag}>`, 'gi'), '')
  }
  
  return cleaned.trim()
}

// Alias for backwards compatibility
export const sanitizeMarkdown = sanitizeMarkdownContent

/**
 * Check if content appears to be safe for markdown parsing
 */
export function isValidMarkdown(text: string): boolean {
  if (!text) return false
  
  // Check for known problematic patterns
  const problematicPatterns = [
    /<thinking>/i,
    /<\/thinking>/i,
    /\u0000/,  // Null characters
    /<[a-z]+\s+[^>]*undefined/i,  // Tags with undefined attributes
  ]
  
  return !problematicPatterns.some(pattern => pattern.test(text))
}

/**
 * Creates a safe code component for ReactMarkdown that handles undefined className
 * @param CodeBlockComponent - Optional custom component for code blocks
 */
export function createCodeComponent(CodeBlockComponent?: React.ComponentType<{ code: string; language: string; showRunButton?: boolean }>) {
  return function CodeComponent({ 
    node, 
    className, 
    children, 
    ...props 
  }: { 
    node?: any
    className?: string
    children?: React.ReactNode
    [key: string]: any 
  }) {
    // Safely handle className - could be undefined
    const safeClassName = className || ''
    const match = /language-(\w+)/.exec(safeClassName)
    const language = match ? match[1] : ''
    const codeString = String(children || '').replace(/\n$/, '')
    
    // Check if this is an inline code or a code block
    const isInline = !safeClassName && !codeString.includes('\n')
    
    if (isInline) {
      return React.createElement('code', {
        className: 'bg-muted px-1 py-0.5 rounded text-sm',
        ...props
      }, children)
    }
    
    // Use custom CodeBlock if provided
    if (CodeBlockComponent) {
      return React.createElement(CodeBlockComponent, {
        code: codeString,
        language: language || 'python',
        showRunButton: language === 'python'
      })
    }
    
    // Fallback to basic pre/code block
    return React.createElement('pre', { className: 'bg-muted p-3 rounded overflow-x-auto' },
      React.createElement('code', { className: safeClassName }, children)
    )
  }
}

interface SafeMarkdownProps {
  children: string | null | undefined
  className?: string
  components?: Record<string, React.ComponentType<any>>
}

/**
 * Error boundary wrapper for ReactMarkdown
 */
class MarkdownErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Markdown rendering error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

/**
 * A safe wrapper around ReactMarkdown that:
 * 1. Sanitizes content before rendering
 * 2. Catches rendering errors gracefully
 * 3. Provides safe code block handling
 */
export function SafeMarkdown({ children, className, components }: SafeMarkdownProps) {
  const sanitized = sanitizeMarkdownContent(children)
  
  if (!sanitized) {
    return null
  }

  const defaultComponents = {
    code: createCodeComponent(),
    ...components
  }

  const fallback = React.createElement('div', { 
    className: 'text-foreground whitespace-pre-wrap' 
  }, sanitized)

  const markdownElement = React.createElement(
    ReactMarkdown,
    { remarkPlugins: [remarkGfm], components: defaultComponents },
    sanitized
  )

  const wrapperElement = React.createElement(
    'div',
    { className: className || 'prose prose-sm dark:prose-invert max-w-none' },
    markdownElement
  )

  return React.createElement(
    MarkdownErrorBoundary,
    { fallback, children: wrapperElement }
  )
}

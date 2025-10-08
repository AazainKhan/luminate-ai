"use client";

import { cn } from "@/lib/utils";
import { type ComponentProps, memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypePrism from "rehype-prism-plus";
import "katex/dist/katex.min.css";
import "prismjs/themes/prism-tomorrow.css";

type ResponseProps = ComponentProps<typeof ReactMarkdown> & { 
  className?: string;
  parseIncompleteMarkdown?: boolean;
  allowedImagePrefixes?: string[];
  allowedLinkPrefixes?: string[];
  defaultOrigin?: string;
};

/**
 * Auto-complete incomplete markdown formatting during streaming
 */
function parseIncomplete(text: string): string {
  if (!text) return text;

  // Count formatting tokens
  const boldCount = (text.match(/\*\*/g) || []).length;
  const italicCount = (text.match(/(?<!\*)\*(?!\*)/g) || []).length;
  const strikeCount = (text.match(/~~/g) || []).length;
  const codeCount = (text.match(/(?<!`)`(?!`)/g) || []).length;

  let result = text;

  // Auto-close bold if odd number
  if (boldCount % 2 !== 0) {
    result += "**";
  }

  // Auto-close italic if odd number (and not inside code)
  if (italicCount % 2 !== 0 && !text.endsWith("`")) {
    result += "*";
  }

  // Auto-close strikethrough if odd number
  if (strikeCount % 2 !== 0) {
    result += "~~";
  }

  // Auto-close inline code if odd number
  if (codeCount % 2 !== 0 && !text.includes("```")) {
    result += "`";
  }

  // Hide incomplete links: [text without closing ]
  result = result.replace(/\[([^\]]+)$/g, "");

  // Hide incomplete images: ![alt without closing ]
  result = result.replace(/!\[([^\]]+)$/g, "");

  return result;
}

/**
 * Custom components for enhanced markdown rendering
 */
const components = {
  // Code blocks with copy button
  pre: ({ children, ...props }: any) => (
    <div className="relative group my-4">
      <pre
        className="overflow-x-auto rounded-lg border bg-secondary p-4 text-sm"
        {...props}
      >
        {children}
      </pre>
      <button
        onClick={() => {
          const code = (children as any)?.props?.children;
          if (code && typeof code === 'string') {
            navigator.clipboard.writeText(code);
          }
        }}
        className="absolute right-2 top-2 rounded bg-background px-2 py-1 text-xs opacity-0 transition-opacity group-hover:opacity-100"
        aria-label="Copy code"
      >
        Copy
      </button>
    </div>
  ),
  
  // Inline code
  code: ({ inline, className, children, ...props }: any) => {
    if (inline) {
      return (
        <code
          className="rounded-md bg-secondary px-1.5 py-0.5 font-mono text-sm"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },

  // Links with security
  a: ({ href, children, ...props }: any) => (
    <a
      href={href}
      className="text-primary underline-offset-4 hover:underline"
      target={href?.startsWith("http") ? "_blank" : undefined}
      rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
      {...props}
    >
      {children}
    </a>
  ),

  // Headings with better styling
  h1: ({ children, ...props }: any) => (
    <h1 className="mt-6 mb-4 text-3xl font-bold tracking-tight first:mt-0" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: any) => (
    <h2 className="mt-6 mb-3 text-2xl font-bold tracking-tight first:mt-0" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: any) => (
    <h3 className="mt-4 mb-2 text-xl font-semibold tracking-tight first:mt-0" {...props}>
      {children}
    </h3>
  ),
  h4: ({ children, ...props }: any) => (
    <h4 className="mt-4 mb-2 text-lg font-semibold first:mt-0" {...props}>
      {children}
    </h4>
  ),

  // Lists with better spacing
  ul: ({ children, ...props }: any) => (
    <ul className="my-4 ml-6 list-disc space-y-1 first:mt-0 last:mb-0" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: any) => (
    <ol className="my-4 ml-6 list-decimal space-y-1 first:mt-0 last:mb-0" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }: any) => (
    <li className="leading-relaxed" {...props}>
      {children}
    </li>
  ),

  // Blockquotes
  blockquote: ({ children, ...props }: any) => (
    <blockquote
      className="my-4 border-l-4 border-primary pl-4 italic text-muted-foreground first:mt-0 last:mb-0"
      {...props}
    >
      {children}
    </blockquote>
  ),

  // Tables
  table: ({ children, ...props }: any) => (
    <div className="my-4 w-full overflow-x-auto first:mt-0 last:mb-0">
      <table className="w-full border-collapse" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }: any) => (
    <thead className="border-b bg-secondary" {...props}>
      {children}
    </thead>
  ),
  tbody: ({ children, ...props }: any) => (
    <tbody className="divide-y" {...props}>
      {children}
    </tbody>
  ),
  tr: ({ children, ...props }: any) => (
    <tr className="transition-colors hover:bg-secondary/50" {...props}>
      {children}
    </tr>
  ),
  th: ({ children, ...props }: any) => (
    <th className="px-4 py-2 text-left font-semibold" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }: any) => (
    <td className="px-4 py-2" {...props}>
      {children}
    </td>
  ),

  // Paragraphs
  p: ({ children, ...props }: any) => (
    <p className="my-3 leading-relaxed first:mt-0 last:mb-0" {...props}>
      {children}
    </p>
  ),

  // Horizontal rules
  hr: ({ ...props }: any) => (
    <hr className="my-6 border-border" {...props} />
  ),

  // Images
  img: ({ src, alt, ...props }: any) => (
    <img
      src={src}
      alt={alt}
      className="my-4 max-w-full rounded-lg border"
      loading="lazy"
      {...props}
    />
  ),
};

export const Response = memo(
  ({ 
    className, 
    children,
    parseIncompleteMarkdown = true,
    allowedImagePrefixes = ["*"],
    allowedLinkPrefixes = ["*"],
    defaultOrigin,
    ...props 
  }: ResponseProps) => {
    // Process content if it's a string and streaming optimization is enabled
    const processedContent = useMemo(() => {
      if (typeof children === 'string' && parseIncompleteMarkdown) {
        return parseIncomplete(children);
      }
      return children;
    }, [children, parseIncompleteMarkdown]);

    return (
      <div 
        className={cn(
          "prose prose-sm max-w-none dark:prose-invert",
          "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
          className
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex, rehypePrism]}
          components={components}
          {...props}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    );
  },
  (prevProps, nextProps) => prevProps.children === nextProps.children
);

Response.displayName = "Response";

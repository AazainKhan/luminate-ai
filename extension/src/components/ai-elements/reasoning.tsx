'use client';

import { useControllableState } from '@radix-ui/react-use-controllable-state';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { Brain, ChevronDown } from 'lucide-react';
import type { ComponentProps } from 'react';
import { createContext, memo, useContext, useEffect, useState, useMemo, useRef, useCallback } from 'react';

type ReasoningContextValue = {
  isStreaming: boolean;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  duration: number;
};

const ReasoningContext = createContext<ReasoningContextValue | null>(null);

const useReasoning = () => {
  const context = useContext(ReasoningContext);
  if (!context) {
    throw new Error('Reasoning components must be used within Reasoning');
  }
  return context;
};

export type ReasoningProps = ComponentProps<typeof Collapsible> & {
  isStreaming?: boolean;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  duration?: number;
};

const AUTO_CLOSE_DELAY = 1000;

export const Reasoning = memo(
  ({
    className,
    isStreaming = false,
    open,
    defaultOpen = false,
    onOpenChange,
    duration: durationProp,
    children,
    ...props
  }: ReasoningProps) => {
    const [isOpen, setIsOpen] = useControllableState({
      prop: open,
      defaultProp: defaultOpen,
      onChange: onOpenChange,
    });
    const [duration, setDuration] = useControllableState({
      prop: durationProp,
      defaultProp: 0,
    });
    const [hasAutoClosedRef, setHasAutoClosedRef] = useState(false);
    const [startTime, setStartTime] = useState<number | null>(null);

    // Track duration when streaming starts and ends
    useEffect(() => {
      if (isStreaming) {
        if (startTime === null) {
          setStartTime(Date.now());
        }
      } else if (startTime !== null) {
        setDuration(Math.round((Date.now() - startTime) / 1000));
        setStartTime(null);
      }
    }, [isStreaming, startTime, setDuration]);

    const handleOpenChange = useCallback((newOpen: boolean) => {
      setIsOpen(newOpen);
    }, [setIsOpen]);

    return (
      <ReasoningContext.Provider
        value={{ isStreaming, isOpen: isOpen ?? false, setIsOpen: handleOpenChange, duration: duration ?? 0 }}
      >
        <Collapsible
          className={cn('not-prose mb-4', className)}
          onOpenChange={handleOpenChange}
          open={isOpen}
          {...(props as any)}
        >
          {children}
        </Collapsible>
      </ReasoningContext.Provider>
    );
  }
);

export type ReasoningTriggerProps = ComponentProps<
  typeof CollapsibleTrigger
> & {
  title?: string;
  currentStep?: string;
};

export const ReasoningTrigger = memo(
  ({
    className,
    title = 'Reasoning',
    currentStep,
    children,
    ...props
  }: ReasoningTriggerProps) => {
    const { isStreaming, isOpen, duration } = useReasoning();
    return (
      <CollapsibleTrigger
        className={cn(
          'flex items-center gap-2 text-muted-foreground text-sm group select-none',
          className
        )}
        {...(props as any)}
      >
        {children ?? (
          <>
            <Brain className="size-4" />
            {isStreaming ? (
              <p className="text-xs font-medium animate-pulse">
                {currentStep ? `Reasoning: ${currentStep}` : "Reasoning..."}
              </p>
            ) : (
              <p className="text-xs font-medium">
                {duration > 0 ? `Reasoned for ${duration} seconds` : "Reasoning"}
              </p>
            )}
            <ChevronDown
              className={cn(
                'size-4 text-muted-foreground transition-transform duration-200',
                isOpen ? 'rotate-180' : 'rotate-0'
              )}
            />
          </>
        )}
      </CollapsibleTrigger>
    );
  }
);

export type ReasoningContentProps = ComponentProps<
  typeof CollapsibleContent
> & {
  children: React.ReactNode;
};

import { SafeMarkdown } from "@/lib/markdown-utils"

export const ReasoningContent = memo(
  ({ className, children, ...props }: ReasoningContentProps) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const { isStreaming } = useReasoning();
    const [isAtBottom, setIsAtBottom] = useState(false);
    const scrollTimeoutRef = useRef<number | null>(null);

    const checkScroll = useCallback(() => {
      if (!contentRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
      const atBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;
      setIsAtBottom(atBottom);
    }, []);

    useEffect(() => {
      checkScroll();
    }, [children, checkScroll]);

    // Throttled auto-scroll to bottom when content changes during streaming
    // Max once per 300ms for smooth, natural scrolling
    useEffect(() => {
      if (isStreaming && contentRef.current) {
        if (scrollTimeoutRef.current !== null) {
          window.clearTimeout(scrollTimeoutRef.current);
        }
        
        scrollTimeoutRef.current = window.setTimeout(() => {
          if (contentRef.current) {
            contentRef.current.scrollTo({
              top: contentRef.current.scrollHeight,
              behavior: 'smooth'
            });
            setIsAtBottom(true);
          }
          scrollTimeoutRef.current = null;
        }, 300);
      }
      
      return () => {
        if (scrollTimeoutRef.current !== null) {
          window.clearTimeout(scrollTimeoutRef.current);
        }
      };
    }, [children, isStreaming]);

    // Parse reasoning content into individual steps with titles and paragraphs
    const blocks = useMemo(() => {
      if (typeof children !== 'string') return [children];
      
      // Split by markdown headers (### or **Title**) or double newlines
      const text = children.trim();
      const parts: Array<{ type: 'title' | 'paragraph'; content: string; key: string }> = [];
      
      // Match headers and paragraphs
      const lines = text.split('\n');
      let currentParagraph = '';
      
      lines.forEach((line, idx) => {
        const trimmed = line.trim();
        
        // Check if it's a header (### Title or **Title**)
        const headerMatch = trimmed.match(/^(###\s*(.+)|\*\*(.+)\*\*)$/);
        
        if (headerMatch) {
          // Save any accumulated paragraph
          if (currentParagraph.trim()) {
            parts.push({
              type: 'paragraph',
              content: currentParagraph.trim(),
              key: `para-${parts.length}`
            });
            currentParagraph = '';
          }
          
          // Add the header
          const title = headerMatch[2] || headerMatch[3];
          parts.push({
            type: 'title',
            content: title,
            key: `title-${parts.length}`
          });
        } else if (trimmed) {
          // Accumulate paragraph content
          currentParagraph += (currentParagraph ? '\n' : '') + line;
        } else if (currentParagraph.trim()) {
          // Empty line and we have content - save paragraph
          parts.push({
            type: 'paragraph',
            content: currentParagraph.trim(),
            key: `para-${parts.length}`
          });
          currentParagraph = '';
        }
      });
      
      // Don't forget the last paragraph
      if (currentParagraph.trim()) {
        parts.push({
          type: 'paragraph',
          content: currentParagraph.trim(),
          key: `para-${parts.length}`
        });
      }
      
      return parts;
    }, [children]);

    return (
      <CollapsibleContent
        className={cn(
          'mt-2 text-sm overflow-hidden',
          'data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down',
          className
        )}
        {...(props as any)}
      >
        <div className="relative">
          <div 
            ref={contentRef}
            onScroll={checkScroll}
            className="rounded-lg border bg-card/50 p-3 prose dark:prose-invert max-w-none text-xs leading-relaxed break-words max-h-[300px] overflow-y-auto scroll-smooth [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-muted-foreground/20 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-muted-foreground/40"
          >
            {typeof children === 'string' ? (
              <div className="flex flex-col gap-3">
                {blocks.map((block, index) => (
                  <div 
                    key={block.key}
                    className="animate-in fade-in slide-in-from-bottom-1 duration-500"
                    style={{
                      animationDelay: `${index * 100}ms`,
                      animationFillMode: 'backwards'
                    }}
                  >
                    {block.type === 'title' ? (
                      <h4 className="text-sm font-semibold text-foreground mb-1 mt-0">
                        {block.content}
                      </h4>
                    ) : (
                      <SafeMarkdown
                        className="text-xs text-muted-foreground leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
                        components={{
                          // Ensure all components are defined to avoid undefined className errors
                          p: (props: any) => <p {...props} />,
                          code: (props: any) => <code {...props} />,
                          pre: (props: any) => <pre {...props} />,
                          a: (props: any) => <a {...props} />,
                          ul: (props: any) => <ul {...props} />,
                          ol: (props: any) => <ol {...props} />,
                          li: (props: any) => <li {...props} />,
                          strong: (props: any) => <strong {...props} />,
                          em: (props: any) => <em {...props} />,
                          blockquote: (props: any) => <blockquote {...props} />,
                          h1: (props: any) => <h1 {...props} />,
                          h2: (props: any) => <h2 {...props} />,
                          h3: (props: any) => <h3 {...props} />,
                          h4: (props: any) => <h4 {...props} />,
                          h5: (props: any) => <h5 {...props} />,
                          h6: (props: any) => <h6 {...props} />,
                          table: (props: any) => <table {...props} />,
                          thead: (props: any) => <thead {...props} />,
                          tbody: (props: any) => <tbody {...props} />,
                          tr: (props: any) => <tr {...props} />,
                          th: (props: any) => <th {...props} />,
                          td: (props: any) => <td {...props} />,
                          del: (props: any) => <del {...props} />,
                          input: (props: any) => <input {...props} />,
                        }}
                      >
                        {block.content}
                      </SafeMarkdown>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              children
            )}
          </div>
          <div 
            className={cn(
              "absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent pointer-events-none transition-opacity duration-300",
              isAtBottom ? "opacity-0" : "opacity-100"
            )}
          />
        </div>
      </CollapsibleContent>
    )
  }
);

Reasoning.displayName = 'Reasoning';
ReasoningTrigger.displayName = 'ReasoningTrigger';
ReasoningContent.displayName = 'ReasoningContent';

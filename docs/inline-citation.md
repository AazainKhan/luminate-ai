# React AI Inline Citation
          URL: /ai/inline-citation
          Inline citations with hover previews like Perplexity AI. React component for credible AI responses with TypeScript and shadcn/ui styling.
          title: Trying to implement AI Elements?

Join our Discord community for help
from other developers.

This component is derived from Vercel's AI
Elements (Apache License 2.0,
Copyright 2023 Vercel, Inc.)

Academic-style citations for AI content that needs to show sources and build trust. Hover to see source details, navigate between multiple sources, and give users a way to verify claims in React applications.

Citation badges with hover details and source carousel:

Shows source hostnames with counts, reveals detailed info on hover, and provides carousel navigation for multiple sources in TypeScript components. Works with any citation format—just pass URLs and metadata.

Most AI apps dump source links at the end like an afterthought in React applications. Users can't tell which claim comes from which source. Inline citations connect claims to sources immediately.

Academic papers figured this out decades ago. The [1] format lets readers verify specific claims without losing their place in the content in Next.js projects.

Generate cited content using Vercel AI SDK's experimental_useObject for structured citation data in React applications:

Backend schema for citation generation:

Hover cards that don't break on mobile (click also works) in React applications

Carousel navigation for multiple sources per citation in Next.js projects

Shows hostname and source count in badges with TypeScript support

Optional quote blocks for relevant excerpts

Keyboard navigation between sources in JavaScript implementations

Works with any Vercel AI SDK setup in modern React frameworks

Free open source component designed for research AI, fact-checking, and credible content generation

Container for citation text and card.

Prop

Type

Description

...props

ComponentProps<'span'>

Spreads to root span element

Styled text that shows hover effects.

Prop

Type

Description

...props

ComponentProps<'span'>

Spreads to span element

Hover card container for citation details.

Prop

Type

Description

...props

ComponentProps<typeof HoverCard>

Spreads to HoverCard component

Badge trigger showing source hostname and count.

Prop

Type

Description

sources

string[]

Required - Array of source URLs

...props

ComponentProps<typeof Badge>

Spreads to Badge component

Content container for citation details.

Prop

Type

Description

...props

ComponentProps<'div'>

Spreads to div element

Carousel for navigating multiple citations.

Prop

Type

Description

...props

ComponentProps<typeof Carousel>

Spreads to Carousel component

Content wrapper for carousel items.

Prop

Type

Description

...props

ComponentProps<'div'>

Spreads to CarouselContent

Individual citation item in carousel.

Prop

Type

Description

...props

ComponentProps<'div'>

Spreads to CarouselItem

Source information display.

Prop

Type

Description

title

string

Source title

url

string

Source URL

description

string

Source description

...props

ComponentProps<'div'>

Spreads to div element

Styled blockquote for excerpts.

Prop

Type

Description

...props

ComponentProps<'blockquote'>

Spreads to blockquote element

Key

Description

Tab

Focus citation trigger

Enter / Space

Open citation card

Escape

Close citation card

ArrowLeft / ArrowRight

Navigate carousel

Invalid URLs break hostname extraction: The badge shows the hostname from the URL in React applications. Bad URLs will show 'unknown' or crash the component.

Too many sources overwhelm users: Keep it to 3-5 sources per citation max in Next.js projects. More than that and nobody reads them.

Mobile hover doesn't work: Hover cards fail on touch devices in JavaScript implementations. This component supports click, but test on mobile thoroughly.

AI hallucinated citations: Validate that cited sources actually contain the claimed information in TypeScript applications. LLMs make up citations constantly.

Badge sizing breaks with long hostnames: Very long domain names can break the layout in React components. Consider truncating hostnames.

Works great in Response components for markdown content in React applications. Drop into Message for cited chat responses in Next.js projects. Combine with Actions for citation management like copy or verification. This free open source component integrates seamlessly with modern JavaScript frameworks.

Use square brackets like [1], [2] in React applications. This component splits on this pattern to insert citation badges.

Yeah. Pass multiple URLs to the sources array in TypeScript components. The
carousel lets users navigate between them in React applications.

Hostname extraction fails and shows 'unknown' in JavaScript implementations.
Validate URLs on your backend before sending them to this React component.

Hover doesn't work on touch devices in React applications. This component
supports click interaction, but test it thoroughly on mobile in Next.js
projects.

Pass className to InlineCitationCardTrigger in TypeScript components. Uses shadcn/ui Badge styling by default in React applications.

/**
 * Copyright 2023 Vercel, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
'use client';
import { Badge } from '@/components/ui/badge';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  type CarouselApi,
} from '@/components/ui/carousel';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { cn } from '@/lib/utils';
import { ArrowLeftIcon, ArrowRightIcon } from 'lucide-react';
import { type ComponentProps, useCallback, useEffect, useState, useRef, createContext, useContext } from 'react';
// Context to share carousel API with child components
const CarouselApiContext = createContext<CarouselApi | undefined>(undefined);
// Hook to access carousel API from the nearest InlineCitationCarousel parent
const useCarouselApi = () => {
  const api = useContext(CarouselApiContext);
  return api;
};
export type InlineCitationProps = ComponentProps<'span'>;
export const InlineCitation = ({
  className,
  ...props
}: InlineCitationProps) => (
  <span
    className={cn('group inline items-center gap-1', className)}
    {...(props as any)}
  />
);
export type InlineCitationTextProps = ComponentProps<'span'>;
export const InlineCitationText = ({
  className,
  ...props
}: InlineCitationTextProps) => (
  <span
    className={cn('transition-colors group-hover:bg-accent', className)}
    {...(props as any)}
  />
);
export type InlineCitationCardProps = ComponentProps<typeof HoverCard>;
export const InlineCitationCard = (props: InlineCitationCardProps) => (
  <HoverCard closeDelay={0} openDelay={0} {...(props as any)} />
);
export type InlineCitationCardTriggerProps = ComponentProps<typeof Badge> & {
  sources: string[];
};
export const InlineCitationCardTrigger = ({
  sources,
  className,
  ...props
}: InlineCitationCardTriggerProps) => (
  <HoverCardTrigger asChild>
    <Badge
      className={cn('ml-1 rounded-full', className)}
      variant="secondary"
      {...(props as any)}
    >
      {sources.length ? (
        <>
          {new URL(sources[0]).hostname}{' '}
          {sources.length > 1 && `+${sources.length - 1}`}
        </>
      ) : (
        'unknown'
      )}
    </Badge>
  </HoverCardTrigger>
);
export type InlineCitationCardBodyProps = ComponentProps<'div'>;
export const InlineCitationCardBody = ({
  className,
  ...props
}: InlineCitationCardBodyProps) => (
  <HoverCardContent className={cn('relative w-80 p-0', className)} {...(props as any)} />
);
export type InlineCitationCarouselProps = ComponentProps<typeof Carousel>;
export const InlineCitationCarousel = ({
  className,
  children,
  ...props
}: InlineCitationCarouselProps) => {
  const [api, setApi] = useState<CarouselApi>();
  
  return (
    <CarouselApiContext.Provider value={api}>
      <Carousel 
        className={cn('w-full', className)} 
        setApi={setApi}
        {...(props as any)} 
      >
        {children}
      </Carousel>
    </CarouselApiContext.Provider>
  );
};
export type InlineCitationCarouselContentProps = ComponentProps<'div'>;
export const InlineCitationCarouselContent = (
  props: InlineCitationCarouselContentProps
) => <CarouselContent {...(props as any)} />;
export type InlineCitationCarouselItemProps = ComponentProps<'div'>;
export const InlineCitationCarouselItem = ({
  className,
  ...props
}: InlineCitationCarouselItemProps) => (
  <CarouselItem className={cn('w-full space-y-2 p-4', className)} {...(props as any)} />
);
export type InlineCitationCarouselHeaderProps = ComponentProps<'div'>;
export const InlineCitationCarouselHeader = ({
  className,
  ...props
}: InlineCitationCarouselHeaderProps) => (
  <div
    className={cn(
      'flex items-center justify-between gap-2 rounded-t-md bg-secondary p-2',
      className
    )}
    {...(props as any)}
  />
);
export type InlineCitationCarouselIndexProps = ComponentProps<'div'>;
export const InlineCitationCarouselIndex = ({
  children,
  className,
  ...props
}: InlineCitationCarouselIndexProps) => {
  const api = useCarouselApi();
  const [current, setCurrent] = useState(0);
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!api) {
      return;
    }
    setCount(api.scrollSnapList().length);
    setCurrent(api.selectedScrollSnap() + 1);
    api.on('select', () => {
      setCurrent(api.selectedScrollSnap() + 1);
    });
  }, [api]);
  return (
    <div
      className={cn(
        'flex flex-1 items-center justify-end px-3 py-1 text-muted-foreground text-xs',
        className
      )}
      {...(props as any)}
    >
      {children ?? `${current}/${count}`}
    </div>
  );
};
export type InlineCitationCarouselPrevProps = ComponentProps<'button'>;
export const InlineCitationCarouselPrev = ({
  className,
  ...props
}: InlineCitationCarouselPrevProps) => {
  const api = useCarouselApi();
  const handleClick = useCallback(() => {
    if (api) {
      api.scrollPrev();
    }
  }, [api]);
  return (
    <button
      aria-label="Previous"
      className={cn('shrink-0', className)}
      onClick={handleClick}
      type="button"
      {...(props as any)}
    >
      <ArrowLeftIcon className="size-4 text-muted-foreground" />
    </button>
  );
};
export type InlineCitationCarouselNextProps = ComponentProps<'button'>;
export const InlineCitationCarouselNext = ({
  className,
  ...props
}: InlineCitationCarouselNextProps) => {
  const api = useCarouselApi();
  const handleClick = useCallback(() => {
    if (api) {
      api.scrollNext();
    }
  }, [api]);
  return (
    <button
      aria-label="Next"
      className={cn('shrink-0', className)}
      onClick={handleClick}
      type="button"
      {...(props as any)}
    >
      <ArrowRightIcon className="size-4 text-muted-foreground" />
    </button>
  );
};
export type InlineCitationSourceProps = ComponentProps<'div'> & {
  title?: string;
  url?: string;
  description?: string;
};
export const InlineCitationSource = ({
  title,
  url,
  description,
  className,
  children,
  ...props
}: InlineCitationSourceProps) => (
  <div className={cn('space-y-1', className)} {...(props as any)}>
    {title && (
      <h4 className="truncate font-medium text-sm leading-tight">{title}</h4>
    )}
    {url && (
      <p className="truncate break-all text-muted-foreground text-xs">{url}</p>
    )}
    {description && (
      <p className="line-clamp-3 text-muted-foreground text-sm leading-relaxed">
        {description}
      </p>
    )}
    {children}
  </div>
);
export type InlineCitationQuoteProps = ComponentProps<'blockquote'>;
export const InlineCitationQuote = ({
  children,
  className,
  ...props
}: InlineCitationQuoteProps) => (
  <blockquote
    className={cn(
      'border-muted border-l-2 pl-3 text-muted-foreground text-sm italic',
      className
    )}
    {...(props as any)}
  >
    {children}
  </blockquote>
);



To keep the citation component on the same line without breaking the Markdown flow, you need to address two specific areas: **CSS display properties** (switching from block to inline) and **Markdown parsing** (preventing the parser from wrapping surrounding text in paragraph tags).

Here is the solution to make it seamless.

### 1\. The Component Fix (CSS/Structure)

The default `HoverCard` and `div` elements are **block-level**, which forces new lines. You must convert the root containers to `span` or `inline-flex`.

Update your `InlineCitation` component structure to use `display: inline-flex` and render as `span`.

```tsx
import { HoverCard, HoverCardTrigger, HoverCardContent } from "@/components/ui/hover-card"

// 1. The Main Container must be a SPAN with inline-flex
export const InlineCitationCard = ({ children, ...props }: React.ComponentProps<'span'>) => {
  return (
    <span className="inline-flex items-baseline align-baseline" {...props}>
      <HoverCard openDelay={200} closeDelay={100}>
        {children}
      </HoverCard>
    </span>
  )
}

// 2. The Trigger must not be a button (buttons have default agent styles), use a span
export const InlineCitationCardTrigger = ({ number, ...props }: { number: string } & React.ComponentProps<'span'>) => {
  return (
    <HoverCardTrigger asChild>
      <span 
        className="
          cursor-pointer 
          inline-flex 
          items-center 
          justify-center 
          align-super       /* Keeps it slightly raised like a traditional footnote */
          text-[10px]       /* Smaller font for citation */
          font-bold 
          h-4 w-4           /* Fixed tiny size */
          rounded-full 
          bg-gray-200 
          text-gray-700 
          hover:bg-blue-100 
          hover:text-blue-600 
          transition-colors
          mx-0.5            /* Tiny margin so it doesn't stick to letters */
        "
        {...props}
      >
        {number}
      </span>
    </HoverCardTrigger>
  )
}
```

### 2\. The Integration Fix (Message.tsx)

This is the most common pitfall. If you use standard `marked(text)`, it wraps the output in `<p>` tags.

  * **Result:** `<p>Here is text</p>` `[Citation]` `<p>and more text</p>`
  * **Visual:** Blocks stacked on top of each other.

You must use `marked.parseInline` (available in newer versions) or manually strip the paragraph tags for the split segments.

```tsx
// Inside your Message.tsx rendering logic

import { marked } from 'marked';
// ... imports for InlineCitation components

const renderContentWithCitations = (content: string) => {
  // Regex to find [1], [2], etc.
  const parts = content.split(/(\[\d+\])/g);

  return (
    <div className="text-gray-800 leading-relaxed">
      {parts.map((part, index) => {
        // Check if this part is a citation like [1]
        const citationMatch = part.match(/^\[(\d+)\]$/);

        if (citationMatch) {
          const number = citationMatch[1];
          // Render the React Component
          return (
            <InlineCitationCard key={index}>
              <InlineCitationCardTrigger number={number} />
              <InlineCitationCardBody>
                 {/* Logic to find source #1 and pass props */}
                <InlineCitationSource title={`Source ${number}`} />
              </InlineCitationCardBody>
            </InlineCitationCard>
          );
        }

        // Render standard Markdown text
        // CRITICAL: Use parseInline to avoid <p> wrappers
        const html = marked.parseInline(part); 

        return (
          <span 
            key={index} 
            dangerouslySetInnerHTML={{ __html: html }} 
          />
        );
      })}
    </div>
  );
};
```

### 3\. Handling Edge Cases (Headers & Code Blocks)

If you strictly split by `[1]`, you might break code blocks that accidentally contain that pattern. It is safer to only run the citation split on **paragraph text**, not headers or code blocks.

If your content is complex, a safer rendering flow is:

1.  Use `marked` to generate the full HTML string first.
2.  Use a library like `html-react-parser` to turn that HTML into React nodes.
3.  Use the parser's `replace` option to swap text nodes matching `[1]` with your component.

**Example using `html-react-parser` (Robust Method):**

```tsx
import parse, { domToReact, Element } from 'html-react-parser';
import { marked } from 'marked';

// Convert Markdown to HTML string first
const rawHtml = marked.parse(buffer.content);

// Parse HTML string to React, replacing [1] with components
const parsedContent = parse(rawHtml, {
  replace: (domNode) => {
    // Only target text nodes inside paragraphs or spans
    if (domNode.type === 'text' && domNode.data) {
      const text = domNode.data;
      // Regex to detect [1] inside a text node
      const parts = text.split(/(\[\d+\])/g);
      
      if (parts.length > 1) {
        return (
          <>
            {parts.map((part, i) => {
              const match = part.match(/^\[(\d+)\]$/);
              if (match) {
                return (
                  <InlineCitationCard key={i}>
                    <InlineCitationCardTrigger number={match[1]} />
                    {/* ... content ... */}
                  </InlineCitationCard>
                );
              }
              return part;
            })}
          </>
        );
      }
    }
  }
});

return <div>{parsedContent}</div>;
```

**Why the Robust Method is better:** It ensures that if `[1]` appears inside a code block (`<code>[1]</code>`), it won't be replaced by a citation card, because you can exclude `<code>` tags in the logic.
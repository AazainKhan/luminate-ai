/**
 * Enhanced Source component with lazy-loaded contextual descriptions
 */

import * as React from 'react'
import { Source } from '@/components/ai-elements/sources'
import { useSourceDescription } from '@/hooks/useSourceDescription'

interface LazySourceProps {
  query: string
  title: string
  content: string
  href?: string
  source_file?: string
  module?: string
  week?: number
  page?: number | string
  index?: number
  // Multi-collection support (RAG v2)
  source_type?: "course" | "oer" | "embedded"
  link_type?: "blackboard" | "mediasite" | "generic_url"
  citation_confidence?: "high" | "medium" | "low"
}

export function LazySource({
  query,
  title,
  content,
  href,
  source_file,
  module,
  week,
  page,
  index = 0,
  source_type = "course",
  link_type,
  citation_confidence,
}: LazySourceProps) {
  const { description, isLoading, generateDescription } = useSourceDescription()
  const hasGeneratedRef = React.useRef(false)

  // Generate description only once when component mounts
  React.useEffect(() => {
    if (hasGeneratedRef.current) return
    
    // Delay generation slightly to avoid hammering the API when sources expand
    const timer = setTimeout(() => {
      hasGeneratedRef.current = true
      generateDescription({
        query,
        title,
        content,
        source_file,
        module,
        week: typeof week === 'number' ? week : undefined,
      })
    }, index * 100) // Stagger requests

    return () => clearTimeout(timer)
  }, []) // Empty deps - only run once on mount

  // Show skeleton while loading, fade in when ready
  const displayDescription = isLoading ? undefined : (description || content.substring(0, 150) + '...')

  return (
    <Source
      key={`source-${index}-${title}`}
      index={index}
      title={title}
      href={href || '#'}
      description={displayDescription}
      filename={source_file}
      page={typeof page === 'number' ? page : undefined}
      isLoading={isLoading}
      sourceType={source_type}
      linkType={link_type}
      citationConfidence={citation_confidence}
    />
  )
}

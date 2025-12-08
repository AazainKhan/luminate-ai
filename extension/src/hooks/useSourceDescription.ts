/**
 * Hook for lazy-loading contextual source descriptions using Gemini 2.5 Flash-Lite
 */

import { useState, useCallback } from 'react'

interface GenerateDescriptionRequest {
  query: string
  title: string
  content: string
  source_file?: string
  module?: string
  week?: number
}

interface GenerateDescriptionResponse {
  description: string
}

interface UseSourceDescriptionResult {
  description: string | null
  isLoading: boolean
  error: Error | null
  generateDescription: (params: GenerateDescriptionRequest) => Promise<void>
}

// Simple in-memory cache for source descriptions (persists across component re-renders)
const descriptionCache = new Map<string, string>()

function getCacheKey(params: GenerateDescriptionRequest): string {
  return `${params.query}:${params.title}:${params.content.substring(0, 100)}`
}

export function useSourceDescription(): UseSourceDescriptionResult {
  const [description, setDescription] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const generateDescription = useCallback(async (params: GenerateDescriptionRequest) => {
    const cacheKey = getCacheKey(params)
    
    // Check cache first
    const cached = descriptionCache.get(cacheKey)
    if (cached) {
      setDescription(cached)
      setIsLoading(false)
      return
    }
    
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/sources/generate-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: GenerateDescriptionResponse = await response.json()
      setDescription(data.description)
      // Cache the result
      descriptionCache.set(cacheKey, data.description)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to generate description')
      setError(error)
      console.error('Error generating source description:', error)
      
      // Fallback to truncated content
      setDescription(params.content.substring(0, 150) + (params.content.length > 150 ? '...' : ''))
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    description,
    isLoading,
    error,
    generateDescription,
  }
}

/**
 * API client for backend communication
 */

// Plasmo injects PLASMO_PUBLIC_* vars at build time via process.env
const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface ChatRequest {
  messages: ChatMessage[]
  stream?: boolean
}

/**
 * Get auth token from Supabase session
 */
async function getAuthToken(): Promise<string | null> {
  const { supabase } = await import("~/lib/supabase")
  const {
    data: { session },
  } = await supabase.auth.getSession()
  return session?.access_token || null
}

/**
 * Make authenticated API request
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken()

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `API request failed: ${response.statusText}`)
  }

  return response.json()
}


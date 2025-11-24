/**
 * Code execution API client
 */

// Plasmo injects PLASMO_PUBLIC_* vars at build time via process.env
const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"

export interface ExecuteRequest {
  code: string
  language?: string
  timeout?: number
}

export interface ExecuteResult {
  success: boolean
  stdout?: string
  stderr?: string
  error?: string
  files?: string[]
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
 * Execute code in E2B sandbox
 */
export async function executeCode(request: ExecuteRequest): Promise<ExecuteResult> {
  const token = await getAuthToken()

  try {
    const response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({
        code: request.code,
        language: request.language || "python",
        timeout: request.timeout || 30,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `Execution failed: ${response.statusText}`)
    }

    return await response.json()
  } catch (error: any) {
    return {
      success: false,
      error: error.message || "Code execution failed",
      stdout: "",
      stderr: "",
    }
  }
}


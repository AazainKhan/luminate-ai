/**
 * Supabase client configuration for Chrome Extension
 */

import { createClient } from "@supabase/supabase-js"

const isDevelopment = process.env.NODE_ENV !== "production"

// Plasmo injects PLASMO_PUBLIC_* vars at build time via process.env
// Access them directly via process.env (Plasmo standard)
let supabaseUrl = process.env.PLASMO_PUBLIC_SUPABASE_URL || ""
const supabaseAnonKey = process.env.PLASMO_PUBLIC_SUPABASE_ANON_KEY || ""

// Ensure URL has protocol (required for Supabase)
if (supabaseUrl && !supabaseUrl.startsWith("http")) {
  supabaseUrl = `https://${supabaseUrl}`
}

// Remove trailing slash if present
supabaseUrl = supabaseUrl.replace(/\/$/, "")

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("❌ Supabase credentials not configured!")
  console.error("PLASMO_PUBLIC_SUPABASE_URL:", supabaseUrl || "MISSING")
  console.error("PLASMO_PUBLIC_SUPABASE_ANON_KEY:", supabaseAnonKey ? "***SET***" : "MISSING")
  
  // Show what env vars are actually available
  const availableVars = Object.keys(process.env).filter(k => 
    k.includes("SUPABASE") || k.includes("PLASMO")
  )
  console.error("Available env vars:", availableVars.length > 0 ? availableVars : "NONE FOUND")
  console.error("⚠️ Please check your .env.local file and rebuild the extension: npm run dev")
  
  // Don't create client with invalid credentials
  throw new Error("Supabase credentials are missing. Check console for details.")
}

// Validate URL format
try {
  new URL(supabaseUrl)
} catch (e) {
  console.error("❌ Invalid Supabase URL format:", supabaseUrl)
  throw new Error(`Invalid Supabase URL: ${supabaseUrl}`)
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false, // Not needed for code entry flow
    flowType: "pkce", // Use PKCE flow for better security in extensions
    storage: typeof chrome !== "undefined" && chrome.storage ? {
      getItem: async (key: string) => {
        return new Promise((resolve) => {
          chrome.storage.local.get([key], (result) => {
            resolve(result[key] || null)
          })
        })
      },
      setItem: async (key: string, value: string) => {
        return new Promise((resolve) => {
          chrome.storage.local.set({ [key]: value }, () => resolve())
        })
      },
      removeItem: async (key: string) => {
        return new Promise((resolve) => {
          chrome.storage.local.remove([key], () => resolve())
        })
      },
    } : undefined,
  },
  global: {
    headers: {
      "X-Client-Info": "luminate-ai-extension",
    },
    // Ensure fetch is available (should be in browser context)
    fetch: typeof fetch !== "undefined" ? fetch : undefined,
  },
})

/**
 * Validate email domain for institutional access
 */
export function validateEmailDomain(email: string): {
  isValid: boolean
  role: "student" | "admin" | null
  error?: string
} {
  if (!email) {
    return {
      isValid: false,
      role: null,
      error: "Email is required",
    }
  }

  if (email.endsWith("@my.centennialcollege.ca")) {
    return {
      isValid: true,
      role: "student",
    }
  }

  if (email.endsWith("@centennialcollege.ca")) {
    return {
      isValid: true,
      role: "admin",
    }
  }

  return {
    isValid: false,
    role: null,
    error: "Institutional Email Required. Please use @my.centennialcollege.ca (students) or @centennialcollege.ca (admins)",
  }
}


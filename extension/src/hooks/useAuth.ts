import { useEffect, useState } from "react"
import { User, Session } from "@supabase/supabase-js"
import { supabase, validateEmailDomain } from "~/lib/supabase"

const isDevelopment = process.env.NODE_ENV !== "production"

// Dev bypass - reads from PLASMO_PUBLIC env var at build time
// Set PLASMO_PUBLIC_DEV_AUTH_BYPASS=true in .env.local to enable
const DEV_AUTH_BYPASS = process.env.PLASMO_PUBLIC_DEV_AUTH_BYPASS === "true"

// Force clear auth on startup (useful for testing login flow)
const FORCE_CLEAR_AUTH = process.env.PLASMO_PUBLIC_FORCE_CLEAR_AUTH === "true"

// Mock user for development bypass
const DEV_MOCK_USER: User = {
  id: "dev-user-123",
  email: "dev@my.centennialcollege.ca",
  app_metadata: {},
  user_metadata: { full_name: "Dev User" },
  aud: "authenticated",
  created_at: new Date().toISOString(),
} as User

const DEV_MOCK_SESSION: Session = {
  access_token: "dev-access-token",
  refresh_token: "dev-refresh-token",
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  token_type: "bearer",
  user: DEV_MOCK_USER,
} as Session

export type UserRole = "student" | "admin" | null

export interface AuthState {
  user: User | null
  session: Session | null
  role: UserRole
  loading: boolean
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    role: null,
    loading: true,
  })

  useEffect(() => {
    let subscription: { unsubscribe: () => void } | null = null

    // Clear auth if force flag is set (for testing login flow)
    const initAuth = async () => {
      if (FORCE_CLEAR_AUTH && !DEV_AUTH_BYPASS) {
        console.log("🔥 Force clearing auth session...")
        await supabase.auth.signOut()
      }
    }

    // Helper to refresh state (used for custom events and initial load)
    const refreshState = async () => {
      if (DEV_AUTH_BYPASS) {
        setAuthState({
          user: null,
          session: null,
          role: null,
          loading: false,
        })
        return
      }

      const { data: { session } } = await supabase.auth.getSession()
      if (session?.user) {
        const validation = validateEmailDomain(session.user.email || "")
        setAuthState({
          user: session.user,
          session,
          role: validation.role,
          loading: false,
        });
      } else {
        setAuthState({
          user: null,
          session: null,
          role: null,
          loading: false,
        })
      }
    }

    // Initial load
    if (DEV_AUTH_BYPASS) {
      setAuthState({
        user: DEV_MOCK_USER,
        session: DEV_MOCK_SESSION,
        role: "student",
        loading: false,
      })
    } else {
      initAuth().then(() => refreshState())

      // Listen for auth changes (Supabase emits this)
      const {
        data: { subscription: sub },
      } = supabase.auth.onAuthStateChange((event, session) => {
        if (session?.user) {
          const validation = validateEmailDomain(session.user.email || "")
          setAuthState({
            user: session.user,
            session,
            role: validation.role,
            loading: false,
          })
        } else {
          setAuthState({
            user: null,
            session: null,
            role: null,
            loading: false,
          })
        }
      })

      subscription = sub
    }

    // Listen for custom auth refresh events (needed for DEV_AUTH_BYPASS)
    const handleAuthRefresh = () => {
      refreshState()
    }

    window.addEventListener("auth-refresh", handleAuthRefresh)

    return () => {
      subscription?.unsubscribe?.()
      window.removeEventListener("auth-refresh", handleAuthRefresh)
    }
  }, [])

  const signOut = async () => {
    if (DEV_AUTH_BYPASS) {
      // In dev bypass mode, manually clear the auth state
      setAuthState({
        user: null,
        session: null,
        role: null,
        loading: false,
      })

      // Notify other listeners (e.g., other hook instances)
      window.dispatchEvent(new Event("auth-refresh"))
      return
    }
    
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error("❌ Sign out error:", error)
      }
      // Notify other listeners to refresh state
      window.dispatchEvent(new Event("auth-refresh"))
    } catch (err) {
      console.error("❌ Sign out exception:", err)
    }
  }

  return {
    ...authState,
    signOut,
  }
}


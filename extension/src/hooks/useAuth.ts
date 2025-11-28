import { useEffect, useState } from "react"
import { User, Session } from "@supabase/supabase-js"
import { supabase, validateEmailDomain } from "~/lib/supabase"

// Dev bypass - reads from PLASMO_PUBLIC env var at build time
// Set PLASMO_PUBLIC_DEV_AUTH_BYPASS=true in .env.local to enable
const DEV_AUTH_BYPASS = process.env.PLASMO_PUBLIC_DEV_AUTH_BYPASS === "true"

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
    // Log bypass status for debugging
    console.log("🔐 Auth bypass check:", { 
      DEV_AUTH_BYPASS, 
      envVar: process.env.PLASMO_PUBLIC_DEV_AUTH_BYPASS 
    })

    // Dev bypass - skip Supabase auth entirely
    if (DEV_AUTH_BYPASS) {
      console.log("🔓 DEV AUTH BYPASS ENABLED - Using mock user")
      setAuthState({
        user: DEV_MOCK_USER,
        session: DEV_MOCK_SESSION,
        role: "student",
        loading: false,
      })
      return
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        const validation = validateEmailDomain(session.user.email || "")
        if (isDevelopment) {
          console.log("✅ Session found:", session.user.email, "Role:", validation.role)
        }
        setAuthState({
          user: session.user,
          session,
          role: validation.role,
          loading: false,
        })
      } else {
        if (isDevelopment) {
          console.log("❌ No session found")
        }
        setAuthState({
          user: null,
          session: null,
          role: null,
          loading: false,
        })
      }
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (isDevelopment) {
        console.log("🔔 Auth state changed:", event, session?.user?.email)
      }
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

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return {
    ...authState,
    signOut,
  }
}


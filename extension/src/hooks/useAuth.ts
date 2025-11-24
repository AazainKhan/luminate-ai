import { useEffect, useState } from "react"
import { User, Session } from "@supabase/supabase-js"
import { supabase, validateEmailDomain } from "~/lib/supabase"

const isDevelopment = process.env.NODE_ENV !== "production"

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


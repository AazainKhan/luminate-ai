import { useState, useEffect } from "react"
import { supabase, validateEmailDomain } from "~/lib/supabase"
import { Mail, Loader2, KeyRound, User, ArrowRight } from "lucide-react"
import { Card, CardContent } from "~/components/ui/card"
import { Label } from "~/components/ui/label"
import { Input } from "~/components/ui/input"
import { Button } from "~/components/ui/button"
import { Alert, AlertDescription } from "~/components/ui/alert"

export function LoginForm() {
  const [email, setEmail] = useState("")
  const [fullName, setFullName] = useState("")
  const [code, setCode] = useState("")
  const [step, setStep] = useState<"email" | "code">("email")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (error && error.includes("after")) {
      const match = error.match(/after (\d+) seconds/)
      if (match) {
        const seconds = parseInt(match[1])
        if (seconds > 0) {
          const timer = setTimeout(() => {
            setError((prev) => prev?.replace(/after \d+ seconds/, `after ${seconds - 1} seconds`) || null)
          }, 1000)
          return () => clearTimeout(timer)
        } else {
          setError(null)
        }
      }
    }
  }, [error])

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!fullName.trim()) {
      setError("Please enter your full name")
      return
    }

    // Validate email domain
    const validation = validateEmailDomain(email)
    if (!validation.isValid) {
      setError(validation.error || "Invalid email domain")
      return
    }

    setLoading(true)

    try {
      // Send OTP code (6-digit) instead of magic link
      // No redirect URL needed - user will enter code manually
      const { error: signInError } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: true,
          data: {
            full_name: fullName,
          },
          // Don't set emailRedirectTo - we'll use code entry instead
        },
      })

      if (signInError) {
        throw signInError
      }

      setStep("code")
    } catch (err: any) {
      setError(err.message || "Failed to send OTP code")
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (code.length !== 6) {
      setError("Please enter a 6-digit code")
      return
    }

    setLoading(true)

    try {
      const { data, error: verifyError } = await supabase.auth.verifyOtp({
        email,
        token: code,
        type: "email",
      })

      if (verifyError) {
        throw verifyError
      }

      if (data.session) {
        console.log("✅ Code verified! User logged in:", data.session.user.email)
        // Auth state will update automatically via useAuth hook
      }
    } catch (err: any) {
      setError(err.message || "Invalid code. Please try again.")
      setCode("") // Clear code on error
    } finally {
      setLoading(false)
    }
  }

  if (step === "code") {
    return (
      <Card className="w-full max-w-md mx-auto border-white/10 bg-slate-950/40 backdrop-blur-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CardContent className="pt-6 space-y-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-purple-500/10 flex items-center justify-center ring-1 ring-purple-500/20">
              <KeyRound className="w-8 h-8 text-purple-400" />
            </div>
            <div className="text-center space-y-1">
              <h2 className="text-xl font-semibold text-white">Check your email</h2>
              <p className="text-slate-300 text-sm">
                We sent a 6-digit code to <br/>
                <span className="text-purple-300 font-medium">{email}</span>
              </p>
            </div>
          </div>

          <form onSubmit={handleVerifyCode} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="code" className="sr-only">
                Verification Code
              </Label>
              <Input
                id="code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={code}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, "").slice(0, 6)
                  setCode(value)
                  setError(null)
                }}
                placeholder="000000"
                required
                autoFocus
                className="w-full px-4 py-6 text-center text-3xl font-mono tracking-[0.5em] bg-slate-900/50 border-slate-700/50 rounded-xl focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:border-transparent text-white placeholder:text-slate-500 transition-all h-auto backdrop-blur-sm [&:-webkit-autofill]:shadow-[0_0_0px_1000px_#0f172a_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:white]"
                disabled={loading}
              />
            </div>

            {error && (
              <Alert variant="destructive" className="bg-red-900/50 border-red-500/50 text-white border backdrop-blur-sm">
                <AlertDescription className="font-medium">{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={loading || code.length !== 6}
              className="w-full py-6 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/20 text-base"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Verifying...
                </>
              ) : (
                "Verify Code"
              )}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setStep("email")
                setCode("")
                setError(null)
              }}
              className="w-full text-sm text-slate-300 hover:text-white hover:bg-transparent transition-colors"
            >
              ← Use a different email
            </Button>
          </form>
        </CardContent>
      </Card>
    )
  }

  const handleMicrosoftLogin = async () => {
    setLoading(true)
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'azure',
        options: {
          scopes: 'email',
          redirectTo: typeof chrome !== 'undefined' && chrome.identity ? chrome.identity.getRedirectURL() : undefined,
        },
      })
      if (error) throw error
    } catch (err: any) {
      setError(err.message || "Failed to sign in with Microsoft")
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto border-white/10 bg-slate-950/40 backdrop-blur-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <CardContent className="pt-6">
        <form onSubmit={handleSendCode} className="flex flex-col space-y-5">
          <div className="space-y-1">
            <Label htmlFor="fullName" className="text-xs font-medium text-slate-300 uppercase tracking-wider ml-1">
              Name
            </Label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none z-10">
                <User className="h-5 w-5 text-slate-400 group-focus-within:text-purple-400 transition-colors" />
              </div>
              <Input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                spellCheck={false}
                autoCorrect="off"
                className="w-full pl-10 pr-4 py-6 bg-slate-900/50 border-slate-700/50 rounded-xl focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:border-transparent text-white placeholder:text-slate-400 transition-all h-auto backdrop-blur-sm [&:-webkit-autofill]:shadow-[0_0_0px_1000px_#0f172a_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:white_!important]"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <Label htmlFor="email" className="text-xs font-medium text-slate-300 uppercase tracking-wider ml-1">
              Email Address
            </Label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none z-10">
                <Mail className="h-5 w-5 text-slate-400 group-focus-within:text-purple-400 transition-colors" />
              </div>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@my.centennialcollege.ca"
                required
                spellCheck={false}
                autoCorrect="off"
                autoCapitalize="off"
                className="w-full pl-10 pr-4 py-6 bg-slate-900/50 border-slate-700/50 rounded-xl focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:border-transparent text-white placeholder:text-slate-400 transition-all h-auto backdrop-blur-sm [&:-webkit-autofill]:shadow-[0_0_0px_1000px_#0f172a_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:white_!important]"
                disabled={loading}
              />
            </div>
            <p className="text-[10px] text-slate-400 ml-1">
              Must use <span className="text-slate-300">@my.centennialcollege.ca</span> or <span className="text-slate-300">@centennialcollege.ca</span>
            </p>
          </div>

          {error && (
            <Alert variant="destructive" className="bg-red-900/50 border-red-500/50 text-white border backdrop-blur-sm">
              <AlertDescription className="font-medium">{error}</AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            disabled={loading || !email}
            className="w-full py-6 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/20 mt-2 text-base"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Sending code...
              </>
            ) : (
              <>
                Continue
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-700/50" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-transparent px-2 text-slate-400 backdrop-blur-sm">Or continue with</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleMicrosoftLogin}
            disabled={loading}
            className="w-full py-6 bg-slate-900/50 border-slate-700/50 text-white hover:bg-slate-800/50 hover:text-white rounded-xl transition-all h-auto backdrop-blur-sm"
          >
            <svg className="mr-2 h-5 w-5" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 1H1V10H10V1Z" fill="#F25022"/>
              <path d="M20 1H11V10H20V1Z" fill="#7FBA00"/>
              <path d="M10 11H1V20H10V11Z" fill="#00A4EF"/>
              <path d="M20 11H11V20H20V11Z" fill="#FFB900"/>
            </svg>
            Microsoft
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

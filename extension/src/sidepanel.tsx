"use client"
import { useState } from "react"
import { useAuth } from "~/hooks/useAuth"
import { LoginForm } from "~/components/auth/LoginForm"
import { Conversation } from "~/components/chat/conversation"
import { PromptInput } from "~/components/chat/prompt-input"
import { NavRail } from "~/components/nav-rail"
import useChat from "~/hooks/use-chat"
import { ThemeProvider } from "~/components/theme-provider"
import type { User, Session } from "@supabase/supabase-js"
import "./style.css"

function AuthenticatedChatView({ user, session }: { user: User; session: Session }) {
  const { messages, append, isLoading } = useChat(session)
  const [input, setInput] = useState("")

  const handleSendMessage = async (content: string, attachments?: File[]) => {
    append({
      role: "user",
      content,
      attachments,
    })
  }

  const handleExportChat = () => {
    if (messages.length === 0) return
    
    const now = new Date()
    const dateStr = now.toISOString().split('T')[0]
    const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-')
    
    // Build markdown content
    let markdown = `# Chat Export - COMP 237\n`
    markdown += `**Date:** ${now.toLocaleDateString()}\n`
    markdown += `**User:** ${user.email}\n\n---\n\n`
    
    for (const msg of messages) {
      const role = msg.role === 'user' ? '## 👤 You' : '## 🤖 Tutor'
      markdown += `${role}\n\n${msg.content}\n\n`
      
      // Include sources if present
      if (msg.sources && msg.sources.length > 0) {
        markdown += `**Sources:**\n`
        for (const source of msg.sources) {
          markdown += `- ${source.file || source.source || 'Course Material'}\n`
        }
        markdown += '\n'
      }
      
      markdown += `---\n\n`
    }
    
    // Download as .md file
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `luminate-chat-${dateStr}-${timeStr}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="relative flex h-screen w-full bg-slate-950 text-slate-50 overflow-hidden font-sans antialiased transition-colors duration-300">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative pr-[54px]">
        {/* Conversation Area */}
        <div className="flex-1 overflow-hidden relative">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 pb-32 max-w-3xl mx-auto">
              <div className="space-y-6 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="flex items-center justify-center mb-4">
                  <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-violet-500/20 ring-1 ring-white/10">
                    <span className="text-2xl font-bold text-white">L</span>
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-semibold text-slate-50 mb-2 tracking-tight">
                    Hi, {user.user_metadata?.full_name?.split(' ')[0] || user.email?.split('@')[0]}
                  </h1>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    Ask anything about your courses, assignments, or learning materials
                  </p>
                </div>
                
                {/* Suggestion Chips */}
                <div className="flex flex-wrap gap-2 justify-center pt-4">
                  <button
                    onClick={() => handleSendMessage("Review my Linear Algebra quiz")}
                    className="px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900/80 border border-slate-800 rounded-full hover:bg-slate-800/80 hover:text-slate-100 transition-colors"
                  >
                    Review my Linear Algebra quiz
                  </button>
                  <button
                    onClick={() => handleSendMessage("Explain gradient descent with examples")}
                    className="px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900/80 border border-slate-800 rounded-full hover:bg-slate-800/80 hover:text-slate-100 transition-colors"
                  >
                    Explain gradient descent with examples
                  </button>
                  <button
                    onClick={() => handleSendMessage("Create flashcards for COMP 237")}
                    className="px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900/80 border border-slate-800 rounded-full hover:bg-slate-800/80 hover:text-slate-100 transition-colors"
                  >
                    Create flashcards for COMP 237
                  </button>
                  <button
                    onClick={() => handleSendMessage("Debug this Python ML code")}
                    className="px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900/80 border border-slate-800 rounded-full hover:bg-slate-800/80 hover:text-slate-100 transition-colors"
                  >
                    Debug this Python ML code
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <Conversation messages={messages} isLoading={isLoading} />
          )}
        </div>

        {/* Input Area - Sticky Bottom */}
        <div className="shrink-0 w-full bg-gradient-to-t from-slate-950 via-slate-950 to-transparent pt-16 pb-10 px-6">
          <PromptInput
            input={input}
            setInput={setInput}
            onSend={handleSendMessage}
            isLoading={isLoading}
            onExport={handleExportChat}
            hasMessages={messages.length > 0}
          />
        </div>
      </div>

      {/* Right Navigation Rail */}
      <NavRail />
    </div>
  )
}


import { GradientBackground } from "~/components/ui/gradient-background"

function IndexSidepanel() {
  const { user, role, loading, session } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="relative flex flex-col h-screen dark font-sans overflow-hidden">
        <GradientBackground />
        <div className="relative z-10 flex flex-col h-full">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-slate-50 mb-2">Luminate AI</h1>
            <p className="text-sm text-slate-400">Sign in to continue</p>
          </div>
          <div className="flex-1 overflow-auto flex items-center justify-center p-4">
            <LoginForm />
          </div>
        </div>
      </div>
    )
  }

  if (role === "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-4 bg-slate-950">
        <p className="text-slate-400 mb-4">
          Admin access detected. Please use the Admin Dashboard.
        </p>
        <button
          onClick={() => {
            chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT })
          }}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Open Admin Dashboard
        </button>
      </div>
    )
  }

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <AuthenticatedChatView user={user} session={session} />
    </ThemeProvider>
  )
}

export default IndexSidepanel
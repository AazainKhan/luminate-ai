"use client"
import { useState } from "react"
import { Conversation } from "@/components/chat/conversation"
import { PromptInput } from "@/components/chat/prompt-input"
import { NavRail } from "@/components/nav-rail"
import useChat from "@/hooks/use-chat" // Use the hook

export default function SidePanelPage() {
  const { messages, append, isLoading } = useChat() // Use hook
  const [input, setInput] = useState("")

  const handleSendMessage = async (content: string, attachments?: File[]) => {
    append({
      id: Date.now().toString(),
      role: "user",
      content,
      attachments,
    })
  }

  return (
    <div className="flex h-screen w-full bg-[#15161e] overflow-hidden dark font-sans">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Conversation Area */}
        <div className="flex-1 overflow-hidden relative">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-start justify-center p-8 pb-32">
              <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">Hi,</h1>
              <p className="text-lg text-gray-400 mb-8">How can I assist you today?</p>
            </div>
          ) : (
            <Conversation messages={messages} isLoading={isLoading} />
          )}
        </div>

        {/* Input Area - Sticky Bottom */}
        <div className="shrink-0 w-full bg-[#15161e]">
          <PromptInput
            input={input}
            setInput={setInput}
            onSend={handleSendMessage}
            isLoading={isLoading}
            toggleHistory={() => {}}
          />
        </div>
      </div>

      {/* Right Navigation Rail */}
      <NavRail />
    </div>
  )
}

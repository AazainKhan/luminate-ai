"use client"

import { useState } from "react"
import type { Message } from "../types"

const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const append = async (message: Message) => {
    setIsLoading(true)
    setMessages((prev) => [...prev, message])

    const contentLower = message.content.toLowerCase()

    setTimeout(() => {
      let assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I'm processing your request...",
      }

      if (contentLower.includes("plan study")) {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Here is a study plan for you:",
          tasks: [
            { title: "Analyze current knowledge", status: "completed" },
            { title: "Identify key gaps", status: "in_progress" },
            { title: "Create schedule", status: "pending" },
          ],
        }
      } else if (contentLower.includes("reason")) {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Here is my reasoning for this problem.",
          reasoning:
            "I need to approach this step-by-step.\n1. First, analyze the constraints.\n2. Second, evaluate potential solutions.\n3. Finally, select the optimal path.",
        }
      } else if (contentLower.includes("code")) {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Here is the code you requested:",
          codeBlocks: [
            {
              language: "python",
              code: "def hello_world():\n    print('Hello, World!')",
            },
          ],
        }
      } else if (contentLower.includes("sources")) {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "I found several sources relevant to your query.",
          sources: [
            { title: "React Documentation", url: "https://react.dev", description: "Official React docs" },
            { title: "Next.js Documentation", url: "https://nextjs.org", description: "Official Next.js docs" },
          ],
        }
      } else {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I'm Luminate AI, your agentic tutor. I can help you understand course materials, research topics, debug code, and solve complex problems using advanced reasoning.",
        }
      }

      setMessages((prevMessages) => [...prevMessages, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  return {
    messages,
    append,
    setMessages,
    isLoading,
  }
}

export default useChat

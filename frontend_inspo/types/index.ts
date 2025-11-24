export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  reasoning?: string
  sources?: Array<{ title: string; url: string; description: string }>
  attachments?: File[]
  tasks?: Array<{ title: string; status: "pending" | "in-progress" | "completed" }>
  tools?: Array<{
    name: string
    args?: Record<string, any>
    result?: any
    status: "pending" | "in-progress" | "completed" | "error"
  }>
  codeBlocks?: Array<{ language: string; code: string }>
  images?: Array<{ src: string; alt: string; caption?: string }>
  citations?: Array<{
    number: string
    text: string
    url: string
    title: string
    description?: string
    quote?: string
  }>
  suggestions?: string[]
}

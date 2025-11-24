"use client"

import { useState } from "react"
import { Copy, RotateCcw, Check, ThumbsUp, ThumbsDown, MoreHorizontal, Flag, Volume2, Pencil } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Reasoning, ReasoningTrigger, ReasoningContent } from "@/components/ai-elements/reasoning"
import { Sources, SourcesTrigger, SourcesContent, Source } from "@/components/ai-elements/sources"
import { Response } from "@/components/ai-elements/response"
import { cn } from "@/lib/utils"
import { CodeBlock, CodeBlockCopyButton } from "@/components/ai-elements/code-block"
import { Task, TaskTrigger, TaskContent, TaskItem } from "@/components/ai-elements/task"
import { Tool } from "@/components/ai-elements/tool"
import { AIImage } from "@/components/ai-elements/image"
import {
  InlineCitation,
  InlineCitationText,
  InlineCitationCard,
  InlineCitationCardTrigger,
  InlineCitationCardBody,
  InlineCitationSource,
  InlineCitationQuote,
} from "@/components/ai-elements/inline-citation"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { Message as MessageType } from "../../types"

interface MessageProps {
  message: MessageType
}

export function Message({ message }: MessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === "user"

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <TooltipProvider>
      <MessageContent message={message} copied={copied} handleCopy={handleCopy} isUser={isUser} />
    </TooltipProvider>
  )
}

function MessageContent({ message, copied, handleCopy, isUser }: { message: MessageType, copied: boolean, handleCopy: () => void, isUser: boolean }) {

  const renderContentWithCitations = (content: string) => {
    if (!message.citations || message.citations.length === 0) {
      return content
    }
    const parts = content.split(/(\[\d+\])/)
    return (
      <InlineCitation>
        {parts.map((part, index) => {
          const match = part.match(/\[(\d+)\]/)
          if (match) {
            const citationNumber = match[1]
            const citation = message.citations?.find((c) => c.number === citationNumber)
            if (citation) {
              return (
                <InlineCitationCard key={index}>
                  <InlineCitationCardTrigger number={citation.number} url={citation.url} />
                  <InlineCitationCardBody>
                    <InlineCitationSource
                      title={citation.title}
                      url={citation.url}
                      description={citation.description}
                    />
                    {citation.quote && <InlineCitationQuote>{citation.quote}</InlineCitationQuote>}
                  </InlineCitationCardBody>
                </InlineCitationCard>
              )
            }
          }
          return <InlineCitationText key={index}>{part}</InlineCitationText>
        })}
      </InlineCitation>
    )
  }

  return (
    <div
      className={cn(
        "flex w-full gap-4 group transition-colors animate-in fade-in slide-in-from-bottom-2 duration-300",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-violet-500/30 text-violet-300 ring-1 ring-violet-500/20">
          <span className="text-xs font-bold">L</span>
        </div>
      )}
      
      <div className={cn("space-y-2 overflow-hidden", isUser ? "flex flex-col items-end max-w-[70%]" : "flex-1 min-w-0")}>
        <div
          className={cn(
            "relative",
            isUser 
              ? "bg-violet-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-md" 
              : "bg-slate-900/50 border border-slate-800/50 backdrop-blur-sm rounded-2xl rounded-tl-sm px-4 py-3 text-slate-100 shadow-sm",
          )}
        >
          {!isUser && message.reasoning && (
            <Reasoning>
              <ReasoningTrigger />
              <ReasoningContent>{message.reasoning}</ReasoningContent>
            </Reasoning>
          )}

          {!isUser && message.tasks && message.tasks.length > 0 && (
            <Task defaultOpen>
              <TaskTrigger title="Processing Request" />
              <TaskContent>
                {message.tasks.map((task, i) => (
                  <TaskItem key={i} status={task.status}>
                    {task.title}
                  </TaskItem>
                ))}
              </TaskContent>
            </Task>
          )}

          {!isUser && message.tools && message.tools.length > 0 && (
            <div className="space-y-2 mb-3">
              {message.tools.map((tool, i) => (
                <Tool key={i} name={tool.name} args={tool.args} result={tool.result} status={tool.status} />
              ))}
            </div>
          )}

          {/* Main content */}
          {isUser ? (
            <p className="text-sm leading-snug whitespace-pre-wrap tracking-tight">
              {message.content}
            </p>
          ) : (
            <Response>
              {message.citations ? String(renderContentWithCitations(message.content)) : message.content}
            </Response>
          )}

          {!isUser && message.codeBlocks && message.codeBlocks.length > 0 && (
            <div className="space-y-3 mt-3">
              {message.codeBlocks.map((block, i) => (
                <CodeBlock key={i} code={block.code} language={block.language} showLineNumbers>
                  <CodeBlockCopyButton code={block.code} />
                </CodeBlock>
              ))}
            </div>
          )}

          {!isUser && message.images && message.images.length > 0 && (
            <div className="space-y-3 mt-3">
              {message.images.map((img, i) => (
                <AIImage key={i} src={img.src} alt={img.alt} caption={img.caption} />
              ))}
            </div>
          )}

          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {message.attachments.map((file, i) => (
                <div key={i} className="px-2 py-1 rounded bg-white/10 text-xs text-gray-300">
                  {file.name}
                </div>
              ))}
            </div>
          )}

          {!isUser && message.sources && message.sources.length > 0 && (
            <Sources>
              <SourcesTrigger count={message.sources.length} />
              <SourcesContent>
                {message.sources.map((source, i) => (
                  <Source key={i} title={source.title} href={source.url} />
                ))}
              </SourcesContent>
            </Sources>
          )}
        </div>

        {isUser && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-white"
              onClick={handleCopy}
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-white">
              <Pencil className="w-3 h-3" />
            </Button>
          </div>
        )}

        {!isUser && (
          <div className="flex items-center gap-1 pt-1 transition-opacity">
            {/* Feedback row with Was this helpful? */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Was this helpful?</span>
              <div className="flex gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-slate-500 hover:text-green-400 hover:bg-green-400/10"
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Good response</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-slate-500 hover:text-red-400 hover:bg-red-400/10"
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Bad response</TooltipContent>
                </Tooltip>
              </div>
            </div>
            
            <div className="flex-1" />
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-slate-500 hover:text-slate-300"
                  onClick={handleCopy}
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied!" : "Copy"}</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-slate-300">
                  <RotateCcw className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Regenerate</TooltipContent>
            </Tooltip>

            <DropdownMenu>
              <Tooltip>
                <TooltipTrigger asChild>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-slate-500 hover:text-slate-300"
                    >
                      <MoreHorizontal className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                </TooltipTrigger>
                <TooltipContent>More options</TooltipContent>
              </Tooltip>
              <DropdownMenuContent align="start" className="w-48 bg-slate-900 border-slate-800">
                <DropdownMenuItem className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
                  <Flag className="w-4 h-4 mr-2" />
                  Report Message
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
                  <Volume2 className="w-4 h-4 mr-2" />
                  Read Aloud
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </div>
  )
}

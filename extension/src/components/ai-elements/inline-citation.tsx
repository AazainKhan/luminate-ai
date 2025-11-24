"use client"

import type React from "react"

import { ExternalLink } from "lucide-react"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"

interface InlineCitationProps {
  children: React.ReactNode
}

export function InlineCitation({ children }: InlineCitationProps) {
  return <span className="inline">{children}</span>
}

interface InlineCitationTextProps {
  children: React.ReactNode
}

export function InlineCitationText({ children }: InlineCitationTextProps) {
  return <span>{children}</span>
}

interface InlineCitationCardProps {
  children: React.ReactNode
}

export function InlineCitationCard({ children }: InlineCitationCardProps) {
  return <HoverCard openDelay={200}>{children}</HoverCard>
}

interface InlineCitationCardTriggerProps {
  number: string
  url: string
}

export function InlineCitationCardTrigger({ number, url }: InlineCitationCardTriggerProps) {
  const hostname = new URL(url).hostname.replace("www.", "")

  return (
    <HoverCardTrigger asChild>
      <button className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-colors mx-0.5">
        [{number}]
      </button>
    </HoverCardTrigger>
  )
}

interface InlineCitationCardBodyProps {
  children: React.ReactNode
}

export function InlineCitationCardBody({ children }: InlineCitationCardBodyProps) {
  return <HoverCardContent className="w-80 bg-[#1e1f2e] border-white/10 p-4">{children}</HoverCardContent>
}

interface InlineCitationSourceProps {
  title: string
  url: string
  description?: string
}

export function InlineCitationSource({ title, url, description }: InlineCitationSourceProps) {
  const hostname = new URL(url).hostname.replace("www.", "")

  return (
    <div className="space-y-2">
      <div className="flex items-start gap-2">
        <ExternalLink className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-white hover:text-blue-400 line-clamp-2"
          >
            {title}
          </a>
          <p className="text-xs text-gray-400 mt-0.5">{hostname}</p>
        </div>
      </div>
      {description && <p className="text-xs text-gray-300 leading-relaxed">{description}</p>}
    </div>
  )
}

interface InlineCitationQuoteProps {
  children: React.ReactNode
}

export function InlineCitationQuote({ children }: InlineCitationQuoteProps) {
  return (
    <blockquote className="mt-3 pl-3 border-l-2 border-blue-500/50 text-xs italic text-gray-400">{children}</blockquote>
  )
}

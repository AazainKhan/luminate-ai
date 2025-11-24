"use client"

import type React from "react"

import { Search, Trash2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface ChatHistoryProps {
  onClose: () => void
}

export function ChatHistory({ onClose }: ChatHistoryProps) {
  return (
    <div className="w-[350px] h-full bg-[#15161e] border-r border-border/40 flex flex-col">
      <div className="p-4 flex items-center justify-between border-b border-border/40">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          Chat history <span className="text-muted-foreground text-sm font-normal">(5)</span>
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="h-8 w-8 text-muted-foreground hover:text-white"
        >
          <X className="w-5 h-5" />
        </Button>
      </div>

      <div className="p-4 space-y-4">
        <div className="bg-[#1e1f2e] rounded-xl p-4 border border-border/40">
          <div className="flex items-center gap-2 mb-3">
            <SmartphoneIcon className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-white">Sync chats across devices</span>
          </div>
          <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg h-9 text-sm font-medium">
            Get app
          </Button>
        </div>

        <div className="flex items-center gap-6 border-b border-border/40 px-1">
          <button className="pb-2 text-sm font-medium text-white border-b-2 border-white">All</button>
          <button className="pb-2 text-sm font-medium text-muted-foreground hover:text-gray-300">Starred</button>
          <div className="ml-auto pb-2">
            <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground">
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search"
            className="pl-9 bg-[#1e1f2e] border-border/40 text-white placeholder:text-muted-foreground focus-visible:ring-indigo-500/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 pt-0 space-y-6">
        <div>
          <h3 className="text-xs font-medium text-muted-foreground mb-3">Today</h3>
          <div className="space-y-1">
            <HistoryItem
              title="Explain Codes"
              preview="Here is a clean, concise explanation of what the code does..."
            />
            <HistoryItem title="Summarize" preview="### Key Concepts Analysis - **Pre-processing in NLP..." />
          </div>
        </div>

        <div>
          <h3 className="text-xs font-medium text-muted-foreground mb-3">Earlier</h3>
          <div className="space-y-1">
            <HistoryItem title="how to make a chrome sidebar" preview="# How to Make an Extension Like Sider..." />
            <HistoryItem title="Summarize" preview="# Summary - **Course status**: Open, with progress..." />
            <HistoryItem title="Summarize" preview="### Abstract This document discusses Stanford's..." />
          </div>
        </div>
      </div>
    </div>
  )
}

function HistoryItem({ title, preview }: { title: string; preview: string }) {
  return (
    <button className="w-full text-left p-3 rounded-xl hover:bg-white/5 transition-colors group">
      <div className="font-medium text-gray-200 mb-1 group-hover:text-indigo-300 transition-colors">{title}</div>
      <div className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{preview}</div>
    </button>
  )
}

function SmartphoneIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="14" height="20" x="5" y="2" rx="2" ry="2" />
      <path d="M12 18h.01" />
    </svg>
  )
}

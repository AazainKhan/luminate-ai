"use client"

import type React from "react"

import { useState } from "react"
import {
  Settings,
  Plus,
  Folder,
  Star,
  Search,
  ChevronRight,
  User,
  LogOut,
  ExternalLink,
  HelpCircle,
  Sun,
  Moon,
  PanelLeftOpen,
  PanelLeftClose,
  ChevronDown,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { useTheme } from "next-themes"

export function NavRail() {
  const [isExpanded, setIsExpanded] = useState(false)
  const { theme, setTheme } = useTheme()

  return (
    <div
      className={cn(
        "h-screen bg-[#0f1016] flex flex-col border-r border-border/30 shrink-0 transition-all duration-300 ease-in-out",
        isExpanded ? "w-[280px]" : "w-[60px]",
      )}
    >
      {/* Header */}
      {isExpanded ? (
        <div className="p-3 space-y-3 border-b border-border/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-indigo-500">
              <div className="h-6 w-6 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-xs">
                L
              </div>
              <span className="font-bold text-white tracking-tight">Luminate AI</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-white"
              onClick={() => setIsExpanded(false)}
            >
              <PanelLeftClose className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="Search chats..."
                className="pl-8 h-8 bg-[#1e1f2e] border-border/40 text-xs text-gray-200 placeholder:text-muted-foreground"
              />
            </div>
            <Button size="icon" className="h-8 w-8 bg-indigo-600 hover:bg-indigo-500 text-white shrink-0">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>
      ) : (
        <div className="p-3 flex flex-col items-center gap-3 border-b border-border/30">
          <div className="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            L
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-white"
            onClick={() => setIsExpanded(true)}
          >
            <PanelLeftOpen className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-white/5"
            onClick={() => setIsExpanded(true)}
          >
            <Plus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-white/5"
            onClick={() => setIsExpanded(true)}
          >
            <Search className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {isExpanded ? (
          <div className="px-2 py-2 space-y-1">
            <div className="pt-2">
              <div className="px-2 text-xs font-semibold text-muted-foreground mb-1">Recent</div>
              <ChatItem title="Spanish Conversation Practice" time="3d ago" />
              <ChatItem title="Linear Algebra Review" time="1w ago" starred />
            </div>
          </div>
        ) : (
          <div className="py-4 flex flex-col items-center gap-4"></div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border/30 bg-[#0f1016]">
        <div className={cn("p-3 flex flex-col gap-3", isExpanded ? "items-start" : "items-center")}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-10 w-10 text-muted-foreground hover:text-white">
                <Settings className="w-5 h-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="right" className="w-64 bg-[#1e1f2e] border-border/40 ml-2">
              <div className="p-2">
                <div className="flex items-center justify-between py-2 px-2">
                  <Label htmlFor="theme-toggle" className="text-sm font-medium text-gray-200">
                    Theme
                  </Label>
                  <div className="flex items-center gap-2">
                    <Sun className="w-4 h-4 text-muted-foreground" />
                    <Switch
                      id="theme-toggle"
                      checked={theme === "dark"}
                      onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
                    />
                    <Moon className="w-4 h-4 text-muted-foreground" />
                  </div>
                </div>
              </div>
              <DropdownMenuSeparator className="bg-border/40" />
              <DropdownMenuItem className="cursor-pointer text-gray-200 focus:bg-white/5 focus:text-white">
                <ExternalLink className="w-4 h-4 mr-2" />
                Luminate AI Settings
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer text-gray-200 focus:bg-white/5 focus:text-white">
                <HelpCircle className="w-4 h-4 mr-2" />
                Help Center
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-semibold text-xs cursor-pointer">
                JD
              </div>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="right" className="w-64 bg-[#1e1f2e] border-border/40 ml-2 mb-2">
              <div className="flex items-center gap-3 p-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm shrink-0">
                  JD
                </div>
                <div className="flex flex-col overflow-hidden">
                  <span className="text-sm font-medium text-white truncate">John Doe</span>
                  <span className="text-xs text-muted-foreground truncate">johndoe@email.com</span>
                </div>
              </div>
              <DropdownMenuSeparator className="bg-border/40" />
              <DropdownMenuItem className="cursor-pointer text-gray-200 focus:bg-white/5 focus:text-white">
                <User className="w-4 h-4 mr-2" />
                Personalisation
                <ExternalLink className="w-3 h-3 ml-auto opacity-50" />
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer text-rose-400 focus:bg-rose-500/10 focus:text-rose-400">
                <LogOut className="w-4 h-4 mr-2" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}

function ChatFolderItem({
  name,
  starred,
  children,
}: {
  name: string
  starred?: boolean
  children: React.ReactNode
}) {
  const [isOpen, setIsOpen] = useState(true)

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-gray-300 hover:bg-white/5 hover:text-white transition-colors group"
      >
        {isOpen ? (
          <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
        )}
        <Folder className={cn("w-4 h-4 shrink-0", isOpen ? "text-indigo-400" : "text-muted-foreground")} />
        <span className="flex-1 text-left font-medium truncate">{name}</span>
        {starred && <Star className="w-3 h-3 fill-yellow-500 text-yellow-500 shrink-0" />}
      </button>
      {isOpen && <div className="ml-2 pl-2 border-l border-white/5 mt-1 space-y-1">{children}</div>}
    </div>
  )
}

function ChatItem({ title, time, starred }: { title: string; time: string; starred?: boolean }) {
  return (
    <div className="group relative px-2 py-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm text-gray-300 group-hover:text-white line-clamp-2 leading-tight">{title}</span>
        {starred && <Star className="w-3 h-3 fill-yellow-500 text-yellow-500 shrink-0 mt-0.5" />}
      </div>
      <div className="mt-1 text-[10px] text-muted-foreground">{time}</div>
    </div>
  )
}

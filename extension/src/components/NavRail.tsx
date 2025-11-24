"use client"

import * as React from "react"

import { useState } from "react"
import {
  Settings,
  Plus,
  Search,
  User,
  LogOut,
  ExternalLink,
  HelpCircle,
  PanelLeftOpen,
  PanelLeftClose,
} from "lucide-react"
import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Input } from "~/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import { useAuth } from "~/hooks/useAuth"

export function NavRail() {
  const [isExpanded, setIsExpanded] = useState(false)
  const { user } = useAuth()

  return (
    <div
      className={cn(
        "h-screen bg-[#0f1016] flex flex-col border-l border-border/30 shrink-0 transition-all duration-300 ease-in-out",
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
              {/* Chat items would go here */}
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
                {user?.email?.[0]?.toUpperCase() || "U"}
              </div>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="right" className="w-64 bg-[#1e1f2e] border-border/40 ml-2 mb-2">
              <div className="flex items-center gap-3 p-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm shrink-0">
                  {user?.email?.[0]?.toUpperCase() || "U"}
                </div>
                <div className="flex flex-col overflow-hidden">
                  <span className="text-sm font-medium text-white truncate">User</span>
                  <span className="text-xs text-muted-foreground truncate">{user?.email || "user@example.com"}</span>
                </div>
              </div>
              <DropdownMenuSeparator className="bg-border/40" />
              <DropdownMenuItem className="cursor-pointer text-gray-200 focus:bg-white/5 focus:text-white">
                <User className="w-4 h-4 mr-2" />
                Profile
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


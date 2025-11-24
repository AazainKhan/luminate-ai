"use client"

import type React from "react"
import { Zap, Brain, FlaskConical, Globe, Navigation, BookOpen, Upload, Settings } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

export function ChatControls() {
  return (
    <div className="w-[320px] bg-[#1e1f2e] rounded-2xl border border-border/40 shadow-xl overflow-hidden">
      <div className="p-4 border-b border-border/40">
        <h2 className="text-lg font-semibold text-white">Chat controls</h2>
      </div>

      <div className="p-2">
        <div className="px-3 py-2">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Model Mode</h3>

          <div className="space-y-4">
            <ModeItem
              icon={Zap}
              label="Fast"
              subtitle="Llama 3.1 via Groq"
              color="text-yellow-400"
              description="Instant responses"
            />
            <ModeItem
              icon={Brain}
              label="Thorough"
              subtitle="Claude 3.5 Sonnet"
              color="text-purple-400"
              description="Deep analysis"
              defaultChecked
            />
            <ModeItem
              icon={FlaskConical}
              label="Reason"
              subtitle="OpenAI o1"
              color="text-blue-400"
              description="Complex reasoning"
            />
          </div>
        </div>

        <div className="px-3 py-2 mt-4">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
            Tutor Capabilities
          </h3>

          <div className="space-y-4">
            <ControlItem icon={Globe} label="Internet Search" color="text-indigo-400" defaultChecked />
            <ControlItem icon={Navigation} label="Navigate" color="text-emerald-400" />
            <ControlItem icon={BookOpen} label="Course Context" color="text-orange-400" defaultChecked />
          </div>
        </div>

        <div className="px-3 py-2 mt-4">
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Admin</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between opacity-50 cursor-not-allowed">
              <div className="flex items-center gap-3">
                <div className={cn("p-1.5 rounded-lg bg-white/5")}>
                  <Upload className="w-4 h-4 text-rose-400" />
                </div>
                <span className="text-sm text-gray-200 font-medium">Course Upload</span>
              </div>
              <Settings className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface ModeItemProps {
  icon: React.ElementType
  label: string
  subtitle: string
  color?: string
  description: string
  defaultChecked?: boolean
}

function ModeItem({ icon: Icon, label, subtitle, color, description, defaultChecked }: ModeItemProps) {
  return (
    <div className="flex items-center justify-between group cursor-pointer hover:bg-white/5 rounded-lg p-2 -mx-2 transition-colors">
      <div className="flex items-center gap-3">
        <div className={cn("p-1.5 rounded-lg bg-white/5")}>
          <Icon className={cn("w-4 h-4", color)} />
        </div>
        <div className="flex flex-col">
          <span className="text-sm text-gray-200 font-medium">{label}</span>
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        </div>
      </div>

      <input
        type="radio"
        name="model-mode"
        defaultChecked={defaultChecked}
        className="w-4 h-4 accent-white cursor-pointer"
      />
    </div>
  )
}

interface ControlItemProps {
  icon: React.ElementType
  label: string
  color?: string
  defaultChecked?: boolean
}

function ControlItem({ icon: Icon, label, color, defaultChecked }: ControlItemProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={cn("p-1.5 rounded-lg bg-white/5")}>
          <Icon className={cn("w-4 h-4", color)} />
        </div>
        <span className="text-sm text-gray-200 font-medium">{label}</span>
      </div>

      <Switch defaultChecked={defaultChecked} className="data-[state=checked]:bg-white" />
    </div>
  )
}

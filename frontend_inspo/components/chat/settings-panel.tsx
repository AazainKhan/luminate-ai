"use client"

import { Globe, Navigation } from "lucide-react"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card } from "@/components/ui/card"

interface SettingsPanelProps {
  settings: {
    internetSearch: boolean
    navigate: boolean
  }
  onSettingsChange: (settings: any) => void
  onClose: () => void
}

export function SettingsPanel({ settings, onSettingsChange, onClose }: SettingsPanelProps) {
  return (
    <Card className="mx-3 mb-3 p-3 space-y-3 border-border">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Settings</h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-sm">
          Close
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <Label htmlFor="internet-search" className="text-sm cursor-pointer">
              Internet Search
            </Label>
          </div>
          <Switch
            id="internet-search"
            checked={settings.internetSearch}
            onCheckedChange={(checked) => onSettingsChange({ ...settings, internetSearch: checked })}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Navigation className="h-4 w-4 text-muted-foreground" />
            <Label htmlFor="navigate" className="text-sm cursor-pointer">
              Navigate
            </Label>
          </div>
          <Switch
            id="navigate"
            checked={settings.navigate}
            onCheckedChange={(checked) => onSettingsChange({ ...settings, navigate: checked })}
          />
        </div>
      </div>
    </Card>
  )
}

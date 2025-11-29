import React, { useState, useEffect, useMemo } from "react"
import { Popover, PopoverContent, PopoverAnchor } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Folder, Check, ChevronRight, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

type MoveItemPopoverProps = {
  isOpen: boolean
  onClose: () => void
  onMove: (targetFolderId: string | null) => void
  folders: { id: string; label: string; parentId?: string | null }[]
  itemId: string
  anchorRef?: React.RefObject<HTMLElement>
}

type FolderNode = {
  id: string
  label: string
  children: FolderNode[]
}

export function MoveItemPopover({ isOpen, onClose, onMove, folders, itemId, anchorRef }: MoveItemPopoverProps) {
  const [selectedFolderId, setSelectedFolderId] = useState<string | null | "root">(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // Reset state when opening
  useEffect(() => {
    if (isOpen) {
      setSelectedFolderId(null)
      setExpandedFolders(new Set())
    }
  }, [isOpen])
  
  // ... (folderTree logic remains same)

  // ...

  const handleMove = () => {
    if (selectedFolderId === "root") {
      onMove(null)
      onClose()
    } else if (selectedFolderId) {
      onMove(selectedFolderId)
      onClose()
    }
  }

  // ...

  return (
    <Popover open={isOpen} onOpenChange={(open) => !open && onClose()}>
      {anchorRef && <PopoverAnchor virtualRef={anchorRef} />}
      <PopoverContent 
        className="w-64 p-0 bg-slate-900 border-slate-800 text-slate-200 shadow-xl" 
        align="start" 
        side="right"
        sideOffset={5}
      >
        <div className="p-3 border-b border-slate-800">
          <h4 className="font-medium text-sm text-slate-100">Move to...</h4>
        </div>
        
        <ScrollArea className="h-[200px] p-2">
          <div className="space-y-0.5">
            {/* Root Option */}
            <div
              className={cn(
                "flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors text-sm mb-1",
                selectedFolderId === "root" ? "bg-violet-600 text-white" : "hover:bg-slate-800 text-slate-300"
              )}
              onClick={() => setSelectedFolderId("root")}
            >
              <div className="w-4" />
              <Folder className="w-3.5 h-3.5 shrink-0 opacity-50" />
              <span className="truncate flex-1 italic">Root (Top Level)</span>
              {selectedFolderId === "root" && <Check className="w-3.5 h-3.5 ml-auto" />}
            </div>

            {folderTree.length > 0 ? (
              folderTree.map(node => renderFolder(node))
            ) : (
              <div className="text-xs text-slate-500 text-center py-2">
                No other folders available
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-2 border-t border-slate-800 flex justify-end gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose} 
            className="h-7 text-xs text-slate-400 hover:text-slate-200"
          >
            Cancel
          </Button>
          <Button 
            size="sm" 
            onClick={handleMove} 
            disabled={!selectedFolderId}
            className="h-7 text-xs bg-violet-600 hover:bg-violet-500 text-white disabled:opacity-50"
          >
            Move
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

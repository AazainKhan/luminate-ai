import React, { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Folder, MessageSquare, RefreshCw, Trash2 } from "lucide-react"
import { useAuth } from "~/hooks/useAuth"
import { formatDistanceToNow } from "date-fns"
import { ConfirmDialog } from "./confirm-dialog"

type TrashDialogProps = {
  isOpen: boolean
  onClose: () => void
}

type TrashItem = {
  id: string
  name: string
  type: "folder" | "chat"
  deletedAt: string
}

export function TrashDialog({ isOpen, onClose }: TrashDialogProps) {
  const [items, setItems] = useState<TrashItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [itemToDelete, setItemToDelete] = useState<{ id: string, type: "folder" | "chat" } | null>(null)
  
  const { session } = useAuth()
  const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"

  const fetchTrash = async () => {
    if (!session?.access_token) return
    setIsLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/trash`, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        const data = await res.json()
        const trashItems: TrashItem[] = [
          ...data.folders.map((f: any) => ({ id: f.id, name: f.name, type: "folder" as const, deletedAt: f.deleted_at })),
          ...data.chats.map((c: any) => ({ id: c.id, name: c.title, type: "chat" as const, deletedAt: c.deleted_at }))
        ].sort((a, b) => new Date(b.deletedAt).getTime() - new Date(a.deletedAt).getTime())
        setItems(trashItems)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRestore = async (id: string, type: "folder" | "chat") => {
    if (!session?.access_token) return
    try {
      await fetch(`${API_BASE_URL}/api/history/trash/restore/${type}/${id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      setItems(prev => prev.filter(i => i.id !== id))
      window.dispatchEvent(new CustomEvent('history-updated'))
    } catch (e) {
      console.error(e)
    }
  }

  const confirmDelete = async () => {
    if (!itemToDelete || !session?.access_token) return
    try {
      await fetch(`${API_BASE_URL}/api/history/trash/${itemToDelete.type}/${itemToDelete.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      setItems(prev => prev.filter(i => i.id !== itemToDelete.id))
      setItemToDelete(null)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchTrash()
    }
  }, [isOpen])

  return (
    <>
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="sm:max-w-[500px] bg-slate-900 border-slate-800 text-slate-200 z-[150]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-slate-100">
              <Trash2 className="w-5 h-5 text-red-400" />
              Trash
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Items are automatically deleted after 30 days.
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-[300px] mt-4 pr-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-full text-slate-500">Loading...</div>
            ) : items.length > 0 ? (
              <div className="space-y-2">
                {items.map(item => (
                  <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors group border border-slate-800/50">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="p-2 rounded-md bg-slate-800 text-slate-400">
                        {item.type === 'folder' ? (
                          <Folder className="w-4 h-4" />
                        ) : (
                          <MessageSquare className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-sm font-medium text-slate-200 truncate">{item.name}</span>
                        <span className="text-[10px] text-slate-500">
                          Deleted {formatDistanceToNow(new Date(item.deletedAt))} ago
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10"
                        onClick={() => handleRestore(item.id, item.type)}
                        title="Restore"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-slate-400 hover:text-red-400 hover:bg-red-400/10"
                        onClick={() => setItemToDelete({ id: item.id, type: item.type })}
                        title="Delete Forever"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
                <Trash2 className="w-10 h-10 opacity-20" />
                <span className="text-sm">Trash is empty</span>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        isOpen={!!itemToDelete}
        onClose={() => setItemToDelete(null)}
        onConfirm={confirmDelete}
        title="Delete Forever?"
        description="This action cannot be undone. The item will be permanently removed."
        confirmText="Delete Forever"
        variant="destructive"
      />
    </>
  )
}

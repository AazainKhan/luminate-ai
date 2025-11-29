import { useState, useEffect, useCallback } from "react"
import { useAuth } from "./useAuth"
import { MessageSquare, Folder } from "lucide-react"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"

export type HistoryItem = {
  id: string
  label: string
  icon: any
  type: "chat" | "folder"
  hasChildren?: boolean
  createdAt: Date
  editedAt: Date
  folderId?: string | null // For chats
  parentId?: string | null // For folders
  isStarred?: boolean
}

export function useHistory() {
  const { session } = useAuth()
  const [items, setItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async () => {
    if (!session?.access_token) return

    try {
      setIsLoading(true)
      const headers = {
        Authorization: `Bearer ${session.access_token}`,
      }

      // Fetch folders and chats in parallel
      const [foldersRes, chatsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/history/folders`, { headers }),
        fetch(`${API_BASE_URL}/api/history/chats`, { headers }),
      ])

      if (!foldersRes.ok || !chatsRes.ok) {
        throw new Error("Failed to fetch history")
      }

      const folders = await foldersRes.json()
      const chats = await chatsRes.json()

      // Transform to HistoryItem
      const folderItems: HistoryItem[] = folders.map((f: any) => {
        const created = new Date(f.created_at)
        const updated = new Date(f.updated_at || f.created_at)
        return {
          id: f.id,
          label: f.name,
          icon: Folder,
          type: "folder",
          hasChildren: true,
          createdAt: isNaN(created.getTime()) ? new Date() : created,
          editedAt: isNaN(updated.getTime()) ? new Date() : updated,
          parentId: f.parent_id,
          isStarred: f.is_starred
        }
      })

      const chatItems: HistoryItem[] = chats.map((c: any) => {
        const created = new Date(c.created_at)
        const updated = new Date(c.updated_at || c.created_at)
        return {
          id: c.id,
          label: c.title,
          icon: MessageSquare,
          type: "chat",
          createdAt: isNaN(created.getTime()) ? new Date() : created,
          editedAt: isNaN(updated.getTime()) ? new Date() : updated,
          folderId: c.folder_id,
          isStarred: c.is_starred
        }
      })

      setItems([...folderItems, ...chatItems])
      setError(null)
    } catch (err) {
      console.error("Error fetching history:", err)
      setError("Failed to load history")
    } finally {
      setIsLoading(false)
    }
  }, [session])

  // Initial fetch
  useEffect(() => {
    fetchHistory()

    const handleRefresh = () => fetchHistory()
    window.addEventListener('history-updated', handleRefresh)
    return () => window.removeEventListener('history-updated', handleRefresh)
  }, [fetchHistory])

  const createFolder = async (name: string, parentId?: string) => {
    if (!session?.access_token) return null
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/folders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ name, parent_id: parentId }),
      })
      if (!res.ok) throw new Error("Failed to create folder")
      const newFolder = await res.json()
      
      const newItem: HistoryItem = {
        id: newFolder.id,
        label: newFolder.name,
        icon: Folder,
        type: "folder",
        hasChildren: false,
        createdAt: new Date(newFolder.created_at),
        editedAt: new Date(newFolder.created_at),
        parentId: newFolder.parent_id
      }
      
      setItems(prev => [newItem, ...prev])
      return newItem
    } catch (err) {
      console.error(err)
      return null
    }
  }

  const createChat = async (title: string, folderId?: string) => {
    if (!session?.access_token) return null
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ title, folder_id: folderId }),
      })
      if (!res.ok) throw new Error("Failed to create chat")
      const newChat = await res.json()
      
      const newItem: HistoryItem = {
        id: newChat.id,
        label: newChat.title,
        icon: MessageSquare,
        type: "chat",
        createdAt: new Date(newChat.created_at),
        editedAt: new Date(newChat.created_at),
        folderId: newChat.folder_id
      }
      
      setItems(prev => [newItem, ...prev])
      return newItem
    } catch (err) {
      console.error(err)
      return null
    }
  }

  const deleteItem = async (id: string, type: "chat" | "folder") => {
    if (!session?.access_token) return false
    try {
      const endpoint = type === "folder" ? "folders" : "chats"
      const res = await fetch(`${API_BASE_URL}/api/history/${endpoint}/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      })
      if (!res.ok) throw new Error(`Failed to delete ${type}`)
      
      setItems(prev => prev.filter(item => item.id !== id))
      return true
    } catch (err) {
      console.error(err)
      return false
    }
  }

  const updateFolder = async (id: string, updates: { name?: string; parentId?: string | null }) => {
    if (!session?.access_token) return null
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/folders/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ 
            name: updates.name, 
            parent_id: updates.parentId 
        }),
      })
      if (!res.ok) throw new Error("Failed to update folder")
      const updatedFolder = await res.json()
      
      setItems(prev => prev.map(item => {
        if (item.id === id && item.type === "folder") {
            return {
                ...item,
                label: updatedFolder.name,
                parentId: updatedFolder.parent_id,
                editedAt: new Date(updatedFolder.updated_at || new Date())
            }
        }
        return item
      }))
      return updatedFolder
    } catch (err) {
      console.error(err)
      return null
    }
  }

  const updateChat = async (id: string, updates: { title?: string; folderId?: string | null }) => {
    if (!session?.access_token) return null
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/chats/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ 
            title: updates.title, 
            folder_id: updates.folderId 
        }),
      })
      if (!res.ok) throw new Error("Failed to update chat")
      const updatedChat = await res.json()
      
      setItems(prev => prev.map(item => {
        if (item.id === id && item.type === "chat") {
            return {
                ...item,
                label: updatedChat.title,
                folderId: updatedChat.folder_id,
                editedAt: new Date(updatedChat.updated_at || new Date())
            }
        }
        return item
      }))
      return updatedChat
    } catch (err) {
      console.error(err)
      return null
    }
  }

  const toggleStar = async (id: string, type: "chat" | "folder", isStarred: boolean) => {
    if (!session?.access_token) return null
    try {
      const endpoint = type === "folder" ? "folders" : "chats"
      const res = await fetch(`${API_BASE_URL}/api/history/${endpoint}/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ is_starred: isStarred }),
      })
      if (!res.ok) throw new Error(`Failed to toggle star for ${type}`)
      
      setItems(prev => prev.map(item => {
        if (item.id === id && item.type === type) {
            return { ...item, isStarred }
        }
        return item
      }))
      return true
    } catch (err) {
      console.error(err)
      return false
    }
  }

  const moveItem = async (id: string, type: "chat" | "folder", targetId: string | null, targetType: "folder" | "root") => {
    if (!session?.access_token) return null
    try {
      const endpoint = type === "folder" ? "folders" : "chats"
      const body: any = {}
      
      if (type === "chat") {
        body.folder_id = targetType === "folder" ? targetId : null
      } else {
        body.parent_id = targetType === "folder" ? targetId : null
      }

      const res = await fetch(`${API_BASE_URL}/api/history/${endpoint}/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(body),
      })
      
      if (!res.ok) throw new Error(`Failed to move ${type}`)
      
      setItems(prev => prev.map(item => {
        if (item.id === id && item.type === type) {
            if (type === "chat") {
                return { ...item, folderId: body.folder_id }
            } else {
                return { ...item, parentId: body.parent_id }
            }
        }
        return item
      }))
      return true
    } catch (err) {
      console.error(err)
      return false
    }
  }

  return {
    items,
    isLoading,
    error,
    createFolder,
    createChat,
    deleteItem,
    updateFolder,
    updateChat,
    toggleStar,
    moveItem,
    refresh: fetchHistory
  }
}

"use client"

import React, { useState, useRef } from "react"
import { TrashDialog } from "./trash-popover"
import { ConfirmDialog } from "./confirm-dialog"
import { RenameDialog } from "./rename-dialog"
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
  MessageSquare,
  MoreHorizontal,
  Laptop,
  GraduationCap,
  Shield,
  FolderPlus,
  MessageSquarePlus,
  Trash2
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu"
import { useTheme } from "next-themes"
import { useAuth } from "~/hooks/useAuth"
import { useClickOutside } from "~/hooks/use-click-outside"
import { useHistory, type HistoryItem } from "~/hooks/use-history"
import { MoveItemPopover } from "./move-item-dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

type ChatItem = {
  id: string
  label: string
  icon: typeof MessageSquare | typeof Folder
  type: "chat" | "folder"
  hasChildren?: boolean
  createdAt: Date
  editedAt: Date
  folderId?: string | null
  parentId?: string | null
}

type SortOption = "date-created" | "date-edited" | "name"

export function NavRail({ onSelectChat, activeChatId }: { onSelectChat?: (chatId: string) => void, activeChatId?: string | null }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { theme, setTheme } = useTheme()
  const currentTheme = (theme as string) || "system"
  const { user, signOut } = useAuth()
  const sidebarRef = useRef<HTMLDivElement>(null)
  const userMenuTriggerRef = useRef<HTMLButtonElement>(null)
  const [showTrash, setShowTrash] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ isOpen: boolean, id: string, type: "chat" | "folder" } | null>(null)
  const [renameDialog, setRenameDialog] = useState<{ isOpen: boolean, id: string, type: "chat" | "folder", initialValue: string } | null>(null)
  const [isAnyMenuOpen, setIsAnyMenuOpen] = useState(false)

  const fullName = user?.user_metadata?.full_name || "User"
  const email = user?.email || ""
  const initials = fullName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
  
  // Mock Role - in real app, get from user metadata
  const role = "Student" 

  // Tree View State
  const [sections, setSections] = useState({
    starred: false,
    recent: true,
    folders: false
  })
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("")
  
  // Sort option
  const [sortBy, setSortBy] = useState<SortOption>("date-edited")
  
  const { items, createFolder, createChat, deleteItem, updateFolder, updateChat, toggleStar: toggleStarApi, moveItem } = useHistory()

  // Chat items state
  const [starredChats, setStarredChats] = useState<ChatItem[]>([])
  const [recentChats, setRecentChats] = useState<ChatItem[]>([])
  const [folderItems, setFolderItems] = useState<ChatItem[]>([])
  
  const [starredItems, setStarredItems] = useState<Set<string>>(new Set())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")
  const searchInputRef = useRef<HTMLInputElement>(null)
  
  // Expanded folders state
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // Sync with backend data
  React.useEffect(() => {
    if (!items) return

    const chats = items.filter(i => i.type === "chat" && !i.folderId).map(i => ({
      ...i,
      icon: MessageSquare,
      folderId: i.folderId
    })) as ChatItem[]
    
    const folders = items.filter(i => i.type === "folder").map(i => ({
      ...i,
      icon: Folder,
      parentId: i.parentId
    })) as ChatItem[]

    setRecentChats(chats)
    setFolderItems(folders)
    
    // Sync starred items from backend
    const starredSet = new Set<string>()
    items.forEach(i => {
      if (i.isStarred) starredSet.add(i.id)
    })
    setStarredItems(starredSet)
    
    // For starred, we filter from all items based on starredItems set
    const starred = items.filter(i => i.isStarred).map(i => ({
      ...i,
      icon: i.type === "folder" ? Folder : MessageSquare,
      folderId: i.folderId,
      parentId: i.parentId
    })) as ChatItem[]
    setStarredChats(starred)

  }, [items])

  // Check for test mode to disable auto-closing
  const isTestMode = typeof window !== 'undefined' && document.body.classList.contains('test-mode')

  // Close sidebar on outside click
  useClickOutside(sidebarRef, () => {
    if (isExpanded && !isTestMode && !isAnyMenuOpen) {
      setIsExpanded(false)
    }
  })

  const toggleSection = (section: keyof typeof sections) => {
    setSections(prev => ({ ...prev, [section]: !prev[section] }))
  }
  
  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folderId)) next.delete(folderId)
      else next.add(folderId)
      return next
    })
  }
  
  const toggleStar = async (itemId: string) => {
    const item = items.find(i => i.id === itemId)
    if (item) {
      await toggleStarApi(itemId, item.type, !item.isStarred)
    }
  }

  const handleNewChat = async () => {
    await createChat("New chat")
    // State will update via useEffect
  }

  const handleNewFolder = async () => {
    await createFolder("New folder")
    // State will update via useEffect
  }

  const handleRename = async (id: string, type: "chat" | "folder", newName: string) => {
    if (type === "chat") {
      await updateChat(id, { title: newName })
    } else {
      await updateFolder(id, { name: newName })
    }
    setEditingId(null)
  }

  const handleRenameClick = (id: string, type: "chat" | "folder", currentName: string) => {
    setRenameDialog({ isOpen: true, id, type, initialValue: currentName })
  }

  const handleRenameConfirm = async (newName: string) => {
    if (renameDialog && newName !== renameDialog.initialValue) {
      await handleRename(renameDialog.id, renameDialog.type, newName)
    }
    setRenameDialog(null)
  }

  const handleDelete = async (id: string, type: "chat" | "folder") => {
    setDeleteConfirmation({ isOpen: true, id, type })
  }

  const confirmDelete = async () => {
    if (deleteConfirmation) {
      await deleteItem(deleteConfirmation.id, deleteConfirmation.type)
      setDeleteConfirmation(null)
    }
  }

  const handleMoveItem = async (itemId: string, itemType: "chat" | "folder", targetFolderId: string | null) => {
    const targetType = targetFolderId ? "folder" : "root"
    await moveItem(itemId, itemType, targetFolderId, targetType)
  }

  const sortItems = (items: ChatItem[]) => {
    const sorted = [...items]
    switch (sortBy) {
      case "name":
        return sorted.sort((a, b) => a.label.localeCompare(b.label))
      case "date-created":
        return sorted.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
      case "date-edited":
        return sorted.sort((a, b) => b.editedAt.getTime() - a.editedAt.getTime())
      default:
        return sorted
    }
  }

  const filterItems = (items: ChatItem[], excludeStarred = false) => {
    let filtered = items
    if (searchQuery) {
      filtered = filtered.filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase()))
    }
    if (excludeStarred) {
      filtered = filtered.filter(item => !starredItems.has(item.id))
    }
    return filtered
  }

  const allFolders = folderItems.map(f => ({ id: f.id, label: f.label, parentId: f.parentId }))

  // Recursive Folder Component
  const RecursiveFolder = ({ item, depth = 0 }: { item: ChatItem, depth?: number }) => {
    const children = items.filter(i => i.folderId === item.id || i.parentId === item.id)
    const isFolderExpanded = expandedFolders.has(item.id)
    
    // Sort children
    const sortedChildren = sortItems(children as ChatItem[])

    return (
      <div key={item.id}>
        <TreeItem
          id={item.id}
          icon={item.icon}
          label={item.label}
          hasChildren={true}
          itemId={item.id}
          active={item.id === activeChatId}
          isStarred={starredItems.has(item.id)}
          onToggleStar={toggleStar}
          onClick={() => toggleFolder(item.id)}
          onRename={() => handleRenameClick(item.id, item.type, item.label)}
          onDelete={() => handleDelete(item.id, item.type)}
          onMove={(targetId) => handleMoveItem(item.id, item.type, targetId)}
          folders={allFolders}
          isExpanded={isFolderExpanded}
          onMenuOpenChange={setIsAnyMenuOpen}
        />
        {isFolderExpanded && (
          <div className="ml-4 border-l border-border pl-2">
            {sortedChildren.length > 0 ? (
              sortedChildren.map(child => (
                child.type === 'folder' ? (
                  <RecursiveFolder key={child.id} item={child} depth={depth + 1} />
                ) : (
                  <TreeItem 
                    key={child.id}
                    itemId={child.id}
                    icon={MessageSquare}
                    label={child.label}
                    active={child.id === activeChatId}
                    isStarred={starredItems.has(child.id)}
                    onToggleStar={toggleStar}
                    onClick={() => onSelectChat?.(child.id)}
                    hasChildren={false}
                    onRename={() => handleRenameClick(child.id, child.type, child.label)}
                    onDelete={() => handleDelete(child.id, child.type)}
                    onMove={(targetId) => handleMoveItem(child.id, child.type, targetId)}
                    folders={allFolders}
                    onMenuOpenChange={setIsAnyMenuOpen}
                  />
                )
              ))
            ) : (
              <div className="text-[10px] text-muted-foreground py-1 px-2 italic">Empty folder</div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="absolute top-0 right-0 h-screen z-50 flex">
        <div
          ref={sidebarRef}
          data-testid="nav-rail"
          onMouseDown={(e) => e.stopPropagation()}
          className={cn(
            "h-full bg-background text-foreground flex flex-col border-l border-r border-border shadow-xl transition-all duration-500 ease-smooth overflow-hidden",
            isExpanded ? "w-[260px]" : "w-[54px]",
          )}
        >
          {/* Header with Logo & Title */}
          <div className="border-b border-border shrink-0">
            {isExpanded ? (
              <div className="p-3 space-y-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 bg-gradient-to-br from-violet-500 to-violet-600 rounded-lg flex items-center justify-center text-white font-bold text-xs shadow-lg">
                      L
                    </div>
                    <span className="text-sm font-bold text-foreground tracking-tight">Luminate AI</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-6 w-6 text-muted-foreground hover:text-foreground" 
                    onClick={() => setIsExpanded(false)}
                    data-testid="nav-rail-collapse"
                  >
                    <PanelLeftClose className="w-3.5 h-3.5" />
                  </Button>
                </div>
                
                {/* Search Bar */}
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                    <Input
                      ref={searchInputRef}
                      placeholder="Search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="h-7 pl-8 bg-muted/50 border-border text-xs text-foreground placeholder:text-muted-foreground focus:bg-muted focus:border-ring"
                    />
                  </div>
                  <DropdownMenu onOpenChange={setIsAnyMenuOpen}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <DropdownMenuTrigger asChild>
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-7 w-7 bg-violet-600 hover:bg-violet-500 text-white shrink-0"
                            data-testid="new-button"
                          >
                            <Plus className="w-3.5 h-3.5" />
                          </Button>
                        </DropdownMenuTrigger>
                      </TooltipTrigger>
                      <TooltipContent side="right">New</TooltipContent>
                    </Tooltip>
                    <DropdownMenuContent align="end" className="w-40 bg-popover border-border" data-testid="new-menu-content">
                      <DropdownMenuItem 
                        onClick={handleNewChat} 
                        className="cursor-pointer text-popover-foreground focus:bg-accent focus:text-accent-foreground"
                        data-testid="new-chat-item"
                      >
                        <MessageSquarePlus className="w-4 h-4 mr-2" />
                        New chat
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={handleNewFolder} 
                        className="cursor-pointer text-popover-foreground focus:bg-accent focus:text-accent-foreground"
                        data-testid="new-folder-item"
                      >
                        <FolderPlus className="w-4 h-4 mr-2" />
                        New folder
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ) : (
              <div className="p-3 flex flex-col items-center gap-2">
                <div className="h-8 w-8 bg-gradient-to-br from-violet-500 to-violet-600 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-lg">
                  L
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-6 w-6 text-muted-foreground hover:text-foreground" 
                  onClick={() => setIsExpanded(true)}
                  data-testid="nav-rail-expand"
                >
                  <PanelLeftOpen className="w-3.5 h-3.5" />
                </Button>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      onClick={() => {
                        setIsExpanded(true)
                        setTimeout(() => searchInputRef.current?.focus(), 100)
                      }}
                    >
                      <Search className="w-3.5 h-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Search</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      onClick={handleNewChat}
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">New Chat</TooltipContent>
                </Tooltip>
              </div>
            )}
          </div>

          {/* Tree View Content - Law of Proximity: Group related items */}
          <ScrollArea className="flex-1 w-full min-h-0">
          <div className="py-3 px-2">
            {isExpanded ? (
              <div className="space-y-3">
                {/* Sort By Control */}
                <div className="px-2 flex items-center gap-2">
                  <div 
                    onClick={(e) => e.stopPropagation()} 
                    onMouseDown={(e) => e.stopPropagation()}
                    className="flex-1"
                  >
                    <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)} onOpenChange={setIsAnyMenuOpen}>
                      <SelectTrigger className="h-7 text-xs bg-muted/50 border-border text-foreground w-full">
                        <SelectValue placeholder="Sort by..." />
                      </SelectTrigger>
                      <SelectContent className="bg-popover border-border text-popover-foreground z-[110]">
                        <SelectItem value="date-edited" className="text-xs">Date edited</SelectItem>
                        <SelectItem value="date-created" className="text-xs">Date created</SelectItem>
                        <SelectItem value="name" className="text-xs">Name</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Starred Section */}
                <CollapsibleSection 
                  label="STARRED" 
                  isOpen={sections.starred} 
                  onToggle={() => toggleSection('starred')}
                  count={filterItems(starredChats).length}
                >
                      {sortItems(filterItems(starredChats)).map((item) => {
                        if (item.type === 'folder') {
                          return <RecursiveFolder key={item.id} item={item} />
                        }
                        return (
                          <TreeItem
                            key={item.id}
                            id={item.id}
                            icon={item.icon}
                            label={item.label}
                            active={item.id === activeChatId}
                            itemId={item.id}
                            isStarred={starredItems.has(item.id)}
                            onToggleStar={toggleStar}
                            hasChildren={item.hasChildren}
                            onClick={() => onSelectChat?.(item.id)}
                            onRename={() => handleRenameClick(item.id, item.type, item.label)}
                            onDelete={() => handleDelete(item.id, item.type)}
                            onMove={(targetId) => handleMoveItem(item.id, item.type, targetId)}
                            folders={allFolders}
                            onMenuOpenChange={setIsAnyMenuOpen}
                          />
                        )
                      })}
                </CollapsibleSection>

                {/* Recent Section - Hick's Law: Limit visible options */}
                <CollapsibleSection 
                  label="RECENT" 
                  isOpen={sections.recent} 
                  onToggle={() => toggleSection('recent')}
                  count={filterItems(recentChats, true).length}
                >
                      {sortItems(filterItems(recentChats, true)).map((item) => (
                        <TreeItem
                          key={item.id}
                          id={item.id}
                          icon={item.icon}
                          label={item.label}
                          itemId={item.id}
                          active={item.id === activeChatId}
                          isStarred={starredItems.has(item.id)}
                          onToggleStar={toggleStar}
                          hasChildren={item.hasChildren}
                          onClick={() => onSelectChat?.(item.id)}
                          onRename={() => handleRenameClick(item.id, item.type, item.label)}
                          onDelete={() => handleDelete(item.id, item.type)}
                          onMove={(targetId) => handleMoveItem(item.id, item.type, targetId)}
                          folders={allFolders}
                          onMenuOpenChange={setIsAnyMenuOpen}
                        />
                      ))}
                </CollapsibleSection>
                
                {/* Folders - Law of Similarity: Consistent styling */}
                <CollapsibleSection 
                  label="FOLDERS" 
                  isOpen={sections.folders} 
                  onToggle={() => toggleSection('folders')}
                  count={filterItems(folderItems.filter(f => !f.parentId), true).length}
                >
                      {sortItems(filterItems(folderItems.filter(f => !f.parentId), true)).map((item) => (
                        <RecursiveFolder key={item.id} item={item} />
                      ))}
                </CollapsibleSection>
              </div>
            ) : (
               <div className="flex flex-col items-center gap-2 pt-2">
                  {/* Icons hidden in collapsed state as requested */}
               </div>
            )}
          </div>
          </ScrollArea>

          {/* User Profile Footer - Fitts's Law: Large clickable area */}
          <div className="p-2 border-t border-border bg-background">
            <DropdownMenu onOpenChange={setIsAnyMenuOpen}>
              <DropdownMenuTrigger asChild>
                <button 
                  ref={userMenuTriggerRef}
                  className={cn(
                    "flex items-center gap-2 w-full p-2 rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors group outline-none",
                    !isExpanded && "justify-center px-0"
                  )}
                  data-testid="user-profile-trigger"
                >
                  <div className="relative shrink-0">
                    <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-white font-medium text-xs shadow-lg ring-2 ring-background">
                      {initials}
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-background rounded-full"></div>
                  </div>
                  
                  {isExpanded && (
                    <div className="flex-1 text-left overflow-hidden">
                      <div className="text-sm font-medium text-foreground truncate">{fullName}</div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                        <GraduationCap className="w-3 h-3" />
                        {role}
                      </div>
                    </div>
                  )}
                  
                  {isExpanded && (
                     <Settings className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  )}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" side={isExpanded ? "top" : "right"} className="w-64 bg-popover border-border ml-2 mb-2 text-popover-foreground z-[100]" data-testid="user-profile-menu">
                <div className="flex items-center gap-3 p-3 bg-muted/50 mb-1">
                  <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white font-semibold text-sm shrink-0">
                    {initials}
                  </div>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-medium text-foreground truncate">{fullName}</span>
                    <span className="text-xs text-muted-foreground truncate">{email}</span>
                  </div>
                </div>
                
                <DropdownMenuSeparator className="bg-border" />
                
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger className="focus:bg-accent focus:text-accent-foreground cursor-pointer" data-testid="theme-submenu-trigger">
                    {currentTheme === "light" ? <Sun className="w-4 h-4 mr-2" /> : currentTheme === "dark" ? <Moon className="w-4 h-4 mr-2" /> : <Laptop className="w-4 h-4 mr-2" />}
                    Theme
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent className="bg-popover border-border text-popover-foreground z-[100]" data-testid="theme-submenu-content">
                      <DropdownMenuRadioGroup value={currentTheme} onValueChange={(value) => setTheme(value)}>
                        <DropdownMenuRadioItem value="light" className="focus:bg-accent focus:text-accent-foreground cursor-pointer" data-testid="theme-light">
                          <Sun className="w-4 h-4 mr-2" /> Light
                        </DropdownMenuRadioItem>
                        <DropdownMenuRadioItem value="dark" className="focus:bg-accent focus:text-accent-foreground cursor-pointer" data-testid="theme-dark">
                          <Moon className="w-4 h-4 mr-2" /> Dark
                        </DropdownMenuRadioItem>
                        <DropdownMenuRadioItem value="system" className="focus:bg-accent focus:text-accent-foreground cursor-pointer" data-testid="theme-system">
                          <Laptop className="w-4 h-4 mr-2" /> System
                        </DropdownMenuRadioItem>
                      </DropdownMenuRadioGroup>
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>

                <DropdownMenuItem className="focus:bg-accent focus:text-accent-foreground" data-testid="settings-item">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>

                <DropdownMenuItem 
                  className="focus:bg-accent focus:text-accent-foreground cursor-pointer" 
                  onSelect={(e) => {
                    e.preventDefault()
                    setShowTrash(true)
                  }}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Trash
                </DropdownMenuItem>
                
                <DropdownMenuSeparator className="bg-border" />
                
                <DropdownMenuItem 
                  className="text-destructive focus:bg-destructive/10 focus:text-destructive"
                  onClick={() => signOut()}
                  data-testid="logout-item"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            <TrashDialog 
              isOpen={showTrash} 
              onClose={() => setShowTrash(false)} 
            />
            
            {deleteConfirmation && (
              <ConfirmDialog
                isOpen={deleteConfirmation.isOpen}
                onClose={() => setDeleteConfirmation(null)}
                onConfirm={confirmDelete}
                title="Delete Item?"
                description="Are you sure you want to delete this item? It will be moved to trash."
                confirmText="Delete"
                variant="destructive"
              />
            )}

            {renameDialog && (
              <RenameDialog
                isOpen={renameDialog.isOpen}
                onClose={() => setRenameDialog(null)}
                onRename={handleRenameConfirm}
                initialValue={renameDialog.initialValue}
                title={`Rename ${renameDialog.type === 'chat' ? 'Chat' : 'Folder'}`}
              />
            )}
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}

function CollapsibleSection({ label, isOpen, onToggle, children, count }: { label: string, isOpen: boolean, onToggle: () => void, children: React.ReactNode, count?: number }) {
   return (
      <div className="mb-2">
         <button 
            onClick={onToggle}
            className="w-full flex items-center gap-1.5 px-2 py-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded transition-colors group"
            data-testid={`section-header-${label}`}
         >
            <ChevronRight className={cn("w-3 h-3 transition-transform duration-200 shrink-0", isOpen && "rotate-90")} />
            <span className="text-[11px] font-bold tracking-wider uppercase group-hover:text-foreground flex-1 text-left">{label}</span>
            {count !== undefined && (
              <span className="text-[10px] text-muted-foreground font-medium">{count}</span>
            )}
         </button>
         {isOpen && (
            <div className="mt-1 space-y-1" data-testid={`section-content-${label}`}>
               {children}
            </div>
         )}
      </div>
   )
}

function TreeItem({ 
  icon: Icon, 
  label, 
  active, 
  hasChildren, 
  itemId, 
  isStarred, 
  onToggleStar, 
  onClick,
  onRename,
  onDelete,
  onMove,
  folders = [],
  isExpanded,
  onMenuOpenChange
}: { 
  icon: any, 
  label: string, 
  active?: boolean, 
  hasChildren?: boolean, 
  itemId: string, 
  isStarred: boolean, 
  onToggleStar: (id: string) => void, 
  onClick?: () => void,
  onRename?: () => void,
  onDelete?: () => void,
  onMove?: (targetId: string) => void,
  folders?: { id: string; label: string; parentId?: string | null }[],
  isExpanded?: boolean,
  onMenuOpenChange?: (open: boolean) => void
}) {
   const [showMove, setShowMove] = useState(false)
   const itemRef = useRef<HTMLDivElement>(null)
   const isMovingRef = useRef(false)

   return (
      <div 
         ref={itemRef}
         className={cn(
            "flex items-center gap-2 px-2 py-2 cursor-pointer border-l-2 border-transparent hover:bg-accent rounded transition-colors group relative pr-8",
            active ? "bg-accent/70 border-l-2 border-violet-500 text-foreground" : "text-muted-foreground hover:text-foreground"
         )}
         data-testid={`tree-item-${itemId}`}
         onClick={onClick}
      >
         {showMove && (
            <MoveItemPopover 
               isOpen={showMove}
               onClose={() => {
                 setShowMove(false)
                 isMovingRef.current = false
               }}
               onMove={(targetId) => {
                  onMove?.(targetId)
                  setShowMove(false)
                  isMovingRef.current = false
               }}
               folders={folders}
               itemId={itemId}
               anchorRef={itemRef}
            />
         )}
         {hasChildren ? (
            <ChevronRight className={cn("w-3 h-3 text-muted-foreground shrink-0 transition-transform duration-200", isExpanded && "rotate-90")} />
         ) : (
            <div className="w-3 shrink-0" /> 
         )}
         <Icon className={cn("w-3.5 h-3.5 shrink-0", active ? "text-violet-400" : "text-muted-foreground")} />
         <span className="text-xs truncate leading-none flex-1">{label}</span>
         
         <div className="flex items-center gap-1 absolute right-1 opacity-0 group-hover:opacity-100 transition-opacity">
           <button
             onClick={(e) => {
               e.stopPropagation()
               onToggleStar(itemId)
             }}
             className={cn(
               "p-0.5 hover:bg-accent rounded shrink-0",
               isStarred && "opacity-100 block"
             )}
             data-testid={`star-button-${itemId}`}
           >
             <Star className={cn(
               "w-3 h-3",
               isStarred ? "fill-yellow-500 text-yellow-500" : "text-muted-foreground"
             )} />
           </button>

           <DropdownMenu onOpenChange={onMenuOpenChange}>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                className="h-6 w-6 p-0 hover:bg-accent"
                onClick={(e) => e.stopPropagation()}
                data-testid={`menu-button-${itemId}`}
              >
                <MoreHorizontal className="h-4 w-4 text-muted-foreground hover:text-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent 
              align="end" 
              className="bg-popover border-border z-[60]"
              onCloseAutoFocus={(e) => {
                if (isMovingRef.current) {
                  e.preventDefault()
                }
              }}
            >
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onRename?.() }} className="text-popover-foreground focus:bg-accent cursor-pointer">
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem 
                onSelect={(e) => { 
                   isMovingRef.current = true
                   setShowMove(true)
                }} 
                className="text-popover-foreground focus:bg-accent cursor-pointer"
              >
                Move to...
              </DropdownMenuItem>
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onDelete?.() }} className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer">
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
         </div>
      </div>
   )
}

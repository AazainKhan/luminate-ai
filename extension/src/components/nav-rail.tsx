"use client"

import type React from "react"

import { useState, useRef } from "react"
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
  GripVertical
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
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu"
import { useTheme } from "next-themes"
import { useAuth } from "~/hooks/useAuth"
import { useClickOutside } from "~/hooks/use-click-outside"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

type ChatItem = {
  id: string
  label: string
  icon: typeof MessageSquare | typeof Folder
  type: "chat" | "folder"
  hasChildren?: boolean
  createdAt: Date
  editedAt: Date
}

type SortOption = "date-created" | "date-edited" | "name"

export function NavRail() {
  const [isExpanded, setIsExpanded] = useState(false)
  const { theme, setTheme } = useTheme()
  const currentTheme = (theme as string) || "system"
  const { user, signOut } = useAuth()
  const sidebarRef = useRef<HTMLDivElement>(null)

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
    starred: true,
    recent: true,
    university: true
  })
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("")
  
  // Sort option
  const [sortBy, setSortBy] = useState<SortOption>("date-edited")
  
  // Chat items state (with mock data)
  const [starredChats, setStarredChats] = useState<ChatItem[]>([
    { id: "linear-algebra", label: "Linear Algebra Review", icon: MessageSquare, type: "chat", createdAt: new Date("2024-11-20"), editedAt: new Date("2024-11-23") },
    { id: "spanish-practice", label: "Spanish Practice", icon: MessageSquare, type: "chat", createdAt: new Date("2024-11-19"), editedAt: new Date("2024-11-22") },
  ])
  
  const [recentChats, setRecentChats] = useState<ChatItem[]>([
    { id: "essay", label: "Essay Brainstorming", icon: MessageSquare, type: "chat", createdAt: new Date("2024-11-21"), editedAt: new Date("2024-11-23") },
    { id: "react", label: "React Components", icon: MessageSquare, type: "chat", createdAt: new Date("2024-11-20"), editedAt: new Date("2024-11-22") },
    { id: "physics", label: "Physics Lab Report", icon: MessageSquare, type: "chat", createdAt: new Date("2024-11-18"), editedAt: new Date("2024-11-21") },
  ])
  
  const [folderItems, setFolderItems] = useState<ChatItem[]>([
    { id: "cs101", label: "CS 101", icon: Folder, type: "folder", hasChildren: true, createdAt: new Date("2024-11-15"), editedAt: new Date("2024-11-22") },
    { id: "math202", label: "MATH 202", icon: Folder, type: "folder", hasChildren: true, createdAt: new Date("2024-11-10"), editedAt: new Date("2024-11-20") },
  ])
  
  const [starredItems, setStarredItems] = useState<Set<string>>(new Set(["linear-algebra", "spanish-practice"]))

  // Close sidebar on outside click
  useClickOutside(sidebarRef, () => {
    if (isExpanded) {
      setIsExpanded(false)
    }
  })

  const toggleSection = (section: keyof typeof sections) => {
    setSections(prev => ({ ...prev, [section]: !prev[section] }))
  }
  
  const toggleStar = (itemId: string) => {
    setStarredItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }

  const handleNewChat = () => {
    const newChat: ChatItem = {
      id: `chat-${Date.now()}`,
      label: "New chat",
      icon: MessageSquare,
      type: "chat",
      createdAt: new Date(),
      editedAt: new Date()
    }
    setRecentChats(prev => [newChat, ...prev])
  }

  const handleNewFolder = () => {
    const newFolder: ChatItem = {
      id: `folder-${Date.now()}`,
      label: "New folder",
      icon: Folder,
      type: "folder",
      hasChildren: true,
      createdAt: new Date(),
      editedAt: new Date()
    }
    setFolderItems(prev => [newFolder, ...prev])
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

  // Drag and drop handlers
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent, items: ChatItem[], setItems: React.Dispatch<React.SetStateAction<ChatItem[]>>) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  return (
    <TooltipProvider>
      <div className="absolute top-0 right-0 h-screen z-50 flex">
        <div
          ref={sidebarRef}
          className={cn(
            "h-full bg-slate-950/90 text-slate-200 flex flex-col border-l border-r border-slate-800 shadow-xl transition-all duration-300 ease-in-out",
            isExpanded ? "w-[260px]" : "w-[54px]",
          )}
        >
          {/* Header with Logo & Title */}
          <div className="border-b border-slate-800 shrink-0">
            {isExpanded ? (
              <div className="p-3 space-y-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 bg-gradient-to-br from-violet-500 to-violet-600 rounded-lg flex items-center justify-center text-white font-bold text-xs shadow-lg">
                      L
                    </div>
                    <span className="text-sm font-bold text-slate-50 tracking-tight">Luminate AI</span>
                  </div>
                  <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-slate-100" onClick={() => setIsExpanded(false)}>
                    <PanelLeftClose className="w-3.5 h-3.5" />
                  </Button>
                </div>
                
                {/* Search Bar */}
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                    <Input
                      placeholder="Search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="h-7 pl-8 bg-slate-900/50 border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:bg-slate-900 focus:border-slate-700"
                    />
                  </div>
                  <DropdownMenu>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <DropdownMenuTrigger asChild>
                          <Button size="icon" variant="ghost" className="h-7 w-7 bg-violet-600 hover:bg-violet-500 text-white shrink-0">
                            <Plus className="w-3.5 h-3.5" />
                          </Button>
                        </DropdownMenuTrigger>
                      </TooltipTrigger>
                      <TooltipContent side="right">New</TooltipContent>
                    </Tooltip>
                    <DropdownMenuContent align="end" className="w-40 bg-slate-900 border-slate-800">
                      <DropdownMenuItem onClick={handleNewChat} className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
                        <MessageSquarePlus className="w-4 h-4 mr-2" />
                        New chat
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleNewFolder} className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
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
                <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-slate-100" onClick={() => setIsExpanded(true)}>
                  <PanelLeftOpen className="w-3.5 h-3.5" />
                </Button>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-slate-100">
                      <Search className="w-3.5 h-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Search</TooltipContent>
                </Tooltip>
                <DropdownMenu>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-slate-100">
                          <Plus className="w-3.5 h-3.5" />
                        </Button>
                      </DropdownMenuTrigger>
                    </TooltipTrigger>
                    <TooltipContent side="right">New</TooltipContent>
                  </Tooltip>
                  <DropdownMenuContent side="right" className="w-40 bg-slate-900 border-slate-800">
                    <DropdownMenuItem onClick={handleNewChat} className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
                      <MessageSquarePlus className="w-4 h-4 mr-2" />
                      New chat
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleNewFolder} className="cursor-pointer text-slate-200 focus:bg-slate-800 focus:text-slate-50">
                      <FolderPlus className="w-4 h-4 mr-2" />
                      New folder
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            )}
          </div>

          {/* Tree View Content - Law of Proximity: Group related items */}
          <ScrollArea className="flex-1">
          <div className="py-3 px-2">
            {isExpanded ? (
              <div className="space-y-3">
                {/* Sort By Control */}
                <div className="px-2">
                  <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
                    <SelectTrigger className="h-7 text-xs bg-slate-900/50 border-slate-800 text-slate-300">
                      <SelectValue placeholder="Sort by..." />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                      <SelectItem value="date-edited" className="text-xs">Date edited</SelectItem>
                      <SelectItem value="date-created" className="text-xs">Date created</SelectItem>
                      <SelectItem value="name" className="text-xs">Name</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Starred Section */}
                <CollapsibleSection 
                  label="STARRED" 
                  isOpen={sections.starred} 
                  onToggle={() => toggleSection('starred')}
                  count={starredChats.length}
                >
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={(event) => handleDragEnd(event, starredChats, setStarredChats)}
                  >
                    <SortableContext
                      items={sortItems(starredChats).map(item => item.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      {sortItems(starredChats).map((item) => (
                        <SortableTreeItem
                          key={item.id}
                          id={item.id}
                          icon={item.icon}
                          label={item.label}
                          active={item.id === "linear-algebra"}
                          itemId={item.id}
                          isStarred={starredItems.has(item.id)}
                          onToggleStar={toggleStar}
                          hasChildren={item.hasChildren}
                        />
                      ))}
                    </SortableContext>
                  </DndContext>
                </CollapsibleSection>

                {/* Recent Section - Hick's Law: Limit visible options */}
                <CollapsibleSection 
                  label="RECENT" 
                  isOpen={sections.recent} 
                  onToggle={() => toggleSection('recent')}
                  count={recentChats.length}
                >
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={(event) => handleDragEnd(event, recentChats, setRecentChats)}
                  >
                    <SortableContext
                      items={sortItems(recentChats).map(item => item.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      {sortItems(recentChats).map((item) => (
                        <SortableTreeItem
                          key={item.id}
                          id={item.id}
                          icon={item.icon}
                          label={item.label}
                          itemId={item.id}
                          isStarred={starredItems.has(item.id)}
                          onToggleStar={toggleStar}
                          hasChildren={item.hasChildren}
                        />
                      ))}
                    </SortableContext>
                  </DndContext>
                </CollapsibleSection>
                
                {/* Folders - Law of Similarity: Consistent styling */}
                <CollapsibleSection 
                  label="UNIVERSITY" 
                  isOpen={sections.university} 
                  onToggle={() => toggleSection('university')}
                  count={folderItems.length}
                >
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={(event) => handleDragEnd(event, folderItems, setFolderItems)}
                  >
                    <SortableContext
                      items={sortItems(folderItems).map(item => item.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      {sortItems(folderItems).map((item) => (
                        <SortableTreeItem
                          key={item.id}
                          id={item.id}
                          icon={item.icon}
                          label={item.label}
                          hasChildren={item.hasChildren}
                          itemId={item.id}
                          isStarred={starredItems.has(item.id)}
                          onToggleStar={toggleStar}
                        />
                      ))}
                    </SortableContext>
                  </DndContext>
                </CollapsibleSection>
              </div>
            ) : (
               <div className="flex flex-col items-center gap-2 pt-2">
                  <Tooltip>
                     <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-slate-100 hover:bg-slate-900/40">
                           <Star className="w-3.5 h-3.5" />
                        </Button>
                     </TooltipTrigger>
                     <TooltipContent side="right">Starred</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                     <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-slate-100 hover:bg-slate-900/40">
                           <MessageSquare className="w-3.5 h-3.5" />
                        </Button>
                     </TooltipTrigger>
                     <TooltipContent side="right">Chats</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                     <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-slate-100 hover:bg-slate-900/40">
                           <Folder className="w-3.5 h-3.5" />
                        </Button>
                     </TooltipTrigger>
                     <TooltipContent side="right">Folders</TooltipContent>
                  </Tooltip>
               </div>
            )}
          </div>
          </ScrollArea>

          {/* User Profile Footer - Fitts's Law: Large clickable area */}
          <div className="p-2 border-t border-slate-800 bg-slate-950">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className={cn(
                  "flex items-center gap-2 w-full p-2 rounded-lg hover:bg-slate-900/40 transition-colors group outline-none",
                  !isExpanded && "justify-center px-0"
                )}>
                  <div className="relative shrink-0">
                    <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-white font-medium text-xs shadow-lg ring-2 ring-slate-950">
                      {initials}
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-slate-950 rounded-full"></div>
                  </div>
                  
                  {isExpanded && (
                    <div className="flex-1 text-left overflow-hidden">
                      <div className="text-sm font-medium text-slate-200 truncate">{fullName}</div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                        <GraduationCap className="w-3 h-3" />
                        {role}
                      </div>
                    </div>
                  )}
                  
                  {isExpanded && (
                     <Settings className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
                  )}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" side={isExpanded ? "top" : "right"} className="w-64 bg-slate-900 border-slate-800 ml-2 mb-2 text-slate-200">
                <div className="flex items-center gap-3 p-3 bg-slate-800/50 mb-1">
                  <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white font-semibold text-sm shrink-0">
                    {initials}
                  </div>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-medium text-slate-50 truncate">{fullName}</span>
                    <span className="text-xs text-slate-400 truncate">{email}</span>
                  </div>
                </div>
                
                <DropdownMenuSeparator className="bg-slate-800" />
                
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger className="focus:bg-slate-800 focus:text-slate-50 cursor-pointer">
                    {currentTheme === "light" ? <Sun className="w-4 h-4 mr-2" /> : currentTheme === "dark" ? <Moon className="w-4 h-4 mr-2" /> : <Laptop className="w-4 h-4 mr-2" />}
                    Theme
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent className="bg-slate-900 border-slate-800 text-slate-200">
                    <DropdownMenuRadioGroup value={currentTheme} onValueChange={(value) => setTheme(value)}>
                      <DropdownMenuRadioItem value="light" className="focus:bg-slate-800 focus:text-slate-50 cursor-pointer">
                        <Sun className="w-4 h-4 mr-2" /> Light
                      </DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="dark" className="focus:bg-slate-800 focus:text-slate-50 cursor-pointer">
                        <Moon className="w-4 h-4 mr-2" /> Dark
                      </DropdownMenuRadioItem>
                      <DropdownMenuRadioItem value="system" className="focus:bg-slate-800 focus:text-slate-50 cursor-pointer">
                        <Laptop className="w-4 h-4 mr-2" /> System
                      </DropdownMenuRadioItem>
                    </DropdownMenuRadioGroup>
                  </DropdownMenuSubContent>
                </DropdownMenuSub>

                <DropdownMenuItem className="focus:bg-slate-800 focus:text-slate-50">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                
                <DropdownMenuSeparator className="bg-slate-800" />
                
                <DropdownMenuItem 
                  className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
                  onClick={() => signOut()}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
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
            className="w-full flex items-center gap-1.5 px-2 py-2 text-slate-500 hover:text-slate-200 hover:bg-slate-900/40 rounded transition-colors group"
         >
            <ChevronRight className={cn("w-3 h-3 transition-transform duration-200 shrink-0", isOpen && "rotate-90")} />
            <span className="text-[11px] font-bold tracking-wider uppercase group-hover:text-slate-200 flex-1 text-left">{label}</span>
            {count !== undefined && (
              <span className="text-[10px] text-slate-500 font-medium">{count}</span>
            )}
         </button>
         {isOpen && (
            <div className="mt-1 space-y-1">
               {children}
            </div>
         )}
      </div>
   )
}

function TreeItem({ icon: Icon, label, active, hasChildren, itemId, isStarred, onToggleStar }: { icon: any, label: string, active?: boolean, hasChildren?: boolean, itemId: string, isStarred: boolean, onToggleStar: (id: string) => void }) {
   return (
      <div className={cn(
         "flex items-center gap-2 px-2 py-2 cursor-pointer border-l-2 border-transparent hover:bg-slate-900/40 rounded transition-colors group relative",
         active ? "bg-slate-900/70 border-l-2 border-violet-500 text-slate-100" : "text-slate-400 hover:text-slate-200"
      )}>
         {hasChildren ? (
            <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
         ) : (
            <div className="w-3 shrink-0" /> 
         )}
         <Icon className={cn("w-3.5 h-3.5 shrink-0", active ? "text-violet-400" : "text-slate-400")} />
         <span className="text-xs truncate leading-none flex-1">{label}</span>
         <button
           onClick={(e) => {
             e.stopPropagation()
             onToggleStar(itemId)
           }}
           className={cn(
             "opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-slate-800/50 rounded shrink-0",
             isStarred && "opacity-100"
           )}
         >
           <Star className={cn(
             "w-3 h-3",
             isStarred ? "fill-yellow-500 text-yellow-500" : "text-slate-500"
           )} />
         </button>
      </div>
   )
}

function SortableTreeItem({ id, icon: Icon, label, active, hasChildren, itemId, isStarred, onToggleStar }: { id: string, icon: any, label: string, active?: boolean, hasChildren?: boolean, itemId: string, isStarred: boolean, onToggleStar: (id: string) => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="relative">
      <div className={cn(
        "flex items-center gap-2 px-2 py-2 cursor-pointer border-l-2 border-transparent hover:bg-slate-900/40 rounded transition-colors group relative",
        active ? "bg-slate-900/70 border-l-2 border-violet-500 text-slate-100" : "text-slate-400 hover:text-slate-200"
      )}>
        <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing shrink-0 text-slate-500 hover:text-slate-300 -ml-1">
          <GripVertical className="w-3 h-3" />
        </div>
        {hasChildren ? (
          <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
        ) : (
          <div className="w-3 shrink-0" /> 
        )}
        <Icon className={cn("w-3.5 h-3.5 shrink-0", active ? "text-violet-400" : "text-slate-400")} />
        <span className="text-xs truncate leading-none flex-1">{label}</span>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggleStar(itemId)
          }}
          className={cn(
            "opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-slate-800/50 rounded shrink-0",
            isStarred && "opacity-100"
          )}
        >
          <Star className={cn(
            "w-3 h-3",
            isStarred ? "fill-yellow-500 text-yellow-500" : "text-slate-500"
          )} />
        </button>
      </div>
    </div>
  )
}

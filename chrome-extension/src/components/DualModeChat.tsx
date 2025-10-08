import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Search, GraduationCap, History, Settings as SettingsIcon, Sparkles, X, LayoutDashboard, GitBranch, StickyNote, Brain } from 'lucide-react';
import { NavigateMode } from './NavigateMode';
import { EducateMode } from './EducateMode';
import { AutoMode } from './AutoMode';
import { Settings } from './Settings';
import { Dashboard } from './dashboard/Dashboard';
import { ConceptGraph } from './graph/ConceptGraph';
import { NotesPanel } from './notes/NotesPanel';
import { Button } from './ui/button';
import { ThemeToggle } from './ui/theme-toggle';
import { ScrollArea } from './ui/scroll-area';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { getStudentId } from '@/utils/studentId';

interface ChatHistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  mode: 'navigate' | 'educate' | 'auto';
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  mode?: 'navigate' | 'educate';
  timestamp: string;
}

interface DualModeChatProps {
  onClose?: () => void;
}

type TabType = 'auto' | 'navigate' | 'educate' | 'dashboard' | 'graph';

export function DualModeChat(_props: DualModeChatProps) {
  const [activeTab, setActiveTab] = useState<TabType>('auto');
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isNotesOpen, setIsNotesOpen] = useState(false);
  const [sessionId] = useState(`session-${Date.now()}`);
  const [studentId, setStudentId] = useState('anonymous');
  const [pendingModeSwitch, setPendingModeSwitch] = useState<{
    mode: 'navigate' | 'educate';
    query: string;
    responseData: any;
  } | null>(null);

  // Load student ID on mount
  useEffect(() => {
    getStudentId().then(setStudentId).catch(() => setStudentId('anonymous'));
  }, []);

  // Add query to history
  const addToHistory = (query: string, mode: 'navigate' | 'educate' | 'auto') => {
    const newItem: ChatHistoryItem = {
      id: Date.now().toString(),
      query,
      timestamp: new Date(),
      mode,
    };
    setChatHistory((prev) => [newItem, ...prev]);
  };

  // Add to conversation history for context tracking
  const addToConversation = (role: 'user' | 'assistant', content: string, mode?: 'navigate' | 'educate') => {
    setConversationHistory((prev) => [
      ...prev,
      {
        role,
        content,
        mode,
        timestamp: new Date().toISOString(),
      }
    ]);
  };

  // Handle auto mode routing to other tabs
  const handleAutoModeSwitch = (mode: 'navigate' | 'educate', query: string, responseData: any) => {
    setPendingModeSwitch({ mode, query, responseData });
    
    // Add to conversation history
    addToConversation('user', query, mode);
    
    // Animate tab switch
    setTimeout(() => {
      setActiveTab(mode);
      addToHistory(query, mode);
    }, 500);
  };

  // Load conversation from history
  const loadFromHistory = (item: ChatHistoryItem) => {
    if (item.mode === 'auto') {
      setActiveTab('auto');
    } else {
      setActiveTab(item.mode);
    }
    setIsHistoryOpen(false);
  };

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header with Gradient Background */}
        <div className="relative border-b bg-card/50 backdrop-blur-xl supports-[backdrop-filter]:bg-card/30 overflow-hidden">
          {/* Animated Background Gradient */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-blue-500/5 animate-gradient-x" />
          
          {/* Content */}
          <div className="relative flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              {/* Logo with Glow Effect */}
              <div className="relative">
                <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 blur-md opacity-50 animate-pulse" />
                <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg">
                  <Sparkles className="h-5 w-5 text-white animate-pulse" />
                </div>
              </div>
              
              {/* Title */}
              <div>
                <h1 className="text-sm font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Luminate AI
                </h1>
                <p className="text-xs text-muted-foreground">COMP-237 Intelligent Assistant</p>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center gap-1">
              <ThemeToggle />
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsNotesOpen(!isNotesOpen)}
                className={cn(
                  "gap-2 transition-all hover:scale-105 active:scale-95",
                  isNotesOpen && "bg-accent text-accent-foreground"
                )}
              >
                <StickyNote className="h-4 w-4" />
                <span className="text-xs hidden sm:inline">Notes</span>
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                className={cn(
                  "gap-2 transition-all hover:scale-105 active:scale-95",
                  isHistoryOpen && "bg-accent text-accent-foreground"
                )}
              >
                <History className="h-4 w-4" />
                <span className="text-xs hidden sm:inline">History</span>
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                className={cn(
                  "gap-2 transition-all hover:scale-105 active:scale-95",
                  isSettingsOpen && "bg-accent text-accent-foreground"
                )}
              >
                <SettingsIcon className="h-4 w-4" />
                <span className="text-xs hidden sm:inline">Settings</span>
              </Button>
            </div>
          </div>

          {/* Enhanced Mode Tabs */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
            <TabsList className="w-full h-auto grid grid-cols-5 gap-0 rounded-none border-t bg-background/50 p-0">
              {/* Auto Tab */}
              <TabsTrigger
                value="auto"
                className={cn(
                  "relative h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-teal-500",
                  "data-[state=active]:bg-teal-500/5 transition-all duration-300",
                  "hover:bg-accent/50 group"
                )}
              >
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-b from-teal-500/10 to-transparent opacity-0 transition-opacity duration-300",
                  activeTab === 'auto' && "opacity-100"
                )} />
                
                <div className="relative flex items-center gap-2.5">
                  <div className={cn(
                    "rounded-lg p-2 transition-all duration-300",
                    activeTab === 'auto' 
                      ? "bg-teal-500/20 text-teal-600 dark:text-teal-400 shadow-md scale-110" 
                      : "bg-muted text-muted-foreground group-hover:bg-teal-500/10"
                  )}>
                    <Brain className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <div className={cn(
                      "text-xs font-semibold transition-colors",
                      activeTab === 'auto' && "text-teal-600 dark:text-teal-400"
                    )}>
                      Auto
                    </div>
                    <div className="text-[10px] text-muted-foreground">Smart Routing</div>
                  </div>
                </div>
              </TabsTrigger>

              <TabsTrigger
                value="navigate"
                className={cn(
                  "relative h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500",
                  "data-[state=active]:bg-blue-500/5 transition-all duration-300",
                  "hover:bg-accent/50 group"
                )}
              >
                {/* Glow effect on active */}
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-b from-blue-500/10 to-transparent opacity-0 transition-opacity duration-300",
                  activeTab === 'navigate' && "opacity-100"
                )} />
                
                <div className="relative flex items-center gap-2.5">
                  <div className={cn(
                    "rounded-lg p-2 transition-all duration-300",
                    activeTab === 'navigate' 
                      ? "bg-blue-500/20 text-blue-600 dark:text-blue-400 shadow-md scale-110" 
                      : "bg-muted text-muted-foreground group-hover:bg-blue-500/10"
                  )}>
                    <Search className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <div className={cn(
                      "text-xs font-semibold transition-colors",
                      activeTab === 'navigate' && "text-blue-600 dark:text-blue-400"
                    )}>
                      Navigate
                    </div>
                    <div className="text-[10px] text-muted-foreground">Fast Search</div>
                  </div>
                </div>
              </TabsTrigger>

              <TabsTrigger
                value="educate"
                className={cn(
                  "relative h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-purple-500",
                  "data-[state=active]:bg-purple-500/5 transition-all duration-300",
                  "hover:bg-accent/50 group"
                )}
              >
                {/* Glow effect on active */}
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-b from-purple-500/10 to-transparent opacity-0 transition-opacity duration-300",
                  activeTab === 'educate' && "opacity-100"
                )} />
                
                <div className="relative flex items-center gap-2.5">
                  <div className={cn(
                    "rounded-lg p-2 transition-all duration-300",
                    activeTab === 'educate' 
                      ? "bg-purple-500/20 text-purple-600 dark:text-purple-400 shadow-md scale-110" 
                      : "bg-muted text-muted-foreground group-hover:bg-purple-500/10"
                  )}>
                    <GraduationCap className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <div className={cn(
                      "text-xs font-semibold transition-colors",
                      activeTab === 'educate' && "text-purple-600 dark:text-purple-400"
                    )}>
                      Educate
                    </div>
                    <div className="text-[10px] text-muted-foreground">Deep Learning</div>
                  </div>
                </div>
              </TabsTrigger>

              {/* Dashboard Tab */}
              <TabsTrigger
                value="dashboard"
                className={cn(
                  "relative h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-green-500",
                  "data-[state=active]:bg-green-500/5 transition-all duration-300",
                  "hover:bg-accent/50 group"
                )}
              >
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-b from-green-500/10 to-transparent opacity-0 transition-opacity duration-300",
                  activeTab === 'dashboard' && "opacity-100"
                )} />
                
                <div className="relative flex items-center gap-2.5">
                  <div className={cn(
                    "rounded-lg p-2 transition-all duration-300",
                    activeTab === 'dashboard' 
                      ? "bg-green-500/20 text-green-600 dark:text-green-400 shadow-md scale-110" 
                      : "bg-muted text-muted-foreground group-hover:bg-green-500/10"
                  )}>
                    <LayoutDashboard className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <div className={cn(
                      "text-xs font-semibold transition-colors",
                      activeTab === 'dashboard' && "text-green-600 dark:text-green-400"
                    )}>
                      Dashboard
                    </div>
                    <div className="text-[10px] text-muted-foreground">Progress</div>
                  </div>
                </div>
              </TabsTrigger>

              {/* Concept Graph Tab */}
              <TabsTrigger
                value="graph"
                className={cn(
                  "relative h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-orange-500",
                  "data-[state=active]:bg-orange-500/5 transition-all duration-300",
                  "hover:bg-accent/50 group"
                )}
              >
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-b from-orange-500/10 to-transparent opacity-0 transition-opacity duration-300",
                  activeTab === 'graph' && "opacity-100"
                )} />
                
                <div className="relative flex items-center gap-2.5">
                  <div className={cn(
                    "rounded-lg p-2 transition-all duration-300",
                    activeTab === 'graph' 
                      ? "bg-orange-500/20 text-orange-600 dark:text-orange-400 shadow-md scale-110" 
                      : "bg-muted text-muted-foreground group-hover:bg-orange-500/10"
                  )}>
                    <GitBranch className="h-4 w-4" />
                  </div>
                  <div className="text-left">
                    <div className={cn(
                      "text-xs font-semibold transition-colors",
                      activeTab === 'graph' && "text-orange-600 dark:text-orange-400"
                    )}>
                      Graph
                    </div>
                    <div className="text-[10px] text-muted-foreground">Concepts</div>
                  </div>
                </div>
              </TabsTrigger>
            </TabsList>

            <AnimatePresence mode="wait">
              <TabsContent value="auto" className="h-[calc(100vh-185px)] m-0">
                <motion.div
                  key="auto"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <AutoMode 
                    onQuery={(q: string) => addToHistory(q, 'auto')} 
                    onModeSwitch={handleAutoModeSwitch}
                    conversationHistory={conversationHistory}
                    sessionId={sessionId}
                    studentId={studentId}
                  />
                </motion.div>
              </TabsContent>

              <TabsContent value="navigate" className="h-[calc(100vh-185px)] m-0">
                <motion.div
                  key="navigate"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <NavigateMode 
                    onQuery={(q: string) => {
                      addToHistory(q, 'navigate');
                      addToConversation('user', q, 'navigate');
                    }}
                    pendingQuery={pendingModeSwitch?.mode === 'navigate' ? pendingModeSwitch : null}
                    onPendingHandled={() => setPendingModeSwitch(null)}
                  />
                </motion.div>
              </TabsContent>

              <TabsContent value="educate" className="h-[calc(100vh-185px)] m-0">
                <motion.div
                  key="educate"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <EducateMode 
                    onQuery={(q: string) => {
                      addToHistory(q, 'educate');
                      addToConversation('user', q, 'educate');
                    }}
                    pendingQuery={pendingModeSwitch?.mode === 'educate' ? pendingModeSwitch : null}
                    onPendingHandled={() => setPendingModeSwitch(null)}
                  />
                </motion.div>
              </TabsContent>

              <TabsContent value="dashboard" className="h-[calc(100vh-185px)] m-0">
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="h-full"
                >
                  <Dashboard />
                </motion.div>
              </TabsContent>

              <TabsContent value="graph" className="h-[calc(100vh-185px)] m-0">
                <motion.div
                  key="graph"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="h-full"
                >
                  <ConceptGraph />
                </motion.div>
              </TabsContent>
            </AnimatePresence>
          </Tabs>
        </div>
      </div>

      {/* Sliding History Sidebar */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-80 bg-card border-l shadow-2xl z-50",
          "transform transition-transform duration-300 ease-out",
          isHistoryOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* History Header */}
        <div className="flex items-center justify-between border-b px-4 py-3 bg-card/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold text-sm">Chat History</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsHistoryOpen(false)}
            className="h-8 w-8 p-0 hover:bg-destructive/10 hover:text-destructive"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* History Content */}
        <ScrollArea className="h-[calc(100vh-57px)]">
          <div className="p-4 space-y-2">
            {chatHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 p-4 mb-4">
                  <History className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">No history yet</p>
                <p className="text-xs text-muted-foreground mt-2 max-w-[200px]">
                  Your conversations will appear here as you chat with Luminate AI
                </p>
              </div>
            ) : (
              chatHistory.map((item) => (
                <button
                  key={item.id}
                  onClick={() => loadFromHistory(item)}
                  className={cn(
                    "w-full text-left p-3 rounded-xl border transition-all duration-200",
                    "hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]",
                    item.mode === 'navigate' 
                      ? "border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-blue-500/0 hover:border-blue-500/40 hover:from-blue-500/10" 
                      : "border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-purple-500/0 hover:border-purple-500/40 hover:from-purple-500/10"
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    {item.mode === 'navigate' ? (
                      <div className="rounded-lg bg-blue-500/20 p-2 mt-0.5">
                        <Search className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                      </div>
                    ) : (
                      <div className="rounded-lg bg-purple-500/20 p-2 mt-0.5">
                        <GraduationCap className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium line-clamp-2 mb-1.5 leading-relaxed">
                        {item.query}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "text-[10px] font-bold uppercase tracking-wider",
                          item.mode === 'navigate' ? "text-blue-600 dark:text-blue-400" : "text-purple-600 dark:text-purple-400"
                        )}>
                          {item.mode}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {item.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Overlay when history is open */}
      {isHistoryOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 transition-opacity duration-300 animate-in fade-in"
          onClick={() => setIsHistoryOpen(false)}
        />
      )}
      
      {/* Settings Panel */}
      <Settings 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />

      {/* Notes Panel */}
      <NotesPanel
        isOpen={isNotesOpen}
        onClose={() => setIsNotesOpen(false)}
      />
    </div>
  );
}

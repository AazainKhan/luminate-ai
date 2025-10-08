import { useState } from 'react';
import { Sparkles, Zap, Brain, ArrowRight, AlertCircle, BookOpen, Search as SearchIcon, Code, Calculator, Lightbulb, Video } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import { PromptInput } from './enhanced/PromptInput';
import { StarterSuggestions } from './ui/starter-suggestions';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  mode?: 'navigate' | 'educate';
  timestamp: string;
}

interface AutoModeProps {
  onQuery?: (query: string) => void;
  onModeSwitch?: (mode: 'navigate' | 'educate', query: string, responseData: any) => void;
  conversationHistory?: ConversationMessage[];
  sessionId?: string;
  studentId?: string;
}

interface RoutingState {
  status: 'idle' | 'analyzing' | 'routing' | 'complete' | 'error';
  selectedMode?: 'navigate' | 'educate';
  confidence?: number;
  reasoning?: string;
  shouldConfirm?: boolean;
  isFollowUp?: boolean;
}

const AUTO_SUGGESTIONS = [
  {
    icon: Brain,
    title: 'Explain Gradient Descent',
    query: 'Explain how gradient descent works',
    color: 'teal'
  },
  {
    icon: SearchIcon,
    title: 'Find Neural Network Materials',
    query: 'Find materials about neural networks',
    color: 'blue'
  },
  {
    icon: Calculator,
    title: 'Quiz on Search Algorithms',
    query: 'Quiz me on search algorithms',
    color: 'purple'
  },
  {
    icon: Lightbulb,
    title: 'Understand Backpropagation',
    query: 'What is backpropagation?',
    color: 'amber'
  },
  {
    icon: BookOpen,
    title: 'Week 5 Resources',
    query: 'Show me resources for Week 5',
    color: 'green'
  },
  {
    icon: Code,
    title: 'Learn A* Search',
    query: 'Help me understand A* search',
    color: 'cyan'
  }
];

export function AutoMode({ 
  onQuery, 
  onModeSwitch, 
  conversationHistory = [],
  sessionId,
  studentId 
}: AutoModeProps) {
  const [messages, setMessages] = useState<any[]>([]);
  const [routingState, setRoutingState] = useState<RoutingState>({ status: 'idle' });
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (message: { text?: string }) => {
    const query = message.text?.trim();
    if (!query || isProcessing) return;

    if (onQuery) {
      onQuery(query);
    }

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsProcessing(true);
    setRoutingState({ status: 'analyzing' });

    try {
      const API_BASE = 'http://localhost:8000';
      
      // Call auto endpoint
      const response = await fetch(`${API_BASE}/api/auto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          student_id: studentId || 'anonymous',
          session_id: sessionId || `auto-${Date.now()}`,
          conversation_history: conversationHistory,
          stream: false
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Update routing state
      setRoutingState({
        status: 'routing',
        selectedMode: result.selected_mode,
        confidence: result.confidence,
        reasoning: result.reasoning,
        shouldConfirm: result.should_confirm,
        isFollowUp: result.is_follow_up,
      });

      // Wait briefly for animation
      await new Promise(resolve => setTimeout(resolve, 500));

      // Switch to the appropriate tab
      if (onModeSwitch) {
        onModeSwitch(result.selected_mode, query, result.response_data);
      }

      setRoutingState({ 
        status: 'complete',
        selectedMode: result.selected_mode,
        confidence: result.confidence,
        reasoning: result.reasoning,
      });

    } catch (error) {
      console.error('Auto mode error:', error);
      setRoutingState({ 
        status: 'error'
      });
      
      // Add error message
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your query. Please try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSuggestionSelect = (query: string) => {
    handleSubmit({ text: query });
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-background via-background to-teal-500/5">
      {/* Routing Status - Only show when routing */}
      <div className="border-b">
        <AnimatePresence>
          {routingState.status !== 'idle' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="p-3"
            >
              {routingState.status === 'analyzing' && (
                <Alert className="border-teal-500/50 bg-teal-500/10">
                  <Sparkles className="h-4 w-4 text-teal-600 animate-pulse" />
                  <AlertDescription className="text-sm">
                    Analyzing your query...
                  </AlertDescription>
                </Alert>
              )}

              {routingState.status === 'routing' && routingState.selectedMode && (
                <Alert className={cn(
                  "border-2",
                  routingState.selectedMode === 'navigate' 
                    ? "border-blue-500/50 bg-blue-500/10" 
                    : "border-purple-500/50 bg-purple-500/10"
                )}>
                  <ArrowRight className={cn(
                    "h-4 w-4 animate-pulse",
                    routingState.selectedMode === 'navigate' ? "text-blue-600" : "text-purple-600"
                  )} />
                  <AlertDescription className="text-sm space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        Routing to {routingState.selectedMode === 'navigate' ? 'Navigate' : 'Educate'} Mode
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {(routingState.confidence! * 100).toFixed(0)}% confident
                      </Badge>
                      {routingState.isFollowUp && (
                        <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-700">
                          Follow-up
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {routingState.reasoning}
                    </p>
                    {routingState.shouldConfirm && (
                      <p className="text-xs text-amber-600 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Low confidence - you can switch modes if needed
                      </p>
                    )}
                  </AlertDescription>
                </Alert>
              )}

              {routingState.status === 'error' && (
                <Alert className="border-red-500/50 bg-red-500/10">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-sm text-red-700">
                    Unable to process query. Please try again.
                  </AlertDescription>
                </Alert>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-background to-teal-50/20 dark:to-teal-950/10">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center min-h-[400px] px-4">
            <div className="text-center mb-8 max-w-2xl">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 to-blue-500 mb-4 shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Auto Mode</h2>
              <p className="text-muted-foreground text-sm">
                I'll intelligently choose between Navigate and Educate modes to best help you
              </p>
            </div>
            <StarterSuggestions
              suggestions={AUTO_SUGGESTIONS}
              onSelect={handleSuggestionSelect}
            />
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "rounded-lg p-4 max-w-[80%]",
              msg.role === 'user' 
                ? "ml-auto bg-teal-500 text-white" 
                : "mr-auto bg-card border"
            )}
          >
            <p className="text-sm">{msg.content}</p>
          </div>
        ))}
      </div>

      {/* Input Area - Fixed to bottom */}
      <div className="mt-auto px-4 py-2 border-t bg-card/50 backdrop-blur">
        <PromptInput
          onSubmit={handleSubmit}
          placeholder="Ask me anything... I'll figure out how to help"
          disabled={isProcessing}
        />
        <div className="flex items-center justify-center gap-2 mt-1.5 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span>Auto mode intelligently routes between Navigate and Educate</span>
        </div>
      </div>
    </div>
  );
}


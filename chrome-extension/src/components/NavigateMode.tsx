import { useState, useEffect } from 'react';
import { Search, ExternalLink, BookOpen, Sparkles, Copy, ThumbsUp, ThumbsDown, RotateCcw, ListTree } from 'lucide-react';
import { useStreamingText } from '../hooks/useStreamingText';
import { queryUnified, streamChat, StreamEvent } from '../services/api';
import { Conversation, ConversationContent, ConversationScrollButton } from './ai-elements/conversation';
import { Response } from './ai-elements/response';
import { PromptInput } from './enhanced/PromptInput';
import { MessageBubble } from './enhanced/MessageBubble';
import { Reasoning, ReasoningTrigger, ReasoningContent } from './ai-elements/reasoning';
import { Actions, Action, copyToClipboard } from './ai-elements/actions';
import { ExternalResources } from './ui/external-resources';
import { Separator } from './ui/separator';
import AgentPlan, { Task } from './ui/agent-plan';
import { StarterSuggestions, NAVIGATE_SUGGESTIONS } from './ui/starter-suggestions';

interface APIResult {
  title: string;
  url?: string;
  module?: string;
  relevance_explanation?: string;
}

interface AgentTrace {
  agent: string;
  action: string;
  status: 'in_progress' | 'completed';
  timestamp: string;
  count?: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  results?: APIResult[];
  relatedTopics?: Array<{ title: string; why_explore: string }>;
  reasoning?: string;
  confidence?: number;
  isStreaming?: boolean;
  fullContent?: string; // Store full content for streaming
  query?: string; // Store original query for external resources
  agentTraces?: AgentTrace[]; // Real-time agent execution traces
  briefSummary?: string; // One-sentence summary of the response
}

interface NavigateModeProps {
  onQuery?: (query: string) => void;
  pendingQuery?: { mode: string; query: string; responseData: any } | null;
  onPendingHandled?: () => void;
}

export function NavigateMode({ onQuery, pendingQuery, onPendingHandled }: NavigateModeProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Handle pending query from Auto mode
  useEffect(() => {
    if (pendingQuery && pendingQuery.query && pendingQuery.responseData) {
      console.log('📥 Navigate: Handling pending query from Auto mode', pendingQuery);
      
      // Add user message
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: pendingQuery.query,
        timestamp: new Date(),
      };

      // Add assistant message with pre-fetched data
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: pendingQuery.responseData.formatted_response || 'Here are the results.',
        briefSummary: pendingQuery.responseData.brief_summary || '',
        timestamp: new Date(),
        results: pendingQuery.responseData.top_results || [],
        relatedTopics: pendingQuery.responseData.related_topics || [],
        query: pendingQuery.query,
      };

      setMessages([userMessage, assistantMessage]);
      
      // Clear the pending query
      if (onPendingHandled) {
        onPendingHandled();
      }
    }
  }, [pendingQuery, onPendingHandled]);

  const stopStreaming = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((msg) =>
        msg.isStreaming ? { ...msg, isStreaming: false } : msg
      )
    );
  };

  const handleSubmit = async (message: { text?: string }) => {
    const value = message.text?.trim();
    if (!value || isStreaming) return;

    if (onQuery) {
      onQuery(value);
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: value,
      timestamp: new Date(),
    };

    const messageId = (Date.now() + 1).toString();
    const assistantMessage: ChatMessage = {
      id: messageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      query: value,
      agentTraces: [],
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      let fullContent = '';
      const traces: AgentTrace[] = [];
      
      for await (const event of streamChat([{role: 'user', content: value}], 'navigate')) {
        if (controller.signal.aborted) break;

        switch (event.type) {
          case 'agent_trace':
            traces.push(event.data as AgentTrace);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId ? { ...msg, agentTraces: [...traces] } : msg
              )
            );
            break;
          
          case 'text_delta':
            fullContent += event.delta || '';
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId ? { ...msg, content: fullContent } : msg
              )
            );
            break;
          
          case 'metadata':
            const results = event.data?.top_results || [];
            const relatedTopics = event.data?.related_topics?.map((topic: any) =>
              typeof topic === 'string' ? { title: topic, why_explore: '' } : topic
            ) || [];
            const briefSummary = event.data?.brief_summary || '';
            
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId ? { ...msg, results, relatedTopics, briefSummary } : msg
              )
            );
            break;
          
          case 'message_done':
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId ? { ...msg, isStreaming: false } : msg
              )
            );
            setIsStreaming(false);
            setAbortController(null);
            break;
          
          case 'error':
            throw new Error(event.error || 'Stream error');
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      
      console.error('Navigate mode error:', error);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== messageId),
        {
          id: messageId,
          role: 'assistant',
          content: '❌ **Connection Error**\n\nBackend not responding. Ensure it\'s running at `http://localhost:8000`',
          timestamp: new Date(),
        },
      ]);
      setIsStreaming(false);
      setAbortController(null);
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Mode Header */}

      {/* Conversation Area */}
      <Conversation className="flex-1 overflow-hidden bg-gradient-to-b from-background to-blue-50/20 dark:to-blue-950/10">
        <ConversationContent className="space-y-1">
          {/* Starter Suggestions - Show when no messages */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[400px] px-4">
              <div className="text-center mb-8 max-w-2xl">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-4 shadow-lg">
                  <Search className="h-8 w-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Navigate Mode</h2>
                <p className="text-muted-foreground text-sm">
                  Find specific COMP-237 course materials, assignments, and external resources
                </p>
              </div>
              <StarterSuggestions 
                suggestions={NAVIGATE_SUGGESTIONS}
                onSelect={(query) => handleSubmit({ text: query })}
              />
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id}>
              <MessageBubble
                role={message.role}
                timestamp={message.timestamp}
                isStreaming={message.isStreaming || false}
                mode="navigate"
              >
                {/* Brief Summary - One sentence overview */}
                {message.briefSummary && message.role === 'assistant' && (
                  <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      {message.briefSummary}
                    </p>
                  </div>
                )}
                
                <Response parseIncompleteMarkdown={true}>
                  {message.content}
                </Response>

                {/* Message Actions */}
                {message.role === 'assistant' && (
                  <Actions className="mt-3">
                    <Action
                      label="Copy response"
                      tooltip="Copy to clipboard"
                      onClick={async () => {
                        const success = await copyToClipboard(message.content);
                        if (success) {
                          console.log('Copied!');
                        }
                      }}
                    >
                      <Copy className="h-4 w-4" />
                    </Action>
                    <Action
                      label="Helpful"
                      tooltip="Mark as helpful"
                      onClick={() => console.log('Helpful')}
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </Action>
                    <Action
                      label="Not helpful"
                      tooltip="Mark as not helpful"
                      onClick={() => console.log('Not helpful')}
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </Action>
                  </Actions>
                )}

                {/* Reasoning Section */}
                {message.reasoning && message.role === 'assistant' && (
                  <div className="mt-3">
                    <Reasoning>
                      <ReasoningTrigger>
                        💭 How I analyzed this query
                      </ReasoningTrigger>
                      <ReasoningContent>
                        <p className="text-sm leading-relaxed">{message.reasoning}</p>
                        {message.confidence !== undefined && (
                          <div className="mt-2 pt-2 border-t border-primary/20">
                            <div className="flex items-center justify-between text-xs">
                              <span>Confidence Score:</span>
                              <span className="font-bold">{(message.confidence * 100).toFixed(0)}%</span>
                            </div>
                            <div className="mt-1 h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                              <div 
                                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                                style={{ width: `${message.confidence * 100}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </ReasoningContent>
                    </Reasoning>
                  </div>
                )}

                {/* Agent Execution Plan - Only show if we have successful agent traces */}
                {message.role === 'assistant' && !message.isStreaming && message.agentTraces && message.agentTraces.length > 0 && message.agentTraces.some(t => t.status === 'completed') && !message.content.includes('Error') && !message.content.includes('failed') && (
                  <div className="mt-4">
                    <Reasoning>
                      <ReasoningTrigger>
                        <div className="flex items-center gap-2">
                          <ListTree className="h-4 w-4" />
                          <span>View Agent Execution Plan</span>
                        </div>
                      </ReasoningTrigger>
                      <ReasoningContent>
                        <div className="mt-2">
                          <AgentPlan tasks={(() => {
                            const completedTraces = message.agentTraces!.filter(t => t.status === 'completed');
                            const groupedByAgent = completedTraces.reduce((acc, trace) => {
                              if (!acc[trace.agent]) {
                                acc[trace.agent] = [];
                              }
                              acc[trace.agent].push(trace);
                              return acc;
                            }, {} as Record<string, typeof completedTraces>);
                            
                            return Object.entries(groupedByAgent).map(([agent, traces], idx) => ({
                              id: String(idx + 1),
                              title: agent.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
                              description: traces[0].action,
                              status: 'completed' as const,
                              priority: (idx < 2 ? 'high' : 'medium') as 'high' | 'medium' | 'low',
                              level: 0,
                              dependencies: idx > 0 ? [String(idx)] : [],
                              subtasks: traces.length > 1 ? traces.slice(1).map((t, i) => ({
                                id: `${idx + 1}.${i + 1}`,
                                title: t.action,
                                description: t.count ? `Processed ${t.count} items` : '',
                                status: 'completed' as const,
                                priority: 'medium' as const
                              })) : []
                            }));
                          })()} />
                        </div>
                      </ReasoningContent>
                    </Reasoning>
                  </div>
                )}

                {/* Search Results */}
                {message.results && message.results.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      <BookOpen className="h-3.5 w-3.5" />
                      Course Materials ({message.results.length})
                    </div>
                    <div className="grid gap-2">
                      {message.results.map((result, idx) => (
                        <a
                          key={idx}
                          href={result.url || '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group block p-4 rounded-xl border bg-card hover:bg-accent transition-all hover:shadow-lg hover:scale-[1.01] hover:border-blue-500/30 active:scale-[0.99]"
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 transition-colors group-hover:bg-blue-500/20">
                              <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-2">
                                <h4 className="text-sm font-semibold leading-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                  {result.title}
                                </h4>
                                <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                              {result.module && (
                                <div className="mt-1.5">
                                  <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600 dark:text-blue-400">
                                    {result.module}
                                  </span>
                                </div>
                              )}
                              {result.relevance_explanation && (
                                <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                                  {result.relevance_explanation}
                                </p>
                              )}
                            </div>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Related Topics */}
                {message.relatedTopics && message.relatedTopics.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold text-muted-foreground mb-2.5 flex items-center gap-1.5">
                      💡 Explore Related Topics
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.relatedTopics.map((topic, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSubmit({ text: topic.title })}
                          className="group relative overflow-hidden text-xs font-medium px-4 py-2 rounded-full border border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/15 hover:border-blue-500/40 transition-all hover:shadow-md hover:scale-105 active:scale-95"
                        >
                          <span className="relative z-10">{topic.title}</span>
                          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/10 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* External Resources - Lazy loaded */}
                {message.query && message.role === 'assistant' && !message.isStreaming && (
                  <div className="mt-4">
                    <Separator className="my-4" />
                    <ExternalResources 
                      query={message.query}
                      title="🌐 Load Additional Learning Resources"
                    />
                  </div>
                )}
              </MessageBubble>
            </div>
          ))}

          {/* Loading State */}
          {isStreaming && messages.filter(m => m.isStreaming).length === 0 && (
            <MessageBubble
              role="assistant"
              timestamp={new Date()}
              isStreaming={true}
              mode="navigate"
            >
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600" />
                </div>
                <p className="text-sm text-muted-foreground">
                  Searching course materials...
                </p>
              </div>
            </MessageBubble>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* Enhanced Prompt Input */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 px-4 py-2 shadow-lg">
        <PromptInput
          onSubmit={handleSubmit}
          onStop={stopStreaming}
          placeholder="Ask about COMP-237 topics, assignments, or resources..."
          disabled={false}
          isStreaming={isStreaming}
          mode="navigate"
        />
      </div>
    </div>
  );
}

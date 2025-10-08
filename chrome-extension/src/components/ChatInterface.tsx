import { useState, useEffect, useRef } from 'react';
import { Sparkles, X, Copy, RotateCcw, Trash2 } from 'lucide-react';
import { queryNavigateMode } from '../services/api';
import {
  initializeSession,
  setupAutoSave,
  saveMessagesLocally,
  clearLocalSession,
} from '../services/session';
import { copyToClipboard, formatMessageForSharing } from '../utils/clipboard';
import {
  Conversation,
  ConversationHeader,
  ConversationContent,
  ConversationFooter,
} from './ui/conversation';
import { Message, MessageContent } from './ui/message';
import { Response } from './ui/response';
import { PromptInput } from './ui/prompt-input';
import { Sources } from './ui/sources';
import { ExternalResources } from './ui/external-resources';
import { Suggestion, SuggestionGroup } from './ui/suggestion';
import { Loader } from './ui/loader';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { FullResponseSkeleton } from './ui/skeleton';

interface APIResult {
  title: string;
  url?: string;
  module?: string;
  relevance_explanation?: string;
  has_prerequisites?: boolean;
  has_next_steps?: boolean;
}

interface ExternalResource {
  title: string;
  url: string;
  description?: string;
  type: string;
  channel?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  query?: string;  // Store original query for lazy loading
  results?: APIResult[];
  relatedTopics?: Array<{ title: string; why_explore: string }>;
  externalResources?: ExternalResource[];  // Keep for backward compatibility but won't use
}

interface ChatInterfaceProps {
  onClose?: () => void;
}

export function ChatInterface({ onClose }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "👋 Hi! I'm Luminate AI, your COMP237 course assistant. Ask me anything about machine learning concepts, assignments, or course topics!",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const autoSaveCleanup = useRef<(() => void) | null>(null);

  // Initialize session and load previous messages
  useEffect(() => {
    const loadSession = async () => {
      try {
        const savedMessages = await initializeSession();
        if (savedMessages.length > 0) {
          setMessages(savedMessages);
          console.log('✓ Loaded', savedMessages.length, 'messages from session');
        }
      } catch (error) {
        console.error('Failed to load session:', error);
      }
    };
    
    loadSession();
  }, []);

  // Set up auto-save
  useEffect(() => {
    autoSaveCleanup.current = setupAutoSave(() => messages);
    
    return () => {
      if (autoSaveCleanup.current) {
        autoSaveCleanup.current();
      }
    };
  }, [messages]);

  // Save messages whenever they change
  useEffect(() => {
    if (messages.length > 1) {  // Don't save initial message only
      saveMessagesLocally(messages);
    }
  }, [messages]);

  const handleCopy = async (message: ChatMessage) => {
    const formattedText = formatMessageForSharing(
      message.content,
      message.results,
      message.relatedTopics
    );
    
    const success = await copyToClipboard(formattedText);
    if (success) {
      setCopySuccess(message.id);
      setTimeout(() => setCopySuccess(null), 2000);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Are you sure you want to clear all conversation history?')) {
      setMessages([{
        id: '1',
        role: 'assistant',
        content:
          "👋 Hi! I'm Luminate AI, your COMP237 course assistant. Ask me anything about machine learning concepts, assignments, or course topics!",
        timestamp: new Date(),
      }]);
      clearLocalSession();
    }
  };

  const handleRetry = async (originalMessage: ChatMessage) => {
    if (!originalMessage.content || isLoading) return;
    
    setRetryCount(prev => prev + 1);
    await handleSubmit(originalMessage.content);
  };

  const handleSubmit = async (value: string) => {
    if (!value.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: value,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await queryNavigateMode(value);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.formatted_response,
        timestamp: new Date(),
        query: value,  // Store the original query
        results: response.top_results,
        relatedTopics: response.related_topics,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setRetryCount(0); // Reset retry count on success
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error?.message?.includes('429')
          ? '⏱️ Rate limit reached. Please wait a moment before trying again.'
          : error?.message?.includes('503')
          ? '⚠️ The backend service is currently unavailable. Please ensure it is running on localhost:8000.'
          : '❌ Sorry, I encountered an error. Please try again or make sure the Luminate AI backend is running.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Convert API results to Sources format
  const convertToSources = (results: APIResult[]) => {
    return results.map((result) => ({
      title: result.title || 'Untitled',
      module: result.module,
      url: result.url,
      relevance_explanation: result.relevance_explanation,
    }));
  };

  return (
    <Conversation className="h-full bg-background">
      <ConversationHeader>
        <div className="flex items-center gap-3 flex-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold">Luminate AI</h1>
            <p className="text-xs text-muted-foreground">
              COMP237 Course Assistant
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 1 && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClearHistory}
              className="h-8 w-8"
              title="Clear conversation history"
            >
              <Trash2 className="h-4 w-4" />
              <span className="sr-only">Clear history</span>
            </Button>
          )}
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Button>
          )}
        </div>
      </ConversationHeader>

      <ConversationContent autoScroll>
        {messages.map((message) => (
          <Message key={message.id} role={message.role}>
            <MessageContent>
              <div className="flex items-start justify-between gap-2">
                <Response className="flex-1">{message.content}</Response>
                {message.role === 'assistant' && message.results && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleCopy(message)}
                    className="h-8 w-8 shrink-0"
                    title={copySuccess === message.id ? 'Copied!' : 'Copy response'}
                  >
                    <Copy className={`h-4 w-4 ${copySuccess === message.id ? 'text-green-500' : ''}`} />
                    <span className="sr-only">Copy</span>
                  </Button>
                )}
              </div>

              {message.results && message.results.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <Sources sources={convertToSources(message.results)} />
                </>
              )}

              {message.query && (
                <>
                  <Separator className="my-4" />
                  <ExternalResources query={message.query} />
                </>
              )}

              {message.relatedTopics && message.relatedTopics.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold">Explore Related Topics</h4>
                    <SuggestionGroup>
                      {message.relatedTopics.map((topic, idx) => (
                        <Suggestion
                          key={idx}
                          onClick={() => handleSubmit(topic.title)}
                          title={topic.why_explore}
                        >
                          {topic.title}
                        </Suggestion>
                      ))}
                    </SuggestionGroup>
                  </div>
                </>
              )}
              
              {message.role === 'assistant' && message.content.includes('error') && (
                <div className="mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const prevUserMsg = messages[messages.indexOf(message) - 1];
                      if (prevUserMsg?.role === 'user') {
                        handleRetry(prevUserMsg);
                      }
                    }}
                    className="gap-2"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Retry
                  </Button>
                </div>
              )}
            </MessageContent>
          </Message>
        ))}

        {isLoading && (
          <Message role="assistant">
            <MessageContent>
              <FullResponseSkeleton />
            </MessageContent>
          </Message>
        )}
      </ConversationContent>

      <ConversationFooter className="max-w-4xl mx-auto w-full">
        <PromptInput
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onSubmit={handleSubmit}
          placeholder="Ask about machine learning concepts, assignments, or topics..."
          isLoading={isLoading}
        />
      </ConversationFooter>
    </Conversation>
  );
}

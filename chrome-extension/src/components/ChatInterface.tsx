import { useState } from 'react';
import { Sparkles, X } from 'lucide-react';
import { queryNavigateMode } from '../services/api';
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
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          'Sorry, I encountered an error. Please make sure the Luminate AI backend is running on localhost:8000.',
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
        <div className="flex items-center gap-3">
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
      </ConversationHeader>

      <ConversationContent autoScroll>
        {messages.map((message) => (
          <Message key={message.id} role={message.role}>
            <MessageContent>
              <Response>{message.content}</Response>

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
            </MessageContent>
          </Message>
        ))}

        {isLoading && (
          <Message role="assistant">
            <MessageContent>
              <Loader size="md" text="Thinking..." />
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

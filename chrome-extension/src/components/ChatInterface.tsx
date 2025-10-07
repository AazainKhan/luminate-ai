import { useState } from 'react';
import { Sparkles, X } from 'lucide-react';
import { queryNavigateMode, queryEducateMode, EducateResponse } from '../services/api';
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

type Mode = 'navigate' | 'educate';

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
  mode: Mode;  // Track which mode was used
  
  // Navigate mode fields
  query?: string;
  results?: APIResult[];
  relatedTopics?: Array<{ title: string; why_explore: string }>;
  externalResources?: ExternalResource[];
  
  // Educate mode fields
  educateData?: EducateResponse;
}

interface ChatInterfaceProps {
  onClose?: () => void;
}

export function ChatInterface({ onClose }: ChatInterfaceProps) {
  const [mode, setMode] = useState<Mode>('navigate');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "👋 Hi! I'm Luminate AI, your COMP237 course assistant.\n\n**Navigate Mode**: Find specific course materials and resources.\n**Educate Mode**: Get explanations, problem-solving help, and tutoring.\n\nSwitch modes anytime using the buttons above!",
      timestamp: new Date(),
      mode: 'navigate'
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
      mode: mode,
    };

    setMessages((prev: ChatMessage[]) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (mode === 'navigate') {
        // Navigate Mode: Find course materials
        const response = await queryNavigateMode(value);

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.formatted_response,
          timestamp: new Date(),
          mode: 'navigate',
          query: value,
          results: response.top_results,
          relatedTopics: response.related_topics,
        };

        setMessages((prev: ChatMessage[]) => [...prev, assistantMessage]);
      } else {
        // Educate Mode: Tutoring and learning support
        const conversationHistory = messages.slice(-6).map((msg: ChatMessage) => ({
          role: msg.role,
          content: msg.content
        }));

        const response = await queryEducateMode(value, conversationHistory);

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.main_content,
          timestamp: new Date(),
          mode: 'educate',
          educateData: response,
        };

        setMessages((prev: ChatMessage[]) => [...prev, assistantMessage]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          'Sorry, I encountered an error. Please make sure the Luminate AI backend is running on localhost:8000.',
        timestamp: new Date(),
        mode: mode,
      };
      setMessages((prev: ChatMessage[]) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeSwitch = (newMode: Mode) => {
    setMode(newMode);
    // Add system message about mode switch
    const modeMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: newMode === 'navigate' 
        ? "🧭 Switched to Navigate Mode. Ask me to find specific course materials, assignments, or topics."
        : "🎓 Switched to Educate Mode. I'll help you understand concepts, solve problems, and learn more deeply!",
      timestamp: new Date(),
      mode: newMode,
    };
    setMessages((prev: ChatMessage[]) => [...prev, modeMessage]);
  };

  // Convert API results to Sources format
  const convertToSources = (results: APIResult[]) => {
    return results.map((result: APIResult) => ({
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
        <div className="flex items-center gap-2">
          {/* Mode Switcher */}
          <div className="flex gap-1 p-1 bg-muted rounded-lg">
            <Button
              variant={mode === 'navigate' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handleModeSwitch('navigate')}
              className="text-xs"
            >
              🧭 Navigate
            </Button>
            <Button
              variant={mode === 'educate' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handleModeSwitch('educate')}
              className="text-xs"
            >
              🎓 Educate
            </Button>
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
        </div>
      </ConversationHeader>

      <ConversationContent autoScroll>
        {messages.map((message: ChatMessage) => (
          <Message key={message.id} role={message.role}>
            <MessageContent>
              <Response>{message.content}</Response>

              {/* Navigate Mode: Show course materials */}
              {message.mode === 'navigate' && message.results && message.results.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <Sources sources={convertToSources(message.results)} />
                </>
              )}

              {message.mode === 'navigate' && message.query && (
                <>
                  <Separator className="my-4" />
                  <ExternalResources query={message.query} />
                </>
              )}

              {/* Educate Mode: Show educational content */}
              {message.mode === 'educate' && message.educateData && (
                <>
                  {/* Show hints for problem-solving */}
                  {message.educateData.hints && (
                    <>
                      <Separator className="my-4" />
                      <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                        <h4 className="text-sm font-semibold">💡 Hints</h4>
                        <div className="space-y-2 text-sm">
                          <details>
                            <summary className="cursor-pointer font-medium">Light Hint</summary>
                            <p className="mt-2 text-muted-foreground">{message.educateData.hints.light_hint}</p>
                          </details>
                          <details>
                            <summary className="cursor-pointer font-medium">Medium Hint</summary>
                            <p className="mt-2 text-muted-foreground">{message.educateData.hints.medium_hint}</p>
                          </details>
                          <details>
                            <summary className="cursor-pointer font-medium">Full Solution</summary>
                            <div className="mt-2 space-y-2">
                              <p className="font-medium">Steps:</p>
                              <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                                {message.educateData.hints.full_solution.steps.map((step: string, idx: number) => (
                                  <li key={idx}>{step}</li>
                                ))}
                              </ol>
                              <p className="mt-3">{message.educateData.hints.full_solution.explanation}</p>
                            </div>
                          </details>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Show Socratic questions */}
                  {message.educateData.socratic_questions && message.educateData.socratic_questions.length > 0 && (
                    <>
                      <Separator className="my-4" />
                      <div className="space-y-3 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                        <h4 className="text-sm font-semibold">🤔 Think About This</h4>
                        <div className="space-y-2">
                          {message.educateData.socratic_questions.map((q: { question: string; purpose: string }, idx: number) => (
                            <div key={idx} className="text-sm">
                              <p className="font-medium">{q.question}</p>
                              <p className="text-xs text-muted-foreground mt-1">{q.purpose}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  {/* Show misconception alert */}
                  {message.educateData.misconception_alert && (
                    <>
                      <Separator className="my-4" />
                      <div className="p-4 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                        <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200">
                          ⚠️ Common Misconception
                        </h4>
                        <p className="text-sm mt-2">{message.educateData.misconception_alert}</p>
                      </div>
                    </>
                  )}

                  {/* Show sources */}
                  {message.educateData.sources && message.educateData.sources.length > 0 && (
                    <>
                      <Separator className="my-4" />
                      <Sources sources={message.educateData.sources} />
                    </>
                  )}

                  {/* Show related concepts */}
                  {message.educateData.related_concepts && message.educateData.related_concepts.length > 0 && (
                    <>
                      <Separator className="my-4" />
                      <div className="space-y-3">
                        <h4 className="text-sm font-semibold">Explore Related Topics</h4>
                        <SuggestionGroup>
                          {message.educateData.related_concepts.map((concept: { title: string; why_explore: string }, idx: number) => (
                            <Suggestion
                              key={idx}
                              onClick={() => handleSubmit(concept.title)}
                              title={concept.why_explore}
                            >
                              {concept.title}
                            </Suggestion>
                          ))}
                        </SuggestionGroup>
                      </div>
                    </>
                  )}
                </>
              )}

              {/* Related topics for Navigate mode */}
              {message.mode === 'navigate' && message.relatedTopics && message.relatedTopics.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold">Explore Related Topics</h4>
                    <SuggestionGroup>
                      {message.relatedTopics.map((topic: { title: string; why_explore: string }, idx: number) => (
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

              {/* Follow-up suggestions for Educate mode */}
              {message.mode === 'educate' && message.educateData?.follow_up_suggestions && message.educateData.follow_up_suggestions.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold">Try Asking</h4>
                    <SuggestionGroup>
                      {message.educateData.follow_up_suggestions.map((suggestion: string, idx: number) => (
                        <Suggestion
                          key={idx}
                          onClick={() => handleSubmit(suggestion)}
                        >
                          {suggestion}
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
              <Loader size="md" text={mode === 'navigate' ? 'Searching...' : 'Thinking...'} />
            </MessageContent>
          </Message>
        )}
      </ConversationContent>

      <ConversationFooter className="max-w-4xl mx-auto w-full">
        <PromptInput
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onSubmit={handleSubmit}
          placeholder={
            mode === 'navigate'
              ? "Find course materials, assignments, or topics..."
              : "Ask about concepts, get help solving problems..."
          }
          isLoading={isLoading}
        />
      </ConversationFooter>
    </Conversation>
  );
}

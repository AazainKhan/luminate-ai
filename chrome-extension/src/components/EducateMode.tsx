import { useState, useRef, useCallback, useEffect } from 'react';
import { GraduationCap, Sparkles, Brain, Lightbulb, Copy, ThumbsUp, ThumbsDown, RotateCcw, Square, ListTree } from 'lucide-react';
import { queryUnified } from '../services/api';
import { Conversation, ConversationContent, ConversationScrollButton } from './ai-elements/conversation';
import { Response } from './ai-elements/response';
import { PromptInput } from './enhanced/PromptInput';
import { MessageBubble } from './enhanced/MessageBubble';
import { Reasoning, ReasoningTrigger, ReasoningContent } from './ai-elements/reasoning';
import { Actions, Action, copyToClipboard } from './ai-elements/actions';
import { Branch, BranchMessages, BranchSelector, BranchPrevious, BranchPage, BranchNext } from './ai/branch';
import { StudyPlanViewer } from './educate/StudyPlanViewer';
import { LearningPathViewer } from './educate/LearningPathViewer';
import AgentPlan, { Task } from './ui/agent-plan';
import { StarterSuggestions, EDUCATE_SUGGESTIONS } from './ui/starter-suggestions';

interface ResponseBranch {
  content: string;
  reasoning?: string;
  confidence?: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;  // Current branch content
  branches?: ResponseBranch[];  // Multiple response variations
  currentBranch?: number;  // Currently selected branch index
  timestamp: Date;
  reasoning?: string;
  confidence?: number;
  isStreaming?: boolean;
  fullContent?: string;
  // New fields for task visualization
  studyPlan?: any;
  planType?: 'weekly' | 'exam_prep' | 'topic_order';
  teachingStrategy?: string;
  interactionData?: any;
  showTaskView?: boolean;
  interactionType?: string;  // Type of interactive response
}

interface EducateModeProps {
  onQuery?: (query: string) => void;
  pendingQuery?: { mode: string; query: string; responseData: any } | null;
  onPendingHandled?: () => void;
}

export function EducateMode({ onQuery, pendingQuery, onPendingHandled }: EducateModeProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Handle pending query from Auto mode
  useEffect(() => {
    if (pendingQuery && pendingQuery.query && pendingQuery.responseData) {
      console.log('📥 Educate: Handling pending query from Auto mode', pendingQuery);
      
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
        content: pendingQuery.responseData.formatted_response || 'Let me help you understand that.',
        timestamp: new Date(),
        teachingStrategy: pendingQuery.responseData.teaching_strategy,
        studyPlan: pendingQuery.responseData.tasks ? { tasks: pendingQuery.responseData.tasks } : null,
      };

      setMessages([userMessage, assistantMessage]);
      
      // Clear the pending query
      if (onPendingHandled) {
        onPendingHandled();
      }
    }
  }, [pendingQuery, onPendingHandled]);
  const [isLoading, setIsLoading] = useState(false);
  const streamIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessageRef = useRef<string | null>(null);
  
  // Stop streaming function
  const stopStreaming = useCallback(() => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
    setIsLoading(false);
    
    // Mark current message as complete
    if (currentMessageRef.current) {
      setMessages(prev => prev.map(msg => 
        msg.id === currentMessageRef.current 
          ? { ...msg, isStreaming: false }
          : msg
      ));
      currentMessageRef.current = null;
    }
  }, []);

  // Rerun function - generates a new branch for the last assistant message
  const handleRerun = useCallback(async (messageId: string) => {
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) return;
    
    // Find the preceding user message
    let userQuery = '';
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userQuery = messages[i].content;
        break;
      }
    }
    
    if (!userQuery) return;
    
    setIsLoading(true);
    
    try {
      // Call API to get new variation
      const apiResponse = await queryUnified(userQuery);
      let responseContent = apiResponse.response.formatted_response;
      const reasoning = apiResponse.reasoning;
      const confidence = apiResponse.confidence;
      
      if (apiResponse.mode === 'navigate') {
        const confidencePercent = (confidence * 100).toFixed(0);
        responseContent = `🔵 **Switched to Navigate Mode** (${confidencePercent}% confidence)\n\n` +
          `*This query is better suited for quick information retrieval.*\n\n---\n\n${responseContent}`;
      }
      
      // Add new branch to the message
      setMessages(prev => prev.map(msg => {
        if (msg.id === messageId) {
          const branches = msg.branches || [{ content: msg.content, reasoning: msg.reasoning, confidence: msg.confidence }];
          const newBranches = [...branches, { content: responseContent, reasoning, confidence }];
          return {
            ...msg,
            branches: newBranches,
            currentBranch: newBranches.length - 1,  // Switch to new branch
            content: responseContent,
            reasoning,
            confidence,
            fullContent: responseContent,
            isStreaming: true
          };
        }
        return msg;
      }));
      
      // Stream the new response
      currentMessageRef.current = messageId;
      let index = 0;
      streamIntervalRef.current = setInterval(() => {
        if (index < responseContent.length) {
          setMessages(prev => prev.map(msg =>
            msg.id === messageId
              ? { ...msg, content: responseContent.substring(0, index + 1) }
              : msg
          ));
          index += 1;
        } else {
          if (streamIntervalRef.current) {
            clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
          }
          setMessages(prev => prev.map(msg =>
            msg.id === messageId ? { ...msg, isStreaming: false } : msg
          ));
          setIsLoading(false);
          currentMessageRef.current = null;
        }
      }, 10);
    } catch (error) {
      console.error('Rerun error:', error);
      setIsLoading(false);
    }
  }, [messages]);

  const handleSubmit = async (message: { text?: string }) => {
    const value = message.text?.trim();
    if (!value || isLoading) return;

    if (onQuery) {
      onQuery(value);
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: value,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call unified API (orchestrator will route to appropriate mode)
      const apiResponse = await queryUnified(value);
      
      // Format response based on mode
      let responseContent = apiResponse.response.formatted_response;
      const reasoning = apiResponse.reasoning;
      const confidence = apiResponse.confidence;
      
      // Extract task data if present (use any to handle dynamic response structure)
      const responseData = apiResponse.response as any;
      const studyPlan = responseData.tasks ? { tasks: responseData.tasks } : null;
      const planType = responseData.plan_type || 'weekly';
      const teachingStrategy = responseData.teaching_strategy;
      const interactionData = apiResponse.response;
      const showTaskView = responseData.show_task_view || false;
      
      // If orchestrator routed to Navigate mode, show indicator
      if (apiResponse.mode === 'navigate') {
        const confidencePercent = (confidence * 100).toFixed(0);
        responseContent = `🔵 **Switched to Navigate Mode** (${confidencePercent}% confidence)\n\n` +
          `*This query is better suited for quick information retrieval.*\n\n---\n\n${responseContent}`;
      }

      // Create initial message with streaming and branch support
      const messageId = (Date.now() + 1).toString();
      const assistantMessage: ChatMessage = {
        id: messageId,
        role: 'assistant',
        content: '',
        fullContent: responseContent,
        timestamp: new Date(),
        reasoning,
        confidence,
        isStreaming: true,
        branches: [{ content: responseContent, reasoning, confidence }],
        currentBranch: 0,
        // Add task visualization data
        studyPlan,
        planType,
        teachingStrategy,
        interactionData,
        showTaskView
      };

      setMessages((prev) => [...prev, assistantMessage]);
      currentMessageRef.current = messageId;

      // Stream character by character
      let index = 0;
      streamIntervalRef.current = setInterval(() => {
        if (index < responseContent.length) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId
                ? { ...msg, content: responseContent.substring(0, index + 1) }
                : msg
            )
          );
          index += 1;
        } else {
          if (streamIntervalRef.current) {
            clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, isStreaming: false } : msg
            )
          );
          setIsLoading(false);
          currentMessageRef.current = null;
        }
      }, 10);
    } catch (error) {
      console.error('Educate mode error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          '❌ **Connection Error**\n\nI couldn\'t reach the Luminate AI backend. Please ensure it\'s running:\n\n' +
          '```bash\ncd development/backend\npython fastapi_service/main.py\n```\n\n' +
          'The server should be accessible at `http://localhost:8000`',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      stopStreaming();
    } finally {
      if (!streamIntervalRef.current) {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">

      {/* Conversation Area */}
      <Conversation className="flex-1 overflow-hidden bg-gradient-to-b from-background to-purple-50/20 dark:to-purple-950/10">
        <ConversationContent className="space-y-1">
          {/* Starter Suggestions - Show when no messages */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[400px] px-4">
              <div className="text-center mb-8 max-w-2xl">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 mb-4 shadow-lg">
                  <GraduationCap className="h-8 w-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Educate Mode</h2>
                <p className="text-muted-foreground text-sm">
                  Deep learning support with 4-level math translations and step-by-step explanations
                </p>
              </div>
              <StarterSuggestions 
                suggestions={EDUCATE_SUGGESTIONS}
                onSelect={(query) => handleSubmit({ text: query })}
              />
            </div>
          )}
          
          {messages.map((message) => {
            // For assistant messages with branches
            if (message.role === 'assistant' && message.branches && message.branches.length > 0) {
              const totalBranches = message.branches.length;
              const currentBranch = message.currentBranch || 0;
              
              return (
                <div key={message.id}>
                  <Branch
                    totalBranches={totalBranches}
                    defaultBranch={currentBranch}
                    onBranchChange={(branchIndex) => {
                      // Update current branch when user navigates
                      setMessages(prev => prev.map(msg =>
                        msg.id === message.id
                          ? {
                              ...msg,
                              currentBranch: branchIndex,
                              content: msg.branches![branchIndex].content,
                              reasoning: msg.branches![branchIndex].reasoning,
                              confidence: msg.branches![branchIndex].confidence
                            }
                          : msg
                      ));
                    }}
                  >
                    <MessageBubble
                      role={message.role}
                      timestamp={message.timestamp}
                      isStreaming={message.isStreaming || false}
                      mode="educate"
                    >
                      <BranchMessages>
                        {message.branches.map((branch, idx) => (
                          <Response key={idx} parseIncompleteMarkdown={true}>
                            {idx === currentBranch ? message.content : branch.content}
                          </Response>
                        ))}
                      </BranchMessages>

                      {/* Message Actions */}
                      <Actions className="mt-3">
                        {/* Stop button (only when streaming) */}
                        {message.isStreaming && (
                          <Action
                            label="Stop"
                            tooltip="Stop generating"
                            onClick={stopStreaming}
                          >
                            <Square className="h-4 w-4" />
                          </Action>
                        )}
                        
                        {/* Rerun button */}
                        {!message.isStreaming && (
                          <Action
                            label="Rerun"
                            tooltip="Generate new variation"
                            onClick={() => handleRerun(message.id)}
                            disabled={isLoading}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Action>
                        )}
                        
                        <Action
                          label="Copy response"
                          tooltip="Copy explanation"
                          onClick={async () => {
                            await copyToClipboard(message.content);
                          }}
                        >
                          <Copy className="h-4 w-4" />
                        </Action>
                        <Action
                          label="Helpful"
                          tooltip="This helped me learn"
                          onClick={() => console.log('Helpful')}
                        >
                          <ThumbsUp className="h-4 w-4" />
                        </Action>
                        <Action
                          label="Not helpful"
                          tooltip="I need more clarification"
                          onClick={() => console.log('Not helpful')}
                        >
                          <ThumbsDown className="h-4 w-4" />
                        </Action>
                      </Actions>

                      {/* Branch Navigation */}
                      <BranchSelector from={message.role}>
                        <BranchPrevious />
                        <BranchPage />
                        <BranchNext />
                      </BranchSelector>

                      {/* Reasoning Section */}
                      {message.reasoning && (
                        <div className="mt-3">
                          <Reasoning>
                            <ReasoningTrigger>
                              <div className="flex items-center gap-2">
                                <Lightbulb className="h-4 w-4" />
                                <span>My teaching approach</span>
                              </div>
                            </ReasoningTrigger>
                            <ReasoningContent>
                              <p className="text-sm leading-relaxed">{message.reasoning}</p>
                              {message.confidence !== undefined && (
                                <div className="mt-3 pt-3 border-t border-primary/20">
                                  <div className="flex items-center justify-between text-xs">
                                    <span className="flex items-center gap-1.5">
                                      <Brain className="h-3.5 w-3.5" />
                                      Confidence Score:
                                    </span>
                                    <span className="font-bold">{(message.confidence * 100).toFixed(0)}%</span>
                                  </div>
                                  <div className="mt-1.5 h-2 w-full rounded-full bg-secondary overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-purple-500 to-violet-500 transition-all duration-500"
                                      style={{ width: `${message.confidence * 100}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </ReasoningContent>
                          </Reasoning>
                        </div>
                      )}
                      
                      {/* Agent Execution Plan */}
                      {!message.isStreaming && !message.content.includes('Error') && !message.content.includes('failed') && (
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
                                <AgentPlan tasks={[
                                  {
                                    id: "1",
                                    title: "Math Formula Detection",
                                    description: "Check if query requests mathematical explanation",
                                    status: "completed",
                                    priority: "high",
                                    level: 0,
                                    dependencies: [],
                                    subtasks: [
                                      {
                                        id: "1.1",
                                        title: "Keyword matching",
                                        description: "Scan for: explain, formula, equation, algorithm, etc.",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["pattern-matcher"]
                                      },
                                      {
                                        id: "1.2",
                                        title: "Topic identification",
                                        description: "Match against 5 supported formulas (gradient descent, backprop, etc.)",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["topic-classifier"]
                                      }
                                    ]
                                  },
                                  {
                                    id: "2",
                                    title: "4-Level Translation",
                                    description: "Generate multi-level explanation",
                                    status: "completed",
                                    priority: "high",
                                    level: 0,
                                    dependencies: ["1"],
                                    subtasks: [
                                      {
                                        id: "2.1",
                                        title: "Level 1: Intuition",
                                        description: "Plain language analogy (e.g., blindfolded hill descent)",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["gemini-2.5-flash", "analogy-generator"]
                                      },
                                      {
                                        id: "2.2",
                                        title: "Level 2: Mathematics",
                                        description: "LaTeX formula with variable explanations",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["latex-renderer", "math-explainer"]
                                      },
                                      {
                                        id: "2.3",
                                        title: "Level 3: Code",
                                        description: "Working Python implementation (25-30 lines)",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["code-generator", "syntax-highlighter"]
                                      },
                                      {
                                        id: "2.4",
                                        title: "Level 4: Misconceptions",
                                        description: "Common mistakes and corrections",
                                        status: "completed",
                                        priority: "medium",
                                        tools: ["misconception-detector"]
                                      }
                                    ]
                                  },
                                  {
                                    id: "3",
                                    title: "Response Formatting",
                                    description: "Format for KaTeX markdown rendering",
                                    status: "completed",
                                    priority: "medium",
                                    level: 0,
                                    dependencies: ["2"],
                                    subtasks: [
                                      {
                                        id: "3.1",
                                        title: "Markdown generation",
                                        description: "Structure with headers and sections",
                                        status: "completed",
                                        priority: "high",
                                        tools: ["markdown-formatter"]
                                      },
                                      {
                                        id: "3.2",
                                        title: "Add next steps",
                                        description: "Suggest practice actions and variations",
                                        status: "completed",
                                        priority: "low",
                                        tools: ["pedagogy-advisor"]
                                      }
                                    ]
                                  }
                                ]} />
                              </div>
                            </ReasoningContent>
                          </Reasoning>
                        </div>
                      )}
                    </MessageBubble>
                  </Branch>
                </div>
              );
            }
            
            // Regular message rendering for user messages and simple assistant messages
            return (
              <div key={message.id}>
                <MessageBubble
                  role={message.role}
                  timestamp={message.timestamp}
                  isStreaming={message.isStreaming || false}
                  mode="educate"
                >
                  {/* Teaching Strategy Badge */}
                  {message.teachingStrategy && message.role === 'assistant' && (
                    <div className="mb-3 flex items-center gap-2">
                      <div className="inline-flex items-center rounded-full bg-purple-100 dark:bg-purple-900/30 px-3 py-1 text-xs font-medium text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                        <Brain className="h-3 w-3 mr-1.5" />
                        {message.teachingStrategy === 'scaffolded_hints' && 'Progressive Hints'}
                        {message.teachingStrategy === 'direct_explanation' && 'Direct Explanation'}
                        {message.teachingStrategy === 'worked_example' && 'Worked Example'}
                        {message.teachingStrategy === 'quiz' && 'Interactive Quiz'}
                        {message.teachingStrategy === 'socratic_dialogue' && 'Socratic Dialogue'}
                        {message.teachingStrategy === 'concept_map' && 'Concept Map'}
                        {!['scaffolded_hints', 'direct_explanation', 'worked_example', 'quiz', 'socratic_dialogue', 'concept_map'].includes(message.teachingStrategy) && message.teachingStrategy}
                      </div>
                    </div>
                  )}
                  
                  <Response parseIncompleteMarkdown={true}>
                    {message.content}
                  </Response>

                  {/* Actions for non-branched messages */}
                  {message.role === 'assistant' && (
                    <Actions className="mt-3">
                      {message.isStreaming && (
                        <Action
                          label="Stop"
                          tooltip="Stop generating"
                          onClick={stopStreaming}
                        >
                          <Square className="h-4 w-4" />
                        </Action>
                      )}
                      {!message.isStreaming && (
                        <Action
                          label="Rerun"
                          tooltip="Generate new variation"
                          onClick={() => handleRerun(message.id)}
                          disabled={isLoading}
                        >
                          <RotateCcw className="h-4 w-4" />
                        </Action>
                      )}
                      <Action
                        label="Copy response"
                        tooltip="Copy explanation"
                        onClick={async () => {
                          await copyToClipboard(message.content);
                        }}
                      >
                        <Copy className="h-4 w-4" />
                      </Action>
                    </Actions>
                  )}

                  {/* Reasoning for simple messages */}
                  {message.reasoning && message.role === 'assistant' && (
                    <div className="mt-3">
                      <Reasoning>
                        <ReasoningTrigger>
                          <div className="flex items-center gap-2">
                            <Lightbulb className="h-4 w-4" />
                            <span>My teaching approach</span>
                          </div>
                        </ReasoningTrigger>
                        <ReasoningContent>
                          <p className="text-sm leading-relaxed">{message.reasoning}</p>
                          {message.confidence !== undefined && (
                            <div className="mt-3 pt-3 border-t border-primary/20">
                              <div className="flex items-center justify-between text-xs">
                                <span className="flex items-center gap-1.5">
                                  <Brain className="h-3.5 w-3.5" />
                                  Confidence Score:
                                </span>
                                <span className="font-bold">{(message.confidence * 100).toFixed(0)}%</span>
                              </div>
                              <div className="mt-1.5 h-2 w-full rounded-full bg-secondary overflow-hidden">
                                <div 
                                  className="h-full bg-gradient-to-r from-purple-500 to-violet-500 transition-all duration-500"
                                  style={{ width: `${message.confidence * 100}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </ReasoningContent>
                      </Reasoning>
                    </div>
                  )}

                  {/* Agent Execution Plan for simple messages */}
                  {message.role === 'assistant' && !message.isStreaming && !message.content.includes('Error') && !message.content.includes('failed') && (
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
                            <AgentPlan tasks={[
                              {
                                id: "1",
                                title: "Query Classification",
                                description: "Determine if math formula or conceptual question",
                                status: "completed",
                                priority: "high",
                                level: 0,
                                dependencies: [],
                                subtasks: [
                                  {
                                    id: "1.1",
                                    title: "Pattern matching",
                                    description: "Check for math keywords and formulas",
                                    status: "completed",
                                    priority: "high",
                                    tools: ["keyword-detector"]
                                  }
                                ]
                              },
                              {
                                id: "2",
                                title: "Context Retrieval",
                                description: "Get relevant course materials from ChromaDB",
                                status: "completed",
                                priority: "high",
                                level: 0,
                                dependencies: ["1"],
                                subtasks: [
                                  {
                                    id: "2.1",
                                    title: "Semantic search",
                                    description: "Query 917 documents for relevant content",
                                    status: "completed",
                                    priority: "high",
                                    tools: ["chromadb"]
                                  }
                                ]
                              },
                              {
                                id: "3",
                                title: "Explanation Generation",
                                description: "Create adaptive educational response",
                                status: "completed",
                                priority: "high",
                                level: 0,
                                dependencies: ["2"],
                                subtasks: [
                                  {
                                    id: "3.1",
                                    title: "Conceptual explanation",
                                    description: "Generate clear, pedagogical answer",
                                    status: "completed",
                                    priority: "high",
                                    tools: ["gemini-2.5-flash"]
                                  },
                                  {
                                    id: "3.2",
                                    title: "Add sources",
                                    description: "Include course material references",
                                    status: "completed",
                                    priority: "medium",
                                    tools: ["source-formatter"]
                                  }
                                ]
                              }
                            ]} />
                          </div>
                        </ReasoningContent>
                      </Reasoning>
                    </div>
                  )}

                  {/* Task Visualization */}
                  {message.role === 'assistant' && message.showTaskView && message.studyPlan && (
                    <div className="mt-4">
                      <StudyPlanViewer
                        studyPlanData={message.studyPlan}
                        planType={message.planType}
                      />
                    </div>
                  )}
                  
                  {message.role === 'assistant' && message.teachingStrategy && message.interactionData?.tasks && (
                    <div className="mt-4">
                      <LearningPathViewer
                        teachingStrategy={message.teachingStrategy}
                        interactionData={message.interactionData}
                      />
                    </div>
                  )}
                </MessageBubble>
              </div>
            );
          })}

          {/* Loading State */}
          {isLoading && !currentMessageRef.current && (
            <MessageBubble
              role="assistant"
              timestamp={new Date()}
              isStreaming={true}
              mode="educate"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-purple-600 [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-purple-600 [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-purple-600" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Analyzing your question...
                  </p>
                </div>
                <p className="text-xs text-muted-foreground/70 italic">
                  Preparing a detailed, multi-level explanation tailored to your learning needs
                </p>
              </div>
            </MessageBubble>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* Enhanced Prompt Input with Stop Support */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 px-4 py-2 shadow-lg">
        <PromptInput 
          onSubmit={handleSubmit}
          onStop={stopStreaming}
          placeholder="Ask me to explain a concept, solve a problem, or visualize an algorithm..."
          disabled={isLoading && !currentMessageRef.current}
          isStreaming={isLoading && !!currentMessageRef.current}
          mode="educate"
        />
      </div>
    </div>
  );
}

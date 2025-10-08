/**
 * useAIChat Hook
 * Manages streaming chat with agent traces
 */

import { useState, useCallback, useRef } from 'react';
import { streamChat, StreamEvent } from '@/services/api';
import { getStudentId, getSessionId } from '@/utils/studentId';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agentTraces?: AgentTrace[];
  metadata?: any;
  isStreaming?: boolean;
}

interface AgentTrace {
  agent: string;
  action: string;
  input?: any;
  output?: any;
  count?: number;
  timestamp?: string;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export function useAIChat(mode: 'navigate' | 'educate') {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const currentMessageIdRef = useRef<string>('');

  /**
   * Send a message
   */
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Create user message
    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Add user message
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    // Create assistant message placeholder
    const assistantMessageId = `assistant_${Date.now()}`;
    currentMessageIdRef.current = assistantMessageId;

    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      agentTraces: [],
      isStreaming: true,
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, assistantMessage],
    }));

    try {
      const studentId = await getStudentId();
      const sessionId = getSessionId();

      // Prepare messages for API
      const apiMessages = state.messages.map(m => ({
        role: m.role,
        content: m.content,
      }));
      apiMessages.push({ role: 'user', content });

      // Stream the response
      const stream = streamChat(apiMessages, mode, studentId, sessionId);

      for await (const event of stream) {
        handleStreamEvent(event, assistantMessageId);
      }

      // Mark as done
      setState(prev => ({
        ...prev,
        messages: prev.messages.map(m =>
          m.id === assistantMessageId
            ? { ...m, isStreaming: false }
            : m
        ),
        isLoading: false,
      }));

    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to send message',
      }));

      // Remove placeholder message on error
      setState(prev => ({
        ...prev,
        messages: prev.messages.filter(m => m.id !== assistantMessageId),
      }));
    }
  }, [mode, state.messages]);

  /**
   * Handle streaming events
   */
  const handleStreamEvent = useCallback((event: StreamEvent, messageId: string) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map(m => {
        if (m.id !== messageId) return m;

        switch (event.type) {
          case 'text_delta':
            return {
              ...m,
              content: m.content + (event.delta || ''),
            };

          case 'agent_trace':
            return {
              ...m,
              agentTraces: [...(m.agentTraces || []), event.data as AgentTrace],
            };

          case 'metadata':
            return {
              ...m,
              metadata: event.data,
            };

          case 'message_done':
            return {
              ...m,
              isStreaming: false,
            };

          case 'error':
            // Error is handled in sendMessage
            return m;

          default:
            return m;
        }
      }),
    }));
  }, []);

  /**
   * Stop streaming
   */
  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isLoading: false,
      messages: prev.messages.map(m =>
        m.id === currentMessageIdRef.current
          ? { ...m, isStreaming: false }
          : m
      ),
    }));
  }, []);

  /**
   * Clear chat history
   */
  const clear = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      error: null,
    });
  }, []);

  /**
   * Reload last message
   */
  const reload = useCallback(() => {
    if (state.messages.length < 2) return;

    // Find last user message
    const lastUserMessage = [...state.messages]
      .reverse()
      .find(m => m.role === 'user');

    if (lastUserMessage) {
      // Remove messages after the last user message
      setState(prev => ({
        ...prev,
        messages: prev.messages.filter(
          m => new Date(m.timestamp) <= new Date(lastUserMessage.timestamp)
        ),
      }));

      // Resend
      sendMessage(lastUserMessage.content);
    }
  }, [state.messages, sendMessage]);

  /**
   * Get agent trace summary
   */
  const getAgentTraceSummary = (messageId: string): string[] => {
    const message = state.messages.find(m => m.id === messageId);
    if (!message || !message.agentTraces) return [];

    return message.agentTraces.map(trace => {
      if (trace.count !== undefined) {
        return `${trace.agent}: ${trace.action} (${trace.count})`;
      }
      return `${trace.agent}: ${trace.action}`;
    });
  };

  return {
    // State
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    sendMessage,
    stop,
    clear,
    reload,

    // Utilities
    getAgentTraceSummary,
  };
}


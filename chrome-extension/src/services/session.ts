/**
 * Session management utility
 * Handles conversation persistence using chrome.storage
 */

import { ConversationMessage, saveConversation, loadConversation } from './api';

const SESSION_STORAGE_KEY = 'luminate_session_id';
const MESSAGES_STORAGE_KEY = 'luminate_messages';
const AUTO_SAVE_INTERVAL_MS = 30000; // Auto-save every 30 seconds

/**
 * Get or create a session ID
 */
export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  
  return sessionId;
}

/**
 * Save messages to local storage
 */
export function saveMessagesLocally(messages: any[]): void {
  try {
    localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  } catch (error) {
    console.error('Failed to save messages locally:', error);
  }
}

/**
 * Load messages from local storage
 */
export function loadMessagesLocally(): any[] {
  try {
    const data = localStorage.getItem(MESSAGES_STORAGE_KEY);
    if (data) {
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Failed to load messages locally:', error);
  }
  return [];
}

/**
 * Clear local session data
 */
export function clearLocalSession(): void {
  localStorage.removeItem(SESSION_STORAGE_KEY);
  localStorage.removeItem(MESSAGES_STORAGE_KEY);
}

/**
 * Save conversation to backend
 */
export async function saveConversationToBackend(messages: any[]): Promise<boolean> {
  try {
    const sessionId = getSessionId();
    
    // Convert to API format
    const apiMessages: ConversationMessage[] = messages.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp.toISOString ? msg.timestamp.toISOString() : msg.timestamp,
      results: msg.results,
      related_topics: msg.relatedTopics,
    }));
    
    await saveConversation(sessionId, apiMessages);
    return true;
  } catch (error) {
    console.error('Failed to save conversation to backend:', error);
    return false;
  }
}

/**
 * Load conversation from backend
 */
export async function loadConversationFromBackend(): Promise<any[]> {
  try {
    const sessionId = getSessionId();
    const response = await loadConversation(sessionId);
    
    if (!response.messages || response.messages.length === 0) {
      return [];
    }
    
    // Convert from API format
    return response.messages.map((msg, index) => ({
      id: `${index}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp: new Date(msg.timestamp),
      results: msg.results,
      relatedTopics: msg.related_topics,
    }));
  } catch (error) {
    console.error('Failed to load conversation from backend:', error);
    return [];
  }
}

/**
 * Set up auto-save for conversation
 */
export function setupAutoSave(
  getMessages: () => any[],
  interval: number = AUTO_SAVE_INTERVAL_MS
): () => void {
  const intervalId = setInterval(async () => {
    const messages = getMessages();
    if (messages.length > 0) {
      // Save locally first (faster)
      saveMessagesLocally(messages);
      
      // Try to save to backend (may fail if offline)
      await saveConversationToBackend(messages).catch(() => {
        // Silently fail - local storage is our backup
      });
    }
  }, interval);
  
  // Return cleanup function
  return () => clearInterval(intervalId);
}

/**
 * Initialize session and load previous messages
 */
export async function initializeSession(): Promise<any[]> {
  // Try to load from backend first
  const backendMessages = await loadConversationFromBackend();
  if (backendMessages.length > 0) {
    return backendMessages;
  }
  
  // Fallback to local storage
  const localMessages = loadMessagesLocally();
  return localMessages;
}

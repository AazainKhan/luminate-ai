/**
 * API service for Luminate AI backend
 * Enhanced with retry logic, better error handling, and conversation persistence
 */

const API_BASE_URL = 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;
const BACKOFF_MULTIPLIER = 2;

export interface NavigateResponse {
  formatted_response: string;
  top_results: Array<{
    title: string;
    url?: string;
    module?: string;
    relevance_explanation?: string;
    has_prerequisites?: boolean;
    has_next_steps?: boolean;
  }>;
  related_topics: Array<{title: string; why_explore: string}>;
  external_resources?: Array<{
    title: string;
    url: string;
    description?: string;
    type: string;
    channel?: string;
  }>;
  next_steps?: string[];
}

export interface ExternalResourcesResponse {
  resources: Array<{
    title: string;
    url: string;
    description?: string;
    type: string;
    channel?: string;
  }>;
  count: number;
}

export interface ConversationMessage {
  role: string;
  content: string;
  timestamp: string;
  results?: any[];
  related_topics?: any[];
}

export interface SaveConversationResponse {
  success: boolean;
  session_id: string;
  message_count: number;
  timestamp: string;
}

export interface LoadConversationResponse {
  session_id: string;
  messages: ConversationMessage[];
  last_updated: string;
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fetch with retry logic
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = MAX_RETRIES
): Promise<Response> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      // If we get a rate limit error, wait and retry
      if (response.status === 429) {
        const delay = RETRY_DELAY_MS * Math.pow(BACKOFF_MULTIPLIER, attempt);
        console.log(`Rate limited. Retrying in ${delay}ms... (attempt ${attempt + 1}/${retries})`);
        await sleep(delay);
        continue;
      }
      
      // If we get a server error, retry
      if (response.status >= 500 && attempt < retries - 1) {
        const delay = RETRY_DELAY_MS * Math.pow(BACKOFF_MULTIPLIER, attempt);
        console.log(`Server error ${response.status}. Retrying in ${delay}ms... (attempt ${attempt + 1}/${retries})`);
        await sleep(delay);
        continue;
      }
      
      return response;
    } catch (error) {
      lastError = error as Error;
      
      // Network error - retry if we have attempts left
      if (attempt < retries - 1) {
        const delay = RETRY_DELAY_MS * Math.pow(BACKOFF_MULTIPLIER, attempt);
        console.log(`Network error. Retrying in ${delay}ms... (attempt ${attempt + 1}/${retries})`);
        await sleep(delay);
        continue;
      }
    }
  }
  
  throw lastError || new Error('Max retries exceeded');
}

/**
 * Lazy load external resources
 */
export async function fetchExternalResources(query: string): Promise<ExternalResourcesResponse> {
  try {
    const response = await fetchWithRetry(`${API_BASE_URL}/external-resources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('External resources API error:', error);
    throw error;
  }
}

/**
 * Query Navigate Mode endpoint
 */
export async function queryNavigateMode(query: string): Promise<NavigateResponse> {
  try {
    const response = await fetchWithRetry(`${API_BASE_URL}/langgraph/navigate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Navigate Mode API error:', error);
    throw error;
  }
}

/**
 * Health check for backend
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: AbortSignal.timeout(5000) // 5 second timeout
    });
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

/**
 * Get API statistics
 */
export async function getAPIStats(): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/stats`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch API stats:', error);
    return null;
  }
}

/**
 * Save conversation history
 */
export async function saveConversation(
  sessionId: string,
  messages: ConversationMessage[]
): Promise<SaveConversationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversation/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId, messages }),
    });

    if (!response.ok) {
      throw new Error(`Failed to save conversation: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to save conversation:', error);
    throw error;
  }
}

/**
 * Load conversation history
 */
export async function loadConversation(sessionId: string): Promise<LoadConversationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversation/load/${sessionId}`);

    if (!response.ok) {
      throw new Error(`Failed to load conversation: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to load conversation:', error);
    throw error;
  }
}

/**
 * Delete conversation history
 */
export async function deleteConversation(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/conversation/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete conversation: ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to delete conversation:', error);
    throw error;
  }
}

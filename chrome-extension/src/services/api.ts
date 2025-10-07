/**
 * API service for Luminate AI backend
 */

const API_BASE_URL = 'http://localhost:8000';

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

export interface EducateResponse {
  response_type: 'concept' | 'problem' | 'clarification' | 'assessment';
  main_content: string;
  hints?: {
    current_hint_level: 'light' | 'medium' | 'full';
    light_hint: string;
    medium_hint: string;
    full_solution: {
      steps: string[];
      explanation: string;
      code_example?: string;
      key_insights?: string[];
    };
  };
  socratic_questions?: Array<{
    question: string;
    technique: string;
    purpose: string;
  }>;
  sources: Array<{
    title: string;
    url?: string;
    module?: string;
    relevance_explanation?: string;
  }>;
  related_concepts: Array<{title: string; why_explore: string}>;
  follow_up_suggestions: string[];
  misconception_alert?: string;
  assessment_questions?: Array<{
    question: string;
    difficulty: 'easy' | 'medium' | 'hard';
    type: 'multiple_choice' | 'short_answer' | 'true_false';
    options?: string[];
    correct_answer: string;
    explanation: string;
  }>;
  metadata: {
    intent: string;
    complexity_level: string;
    execution_time_ms: number;
    timestamp: string;
  };
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

/**
 * Lazy load external resources
 */
export async function fetchExternalResources(query: string): Promise<ExternalResourcesResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/external-resources`, {
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
    const response = await fetch(`${API_BASE_URL}/langgraph/navigate`, {
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
    console.error('Navigate Mode API error:', error);
    throw error;
  }
}

/**
 * Query Educate Mode endpoint
 */
export async function queryEducateMode(
  query: string,
  conversationHistory?: Array<{role: string; content: string}>
): Promise<EducateResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/langgraph/educate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query,
        conversation_history: conversationHistory 
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Educate Mode API error:', error);
    throw error;
  }
}

/**
 * Health check for backend
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

/**
 * API service for Luminate AI backend
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// UNIFIED QUERY API (Dual-Mode with Orchestrator)
// ============================================================================

export interface UnifiedQueryResponse {
  mode: 'navigate' | 'educate';
  confidence: number;
  reasoning: string;
  response: {
    formatted_response: string;
    top_results?: Array<{
      title: string;
      excerpt: string;
      live_url?: string;
      url?: string; // Added after transformation
      module: string;
      relevance_explanation?: string;
    }>;
    related_topics?: Array<{
      title: string;
      why_explore?: string;
    }> | string[]; // Can be array of objects or strings
    external_resources?: Array<{
      title: string;
      url: string;
      description?: string;
      type: string;
      channel?: string;
    }>;
    total_results?: number;
    level?: string;
    misconceptions_detected?: any[];
    next_steps?: string[];
  };
  timestamp: string;
}

/**
 * Unified query that routes to Navigate or Educate mode
 */
export async function queryUnified(
  query: string,
  studentId?: string,
  sessionId?: string
): Promise<UnifiedQueryResponse> {
  try {
    console.log('🔵 Making unified query to:', `${API_BASE_URL}/api/query`);
    
    const response = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        student_id: studentId,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`API error (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ Unified query response:', data);
    
    // Transform backend response to match frontend expectations
    // Backend uses: top_results, related_topics, live_url, external_resources
    // Frontend expects: top_results (with url instead of live_url), related_topics
    if (data.response?.top_results) {
      data.response.top_results = data.response.top_results.map((result: any) => ({
        ...result,
        url: result.live_url || result.url, // Normalize URL field
      }));
    }
    
    return data;
  } catch (error) {
    console.error('❌ Unified query error:', error);
    
    // Provide helpful error message
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        'Unable to connect to Luminate AI backend. Please ensure:\n' +
        '1. Backend is running at http://localhost:8000\n' +
        '2. Extension has been reloaded in chrome://extensions/\n' +
        '3. CORS is properly configured'
      );
    }
    
    throw error;
  }
}

// ============================================================================
// LEGACY ENDPOINTS (for backwards compatibility)
// ============================================================================

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

// ============================================================================
// STREAMING CHAT API
// ============================================================================

export interface StreamEvent {
  type: 'message_start' | 'text_delta' | 'agent_trace' | 'metadata' | 'message_done' | 'error';
  id?: string;
  delta?: string;
  data?: any;
  error?: string;
}

/**
 * Stream chat responses with agent traces
 */
export async function* streamChat(
  messages: Array<{role: string; content: string}>,
  mode: 'navigate' | 'educate',
  studentId?: string,
  sessionId?: string
): AsyncGenerator<StreamEvent, void, unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/${mode}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages,
        mode,
        student_id: studentId,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data.trim()) {
            try {
              yield JSON.parse(data) as StreamEvent;
            } catch (e) {
              console.error('Failed to parse SSE data:', data);
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream chat error:', error);
    yield { type: 'error', error: String(error) };
  }
}

// ============================================================================
// QUIZ API
// ============================================================================

export interface QuizOption {
  id: string;
  text: string;
}

export interface QuizQuestion {
  id: string;
  prompt: string;
  options: QuizOption[];
  correct_answer: string;
  explanation: string;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  questions: QuizQuestion[];
  topic: string;
  difficulty: string;
}

export interface QuizSubmitResponse {
  score: number;
  total_questions: number;
  correct_count: number;
  results: Array<{
    question_id: string;
    selected: string;
    correct: string;
    is_correct: boolean;
    explanation: string;
  }>;
}

/**
 * Generate a quiz on a topic
 */
export async function generateQuiz(
  topic: string,
  difficulty: 'easy' | 'medium' | 'hard' = 'medium',
  count: number = 5
): Promise<QuizGenerateResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/quiz/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ topic, difficulty, count }),
    });

    if (!response.ok) {
      throw new Error(`Quiz generation failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Generate quiz error:', error);
    throw error;
  }
}

/**
 * Submit quiz answers
 */
export async function submitQuiz(
  quizId: string,
  studentId: string,
  answers: Record<string, string>,
  timeTakenSeconds?: number
): Promise<QuizSubmitResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/quiz/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        quiz_id: quizId,
        student_id: studentId,
        answers,
        time_taken_seconds: timeTakenSeconds,
      }),
    });

    if (!response.ok) {
      throw new Error(`Quiz submission failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Submit quiz error:', error);
    throw error;
  }
}

// ============================================================================
// NOTES API
// ============================================================================

export interface Note {
  id: string;
  student_id: string;
  topic?: string;
  content: string;
  context?: any;
  created_at: string;
  updated_at: string;
}

/**
 * Create a new note
 */
export async function createNote(
  studentId: string,
  content: string,
  topic?: string,
  context?: any
): Promise<Note> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id: studentId,
        content,
        topic,
        context,
      }),
    });

    if (!response.ok) {
      throw new Error(`Create note failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Create note error:', error);
    throw error;
  }
}

/**
 * Get all notes for a student
 */
export async function fetchNotes(studentId: string): Promise<Note[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/${studentId}`);

    if (!response.ok) {
      throw new Error(`Fetch notes failed: ${response.status}`);
    }

    const data = await response.json();
    return data.notes || [];
  } catch (error) {
    console.error('Fetch notes error:', error);
    return [];
  }
}

/**
 * Update a note
 */
export async function updateNote(
  noteId: string,
  content?: string,
  topic?: string
): Promise<Note> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/${noteId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content, topic }),
    });

    if (!response.ok) {
      throw new Error(`Update note failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Update note error:', error);
    throw error;
  }
}

/**
 * Delete a note
 */
export async function deleteNote(noteId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/${noteId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Delete note failed: ${response.status}`);
    }
  } catch (error) {
    console.error('Delete note error:', error);
    throw error;
  }
}

// ============================================================================
// DASHBOARD API
// ============================================================================

export interface DashboardStats {
  topics_mastered: number;
  current_streak: number;
  total_quizzes: number;
  average_score: number;
  weak_topics: string[];
  recommended_topics: string[];
  recent_activity: Array<{
    type: string;
    topic: string;
    score?: number;
    timestamp: string;
  }>;
}

/**
 * Fetch dashboard statistics
 */
export async function fetchDashboard(studentId: string): Promise<DashboardStats> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/${studentId}`);

    if (!response.ok) {
      throw new Error(`Fetch dashboard failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Fetch dashboard error:', error);
    throw error;
  }
}

// ============================================================================
// CONCEPT GRAPH API
// ============================================================================

export interface ConceptNode {
  id: string;
  label: string;
  mastery: number;
  module?: string;
}

export interface ConceptEdge {
  source: string;
  target: string;
  type: 'prerequisite' | 'related' | 'next_step';
  strength: number;
}

export interface ConceptGraph {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
}

/**
 * Fetch concept relationship graph
 */
export async function fetchConceptGraph(studentId?: string): Promise<ConceptGraph> {
  try {
    const url = new URL(`${API_BASE_URL}/api/concept-graph`);
    if (studentId) {
      url.searchParams.set('student_id', studentId);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Fetch concept graph failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Fetch concept graph error:', error);
    throw error;
  }
}

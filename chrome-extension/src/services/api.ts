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

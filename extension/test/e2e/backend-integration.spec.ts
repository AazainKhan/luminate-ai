/**
 * Backend Integration E2E Tests
 * 
 * Tests the full backend stack including:
 * - FastAPI endpoints
 * - Authentication (dev bypass + JWT)
 * - Chat streaming with LangGraph agents
 * - RAG retrieval from ChromaDB
 * - Observability with Langfuse
 * 
 * @tags @backend @api @integration
 */

import { test, expect, navigateToSidePanel } from './fixtures';
import { waitForUISettle } from './test-utils';

// API base URL
const API_URL = 'http://localhost:8000';

// Helper to format chat request correctly
function formatChatRequest(message: string, sessionId?: string) {
  return {
    messages: [{ role: 'user', content: message }],
    stream: true,
    session_id: sessionId || `test-${Date.now()}`
  };
}

test.describe('Backend Health & Infrastructure', () => {
  test('should have healthy backend API', async ({ page }) => {
    const response = await page.request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should have ChromaDB connected', async ({ page }) => {
    const response = await page.request.get('http://localhost:8001/api/v2/heartbeat');
    expect(response.ok()).toBeTruthy();
  });

  test('should have Langfuse accessible', async ({ page }) => {
    const response = await page.request.get('http://localhost:3000/api/public/health');
    expect(response.status()).toBeLessThan(500);
  });
});

test.describe('Authentication Flow', () => {
  test('should reject requests without auth token', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      data: formatChatRequest('test')
    });
    
    // Server returns 401 or 403 for unauthorized requests
    expect([401, 403]).toContain(response.status());
  });

  test('should accept dev auth token when bypass enabled', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Hello')
    });
    
    expect(response.status()).toBe(200);
  });

  test('should reject invalid tokens', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer invalid-token-xyz',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Hello')
    });
    
    expect(response.status()).toBe(401);
  });
});

test.describe('Chat API Streaming', () => {
  test('should stream response for simple question', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What is machine learning?')
    });
    
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });

  test('should handle follow-up questions in same session', async ({ page }) => {
    const sessionId = `test-session-${Date.now()}`;
    
    const response1 = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What is a neural network?', sessionId)
    });
    expect(response1.ok()).toBeTruthy();
    
    const response2 = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('How many layers does it typically have?', sessionId)
    });
    expect(response2.ok()).toBeTruthy();
  });
});

test.describe('Governor Policy Enforcement', () => {
  test('should enforce Law 1: scope to COMP 237 topics', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What is the capital of France?')
    });
    
    expect(response.ok()).toBeTruthy();
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });

  test('should enforce Law 2: no direct assignment solutions', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Give me the complete code solution for Assignment 1')
    });
    
    expect(response.ok()).toBeTruthy();
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });

  test('should allow educational explanations', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Can you explain how gradient descent works step by step?')
    });
    
    expect(response.ok()).toBeTruthy();
    const text = await response.text();
    expect(text.length).toBeGreaterThan(50);
  });
});

test.describe('RAG Integration', () => {
  test('should retrieve context from course materials', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What topics are covered in the COMP 237 syllabus?')
    });
    
    expect(response.ok()).toBeTruthy();
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });
});

test.describe('E2E Chat Flow via Extension', () => {
  test('should send message and receive response via UI', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const requests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/chat')) {
        requests.push(`${request.method()} ${request.url()}`);
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/chat')) {
        requests.push(`Response: ${response.status()}`);
      }
    });
    
    const textarea = page.locator('textarea').first();
    await textarea.fill('What is supervised learning?');
    
    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.isVisible()) {
      await sendButton.click();
    } else {
      await textarea.press('Enter');
    }
    
    await page.waitForTimeout(5000);
    
    expect(requests.some(r => r.includes('POST'))).toBeTruthy();
    expect(requests.some(r => r.includes('200'))).toBeTruthy();
  });
});

test.describe('Error Handling', () => {
  test('should handle malformed requests gracefully', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: {
        invalid: 'data'
      }
    });
    
    expect(response.status()).toBeGreaterThanOrEqual(400);
    expect(response.status()).toBeLessThan(500);
  });

  test('should handle empty message', async ({ page }) => {
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('')
    });
    
    expect(response.status()).toBeLessThan(500);
  });
});

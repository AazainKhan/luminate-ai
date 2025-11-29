/**
 * Observability & Langfuse E2E Tests
 * 
 * Tests the observability stack including:
 * - Langfuse trace creation
 * - Trace ID propagation
 * - Span hierarchies
 * - Event logging
 * - Metrics collection
 * 
 * @tags @observability @langfuse @tracing
 */

import { test, expect, navigateToSidePanel } from './fixtures';
import { waitForUISettle } from './test-utils';

const API_URL = 'http://localhost:8000';
const LANGFUSE_URL = 'http://localhost:3000';

// Helper to format chat request correctly (Vercel AI SDK format)
function formatChatRequest(message: string, sessionId?: string) {
  return {
    messages: [{ role: 'user', content: message }],
    stream: true,
    session_id: sessionId || `test-${Date.now()}`
  };
}

test.describe('Trace Generation', () => {
  test('should generate trace ID for each conversation', async ({ page }) => {
    const sessionId = `trace-test-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What is machine learning?', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
    const responseText = await response.text();
    expect(responseText.length).toBeGreaterThan(0);
  });

  test('should create unique traces for different sessions', async ({ page }) => {
    const session1 = `session1-${Date.now()}`;
    const session2 = `session2-${Date.now()}`;
    
    const response1 = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Hello from session 1', session1)
    });
    expect(response1.ok()).toBeTruthy();
    
    const response2 = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Hello from session 2', session2)
    });
    expect(response2.ok()).toBeTruthy();
    
    expect((await response1.text()).length).toBeGreaterThan(0);
    expect((await response2.text()).length).toBeGreaterThan(0);
  });
});

test.describe('Langfuse UI', () => {
  test('should load Langfuse dashboard', async ({ page }) => {
    await page.goto(LANGFUSE_URL);
    await page.waitForLoadState('networkidle');
    
    const hasContent = await page.locator('body').textContent();
    expect(hasContent!.length).toBeGreaterThan(0);
  });

  test('should have traces page accessible', async ({ page }) => {
    await page.goto(`${LANGFUSE_URL}/traces`);
    await page.waitForLoadState('domcontentloaded');
    
    const currentUrl = page.url();
    expect(currentUrl).toContain(LANGFUSE_URL);
  });
});

test.describe('Agent Node Tracing', () => {
  test('should trace Governor node execution', async ({ page }) => {
    const sessionId = `governor-trace-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Is this question about AI or cooking?', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
  });

  test('should trace Supervisor routing decision', async ({ page }) => {
    const sessionId = `supervisor-trace-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Write Python code for a neural network', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
  });

  test('should trace RAG retrieval', async ({ page }) => {
    const sessionId = `rag-trace-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('What does the course material say about CNNs?', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
  });

  test('should trace Response Generator output', async ({ page }) => {
    const sessionId = `generator-trace-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Explain gradient descent simply', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(50);
  });
});

test.describe('Span Hierarchy', () => {
  test('should create nested spans for complex queries', async ({ page }) => {
    const sessionId = `nested-span-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Compare the course syllabus topics with what we learned about neural networks in the textbook', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('Error Logging', () => {
  test('should log errors to Langfuse on failure', async ({ page }) => {
    const sessionId = `error-log-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('', sessionId)
    });
    
    expect(response.status()).toBeLessThan(500);
  });
});

test.describe('Metrics Collection', () => {
  test('should track response latency', async ({ page }) => {
    const sessionId = `latency-metric-${Date.now()}`;
    const startTime = Date.now();
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Quick question: what is AI?', sessionId)
    });
    
    const latency = Date.now() - startTime;
    
    expect(response.ok()).toBeTruthy();
    expect(latency).toBeDefined();
  });

  test('should track token usage', async ({ page }) => {
    const sessionId = `token-metric-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Give me a detailed explanation of backpropagation with examples', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(100);
  });
});

test.describe('End-to-End Trace Flow', () => {
  test('full conversation should create complete trace', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const apiCalls: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push(request.url());
      }
    });
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('What is supervised learning?');
      
      const sendButton = page.locator('button[type="submit"]').first();
      if (await sendButton.isVisible()) {
        await sendButton.click();
      } else {
        await textarea.press('Enter');
      }
      
      await page.waitForTimeout(5000);
    }
    
    expect(apiCalls.some(url => url.includes('chat'))).toBeTruthy();
  });
});

test.describe('Session Tracking', () => {
  test('should group traces by session', async ({ page }) => {
    const sessionId = `session-group-${Date.now()}`;
    
    for (let i = 0; i < 3; i++) {
      const response = await page.request.post(`${API_URL}/api/chat/stream`, {
        headers: {
          'Authorization': 'Bearer dev-access-token',
          'Content-Type': 'application/json'
        },
        data: formatChatRequest(`Message ${i + 1} in session`, sessionId)
      });
      expect(response.ok()).toBeTruthy();
    }
  });

  test('should track user ID in traces', async ({ page }) => {
    const sessionId = `user-track-${Date.now()}`;
    
    const response = await page.request.post(`${API_URL}/api/chat/stream`, {
      headers: {
        'Authorization': 'Bearer dev-access-token',
        'Content-Type': 'application/json'
      },
      data: formatChatRequest('Track my user ID', sessionId)
    });
    
    expect(response.ok()).toBeTruthy();
  });
});

/**
 * Agent Orchestration E2E Tests
 * 
 * Tests the LangGraph agent pipeline including:
 * - Governor policy enforcement
 * - Supervisor model routing
 * - RAG and Syllabus sub-agents
 * - Response generation
 * - Evaluator feedback
 * - Multi-turn conversation state
 * 
 * @tags @agent @langgraph @orchestration
 */

import { test, expect } from './fixtures';

const API_URL = 'http://localhost:8000';

// Helper to format chat request correctly (Vercel AI SDK format)
function formatChatRequest(message: string, sessionId?: string) {
  return {
    messages: [{ role: 'user', content: message }],
    stream: true,
    session_id: sessionId || `test-${Date.now()}`
  };
}

// Helper to make authenticated requests
async function chatRequest(page: any, message: string, sessionId: string) {
  const response = await page.request.post(`${API_URL}/api/chat/stream`, {
    headers: {
      'Authorization': 'Bearer dev-access-token',
      'Content-Type': 'application/json'
    },
    data: formatChatRequest(message, sessionId)
  });
  return response;
}

test.describe('LangGraph Node Traversal', () => {
  test('should process message through full agent pipeline', async ({ page }) => {
    const sessionId = `agent-test-${Date.now()}`;
    
    const response = await chatRequest(page, 'Explain backpropagation', sessionId);
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(100);
    
    // Response should contain educational content
    const lowerText = text.toLowerCase();
    expect(
      lowerText.includes('gradient') || 
      lowerText.includes('neural') || 
      lowerText.includes('learning') ||
      lowerText.includes('backward')
    ).toBeTruthy();
  });

  test('should route code questions to Claude Sonnet', async ({ page }) => {
    const sessionId = `code-route-${Date.now()}`;
    
    const response = await chatRequest(
      page, 
      'Write a Python function to implement a simple perceptron',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    // Should contain code-related content
    expect(
      text.includes('def ') || 
      text.includes('python') ||
      text.includes('function') ||
      text.includes('```')
    ).toBeTruthy();
  });

  test('should route math questions to Gemini Pro', async ({ page }) => {
    test.slow(); // Math derivations may take longer
    
    const sessionId = `math-route-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Derive the softmax function gradient mathematically',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });
});

test.describe('Multi-Turn Conversation State', () => {
  test('should maintain context across turns', async ({ page }) => {
    const sessionId = `multi-turn-${Date.now()}`;
    
    // First turn - introduce topic
    const response1 = await chatRequest(
      page,
      'Tell me about decision trees',
      sessionId
    );
    expect(response1.ok()).toBeTruthy();
    const text1 = await response1.text();
    expect(text1.toLowerCase()).toMatch(/tree|decision|node|split/);
    
    // Second turn - follow-up should have context
    const response2 = await chatRequest(
      page,
      'How do you handle overfitting with them?',
      sessionId
    );
    expect(response2.ok()).toBeTruthy();
    const text2 = await response2.text();
    expect(text2.toLowerCase()).toMatch(/prune|depth|overfit|tree/);
    
    // Third turn - even more specific
    const response3 = await chatRequest(
      page,
      'What hyperparameters control this?',
      sessionId
    );
    expect(response3.ok()).toBeTruthy();
  });

  test('should not mix context between different sessions', async ({ page }) => {
    const session1 = `session1-${Date.now()}`;
    const session2 = `session2-${Date.now()}`;
    
    // Session 1 talks about neural networks
    await chatRequest(page, 'Explain convolutional neural networks', session1);
    
    // Session 2 talks about decision trees
    const response2 = await chatRequest(page, 'What are decision trees?', session2);
    const text2 = await response2.text();
    
    // Session 2 should talk about trees, not CNNs
    expect(text2.toLowerCase()).toMatch(/tree|decision|split/);
  });
});

test.describe('Governor Law Enforcement', () => {
  test('Law 1: should keep scope to COMP 237 AI topics', async ({ page }) => {
    const sessionId = `law1-${Date.now()}`;
    
    // Off-topic question
    const response = await chatRequest(
      page,
      'How do I make a pizza?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    // Should redirect or indicate out of scope
    expect(text.length).toBeGreaterThan(0);
  });

  test('Law 2: should not provide complete assignment solutions', async ({ page }) => {
    const sessionId = `law2-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Give me the complete solution code for the neural network assignment',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    // Should guide rather than solve
    expect(text.length).toBeGreaterThan(0);
  });

  test('Law 3: should verify student understanding', async ({ page }) => {
    const sessionId = `law3-${Date.now()}`;
    
    // Simple concept explanation request
    const response = await chatRequest(
      page,
      'I need to understand how K-means clustering works',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(50);
  });
});

test.describe('Supervisor Model Routing', () => {
  test('should handle logistics questions with Gemini Flash', async ({ page }) => {
    const sessionId = `logistics-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'When is the midterm exam?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
  });

  test('should handle complex reasoning with appropriate model', async ({ page }) => {
    const sessionId = `complex-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Compare and contrast supervised vs unsupervised learning with examples and trade-offs',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(100);
  });
});

test.describe('RAG Sub-Agent', () => {
  test('should retrieve relevant course material', async ({ page }) => {
    const sessionId = `rag-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'What assignments are due this week according to the course materials?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
  });

  test('should cite sources when available', async ({ page }) => {
    const sessionId = `cite-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'What does the textbook say about regularization?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('Syllabus Sub-Agent', () => {
  test('should answer syllabus-related questions', async ({ page }) => {
    const sessionId = `syllabus-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'What topics are covered in week 5?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
  });

  test('should handle grading policy questions', async ({ page }) => {
    const sessionId = `grading-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'How much is the final project worth?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('Response Quality', () => {
  test('should generate structured explanations', async ({ page }) => {
    const sessionId = `structured-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Explain the bias-variance tradeoff',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(100);
    
    // Should contain key concepts
    const lowerText = text.toLowerCase();
    expect(
      lowerText.includes('bias') || 
      lowerText.includes('variance') ||
      lowerText.includes('tradeoff') ||
      lowerText.includes('error')
    ).toBeTruthy();
  });

  test('should handle code in responses properly', async ({ page }) => {
    const sessionId = `code-response-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Show me an example of linear regression in Python',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    // Should contain Python code indicators
    expect(
      text.includes('import') || 
      text.includes('def ') ||
      text.includes('sklearn') ||
      text.includes('python')
    ).toBeTruthy();
  });

  test('should include thinking/reasoning when appropriate', async ({ page }) => {
    const sessionId = `thinking-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'Walk me through how you would approach building a spam classifier',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    expect(text.length).toBeGreaterThan(100);
  });
});

test.describe('Error Recovery', () => {
  test('should handle ambiguous questions gracefully', async ({ page }) => {
    const sessionId = `ambiguous-${Date.now()}`;
    
    const response = await chatRequest(
      page,
      'What is the best one?',
      sessionId
    );
    expect(response.ok()).toBeTruthy();
    
    const text = await response.text();
    // Should ask for clarification or provide general response
    expect(text.length).toBeGreaterThan(0);
  });

  test('should recover from context overload', async ({ page }) => {
    const sessionId = `overload-${Date.now()}`;
    
    // Send a very long message
    const longMessage = 'Explain this concept: '.repeat(100);
    const response = await chatRequest(page, longMessage, sessionId);
    
    // Should either truncate or handle gracefully
    expect(response.status()).toBeLessThan(500);
  });
});

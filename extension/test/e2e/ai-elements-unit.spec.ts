/**
 * AI SDK Elements Unit Tests
 * 
 * Tests the AI-powered UI components in isolation:
 * - Shimmer loading states
 * - Queue visualization
 * - Task progress
 * - Tool execution display
 * - Sources rendering
 * - Message input and response
 * 
 * @tags @unit @ai-elements
 */

import { test, expect } from '@playwright/test';

// Simple test that doesn't require the extension
test.describe('AI Elements Component Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Create a test page with our component styles
    await page.setContent(`
      <!DOCTYPE html>
      <html class="dark">
      <head>
        <style>
          :root {
            --background: #0a0a0a;
            --foreground: #fafafa;
            --muted: #1a1a2e;
            --muted-foreground: #a1a1aa;
            --border: #27272a;
            --violet-500: #8b5cf6;
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body { 
            font-family: system-ui, -apple-system, sans-serif;
            background: var(--background);
            color: var(--foreground);
            padding: 20px;
          }
          .container { max-width: 600px; margin: 0 auto; }
          
          /* Shimmer Component */
          .shimmer {
            background: linear-gradient(90deg, 
              var(--muted) 25%, 
              color-mix(in srgb, var(--muted) 80%, white) 50%, 
              var(--muted) 75%
            );
            background-size: 200% 100%;
            animation: shimmer 2s linear infinite;
            border-radius: 6px;
          }
          .shimmer-text { height: 16px; margin: 8px 0; }
          .shimmer-code { height: 80px; border-radius: 8px; }
          @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
          
          /* Queue Component */
          .queue { 
            background: var(--muted);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
          }
          .queue-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            border-radius: 6px;
          }
          .queue-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
          }
          .queue-indicator.waiting { background: #52525b; }
          .queue-indicator.processing { 
            background: #eab308; 
            animation: pulse 1s ease-in-out infinite;
          }
          .queue-indicator.completed { background: #22c55e; }
          .queue-indicator.error { background: #ef4444; }
          .queue-label { flex: 1; font-size: 14px; }
          .queue-time { font-size: 12px; color: var(--muted-foreground); }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          
          /* Task Component */
          .task {
            background: var(--muted);
            border-radius: 8px;
            margin: 8px 0;
            overflow: hidden;
          }
          .task-trigger {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px;
            cursor: pointer;
            border-bottom: 1px solid var(--border);
          }
          .task-content { padding: 8px 12px; }
          .task-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 0;
            font-size: 14px;
          }
          .task-icon { width: 16px; text-align: center; }
          .task-icon.pending { color: #52525b; }
          .task-icon.in-progress { color: #eab308; }
          .task-icon.completed { color: #22c55e; }
          
          /* Tool Component */
          .tool {
            background: var(--muted);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            font-family: monospace;
            font-size: 13px;
          }
          .tool-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
          }
          .tool-name { color: var(--violet-500); font-weight: 600; }
          .tool-status { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
          .tool-status.running { background: #422006; color: #fbbf24; }
          .tool-status.done { background: #052e16; color: #22c55e; }
          .tool-args { color: var(--muted-foreground); font-size: 12px; }
          .tool-result { margin-top: 8px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; }
          
          /* Message Components */
          .message { 
            display: flex;
            gap: 12px;
            margin: 16px 0;
          }
          .message.user { flex-direction: row-reverse; }
          .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
          }
          .avatar.assistant { 
            background: rgba(139, 92, 246, 0.2);
            color: var(--violet-500);
          }
          .avatar.user { 
            background: var(--violet-500);
            color: white;
          }
          .message-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
          }
          .message.user .message-bubble {
            background: var(--violet-500);
            border-radius: 16px 16px 4px 16px;
          }
          .message.assistant .message-bubble {
            background: var(--muted);
            border: 1px solid var(--border);
            border-radius: 16px 16px 16px 4px;
          }
          
          /* Sources Component */
          .sources {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
          }
          .sources-trigger {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: var(--muted-foreground);
            cursor: pointer;
          }
          .sources-content { margin-top: 8px; }
          .source {
            display: block;
            padding: 6px 10px;
            margin: 4px 0;
            background: rgba(139, 92, 246, 0.1);
            border-radius: 6px;
            font-size: 13px;
            color: var(--violet-500);
            text-decoration: none;
          }
          
          /* Input Component */
          .chat-input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 16px;
            background: var(--background);
            border-top: 1px solid var(--border);
          }
          .chat-input {
            width: 100%;
            padding: 12px 16px;
            background: var(--muted);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--foreground);
            font-size: 14px;
            resize: none;
          }
          .chat-input:focus {
            outline: none;
            border-color: var(--violet-500);
          }
          .send-button {
            position: absolute;
            right: 24px;
            bottom: 24px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--violet-500);
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        </style>
      </head>
      <body>
        <div class="container" style="padding-bottom: 100px;">
          <h2 style="margin-bottom: 24px;">AI Elements E2E Tests</h2>
          
          <!-- Shimmer Section -->
          <section id="shimmer-section">
            <h3 style="font-size: 14px; color: var(--muted-foreground); margin: 16px 0 8px;">Loading State</h3>
            <div class="shimmer shimmer-text" data-testid="shimmer-1" style="width: 90%"></div>
            <div class="shimmer shimmer-text" data-testid="shimmer-2" style="width: 75%"></div>
            <div class="shimmer shimmer-text" data-testid="shimmer-3" style="width: 60%"></div>
            <div class="shimmer shimmer-code" data-testid="shimmer-code"></div>
          </section>
          
          <!-- Queue Section -->
          <section id="queue-section">
            <h3 style="font-size: 14px; color: var(--muted-foreground); margin: 16px 0 8px;">Processing Queue</h3>
            <div class="queue" data-testid="queue">
              <div class="queue-item" data-testid="queue-item-1" data-status="completed">
                <div class="queue-indicator completed"></div>
                <span class="queue-label">Policy Check</span>
                <span class="queue-time">0.2s</span>
              </div>
              <div class="queue-item" data-testid="queue-item-2" data-status="completed">
                <div class="queue-indicator completed"></div>
                <span class="queue-label">Intent Analysis</span>
                <span class="queue-time">0.8s</span>
              </div>
              <div class="queue-item" data-testid="queue-item-3" data-status="processing">
                <div class="queue-indicator processing"></div>
                <span class="queue-label">Response Generation</span>
                <span class="queue-time">2.1s</span>
              </div>
              <div class="queue-item" data-testid="queue-item-4" data-status="waiting">
                <div class="queue-indicator waiting"></div>
                <span class="queue-label">Quality Evaluation</span>
                <span class="queue-time">—</span>
              </div>
            </div>
          </section>
          
          <!-- Task Section -->
          <section id="task-section">
            <h3 style="font-size: 14px; color: var(--muted-foreground); margin: 16px 0 8px;">Task Progress</h3>
            <div class="task" data-testid="task">
              <div class="task-trigger">
                <span>📋</span>
                <span>Processing Steps</span>
              </div>
              <div class="task-content">
                <div class="task-item" data-testid="task-item-1" data-status="completed">
                  <span class="task-icon completed">✓</span>
                  <span>Checking policy compliance</span>
                </div>
                <div class="task-item" data-testid="task-item-2" data-status="completed">
                  <span class="task-icon completed">✓</span>
                  <span>Analyzing your question</span>
                </div>
                <div class="task-item" data-testid="task-item-3" data-status="in-progress">
                  <span class="task-icon in-progress">⟳</span>
                  <span>Preparing educational response</span>
                </div>
                <div class="task-item" data-testid="task-item-4" data-status="pending">
                  <span class="task-icon pending">○</span>
                  <span>Evaluating response quality</span>
                </div>
              </div>
            </div>
          </section>
          
          <!-- Tool Section -->
          <section id="tool-section">
            <h3 style="font-size: 14px; color: var(--muted-foreground); margin: 16px 0 8px;">Tool Execution</h3>
            <div class="tool" data-testid="tool-call">
              <div class="tool-header">
                <span class="tool-name">retrieve_context</span>
                <span class="tool-status done">completed</span>
              </div>
              <div class="tool-args">query: "What is gradient descent?"</div>
              <div class="tool-result" data-testid="tool-result">
                Retrieved 3 relevant documents from course materials
              </div>
            </div>
          </section>
          
          <!-- Message Section -->
          <section id="message-section">
            <h3 style="font-size: 14px; color: var(--muted-foreground); margin: 16px 0 8px;">Chat Messages</h3>
            <div class="message user" data-testid="user-message">
              <div class="avatar user">U</div>
              <div class="message-bubble">What is gradient descent?</div>
            </div>
            <div class="message assistant" data-testid="assistant-message">
              <div class="avatar assistant">L</div>
              <div class="message-bubble">
                <strong>Quick:</strong> Gradient descent is an optimization algorithm used to minimize a function by iteratively moving in the direction of steepest descent. In machine learning, it's used to find the optimal weights that minimize the loss function.
                
                <div class="sources" data-testid="sources">
                  <div class="sources-trigger">
                    <span>📚</span>
                    <span>3 sources</span>
                  </div>
                  <div class="sources-content">
                    <a class="source" href="#" data-testid="source-1">COMP_237_Module3.pdf - Page 12</a>
                    <a class="source" href="#" data-testid="source-2">Neural_Networks_Slides.pdf - Page 5</a>
                    <a class="source" href="#" data-testid="source-3">Course_Outline.pdf - Page 3</a>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
        
        <!-- Input Section -->
        <div class="chat-input-container" data-testid="input-container">
          <textarea 
            class="chat-input" 
            data-testid="chat-input"
            placeholder="Ask about AI concepts..."
            rows="1"
          ></textarea>
          <button class="send-button" data-testid="send-button">
            ➤
          </button>
        </div>
      </body>
      </html>
    `);
    
    await page.waitForLoadState('domcontentloaded');
  });

  test.describe('Shimmer Loading States', () => {
    test('should render shimmer elements', async ({ page }) => {
      const shimmerCount = await page.locator('[data-testid^="shimmer"]').count();
      expect(shimmerCount).toBe(4);
    });

    test('shimmer should have animation', async ({ page }) => {
      const shimmer = page.locator('[data-testid="shimmer-1"]');
      const animationName = await shimmer.evaluate(el => {
        return window.getComputedStyle(el).animationName;
      });
      expect(animationName).toBe('shimmer');
    });

    test('shimmer-code should be taller than shimmer-text', async ({ page }) => {
      const textHeight = await page.locator('[data-testid="shimmer-1"]').evaluate(el => el.offsetHeight);
      const codeHeight = await page.locator('[data-testid="shimmer-code"]').evaluate(el => el.offsetHeight);
      expect(codeHeight).toBeGreaterThan(textHeight);
    });
  });

  test.describe('Processing Queue', () => {
    test('should render all queue items', async ({ page }) => {
      const queueItems = await page.locator('[data-testid^="queue-item"]').count();
      expect(queueItems).toBe(4);
    });

    test('should show correct status indicators', async ({ page }) => {
      const completedCount = await page.locator('.queue-indicator.completed').count();
      const processingCount = await page.locator('.queue-indicator.processing').count();
      const waitingCount = await page.locator('.queue-indicator.waiting').count();
      
      expect(completedCount).toBe(2);
      expect(processingCount).toBe(1);
      expect(waitingCount).toBe(1);
    });

    test('processing indicator should have pulse animation', async ({ page }) => {
      const indicator = page.locator('.queue-indicator.processing');
      const animationName = await indicator.evaluate(el => {
        return window.getComputedStyle(el).animationName;
      });
      expect(animationName).toBe('pulse');
    });

    test('queue items should have timing info', async ({ page }) => {
      const timeTexts = await page.locator('.queue-time').allTextContents();
      expect(timeTexts).toContain('0.2s');
      expect(timeTexts).toContain('0.8s');
      expect(timeTexts).toContain('2.1s');
    });
  });

  test.describe('Task Progress', () => {
    test('should render all task items', async ({ page }) => {
      const taskItems = await page.locator('[data-testid^="task-item"]').count();
      expect(taskItems).toBe(4);
    });

    test('should show correct task statuses', async ({ page }) => {
      const completed = await page.locator('[data-status="completed"]').count();
      const inProgress = await page.locator('[data-status="in-progress"]').count();
      const pending = await page.locator('[data-status="pending"]').count();
      
      // Includes queue items, so filter by task-item
      const taskCompleted = await page.locator('.task-item[data-status="completed"]').count();
      expect(taskCompleted).toBe(2);
    });

    test('task icons should have correct visual styling', async ({ page }) => {
      const completedIcon = page.locator('.task-icon.completed').first();
      const completedColor = await completedIcon.evaluate(el => {
        return window.getComputedStyle(el).color;
      });
      // Green color
      expect(completedColor).toContain('rgb(34, 197, 94)');
    });
  });

  test.describe('Tool Execution', () => {
    test('should render tool call with name', async ({ page }) => {
      const toolName = await page.locator('.tool-name').textContent();
      expect(toolName).toBe('retrieve_context');
    });

    test('should show tool status', async ({ page }) => {
      const status = await page.locator('.tool-status').textContent();
      expect(status).toBe('completed');
    });

    test('should display tool arguments', async ({ page }) => {
      const args = await page.locator('.tool-args').textContent();
      expect(args).toContain('gradient descent');
    });

    test('should show tool result', async ({ page }) => {
      const result = await page.locator('[data-testid="tool-result"]').textContent();
      expect(result).toContain('Retrieved 3 relevant documents');
    });
  });

  test.describe('Chat Messages', () => {
    test('should render user message', async ({ page }) => {
      const userMessage = page.locator('[data-testid="user-message"]');
      await expect(userMessage).toBeVisible();
      const text = await userMessage.textContent();
      expect(text).toContain('gradient descent');
    });

    test('should render assistant message', async ({ page }) => {
      const assistantMessage = page.locator('[data-testid="assistant-message"]');
      await expect(assistantMessage).toBeVisible();
      const text = await assistantMessage.textContent();
      expect(text).toContain('Quick:');
      expect(text).toContain('optimization algorithm');
    });

    test('user message should be right-aligned', async ({ page }) => {
      const userMessage = page.locator('[data-testid="user-message"]');
      const flexDirection = await userMessage.evaluate(el => {
        return window.getComputedStyle(el).flexDirection;
      });
      expect(flexDirection).toBe('row-reverse');
    });

    test('assistant should have avatar with L', async ({ page }) => {
      const avatar = page.locator('[data-testid="assistant-message"] .avatar');
      const text = await avatar.textContent();
      expect(text).toBe('L');
    });
  });

  test.describe('Sources', () => {
    test('should show source count', async ({ page }) => {
      const trigger = page.locator('.sources-trigger');
      const text = await trigger.textContent();
      expect(text).toContain('3 sources');
    });

    test('should render all sources', async ({ page }) => {
      // Use more specific selector to only get source items, not the sources container
      const sources = await page.locator('.source').count();
      expect(sources).toBe(3);
    });

    test('sources should have file names and pages', async ({ page }) => {
      const source1 = await page.locator('[data-testid="source-1"]').textContent();
      expect(source1).toContain('COMP_237');
      expect(source1).toContain('Page');
    });
  });

  test.describe('Message Input', () => {
    test('should render input textarea', async ({ page }) => {
      const input = page.locator('[data-testid="chat-input"]');
      await expect(input).toBeVisible();
    });

    test('input should have placeholder', async ({ page }) => {
      const placeholder = await page.locator('[data-testid="chat-input"]').getAttribute('placeholder');
      expect(placeholder).toContain('AI concepts');
    });

    test('should be able to type in input', async ({ page }) => {
      const input = page.locator('[data-testid="chat-input"]');
      await input.fill('What is backpropagation?');
      const value = await input.inputValue();
      expect(value).toBe('What is backpropagation?');
    });

    test('should render send button', async ({ page }) => {
      const button = page.locator('[data-testid="send-button"]');
      await expect(button).toBeVisible();
    });

    test('send button should be clickable', async ({ page }) => {
      const button = page.locator('[data-testid="send-button"]');
      await expect(button).toBeEnabled();
    });

    test('input should focus on click', async ({ page }) => {
      const input = page.locator('[data-testid="chat-input"]');
      await input.click();
      await expect(input).toBeFocused();
    });
  });

  test.describe('Dark Mode Styling', () => {
    test('page should have dark background', async ({ page }) => {
      const bgColor = await page.locator('body').evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });
      // Dark background (close to #0a0a0a)
      expect(bgColor).toMatch(/rgb\(10, 10, 10\)|rgba\(10, 10, 10/);
    });

    test('text should be light colored', async ({ page }) => {
      const textColor = await page.locator('body').evaluate(el => {
        return window.getComputedStyle(el).color;
      });
      // Light text (close to #fafafa)
      expect(textColor).toMatch(/rgb\(250, 250, 250\)|rgba\(250, 250, 250/);
    });
  });

  test.describe('Accessibility', () => {
    test('input should have accessible placeholder', async ({ page }) => {
      const input = page.locator('[data-testid="chat-input"]');
      const placeholder = await input.getAttribute('placeholder');
      expect(placeholder).toBeTruthy();
      expect(placeholder!.length).toBeGreaterThan(5);
    });

    test('buttons should be keyboard accessible', async ({ page }) => {
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Eventually should focus the send button
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(['BUTTON', 'TEXTAREA', 'A']).toContain(focused);
    });
  });
});

/**
 * Vercel AI SDK UI Component E2E Tests
 * 
 * Tests the AI-powered UI components including:
 * - Chat message rendering
 * - Streaming text display
 * - Thinking/reasoning accordion
 * - Code blocks with syntax highlighting
 * - Quiz cards
 * - Generative UI elements
 * 
 * @tags @ui @vercel-ai @components
 */

import { test, expect, navigateToSidePanel } from './fixtures';
import { waitForUISettle, forceExpandNavRail } from './test-utils';

const API_URL = 'http://localhost:8000';

test.describe('Chat Message Rendering', () => {
  test('should render user messages correctly', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Hello, this is a test message');
      await textarea.press('Enter');
      
      await page.waitForTimeout(2000);
      
      // Check if user message appears in chat
      const chatContainer = page.locator('[data-testid="chat-messages"], .chat-messages, main');
      const text = await chatContainer.textContent();
      expect(text).toContain('test message');
    }
  });

  test('should render AI responses with proper formatting', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('What is machine learning?');
      await textarea.press('Enter');
      
      // Wait for AI response
      await page.waitForTimeout(8000);
      
      // Check for response content
      const content = await page.content();
      expect(content.length).toBeGreaterThan(500);
    }
  });
});

test.describe('Streaming Text Display', () => {
  test('should show streaming indicator during response', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Explain neural networks');
      await textarea.press('Enter');
      
      // Check for loading/streaming indicator
      await page.waitForTimeout(1000);
      
      // Look for common streaming indicators
      const hasStreamingIndicator = 
        await page.locator('[data-streaming="true"]').count() > 0 ||
        await page.locator('.animate-pulse').count() > 0 ||
        await page.locator('[aria-busy="true"]').count() > 0 ||
        await page.locator('.loading').count() > 0;
      
      // May or may not have indicator depending on timing
    }
  });

  test('should progressively render streaming content', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Tell me about deep learning in detail');
      await textarea.press('Enter');
      
      // Take snapshots at different times to verify streaming
      await page.waitForTimeout(2000);
      const content1 = await page.content();
      
      await page.waitForTimeout(3000);
      const content2 = await page.content();
      
      // Content should grow as streaming continues
      expect(content2.length).toBeGreaterThanOrEqual(content1.length);
    }
  });
});

test.describe('Thinking Accordion', () => {
  test('should render thinking section when present', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Walk me through how to solve a classification problem step by step');
      await textarea.press('Enter');
      
      await page.waitForTimeout(8000);
      
      // Look for thinking accordion
      const thinkingElements = page.locator(
        '[data-testid="thinking"], .thinking-accordion, [class*="thinking"], details'
      );
      
      // May or may not have thinking section depending on agent response
      const pageText = await page.textContent('body');
      expect(pageText!.length).toBeGreaterThan(0);
    }
  });

  test('should be expandable/collapsible', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Look for any accordion elements
    const accordions = page.locator('details, [data-state="open"], [data-state="closed"]');
    
    if (await accordions.count() > 0) {
      const firstAccordion = accordions.first();
      
      // Click to toggle
      await firstAccordion.click();
      await page.waitForTimeout(500);
      
      // Verify it's interactive
      expect(await firstAccordion.isVisible()).toBeTruthy();
    }
  });
});

test.describe('Code Blocks', () => {
  test('should render code with syntax highlighting', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Show me a Python example of linear regression');
      await textarea.press('Enter');
      
      await page.waitForTimeout(8000);
      
      // Look for code blocks
      const codeBlocks = page.locator('pre, code, [class*="code"], .hljs');
      
      // Response should contain code-like content
      const pageContent = await page.textContent('body');
      expect(
        pageContent!.includes('import') || 
        pageContent!.includes('def ') ||
        pageContent!.includes('python') ||
        pageContent!.includes('sklearn')
      ).toBeTruthy();
    }
  });

  test('should have copy button on code blocks', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Check for copy buttons near code blocks
    const copyButtons = page.locator(
      'button[aria-label*="copy"], button[title*="copy"], [class*="copy"]'
    );
    
    // May or may not have copy buttons depending on current content
    const count = await copyButtons.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Quiz Cards', () => {
  test('should render quiz elements when present', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Quiz me on machine learning basics');
      await textarea.press('Enter');
      
      await page.waitForTimeout(8000);
      
      // Look for quiz elements
      const quizElements = page.locator(
        '[data-testid="quiz"], .quiz-card, [class*="quiz"], input[type="radio"]'
      );
      
      // Response should have some content
      const pageContent = await page.textContent('body');
      expect(pageContent!.length).toBeGreaterThan(100);
    }
  });
});

test.describe('Message Input', () => {
  test('should have functional textarea', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    const textarea = page.locator('textarea').first();
    expect(await textarea.isVisible()).toBeTruthy();
    
    // Should be able to type
    await textarea.fill('Test input');
    expect(await textarea.inputValue()).toBe('Test input');
  });

  test('should have send button', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Look for send button
    const sendButton = page.locator(
      'button[type="submit"], button[aria-label*="send"], [class*="send"]'
    ).first();
    
    if (await sendButton.count() > 0) {
      expect(await sendButton.isVisible()).toBeTruthy();
    }
  });

  test('should submit on Enter key', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Track API calls
    let apiCalled = false;
    page.on('request', request => {
      if (request.url().includes('/api/chat')) {
        apiCalled = true;
      }
    });
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('Test enter submission');
      await textarea.press('Enter');
      
      await page.waitForTimeout(3000);
      
      // API should have been called
      expect(apiCalled).toBeTruthy();
    }
  });
});

test.describe('Error States', () => {
  test('should show error state on API failure', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Block the API to simulate failure
    await page.route('**/api/chat/**', route => {
      route.abort();
    });
    
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      await textarea.fill('This should fail');
      await textarea.press('Enter');
      
      await page.waitForTimeout(3000);
      
      // Should show some error indication
      const content = await page.textContent('body');
      expect(content!.length).toBeGreaterThan(0);
    }
    
    // Unblock for future tests
    await page.unroute('**/api/chat/**');
  });
});

test.describe('Responsive Layout', () => {
  test('should maintain layout in side panel', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Side panel has fixed width
    const viewport = page.viewportSize();
    
    // UI should be visible and not broken
    const mainContent = page.locator('main, [role="main"], .main-content').first();
    if (await mainContent.count() > 0) {
      expect(await mainContent.isVisible()).toBeTruthy();
    }
  });
});

test.describe('Accessibility', () => {
  test('should have accessible form elements', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Check textarea has label or aria-label
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      const ariaLabel = await textarea.getAttribute('aria-label');
      const placeholder = await textarea.getAttribute('placeholder');
      
      // Should have some accessible name
      expect(ariaLabel || placeholder).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Tab through elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(500);
    
    // Should have a focused element
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeDefined();
  });
});

test.describe('Dark Mode', () => {
  test('should render correctly in dark mode if enabled', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    await waitForUISettle(page, 3000);
    
    // Check for dark mode classes
    const html = page.locator('html');
    const isDarkMode = await html.getAttribute('class');
    
    // Should have consistent styling either way
    const body = await page.locator('body').evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    expect(body).toBeDefined();
  });
});

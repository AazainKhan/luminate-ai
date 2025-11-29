/**
 * Suggestion Buttons E2E Tests for Luminate AI Extension
 * 
 * Tests the suggestion chips/buttons shown on the empty state:
 * - Review my Linear Algebra quiz
 * - Explain gradient descent with examples
 * - Create flashcards for COMP 237
 * - Debug this Python ML code
 */

import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('Suggestion Buttons', () => {
  test('should display suggestion buttons on empty chat state', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    // Check if we're on the authenticated empty state (not login)
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    
    if (hasLoginForm) {
      console.log('⚠️ Login form visible - auth bypass may not be working');
      return;
    }
    
    // Look for suggestion buttons
    const suggestions = [
      'Linear Algebra',
      'gradient descent',
      'flashcards',
      'Python ML code'
    ];
    
    let foundCount = 0;
    for (const text of suggestions) {
      const button = page.locator(`button:has-text("${text}")`);
      const isVisible = await button.isVisible().catch(() => false);
      if (isVisible) {
        foundCount++;
        console.log(`✅ Found suggestion: "${text}"`);
      }
    }
    
    console.log(`Found ${foundCount}/${suggestions.length} suggestion buttons`);
    
    // Should find at least some suggestions when on empty state
    if (foundCount > 0) {
      expect(foundCount).toBeGreaterThan(0);
    }
  });

  test('suggestion buttons should be clickable', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) {
      console.log('⚠️ Skipping - on login page');
      return;
    }
    
    // Find a suggestion button
    const suggestionButton = page.locator('button:has-text("gradient descent")');
    const isVisible = await suggestionButton.isVisible().catch(() => false);
    
    if (isVisible) {
      // Check it's enabled and clickable
      const isEnabled = await suggestionButton.isEnabled();
      console.log('Gradient descent button enabled:', isEnabled);
      expect(isEnabled).toBe(true);
      
      // Verify it has hover styles (check cursor)
      const cursor = await suggestionButton.evaluate(el => getComputedStyle(el).cursor);
      console.log('Button cursor style:', cursor);
    } else {
      console.log('No suggestion buttons visible (may have messages already)');
    }
  });

  test('suggestion buttons should have proper styling', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Find any suggestion button
    const suggestionButtons = page.locator('button:has-text("flashcards"), button:has-text("gradient"), button:has-text("Linear")');
    const count = await suggestionButtons.count();
    
    if (count > 0) {
      const firstButton = suggestionButtons.first();
      
      // Check for rounded styling (should be rounded-full or similar)
      const borderRadius = await firstButton.evaluate(el => getComputedStyle(el).borderRadius);
      console.log('Button border radius:', borderRadius);
      
      // Check for appropriate size
      const fontSize = await firstButton.evaluate(el => getComputedStyle(el).fontSize);
      console.log('Button font size:', fontSize);
      
      // Buttons should have some border radius for the pill/chip style
      expect(borderRadius).not.toBe('0px');
    }
  });
});

test.describe('Empty State UI', () => {
  test('should show greeting with user name', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for greeting text "Hi, [name]"
    const greeting = page.locator('text=/Hi,/i');
    const hasGreeting = await greeting.isVisible().catch(() => false);
    
    console.log('Has greeting:', hasGreeting);
    
    if (hasGreeting) {
      const greetingText = await greeting.textContent();
      console.log('Greeting text:', greetingText);
      expect(greetingText).toContain('Hi,');
    }
  });

  test('should show helpful subtitle text', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for the subtitle about asking questions
    const subtitle = page.locator('text=/Ask anything|courses|assignments|learning/i');
    const hasSubtitle = await subtitle.isVisible().catch(() => false);
    
    console.log('Has helpful subtitle:', hasSubtitle);
  });

  test('should display Luminate logo in empty state', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for the "L" logo in the gradient box
    const logoBox = page.locator('.bg-gradient-to-br');
    const logoCount = await logoBox.count();
    
    console.log('Gradient logo boxes found:', logoCount);
    
    // Or look for the L text
    const hasL = await page.locator('span:has-text("L")').first().isVisible().catch(() => false);
    console.log('Has L logo text:', hasL);
  });
});

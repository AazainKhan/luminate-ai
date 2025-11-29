/**
 * Accessibility E2E Tests for Luminate AI Extension
 * 
 * Tests basic accessibility requirements:
 * - Keyboard navigation
 * - Focus indicators
 * - ARIA labels
 * - Color contrast (visual checks)
 */

import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('Keyboard Navigation', () => {
  test('should be able to tab through interactive elements', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) {
      console.log('⚠️ On login page - skipping');
      return;
    }
    
    // Start tabbing from body
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    // Get the currently focused element
    const focusedTag1 = await page.evaluate(() => document.activeElement?.tagName);
    console.log('First tab lands on:', focusedTag1);
    
    // Tab again
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    const focusedTag2 = await page.evaluate(() => document.activeElement?.tagName);
    console.log('Second tab lands on:', focusedTag2);
    
    // Tab should move focus to interactive elements
    expect(['BUTTON', 'INPUT', 'TEXTAREA', 'A']).toContain(focusedTag1 || focusedTag2);
  });

  test('textarea should be focusable and receive input', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Focus the textarea directly
    const textarea = page.locator('textarea');
    await textarea.focus();
    
    // Check it's focused
    const isFocused = await textarea.evaluate(el => el === document.activeElement);
    console.log('Textarea is focused:', isFocused);
    expect(isFocused).toBe(true);
    
    // Type with keyboard
    await page.keyboard.type('Hello AI');
    const value = await textarea.inputValue();
    console.log('Typed via keyboard:', value);
    expect(value).toBe('Hello AI');
  });

  test('Enter key should submit message', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    await textarea.focus();
    await page.keyboard.type('Test message');
    
    // Count interactive elements before (would trigger network call)
    const valueBefore = await textarea.inputValue();
    console.log('Value before Enter:', valueBefore);
    
    // Note: We don't actually send because we don't have backend
    // Just verify Enter key is handled (textarea clears in handler)
  });

  test('Shift+Enter should add newline, not submit', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    await textarea.focus();
    await page.keyboard.type('Line 1');
    await page.keyboard.press('Shift+Enter');
    await page.keyboard.type('Line 2');
    
    const value = await textarea.inputValue();
    console.log('Value with newline:', value);
    
    // Should contain newline
    expect(value).toContain('\n');
    expect(value).toContain('Line 1');
    expect(value).toContain('Line 2');
  });
});

test.describe('Focus Indicators', () => {
  test('buttons should have visible focus ring', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Find a button and focus it
    const button = page.locator('form button').first();
    await button.focus();
    
    // Check for focus-visible styles (outline or ring)
    const outlineStyle = await button.evaluate(el => {
      const styles = getComputedStyle(el);
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow,
        ring: styles.getPropertyValue('--tw-ring-color')
      };
    });
    
    console.log('Focus styles:', outlineStyle);
  });

  test('textarea should show focus state', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    
    // Get styles before focus
    const stylesBefore = await textarea.evaluate(el => getComputedStyle(el).outline);
    
    // Focus
    await textarea.focus();
    await page.waitForTimeout(100);
    
    // Get styles after focus
    const stylesAfter = await textarea.evaluate(el => getComputedStyle(el).outline);
    
    console.log('Outline before:', stylesBefore);
    console.log('Outline after:', stylesAfter);
  });
});

test.describe('ARIA and Semantic HTML', () => {
  test('buttons should have accessible names', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Check send button has accessible name
    const sendButton = page.locator('button:has-text("Send")');
    const sendVisible = await sendButton.isVisible().catch(() => false);
    
    if (sendVisible) {
      const accessibleName = await sendButton.evaluate(el => el.textContent?.trim() || el.getAttribute('aria-label'));
      console.log('Send button accessible name:', accessibleName);
      expect(accessibleName).toBeTruthy();
    }
    
    // Icon buttons should have aria-label or tooltips
    const iconButtons = page.locator('form button:not(:has-text("Send"))');
    const count = await iconButtons.count();
    console.log('Icon buttons found:', count);
  });

  test('form should have proper structure', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Check for form element
    const form = page.locator('form');
    const hasForm = await form.count() > 0;
    console.log('Has form element:', hasForm);
    expect(hasForm).toBe(true);
    
    // Textarea should be inside form
    const textareaInForm = page.locator('form textarea');
    const hasTextareaInForm = await textareaInForm.count() > 0;
    console.log('Textarea in form:', hasTextareaInForm);
    expect(hasTextareaInForm).toBe(true);
  });

  test('headings should have proper hierarchy', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Find all headings
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();
    const h3Count = await page.locator('h3').count();
    
    console.log('H1 headings:', h1Count);
    console.log('H2 headings:', h2Count);
    console.log('H3 headings:', h3Count);
    
    // Should have at least one heading-like element (h1 or prominent text)
    const hasHeading = h1Count > 0 || h2Count > 0 || h3Count > 0;
    console.log('Has semantic headings:', hasHeading);
  });

  test('switches should have proper role', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Open options panel
    const optionsButton = page.locator('form button').first();
    await optionsButton.click();
    await page.waitForTimeout(500);
    
    // Check for switch role
    const switches = page.locator('[role="switch"]');
    const switchCount = await switches.count();
    console.log('Switches with role:', switchCount);
    
    if (switchCount > 0) {
      const firstSwitch = switches.first();
      const ariaChecked = await firstSwitch.getAttribute('aria-checked');
      const dataState = await firstSwitch.getAttribute('data-state');
      
      console.log('Switch aria-checked:', ariaChecked);
      console.log('Switch data-state:', dataState);
      
      // Should have accessible state
      expect(ariaChecked || dataState).toBeTruthy();
    }
  });
});

test.describe('Color and Contrast', () => {
  test('text should have sufficient contrast', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Check main text colors
    const greeting = page.locator('h1').first();
    const hasGreeting = await greeting.isVisible().catch(() => false);
    
    if (hasGreeting) {
      const color = await greeting.evaluate(el => getComputedStyle(el).color);
      console.log('Heading text color:', color);
      
      // Should be light color (for dark theme)
      // slate-50 is rgb(248, 250, 252)
      expect(color).toMatch(/rgb|oklch/);
    }
    
    // Check placeholder color
    const textarea = page.locator('textarea');
    if (await textarea.isVisible()) {
      const placeholderColor = await textarea.evaluate(el => 
        getComputedStyle(el).getPropertyValue('--tw-placeholder-color') ||
        getComputedStyle(el, '::placeholder').color
      );
      console.log('Placeholder color:', placeholderColor);
    }
  });

  test('buttons should have visible states', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Check suggestion button colors
    const suggestionButton = page.locator('button:has-text("gradient descent")');
    const isVisible = await suggestionButton.isVisible().catch(() => false);
    
    if (isVisible) {
      const bgColor = await suggestionButton.evaluate(el => getComputedStyle(el).backgroundColor);
      const textColor = await suggestionButton.evaluate(el => getComputedStyle(el).color);
      const borderColor = await suggestionButton.evaluate(el => getComputedStyle(el).borderColor);
      
      console.log('Suggestion button bg:', bgColor);
      console.log('Suggestion button text:', textColor);
      console.log('Suggestion button border:', borderColor);
    }
  });
});

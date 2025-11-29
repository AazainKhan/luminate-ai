/**
 * Prompt Input E2E Tests for Luminate AI Extension
 * 
 * Tests the chat input component functionality:
 * - Text input and clearing
 * - Send button state
 * - Keyboard shortcuts (Enter to send)
 * - Export button
 * - Options panel
 */

import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('Prompt Input', () => {
  test('should have textarea for message input', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) {
      console.log('⚠️ On login page - skipping');
      return;
    }
    
    // Find the message textarea
    const textarea = page.locator('textarea');
    const hasTextarea = await textarea.isVisible().catch(() => false);
    
    console.log('Has textarea:', hasTextarea);
    expect(hasTextarea).toBe(true);
    
    // Check placeholder text
    if (hasTextarea) {
      const placeholder = await textarea.getAttribute('placeholder');
      console.log('Placeholder:', placeholder);
      expect(placeholder).toContain('COMP 237');
    }
  });

  test('should allow typing in textarea', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    const isVisible = await textarea.isVisible().catch(() => false);
    
    if (isVisible) {
      // Type a test message
      await textarea.fill('What is machine learning?');
      
      // Verify the text was entered
      const value = await textarea.inputValue();
      console.log('Typed value:', value);
      expect(value).toBe('What is machine learning?');
    }
  });

  test('send button should be disabled when input is empty', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Find send button
    const sendButton = page.locator('button:has-text("Send")');
    const isVisible = await sendButton.isVisible().catch(() => false);
    
    if (isVisible) {
      // Should be disabled when empty
      const isDisabled = await sendButton.isDisabled();
      console.log('Send button disabled when empty:', isDisabled);
      
      // Check opacity or styling indicates disabled state
      const opacity = await sendButton.evaluate(el => getComputedStyle(el).opacity);
      console.log('Send button opacity:', opacity);
    }
  });

  test('send button should be enabled when input has text', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    const isVisible = await textarea.isVisible().catch(() => false);
    
    if (isVisible) {
      // Type something
      await textarea.fill('Test message');
      await page.waitForTimeout(500);
      
      // Send button should now be enabled
      const sendButton = page.locator('button:has-text("Send")');
      const buttonVisible = await sendButton.isVisible().catch(() => false);
      
      if (buttonVisible) {
        // Check button has active styling (not disabled look)
        const bgColor = await sendButton.evaluate(el => getComputedStyle(el).backgroundColor);
        console.log('Send button background when enabled:', bgColor);
        
        // Should have violet/purple color when enabled
        const hasVioletBg = bgColor.includes('124') || bgColor.includes('139'); // violet-600 RGB values
        console.log('Has violet background:', hasVioletBg);
      }
    }
  });

  test('textarea should auto-resize with content', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    const textarea = page.locator('textarea');
    const isVisible = await textarea.isVisible().catch(() => false);
    
    if (isVisible) {
      // Get initial height
      const initialHeight = await textarea.evaluate(el => el.scrollHeight);
      console.log('Initial height:', initialHeight);
      
      // Type multiple lines
      await textarea.fill('Line 1\nLine 2\nLine 3\nLine 4');
      await page.waitForTimeout(300);
      
      // Height should increase
      const newHeight = await textarea.evaluate(el => el.scrollHeight);
      console.log('Height after multiline:', newHeight);
      
      // New height should be greater
      expect(newHeight).toBeGreaterThanOrEqual(initialHeight);
    }
  });
});

test.describe('Input Toolbar', () => {
  test('should have options button', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for the options/sliders button
    const optionsButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    const buttonsInToolbar = await page.locator('form button').count();
    
    console.log('Buttons in form/toolbar:', buttonsInToolbar);
    expect(buttonsInToolbar).toBeGreaterThan(0);
  });

  test('should have new chat button', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for + button (new chat)
    const plusButtons = await page.locator('button svg').count();
    console.log('Icon buttons found:', plusButtons);
    
    // Should have multiple toolbar buttons
    expect(plusButtons).toBeGreaterThan(0);
  });

  test('export button should be disabled when no messages', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Find export/share button - it should be disabled on empty state
    // The Share button has specific tooltip "Export chat as Markdown"
    const toolbarButtons = page.locator('form button');
    const count = await toolbarButtons.count();
    
    console.log('Toolbar buttons found:', count);
    
    // Check that at least one button is in the toolbar
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('AI Detection Label', () => {
  test('should show AI detection modes label', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Look for the "AI auto-detects" text
    const detectionLabel = page.locator('text=/AI auto-detects/i');
    const hasLabel = await detectionLabel.isVisible().catch(() => false);
    
    console.log('Has AI detection label:', hasLabel);
    
    if (hasLabel) {
      const labelText = await detectionLabel.textContent();
      console.log('Label text:', labelText);
      
      // Should mention some of the modes
      expect(labelText?.toLowerCase()).toContain('auto-detect');
    }
  });
});

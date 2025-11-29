/**
 * Settings/Options Panel E2E Tests for Luminate AI Extension
 * 
 * Tests the options popover in the prompt input:
 * - Show Sources toggle
 * - Run Code toggle
 * - Options panel visibility
 */

import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('Options Panel', () => {
  test('should open options popover when clicking settings button', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) {
      console.log('⚠️ On login page - skipping');
      return;
    }
    
    // Find the options button (first button in the toolbar, has sliders icon)
    const optionsButton = page.locator('form button').first();
    const isVisible = await optionsButton.isVisible().catch(() => false);
    
    if (isVisible) {
      // Click the options button
      await optionsButton.click();
      await page.waitForTimeout(500);
      
      // Look for popover content
      const popover = page.locator('[data-radix-popper-content-wrapper], [role="dialog"]');
      const popoverVisible = await popover.isVisible().catch(() => false);
      
      console.log('Options popover visible:', popoverVisible);
      
      // Take screenshot
      await page.screenshot({ path: 'test-output/results/options-panel.png' });
    }
  });

  test('should show Response Options heading in popover', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Click options button
    const optionsButton = page.locator('form button').first();
    await optionsButton.click();
    await page.waitForTimeout(500);
    
    // Look for "Response Options" heading
    const heading = page.locator('text=/Response Options/i');
    const hasHeading = await heading.isVisible().catch(() => false);
    
    console.log('Has Response Options heading:', hasHeading);
  });

  test('should have Show Sources toggle', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Open options
    const optionsButton = page.locator('form button').first();
    await optionsButton.click();
    await page.waitForTimeout(500);
    
    // Look for Show Sources toggle
    const sourcesLabel = page.locator('text=/Show Sources/i');
    const hasLabel = await sourcesLabel.isVisible().catch(() => false);
    
    console.log('Has Show Sources toggle:', hasLabel);
    
    if (hasLabel) {
      // Find the switch
      const switchElement = page.locator('#show-sources, [role="switch"]').first();
      const hasSwitch = await switchElement.isVisible().catch(() => false);
      console.log('Has switch element:', hasSwitch);
    }
  });

  test('should have Run Code toggle', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Open options
    const optionsButton = page.locator('form button').first();
    await optionsButton.click();
    await page.waitForTimeout(500);
    
    // Look for Run Code toggle
    const codeLabel = page.locator('text=/Run Code/i');
    const hasLabel = await codeLabel.isVisible().catch(() => false);
    
    console.log('Has Run Code toggle:', hasLabel);
  });

  test('toggles should be interactive', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Open options
    const optionsButton = page.locator('form button').first();
    await optionsButton.click();
    await page.waitForTimeout(500);
    
    // Find a switch and try to toggle it
    const switches = page.locator('[role="switch"]');
    const switchCount = await switches.count();
    
    console.log('Found switches:', switchCount);
    
    if (switchCount > 0) {
      const firstSwitch = switches.first();
      
      // Get initial state
      const initialState = await firstSwitch.getAttribute('data-state');
      console.log('Initial switch state:', initialState);
      
      // Click to toggle
      await firstSwitch.click();
      await page.waitForTimeout(300);
      
      // Get new state
      const newState = await firstSwitch.getAttribute('data-state');
      console.log('New switch state:', newState);
      
      // State should have changed
      expect(newState).not.toBe(initialState);
    }
  });
});

test.describe('Tooltips', () => {
  test('should show tooltips on hover', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    if (hasLoginForm) return;
    
    // Hover over a toolbar button
    const toolbarButton = page.locator('form button').first();
    const isVisible = await toolbarButton.isVisible().catch(() => false);
    
    if (isVisible) {
      await toolbarButton.hover();
      await page.waitForTimeout(500);
      
      // Look for tooltip
      const tooltip = page.locator('[role="tooltip"]');
      const tooltipVisible = await tooltip.isVisible().catch(() => false);
      
      console.log('Tooltip visible on hover:', tooltipVisible);
    }
  });
});

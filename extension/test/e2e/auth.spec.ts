/**
 * Authentication E2E Tests for Luminate AI Extension
 * 
 * Tests the Supabase passwordless OTP authentication flow.
 * Note: When PLASMO_PUBLIC_DEV_AUTH_BYPASS=true, auth is bypassed
 * and users go directly to chat UI. These tests verify that behavior.
 */

import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('Authentication Flow', () => {
  test('should bypass login when DEV_AUTH_BYPASS is enabled', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    // Capture console to check auth state
    const authLogs: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('Auth') || msg.text().includes('DEV')) {
        authLogs.push(msg.text());
      }
    });
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Check if auth bypass is enabled
    const bypassEnabled = authLogs.some(log => log.includes('DEV AUTH BYPASS ENABLED'));
    console.log('Auth bypass enabled:', bypassEnabled);
    console.log('Auth logs:', authLogs);
    
    if (bypassEnabled) {
      // With bypass, we should NOT see login form
      const hasLoginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
      expect(hasLoginForm).toBe(false);
      console.log('✅ Login form correctly hidden when bypass is enabled');
    } else {
      // Without bypass, login form should be visible
      await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 10000 });
      console.log('✅ Login form visible when bypass is disabled');
    }
  });

  test('should show user greeting when authenticated', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // With auth bypass, should show greeting with mock user name
    const greeting = page.locator('text=/Hi,|Welcome/i');
    const hasGreeting = await greeting.isVisible().catch(() => false);
    
    // Or check for the empty state message
    const hasEmptyState = await page.locator('text=/Ask anything/i').isVisible().catch(() => false);
    
    console.log('Has greeting:', hasGreeting);
    console.log('Has empty state:', hasEmptyState);
    
    // Either greeting or empty state should be visible when authenticated
    expect(hasGreeting || hasEmptyState).toBe(true);
  });
});

test.describe('Extension Initialization', () => {
  test('should have valid extension ID', async ({ extensionId }) => {
    expect(extensionId).toBeTruthy();
    expect(extensionId.length).toBeGreaterThan(0);
    console.log('Extension ID:', extensionId);
  });

  test('should load extension pages without critical errors', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    // Collect console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Filter out known acceptable errors
    const criticalErrors = errors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('net::ERR_') &&
      !e.includes('Failed to load resource')
    );
    
    console.log('Critical errors:', criticalErrors.length);
    if (criticalErrors.length > 0) {
      console.log('Errors:', criticalErrors);
    }
    
    // Should have no critical errors
    expect(criticalErrors.length).toBe(0);
  });
});

/**
 * Interactive Debug Test - Takes screenshots at each step
 * Run with: pnpm test:e2e:debug --grep "Interactive Debug"
 */

import { test, expect, navigateToSidePanel } from './fixtures';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Ensure test-output directory exists
const outputDir = path.join(__dirname, '..', '..', 'test-output', 'debug-screenshots');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

async function screenshot(page: any, name: string) {
  const filepath = path.join(outputDir, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`📸 Screenshot saved: ${filepath}`);
}

test.describe('Interactive Debug', () => {
  test('should explore the UI step by step', async ({ context, extensionId }) => {
    console.log('\n🚀 Starting interactive debug test...');
    console.log(`📦 Extension ID: ${extensionId}`);
    
    const page = await navigateToSidePanel(context, extensionId);
    console.log(`📍 Navigated to sidepanel`);
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    await screenshot(page, '01-initial-load');
    
    // Check if we see login or chat UI
    const pageContent = await page.content();
    const hasLogin = pageContent.includes('Sign in') || await page.locator('input[type="email"]').isVisible().catch(() => false);
    const hasChat = pageContent.includes('Hi,') || pageContent.includes('Ask anything');
    
    console.log(`🔐 Has login form: ${hasLogin}`);
    console.log(`💬 Has chat UI: ${hasChat}`);
    
    // Wait longer for auth to settle
    await page.waitForTimeout(3000);
    await screenshot(page, '02-after-auth-settle');
    
    // Log all visible text
    const bodyText = await page.locator('body').textContent();
    console.log(`📝 Page text (first 500 chars): ${bodyText?.substring(0, 500)}`);
    
    // Check for nav rail
    const navRail = page.locator('[class*="h-screen"][class*="bg-slate"]').last();
    const navVisible = await navRail.isVisible().catch(() => false);
    console.log(`🧭 Nav rail visible: ${navVisible}`);
    
    if (navVisible) {
      await screenshot(page, '03-nav-rail-visible');
      
      // Try to expand nav rail
      const buttons = navRail.locator('button');
      const buttonCount = await buttons.count();
      console.log(`🔘 Nav rail buttons: ${buttonCount}`);
      
      // Click expand button (usually 2nd button)
      if (buttonCount > 1) {
        await buttons.nth(1).click();
        await page.waitForTimeout(1000);
        await screenshot(page, '04-nav-expanded');
      }
    }
    
    // Check for textarea
    const textarea = page.locator('textarea');
    const textareaVisible = await textarea.isVisible().catch(() => false);
    console.log(`✏️ Textarea visible: ${textareaVisible}`);
    
    if (textareaVisible) {
      // Type a test message
      await textarea.fill('What is machine learning?');
      await screenshot(page, '05-message-typed');
      
      // Find send button
      const sendButton = page.locator('button:has-text("Send")');
      const sendVisible = await sendButton.isVisible().catch(() => false);
      const sendEnabled = await sendButton.isEnabled().catch(() => false);
      console.log(`📤 Send button visible: ${sendVisible}, enabled: ${sendEnabled}`);
      
      if (sendVisible && sendEnabled) {
        await screenshot(page, '06-before-send');
        await sendButton.click();
        
        // Wait and take screenshots during response
        for (let i = 1; i <= 10; i++) {
          await page.waitForTimeout(2000);
          await screenshot(page, `07-after-send-${i * 2}s`);
          
          // Check for response
          const messages = await page.locator('[class*="message"], [data-role]').count();
          console.log(`💬 Messages after ${i * 2}s: ${messages}`);
        }
      }
    }
    
    // Check suggestion buttons
    const suggestions = page.locator('button:has-text("gradient descent")');
    const suggestionsVisible = await suggestions.isVisible().catch(() => false);
    console.log(`💡 Suggestion buttons visible: ${suggestionsVisible}`);
    
    if (suggestionsVisible) {
      await screenshot(page, '08-suggestion-visible');
      await suggestions.click();
      await page.waitForTimeout(5000);
      await screenshot(page, '09-after-suggestion-click');
    }
    
    // Final screenshot
    await screenshot(page, '10-final-state');
    
    console.log('\n✅ Debug test completed. Check test-output/debug-screenshots/');
  });

  test('should test nav rail expansion in detail', async ({ context, extensionId }) => {
    console.log('\n🧭 Testing Nav Rail...');
    
    const page = await navigateToSidePanel(context, extensionId);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    await screenshot(page, 'nav-01-initial');
    
    // Find the nav rail
    const navRails = page.locator('[class*="bg-slate-950"]');
    const count = await navRails.count();
    console.log(`🔍 Found ${count} elements with bg-slate-950`);
    
    // Try different selectors
    const rightPanel = page.locator('.absolute.top-0.right-0');
    const rightVisible = await rightPanel.isVisible().catch(() => false);
    console.log(`➡️ Right panel visible: ${rightVisible}`);
    
    // Look for the "L" logo
    const logo = page.locator('text=L').first();
    const logoVisible = await logo.isVisible().catch(() => false);
    console.log(`🅛 Logo visible: ${logoVisible}`);
    
    if (logoVisible) {
      // Get the parent container
      const logoParent = logo.locator('xpath=ancestor::div[contains(@class, "h-screen")]');
      const parentWidth = await logoParent.evaluate((el) => el.clientWidth).catch(() => 0);
      console.log(`📏 Nav width: ${parentWidth}px`);
    }
    
    // Try clicking on any visible button
    const allButtons = page.locator('button:visible');
    const buttonCount = await allButtons.count();
    console.log(`🔘 Total visible buttons: ${buttonCount}`);
    
    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = allButtons.nth(i);
      const text = await button.textContent().catch(() => '');
      const ariaLabel = await button.getAttribute('aria-label').catch(() => '');
      console.log(`  Button ${i}: "${text.substring(0, 30)}" aria-label="${ariaLabel}"`);
    }
    
    await screenshot(page, 'nav-02-buttons-analyzed');
  });

  test('should test sending message with detailed logging', async ({ context, extensionId }) => {
    console.log('\n💬 Testing Message Send...');
    
    const page = await navigateToSidePanel(context, extensionId);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    
    // Capture network requests
    const requests: string[] = [];
    page.on('request', (request: any) => {
      if (request.url().includes('localhost:8000')) {
        requests.push(`➡️ ${request.method()} ${request.url()}`);
        console.log(`➡️ Request: ${request.method()} ${request.url()}`);
      }
    });
    
    page.on('response', (response: any) => {
      if (response.url().includes('localhost:8000')) {
        console.log(`⬅️ Response: ${response.status()} ${response.url()}`);
      }
    });
    
    // Capture console logs
    page.on('console', (msg: any) => {
      const text = msg.text();
      if (text.includes('error') || text.includes('Error') || text.includes('Auth') || text.includes('chat')) {
        console.log(`🖥️ Console: ${text.substring(0, 200)}`);
      }
    });
    
    await screenshot(page, 'msg-01-initial');
    
    const textarea = page.locator('textarea');
    if (await textarea.isVisible()) {
      await textarea.fill('Hello');
      await screenshot(page, 'msg-02-typed');
      
      const sendBtn = page.locator('button:has-text("Send")');
      if (await sendBtn.isVisible() && await sendBtn.isEnabled()) {
        await sendBtn.click();
        console.log('📤 Send clicked');
        
        // Wait and monitor
        for (let i = 1; i <= 15; i++) {
          await page.waitForTimeout(1000);
          
          const bodyText = await page.locator('body').textContent();
          if (bodyText?.includes('error') || bodyText?.includes('Error')) {
            console.log(`❌ Error detected at ${i}s`);
            await screenshot(page, `msg-error-at-${i}s`);
          }
          
          if (i % 3 === 0) {
            await screenshot(page, `msg-03-after-${i}s`);
          }
        }
      }
    }
    
    console.log('\n📊 Network requests made:');
    requests.forEach(r => console.log(r));
    
    await screenshot(page, 'msg-04-final');
  });
});

/**
 * Playwright Test Fixtures for Chrome Extension Testing
 * 
 * Uses launchPersistentContext with extension loading args
 * per Playwright's official Chrome extension documentation.
 */

import { test as base, chromium, type BrowserContext } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the built extension - prefer prod build (has auth bypass baked in)
const EXTENSION_PATH_PROD = path.join(__dirname, '..', '..', 'build', 'chrome-mv3-prod');
const EXTENSION_PATH_DEV = path.join(__dirname, '..', '..', 'build', 'chrome-mv3-dev');

// Use prod build if it exists, otherwise fall back to dev
const EXTENSION_PATH = fs.existsSync(EXTENSION_PATH_PROD) ? EXTENSION_PATH_PROD : EXTENSION_PATH_DEV;

export const test = base.extend<{
  context: BrowserContext;
  extensionId: string;
}>({
  // Override context to load extension
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      headless: false, // Extensions require headed mode
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
        '--no-first-run',
        '--no-default-browser-check',
      ],
    });
    await use(context);
    await context.close();
  },

  // Get extension ID from service worker
  extensionId: async ({ context }, use) => {
    // For Manifest V3, we get the extension ID from the service worker
    let serviceWorker = context.serviceWorkers()[0];
    
    if (!serviceWorker) {
      // Wait for service worker to register
      serviceWorker = await context.waitForEvent('serviceworker', { timeout: 30000 });
    }

    const extensionId = serviceWorker.url().split('/')[2];
    await use(extensionId);
  },
});

export const expect = test.expect;

// Helper to navigate to extension pages
export async function navigateToSidePanel(context: BrowserContext, extensionId: string) {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/sidepanel.html`);
  return page;
}

export async function navigateToPopup(context: BrowserContext, extensionId: string) {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  return page;
}

export async function navigateToOptions(context: BrowserContext, extensionId: string) {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/options.html`);
  return page;
}

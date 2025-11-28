import { defineConfig } from '@playwright/test';
import path from 'path';

export default defineConfig({
  testDir: './test/e2e',
  testMatch: '**/*.spec.ts',
  timeout: 60000,
  retries: 0,
  workers: 1, // Extensions require single worker
  reporter: [
    ['html', { outputFolder: 'test-output/playwright-report' }],
    ['list']
  ],
  use: {
    headless: false, // Extensions don't work in headless mode with regular Chrome
    viewport: { width: 1280, height: 720 },
    actionTimeout: 10000,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  outputDir: 'test-output/results',
  projects: [
    {
      name: 'chromium-extension',
      use: {
        // We'll use custom fixture for extension loading
      },
    },
  ],
});

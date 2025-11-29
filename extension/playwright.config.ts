import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Luminate AI E2E Test Configuration
 * 
 * Key features:
 * - Sharding support for parallel CI execution
 * - Enhanced logging and reporting
 * - Categorized test projects
 * - Failure screenshots and traces
 */
export default defineConfig({
  testDir: './test/e2e',
  testMatch: '**/*.spec.ts',
  
  // Timeouts
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  
  // Retry failed tests once
  retries: process.env.CI ? 2 : 1,
  
  // Workers: 1 for extension tests (Chrome limitation), but can shard across processes
  workers: 1,
  
  // Rich reporting for debugging
  reporter: [
    ['html', { 
      outputFolder: 'test-output/playwright-report',
      open: 'never' // Don't auto-open in CI
    }],
    ['list', { printSteps: true }],
    ['json', { outputFile: 'test-output/results.json' }],
    // Custom reporter for structured logging
    ['./test/e2e/reporters/structured-logger.ts'],
  ],
  
  // Global settings
  use: {
    headless: false, // Extensions require headed mode
    viewport: { width: 1280, height: 720 },
    actionTimeout: 15000,
    navigationTimeout: 30000,
    
    // Capture artifacts on failure
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Slow down for visibility during debug
    // launchOptions: { slowMo: 100 },
  },
  
  outputDir: 'test-output/results',
  
  // Preserve output for debugging
  preserveOutput: 'failures-only',
  
  // Test projects - can run specific categories
  projects: [
    // Core UI tests - fastest, run first
    {
      name: 'ui-core',
      testMatch: /\/(sidepanel|navigation|auth)\.spec\.ts$/,
      use: {},
    },
    // Nav rail and sidebar tests
    {
      name: 'ui-sidebar',
      testMatch: /\/(sidebar|folders|starring|new-items|user-menu)\.spec\.ts$/,
      use: {},
    },
    // Backend integration tests
    {
      name: 'backend',
      testMatch: /\/(backend-integration|chat-api)\.spec\.ts$/,
      use: {},
    },
    // Full E2E flows
    {
      name: 'e2e-flows',
      testMatch: /\/(chat-flow|mastery|educational)\.spec\.ts$/,
      use: {},
    },
    // Debug/interactive tests - run manually
    {
      name: 'debug',
      testMatch: /\/debug.*\.spec\.ts$/,
      use: {},
    },
    // Default: run all
    {
      name: 'chromium-extension',
      testMatch: '**/*.spec.ts',
      testIgnore: /\/debug.*\.spec\.ts$/, // Skip debug tests in full run
      use: {},
    },
  ],
  
  // Global setup/teardown
  globalSetup: './test/e2e/global-setup.ts',
  globalTeardown: './test/e2e/global-teardown.ts',
});

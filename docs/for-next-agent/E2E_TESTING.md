# End-to-End Testing for Chrome Extension

## Overview

E2E tests use **Playwright** with official Chrome extension support via `launchPersistentContext`.

---

## Quick Start

```bash
cd extension

# Run all tests
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug

# Interactive UI mode
npm run test:e2e:ui

# View HTML report
npm run test:e2e:report
```

---

## Dev Auth Bypass

For E2E testing, authentication is bypassed using an environment variable:

**In `extension/.env.local`:**
```
PLASMO_PUBLIC_DEV_AUTH_BYPASS=true
```

When enabled:
- Login screen is skipped
- Mock user: `dev@my.centennialcollege.ca` (student role)
- Chat UI is immediately accessible

**To disable for production testing:**
```
PLASMO_PUBLIC_DEV_AUTH_BYPASS=false
```

---

## Test Structure

```
extension/
├── playwright.config.ts      # Playwright configuration
├── test/
│   └── e2e/
│       ├── fixtures.ts       # Extension loading fixtures
│       ├── auth.spec.ts      # Authentication tests
│       └── chat.spec.ts      # Chat functionality tests
└── test-output/              # Screenshots, reports
```

---

## Key Files

### `playwright.config.ts`
```typescript
export default defineConfig({
  testDir: './test/e2e',
  timeout: 60000,
  workers: 1,  // Extensions require single worker
  use: {
    headless: false,  // Extensions need headed mode
  },
});
```

### `fixtures.ts`
```typescript
import { test as base, chromium } from '@playwright/test';

const EXTENSION_PATH = path.join(__dirname, '..', '..', 'build', 'chrome-mv3-prod');

export const test = base.extend({
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    await use(context);
    await context.close();
  },
  
  extensionId: async ({ context }, use) => {
    let serviceWorker = context.serviceWorkers()[0];
    if (!serviceWorker) {
      serviceWorker = await context.waitForEvent('serviceworker');
    }
    const extensionId = serviceWorker.url().split('/')[2];
    await use(extensionId);
  },
});
```

---

## Test Scenarios

| Test | Description | Status |
|------|-------------|--------|
| Auth bypass detection | Verify auth bypass works | ✅ |
| User greeting | Show greeting when authenticated | ✅ |
| Extension ID | Valid extension loaded | ✅ |
| No critical errors | No console errors on load | ✅ |
| Chat UI visible | Chat container renders | ✅ |
| Accessible buttons | 16+ buttons found | ✅ |
| Chat input detected | Textarea and suggestions visible | ✅ |
| Dark theme default | Dark mode applied | ✅ |

---

## Writing New Tests

```typescript
import { test, expect, navigateToSidePanel } from './fixtures';

test.describe('My Feature', () => {
  test('should do something', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    await page.waitForLoadState('domcontentloaded');
    
    // Your assertions
    await expect(page.locator('button')).toBeVisible();
  });
});
```

---

## Debugging Tips

1. **Use headed mode**: `npm run test:e2e:headed`
2. **Debug mode**: `npm run test:e2e:debug` (pauseOnFirst)
3. **Screenshots**: Automatically captured on failure in `test-output/results/`
4. **Console logs**: Capture with `page.on('console', msg => ...)`
5. **HTML report**: `npm run test:e2e:report`

---

## CI/CD Integration

**TODO:** Update `.github/workflows/e2e-tests.yml` to use Playwright:

```yaml
- name: Run E2E tests
  run: |
    cd extension
    npm run test:e2e
```

Note: Playwright can run in CI with `xvfb-run` on Linux for headed mode.

---

## Why Playwright Over WebdriverIO?

| Feature | Playwright | WebdriverIO |
|---------|-----------|-------------|
| Extension Support | ✅ Official docs | ⚠️ Workarounds needed |
| Manifest V3 | ✅ Built-in SW support | ❌ CDP deprecated |
| Setup | Simple 2 args | Complex config |
| Speed | Fast | Slower |
| Maintenance | Microsoft active | Community |

---

## Resources

- [Playwright Chrome Extensions](https://playwright.dev/docs/chrome-extensions)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [launchPersistentContext](https://playwright.dev/docs/api/class-browsertype#browser-type-launch-persistent-context)

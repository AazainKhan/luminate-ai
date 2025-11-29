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
│       ├── fixtures.ts         # Extension loading fixtures
│       ├── auth.spec.ts        # Authentication tests (4 tests)
│       ├── chat.spec.ts        # Chat UI tests (4 tests)
│       ├── navigation.spec.ts  # Navigation tests (6 tests)
│       ├── suggestions.spec.ts # Suggestion buttons (6 tests)
│       ├── prompt-input.spec.ts # Input component tests (9 tests)
│       ├── options-panel.spec.ts # Settings panel tests (6 tests)
│       └── accessibility.spec.ts # A11y tests (12 tests)
└── test-output/                # Screenshots, reports
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

### Authentication (`auth.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Auth bypass detection | Verify auth bypass works | ✅ |
| User greeting | Show greeting when authenticated | ✅ |
| Extension ID | Valid extension loaded | ✅ |
| No critical errors | No console errors on load | ✅ |

### Chat Interface (`chat.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Chat UI visible | Chat container renders | ✅ |
| Accessible buttons | 16+ buttons found | ✅ |
| Chat input detected | Textarea and suggestions visible | ✅ |
| Dark theme default | Dark mode applied | ✅ |

### Navigation (`navigation.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Side panel title | Luminate branding visible | ✅ |
| Nav rail display | Navigation on authenticated view | ✅ |
| Layout structure | Flex containers present | ✅ |
| Loading states | Content loads properly | ✅ |
| Page refresh | Handles refresh gracefully | ✅ |
| Direct navigation | URL navigation works | ✅ |

### Suggestion Buttons (`suggestions.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Display suggestions | 4 suggestion buttons visible | ✅ |
| Clickable buttons | Buttons are enabled | ✅ |
| Button styling | Rounded pill style | ✅ |
| User greeting | "Hi, Dev" greeting shown | ✅ |
| Subtitle text | Helpful text visible | ✅ |
| Logo display | L logo in gradient box | ✅ |

### Prompt Input (`prompt-input.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Textarea present | Message input visible | ✅ |
| Typing works | Can type in textarea | ✅ |
| Send disabled empty | Button disabled when empty | ✅ |
| Send enabled text | Button enabled with text | ✅ |
| Auto-resize | Textarea grows with content | ✅ |
| Options button | Toolbar has options | ✅ |
| New chat button | + button present | ✅ |
| Export button | Share button in toolbar | ✅ |
| AI detection label | Auto-detect modes shown | ✅ |

### Options Panel (`options-panel.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Popover opens | Click opens options | ✅ |
| Response Options | Heading visible | ✅ |
| Show Sources toggle | Toggle present | ✅ |
| Run Code toggle | Toggle present | ✅ |
| Toggles interactive | Can toggle on/off | ✅ |
| Tooltips | Hover shows tooltip | ✅ |

### Accessibility (`accessibility.spec.ts`)
| Test | Description | Status |
|------|-------------|--------|
| Tab navigation | Tab moves through elements | ✅ |
| Textarea focus | Focus and type works | ✅ |
| Enter submit | Enter key handled | ✅ |
| Shift+Enter newline | Adds newline, no submit | ✅ |
| Focus ring | Buttons have focus styles | ✅ |
| Textarea focus state | Visual focus indication | ✅ |
| Accessible names | Buttons have text/aria | ✅ |
| Form structure | Proper form element | ✅ |
| Heading hierarchy | H1 present | ✅ |
| Switch roles | role="switch" present | ✅ |
| Text contrast | Light text on dark bg | ✅ |
| Button states | Visible state changes | ✅ |

**Total: 47 tests passing**

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

The GitHub Actions workflow (`.github/workflows/e2e-tests.yml`) runs Playwright tests on push/PR:

```yaml
- name: Build extension (dev mode)
  run: |
    cd extension
    pnpm dev &
    DEV_PID=$!
    # Wait for dev build folder to exist
    for i in {1..60}; do
      if [ -d "build/chrome-mv3-dev" ]; then break; fi
      sleep 1
    done
    kill $DEV_PID 2>/dev/null || true

- name: Run E2E tests
  run: |
    cd extension
    xvfb-run --auto-servernum pnpm test:e2e
```

**Key CI/CD notes:**
- Uses dev build (`chrome-mv3-dev`) for consistency with local testing
- Starts `pnpm dev`, waits for build, then kills the watch process
- Uses `xvfb-run` for headed mode on Linux (extensions require headed mode)
- Builds with `PLASMO_PUBLIC_DEV_AUTH_BYPASS=true` for test auth
- Uploads Playwright HTML report as artifact

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

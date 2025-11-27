# End-to-End Testing for Chrome Extension

## Overview

This document provides resources and guidance for implementing end-to-end (E2E) testing for the Luminate AI Chrome Extension.

---

## Recommended Testing Frameworks

### 1. WebdriverIO (Recommended)
**Official Chrome Extension Testing Support**

📚 **Documentation:** https://webdriver.io/docs/extension-testing/web-extensions/

**Why WebdriverIO:**
- First-class Chrome extension support
- Can test side panels, popups, and content scripts
- Integrates with CI/CD pipelines
- Supports parallel testing

**Setup:**
```bash
cd extension
pnpm add -D @wdio/cli @wdio/local-runner @wdio/mocha-framework
npx wdio config
```

**Example Test (Side Panel):**
```typescript
import { browser } from '@wdio/globals'

describe('Luminate AI Side Panel', () => {
  before(async () => {
    // Load extension
    await browser.url('chrome-extension://YOUR_EXTENSION_ID/sidepanel.html')
  })

  it('should display chat interface', async () => {
    const chatContainer = await $('[data-testid="chat-container"]')
    await expect(chatContainer).toBeDisplayed()
  })

  it('should send a message', async () => {
    const input = await $('textarea[placeholder*="Ask anything"]')
    await input.setValue('What is gradient descent?')
    
    const sendButton = await $('button*=Send')
    await sendButton.click()
    
    // Wait for response
    const response = await $('[data-testid="ai-message"]')
    await expect(response).toBeDisplayed()
  })
})
```

---

### 2. Puppeteer (Alternative)
**Google's Official Browser Automation**

📚 **Documentation:** https://developer.chrome.com/docs/extensions/how-to/test/end-to-end-testing

**Setup:**
```bash
pnpm add -D puppeteer
```

**Example:**
```typescript
import puppeteer from 'puppeteer'
import path from 'path'

const extensionPath = path.join(__dirname, '../build/chrome-mv3-prod')

async function runTest() {
  const browser = await puppeteer.launch({
    headless: false,
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`,
    ],
  })

  // Get extension ID
  const targets = await browser.targets()
  const extensionTarget = targets.find(t => t.type() === 'service_worker')
  const extensionId = extensionTarget?.url().split('/')[2]

  // Open side panel
  const page = await browser.newPage()
  await page.goto(`chrome-extension://${extensionId}/sidepanel.html`)

  // Test interactions...
}
```

---

## Testing Strategy

### Unit Tests (Existing)
- Components: `extension/src/__tests__/`
- Use Vitest or Jest

### Integration Tests
- API mocking with MSW
- Component integration

### E2E Tests (New - Implement These)
1. **Authentication Flow**
   - Login with OTP
   - Domain validation (@my.centennialcollege.ca)
   - Session persistence

2. **Chat Functionality**
   - Send message → receive response
   - Streaming responses
   - Code execution
   - Intent routing (tutor/math/code)

3. **Admin Panel** (if admin)
   - File upload
   - ETL status

---

## CI/CD Integration

**GitHub Actions Example:**
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: |
          cd extension
          pnpm install
          
      - name: Build extension
        run: |
          cd extension
          pnpm build
          
      - name: Run E2E tests
        run: |
          cd extension
          pnpm test:e2e
```

---

## Key Test Scenarios

| Priority | Scenario | Agent/Feature |
|----------|----------|---------------|
| 🔴 High | Login → Chat → Response | Auth + Agent |
| 🔴 High | Tutor mode scaffolding | PedagogicalTutor |
| 🔴 High | Math derivation rendering | MathAgent |
| 🟡 Med | Code execution | E2B Sandbox |
| 🟡 Med | Export chat as .md | UI Feature |
| 🟢 Low | Admin file upload | ETL Pipeline |

---

## Next Steps for Agent

1. Install WebdriverIO: `pnpm add -D @wdio/cli`
2. Create `extension/wdio.conf.ts`
3. Add test files to `extension/test/e2e/`
4. Implement authentication test first
5. Add to CI/CD pipeline

---

## Resources

- [WebdriverIO Extension Testing](https://webdriver.io/docs/extension-testing/web-extensions/)
- [Chrome E2E Testing Guide](https://developer.chrome.com/docs/extensions/how-to/test/end-to-end-testing)
- [Puppeteer Extension Testing](https://pptr.dev/guides/chrome-extensions)
- [Plasmo Testing Guide](https://docs.plasmo.com/framework/workflows/testing)

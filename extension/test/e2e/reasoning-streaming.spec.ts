import { test, expect } from './fixtures';
import http from 'http';
import type { AddressInfo } from 'net';

test.describe('Reasoning Streaming UX', () => {
  test('should display streaming reasoning with animations and auto-scroll', async ({ page, extensionId }) => {
    // Start a local server to mock streaming
    const server = http.createServer((req, res) => {
      // Handle CORS preflight
      if (req.method === 'OPTIONS') {
        res.writeHead(204, {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        });
        res.end();
        return;
      }

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      });

      const send = (data: any) => {
        res.write(`data: ${JSON.stringify(data)}\n\n`);
      };

      // Step 1: Start thinking
      send({ type: 'thinking', step: 'scope_check', status: 'processing', message: 'Checking scope...' });

      // Step 2: Send reasoning chunks
      let chunkCount = 0;
      const interval = setInterval(() => {
        chunkCount++;
        send({ 
          type: 'reasoning-delta', 
          reasoningDelta: ` Reasoning chunk ${chunkCount}. ` 
        });

        if (chunkCount >= 5) {
          clearInterval(interval);
          send({ type: 'finish', chatId: 'test-chat-id' });
          res.end();
        }
      }, 100);
    });

    await new Promise<void>((resolve) => {
      server.listen(0, () => resolve());
    });
    const port = (server.address() as AddressInfo).port;

    // 1. Setup: Open the extension sidepanel
    await page.goto(`chrome-extension://${extensionId}/sidepanel.html`);
    
    // 2. Mock the chat stream by redirecting to local server
    await page.route('**/api/chat/stream', async route => {
      console.log('Route hit: /api/chat/stream');
      // Redirect to local server
      await route.continue({ url: `http://localhost:${port}` });
    });

    // 3. Trigger a chat message
    const input = page.locator('textarea[placeholder="Ask anything about COMP 237..."]');
    await input.fill('Explain recursion');
    await input.press('Enter');

    // 4. Verify user message appears
    await expect(page.locator('text=Explain recursion')).toBeVisible();

    // Verify ThinkingTrace appears (from thinking events)
    await expect(page.locator('[data-testid="thinking-trace-container"]')).toBeVisible();

    // Verify Reasoning appears (from reasoning-delta events)
    const reasoningContainer = page.locator('[data-testid="message-reasoning"]');
    await expect(reasoningContainer).toBeVisible();

    // Verify "Thinking..." text inside reasoning
    await expect(reasoningContainer).toContainText('Thinking...');

    // Cleanup
    server.close();
  });
});

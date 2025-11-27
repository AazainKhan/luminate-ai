/**
 * E2E Test Helpers for Luminate AI Chrome Extension
 * 
 * Provides utilities for:
 * - Extension navigation
 * - Authentication simulation
 * - Common assertions
 */

/**
 * Get the extension ID from the loaded extension
 */
export async function getExtensionId(): Promise<string> {
  // Navigate to chrome://extensions to find our extension
  await browser.url('chrome://extensions/')
  
  // Enable developer mode if not already enabled
  const devModeToggle = await $('extensions-manager').$('extensions-toolbar').$('#devMode')
  const isDevMode = await devModeToggle.getAttribute('checked')
  if (!isDevMode) {
    await devModeToggle.click()
    await browser.pause(500)
  }

  // Find Luminate AI extension
  const extensions = await $$('extensions-item')
  for (const ext of extensions) {
    const name = await ext.$('#name').getText()
    if (name.includes('Luminate AI')) {
      const id = await ext.getAttribute('id')
      return id
    }
  }

  throw new Error('Luminate AI extension not found. Make sure it is built and loaded.')
}

/**
 * Navigate to the extension's side panel
 */
export async function openSidePanel(extensionId: string): Promise<void> {
  await browser.url(`chrome-extension://${extensionId}/sidepanel.html`)
  await browser.pause(1000) // Wait for React to mount
}

/**
 * Navigate to the extension's admin panel
 */
export async function openAdminPanel(extensionId: string): Promise<void> {
  await browser.url(`chrome-extension://${extensionId}/admin-sidepanel.html`)
  await browser.pause(1000)
}

/**
 * Wait for the chat interface to be ready
 */
export async function waitForChatReady(): Promise<void> {
  // Wait for the chat container
  const chatContainer = await $('[data-testid="chat-container"]')
  await chatContainer.waitForExist({ timeout: 10000 })
  
  // Wait for input to be enabled
  const input = await $('textarea')
  await input.waitForEnabled({ timeout: 5000 })
}

/**
 * Send a chat message
 */
export async function sendMessage(message: string): Promise<void> {
  const input = await $('textarea')
  await input.setValue(message)
  
  // Find and click send button (or press Enter)
  const sendButton = await $('button[type="submit"]')
  if (await sendButton.isExisting()) {
    await sendButton.click()
  } else {
    await input.keys(['Enter'])
  }
}

/**
 * Wait for AI response
 */
export async function waitForResponse(timeout = 30000): Promise<string> {
  // Wait for loading to finish
  await browser.waitUntil(
    async () => {
      const loading = await $('[data-testid="loading-indicator"]')
      return !(await loading.isExisting())
    },
    { timeout, timeoutMsg: 'AI response took too long' }
  )

  // Get the last AI message
  const messages = await $$('[data-testid="ai-message"]')
  if (messages.length === 0) {
    throw new Error('No AI messages found')
  }
  
  const lastMessage = messages[messages.length - 1]
  return await lastMessage.getText()
}

/**
 * Mock authentication by setting localStorage tokens
 * NOTE: This is for testing only - real auth uses Supabase OTP
 */
export async function mockAuthentication(
  extensionId: string,
  role: 'student' | 'admin' = 'student'
): Promise<void> {
  await browser.url(`chrome-extension://${extensionId}/sidepanel.html`)
  
  // Set mock auth tokens in localStorage
  const mockUser = {
    id: 'test-user-id',
    email: role === 'admin' 
      ? 'test@centennialcollege.ca' 
      : 'test@my.centennialcollege.ca',
    role: role
  }
  
  await browser.execute((user) => {
    localStorage.setItem('luminate-mock-user', JSON.stringify(user))
    localStorage.setItem('luminate-mock-auth', 'true')
  }, mockUser)

  // Reload to apply mock auth
  await browser.refresh()
  await browser.pause(1000)
}

/**
 * Clear all stored data
 */
export async function clearStorage(): Promise<void> {
  await browser.execute(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
}

/**
 * Take a screenshot with a descriptive name
 */
export async function screenshot(name: string): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  await browser.saveScreenshot(`./test-output/screenshots/${timestamp}-${name}.png`)
}

/**
 * Check if an element contains specific text
 */
export async function expectTextContent(
  selector: string,
  expectedText: string
): Promise<void> {
  const element = await $(selector)
  await element.waitForExist({ timeout: 5000 })
  const text = await element.getText()
  expect(text).toContain(expectedText)
}

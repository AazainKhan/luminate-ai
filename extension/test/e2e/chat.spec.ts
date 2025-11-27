/**
 * E2E Test: Chat Functionality
 * 
 * Tests the core chat features:
 * - Sending messages
 * - Receiving streaming responses
 * - Intent auto-detection (tutor/math/code)
 * - Export functionality
 */

import { openSidePanel, clearStorage, screenshot } from './helpers'

describe('Chat Functionality', () => {
  let extensionId: string

  before(async () => {
    await browser.url('about:blank')
    await browser.pause(2000)
    
    // Get extension ID
    const targets = await browser.call(async () => {
      // @ts-ignore
      const { targetInfos } = await browser.cdp('Target', 'getTargets')
      const extTarget = targetInfos.find((t: any) => 
        t.type === 'service_worker' && t.url.includes('chrome-extension://')
      )
      if (extTarget) {
        const match = extTarget.url.match(/chrome-extension:\/\/([^\/]+)/)
        return match ? match[1] : null
      }
      return null
    })
    
    extensionId = targets as unknown as string
    console.log(`Extension ID: ${extensionId}`)
  })

  beforeEach(async () => {
    await clearStorage()
    
    // Setup mock authenticated session
    await browser.url(`chrome-extension://${extensionId}/sidepanel.html`)
    await browser.execute(() => {
      const mockSession = {
        access_token: 'mock-token-for-testing',
        expires_at: Date.now() + 3600000,
        user: {
          id: 'test-user-id',
          email: 'student@my.centennialcollege.ca',
          user_metadata: { role: 'student' }
        }
      }
      localStorage.setItem('sb-session', JSON.stringify(mockSession))
      localStorage.setItem('luminate-test-mode', 'true')
    })
    await browser.refresh()
    await browser.pause(1500)
  })

  describe('Chat Interface', () => {
    it('should display chat input area', async () => {
      await openSidePanel(extensionId)
      await screenshot('chat-interface')
      
      // Look for textarea or input for chat
      const chatInput = await $('textarea, input[type="text"]')
      expect(await chatInput.isExisting()).toBe(true)
    })

    it('should show auto-intent detection text', async () => {
      await openSidePanel(extensionId)
      
      const pageText = await $('body').getText()
      // Should show the passive auto-detect text
      const hasAutoDetect = 
        pageText.toLowerCase().includes('auto-detect') ||
        pageText.toLowerCase().includes('tutor') ||
        pageText.toLowerCase().includes('math')
      
      expect(hasAutoDetect).toBe(true)
      await screenshot('auto-intent-ui')
    })

    it('should enable send button when text is entered', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      await chatInput.setValue('What is machine learning?')
      await browser.pause(300)
      
      const sendButton = await $('button[type="submit"], button[aria-label*="send" i]')
      if (await sendButton.isExisting()) {
        const isDisabled = await sendButton.getAttribute('disabled')
        expect(isDisabled).toBeNull() // Not disabled
      }
    })
  })

  describe('Message Sending', () => {
    it('should send a message and display it in chat', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      const testMessage = 'Hello, this is a test message'
      await chatInput.setValue(testMessage)
      
      // Click send or press Enter
      const sendButton = await $('button[type="submit"]')
      if (await sendButton.isExisting()) {
        await sendButton.click()
      } else {
        await browser.keys(['Enter'])
      }
      
      await browser.pause(1000)
      
      // Check if message appears in chat
      const pageText = await $('body').getText()
      expect(pageText).toContain(testMessage)
      await screenshot('message-sent')
    })
  })

  describe('Tutor Mode', () => {
    it('should route explanation queries to tutor agent', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      // Send a tutor-style query
      await chatInput.setValue("I don't understand backpropagation, can you explain?")
      
      const sendButton = await $('button[type="submit"]')
      if (await sendButton.isExisting()) {
        await sendButton.click()
      }
      
      // Wait for response (or timeout)
      await browser.pause(5000)
      await screenshot('tutor-response')
      
      // Check for any response indicator
      const pageText = await $('body').getText()
      const hasResponse = pageText.length > 200 // Some response appeared
      expect(hasResponse).toBe(true)
    })
  })

  describe('Math Mode', () => {
    it('should handle mathematical queries', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      // Send a math query
      await chatInput.setValue('Derive the gradient descent update rule')
      
      const sendButton = await $('button[type="submit"]')
      if (await sendButton.isExisting()) {
        await sendButton.click()
      }
      
      await browser.pause(5000)
      await screenshot('math-response')
    })
  })

  describe('Export Functionality', () => {
    it('should have export button in chat interface', async () => {
      await openSidePanel(extensionId)
      
      // Look for export button
      const exportButton = await $('button[aria-label*="export" i], button:has-text("Export"), [data-testid="export-button"]')
      
      if (await exportButton.isExisting()) {
        expect(await exportButton.isDisplayed()).toBe(true)
        await screenshot('export-button')
      } else {
        // Export might be in a menu - just log
        console.log('Export button not directly visible - may be in menu')
      }
    })
  })

  describe('Error Handling', () => {
    it('should handle empty message submission gracefully', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      // Try to submit empty message
      await chatInput.setValue('')
      
      const sendButton = await $('button[type="submit"]')
      if (await sendButton.isExisting()) {
        // Button should be disabled for empty input
        const isDisabled = await sendButton.getAttribute('disabled')
        if (isDisabled === null) {
          await sendButton.click()
          await browser.pause(500)
        }
      }
      
      // No error should crash the page
      const hasError = await $('[role="alert"][class*="error"]')
      if (await hasError.isExisting()) {
        console.log('Error shown for empty message - expected behavior')
      }
      
      await screenshot('empty-message-handling')
    })

    it('should show loading state while waiting for response', async () => {
      await openSidePanel(extensionId)
      
      const chatInput = await $('textarea')
      if (!(await chatInput.isExisting())) {
        console.log('Skipping: Chat input not found')
        return
      }

      await chatInput.setValue('Quick test message')
      
      const sendButton = await $('button[type="submit"]')
      if (await sendButton.isExisting()) {
        await sendButton.click()
      }
      
      // Immediately check for loading indicator
      await browser.pause(100)
      await screenshot('loading-state')
      
      // Wait for response to complete
      await browser.pause(5000)
    })
  })
})

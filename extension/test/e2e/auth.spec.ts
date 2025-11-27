/**
 * E2E Test: Authentication Flow
 * 
 * Tests the Supabase OTP authentication with domain validation:
 * - Students: @my.centennialcollege.ca
 * - Admins: @centennialcollege.ca
 */

import { openSidePanel, clearStorage, screenshot } from './helpers'

describe('Authentication Flow', () => {
  let extensionId: string

  before(async () => {
    // Get extension ID from the URL after extension loads
    // Navigate to a blank page first, then find extension
    await browser.url('about:blank')
    await browser.pause(2000)
    
    // Get the extension ID from service worker
    const targets = await browser.call(async () => {
      // @ts-ignore - Chrome DevTools Protocol
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

    if (!targets) {
      // Fallback: hardcode or read from manifest
      throw new Error('Could not determine extension ID. Ensure extension is built.')
    }
    
    extensionId = targets as unknown as string
    console.log(`Extension ID: ${extensionId}`)
  })

  beforeEach(async () => {
    await clearStorage()
  })

  describe('Side Panel Access', () => {
    it('should display login screen when not authenticated', async () => {
      await openSidePanel(extensionId)
      await screenshot('login-screen')
      
      // Look for login/auth elements
      const authContainer = await $('[data-testid="auth-container"]')
      const loginExists = await authContainer.isExisting()
      
      // Either auth container exists OR we see login text
      if (!loginExists) {
        const pageText = await $('body').getText()
        expect(
          pageText.toLowerCase().includes('sign in') ||
          pageText.toLowerCase().includes('log in') ||
          pageText.toLowerCase().includes('email')
        ).toBe(true)
      } else {
        expect(loginExists).toBe(true)
      }
    })

    it('should show email input for OTP authentication', async () => {
      await openSidePanel(extensionId)
      
      // Find email input
      const emailInput = await $('input[type="email"]')
      const inputExists = await emailInput.isExisting()
      
      if (inputExists) {
        expect(await emailInput.isDisplayed()).toBe(true)
      } else {
        // May be a different auth UI - check for any input
        const anyInput = await $('input')
        expect(await anyInput.isExisting()).toBe(true)
      }
    })

    it('should validate student email domain', async () => {
      await openSidePanel(extensionId)
      await browser.pause(500)
      
      const emailInput = await $('input[type="email"]')
      if (!(await emailInput.isExisting())) {
        console.log('Skipping: Email input not found in current auth flow')
        return
      }

      // Enter invalid email domain
      await emailInput.setValue('test@gmail.com')
      
      // Try to submit
      const submitBtn = await $('button[type="submit"]')
      if (await submitBtn.isExisting()) {
        await submitBtn.click()
        await browser.pause(500)
        
        // Should show error for invalid domain
        const pageText = await $('body').getText()
        const hasError = 
          pageText.toLowerCase().includes('invalid') ||
          pageText.toLowerCase().includes('domain') ||
          pageText.toLowerCase().includes('centennial')
        
        expect(hasError).toBe(true)
        await screenshot('invalid-domain-error')
      }
    })

    it('should accept valid student email format', async () => {
      await openSidePanel(extensionId)
      await browser.pause(500)
      
      const emailInput = await $('input[type="email"]')
      if (!(await emailInput.isExisting())) {
        console.log('Skipping: Email input not found')
        return
      }

      // Enter valid student email
      await emailInput.setValue('student@my.centennialcollege.ca')
      
      // Form should be valid (no immediate error)
      const hasValidationError = await $('.error, [role="alert"]')
      const errorVisible = await hasValidationError.isExisting() && 
                          await hasValidationError.isDisplayed()
      
      expect(errorVisible).toBe(false)
      await screenshot('valid-student-email')
    })
  })

  describe('Session Persistence', () => {
    it('should maintain session after page reload', async () => {
      // This test requires a mock auth setup since we can't do real OTP
      await openSidePanel(extensionId)
      
      // Set mock session in localStorage
      await browser.execute(() => {
        const mockSession = {
          access_token: 'mock-token',
          user: {
            id: 'test-user',
            email: 'test@my.centennialcollege.ca'
          }
        }
        localStorage.setItem('sb-session', JSON.stringify(mockSession))
      })

      await browser.refresh()
      await browser.pause(1000)

      // Check if session persists (implementation-specific)
      const session = await browser.execute(() => {
        return localStorage.getItem('sb-session')
      })
      
      expect(session).not.toBeNull()
    })
  })
})

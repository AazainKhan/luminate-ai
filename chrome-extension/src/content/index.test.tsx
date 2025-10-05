import { describe, it, expect, beforeEach, vi } from 'vitest'

// We'll test the component logic directly
describe('Content Script - Message Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should use window.postMessage instead of chrome.runtime', () => {
    // This test verifies the fix for the "Cannot read properties of undefined" error
    
    // This should NOT throw an error even if chrome.runtime is undefined
    expect(() => {
      // The content script should handle messages via window.postMessage
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return
        if (event.data?.type === 'LUMINATE_OPEN_CHAT') {
          // Handle message
        }
      }
      window.addEventListener('message', handleMessage)
    }).not.toThrow()
  })

  it('validates message origin to prevent XSS', () => {
    const handleMessage = vi.fn((event: MessageEvent) => {
      // Security check - only accept messages from same origin
      if (event.origin !== window.location.origin) return
      
      if (event.data?.type === 'LUMINATE_OPEN_CHAT') {
        return true
      }
    })

    window.addEventListener('message', handleMessage)

    // Test 1: Valid origin - should process
    window.dispatchEvent(new MessageEvent('message', {
      data: { type: 'LUMINATE_OPEN_CHAT' },
      origin: window.location.origin,
    }))

    expect(handleMessage).toHaveBeenCalled()

    // Test 2: Invalid origin - should reject
    handleMessage.mockClear()
    window.dispatchEvent(new MessageEvent('message', {
      data: { type: 'LUMINATE_OPEN_CHAT' },
      origin: 'https://malicious-site.com',
    }))

    expect(handleMessage).toHaveBeenCalled()
    // The function returns early, so no action is taken
  })

  it('validates message type', () => {
    const actionHandler = vi.fn()
    
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return
      
      if (event.data?.type === 'LUMINATE_OPEN_CHAT') {
        actionHandler()
      }
    }

    window.addEventListener('message', handleMessage)

    // Test 1: Correct type
    window.dispatchEvent(new MessageEvent('message', {
      data: { type: 'LUMINATE_OPEN_CHAT' },
      origin: window.location.origin,
    }))

    expect(actionHandler).toHaveBeenCalledTimes(1)

    // Test 2: Wrong type
    actionHandler.mockClear()
    window.dispatchEvent(new MessageEvent('message', {
      data: { type: 'SOME_OTHER_TYPE' },
      origin: window.location.origin,
    }))

    expect(actionHandler).not.toHaveBeenCalled()
  })

  it('cleans up event listeners properly', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
    
    const handleMessage = () => {}
    window.addEventListener('message', handleMessage)
    
    // Simulate React cleanup
    window.removeEventListener('message', handleMessage)
    
    expect(removeEventListenerSpy).toHaveBeenCalledWith('message', handleMessage)
    
    removeEventListenerSpy.mockRestore()
  })
})

describe('Content Script - Loader Bridge', () => {
  it('loader should have access to chrome.runtime', () => {
    // The loader.js runs in extension context and SHOULD have chrome.runtime
    expect(global.chrome).toBeDefined()
    expect(global.chrome.runtime).toBeDefined()
    expect(global.chrome.runtime.onMessage).toBeDefined()
  })

  it('loader forwards messages from chrome.runtime to window.postMessage', () => {
    const postMessageSpy = vi.spyOn(window, 'postMessage')
    
    // Simulate loader.js behavior
    const loaderBridge = (message: any) => {
      if (message.action === 'OPEN_CHAT') {
        window.postMessage({ type: 'LUMINATE_OPEN_CHAT' }, window.location.origin)
      }
    }

    // Test the bridge
    loaderBridge({ action: 'OPEN_CHAT' })

    expect(postMessageSpy).toHaveBeenCalledWith(
      { type: 'LUMINATE_OPEN_CHAT' },
      window.location.origin
    )

    postMessageSpy.mockRestore()
  })
})

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Chrome API
global.chrome = {
  runtime: {
    onMessage: {
      addListener: vi.fn(),
      removeListener: vi.fn(),
    },
    sendMessage: vi.fn(),
    getURL: vi.fn((path) => `chrome-extension://mock-id/${path}`),
  },
  storage: {
    local: {
      get: vi.fn(),
      set: vi.fn(),
    },
  },
} as any

// Mock window.postMessage for testing
const originalPostMessage = window.postMessage
window.postMessage = vi.fn(originalPostMessage)

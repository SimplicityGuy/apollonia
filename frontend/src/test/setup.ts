import '@testing-library/jest-dom'
import { beforeEach, afterEach, vi } from 'vitest'
import './matchers'

// Extend global for vitest environment
declare global {
  var IntersectionObserver: typeof IntersectionObserver
  var ResizeObserver: typeof ResizeObserver
}

// Global test setup
beforeEach(() => {
  // Reset any mocks or global state before each test
  vi.clearAllMocks()

  // Clear all timers
  vi.clearAllTimers()

  // Reset document body
  document.body.innerHTML = ''

  // Reset viewport
  window.innerWidth = 1024
  window.innerHeight = 768

  // Mock console methods to reduce noise in tests
  console.warn = vi.fn()
  console.error = vi.fn()
})

afterEach(() => {
  // Cleanup after each test
  vi.resetAllMocks()

  // Restore real timers if they were mocked
  vi.useRealTimers()

  // Clear any remaining DOM elements
  document.body.innerHTML = ''

  // Check for console errors and warnings
  if ((console.error as any).mock?.calls.length > 0) {
    const errors = (console.error as any).mock.calls
    console.log('Console errors during test:', errors)
  }

  if ((console.warn as any).mock?.calls.length > 0) {
    const warnings = (console.warn as any).mock.calls
    console.log('Console warnings during test:', warnings)
  }
})

// Mock IntersectionObserver for components that use it
;(globalThis as any).IntersectionObserver = class IntersectionObserver {
  root: Element | null = null
  rootMargin: string = '0px'
  thresholds: ReadonlyArray<number> = [0]

  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return []
  }
} as unknown as typeof IntersectionObserver

// Mock ResizeObserver for components that use it
;(globalThis as any).ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

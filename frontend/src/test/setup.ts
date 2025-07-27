import '@testing-library/jest-dom'
import { beforeEach, vi } from 'vitest'

// Extend global for vitest environment
declare global {
  var IntersectionObserver: typeof IntersectionObserver
  var ResizeObserver: typeof ResizeObserver
}

// Global test setup
beforeEach(() => {
  // Reset any mocks or global state before each test
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

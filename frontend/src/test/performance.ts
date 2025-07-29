import { vi } from 'vitest'

// ============================================================================
// Performance Testing Utilities
// ============================================================================

/**
 * Measure the performance of a test function
 */
export const measurePerformance = async (
  name: string,
  fn: () => Promise<void> | void,
  threshold = 1000 // Default 1 second threshold
) => {
  const start = performance.now()
  await fn()
  const end = performance.now()
  const duration = end - start

  console.log(`Performance: ${name} took ${duration.toFixed(2)}ms`)

  if (duration > threshold) {
    console.warn(`⚠️ Performance warning: ${name} exceeded threshold of ${threshold}ms`)
  }

  return duration
}

/**
 * Run a function multiple times and measure average performance
 */
export const benchmarkFunction = async (
  name: string,
  fn: () => Promise<void> | void,
  iterations = 10
) => {
  const times: number[] = []

  for (let i = 0; i < iterations; i++) {
    const duration = await measurePerformance(`${name} (iteration ${i + 1})`, fn, Infinity)
    times.push(duration)
  }

  const average = times.reduce((a, b) => a + b, 0) / times.length
  const min = Math.min(...times)
  const max = Math.max(...times)

  console.log(`
Benchmark Results for ${name}:
- Average: ${average.toFixed(2)}ms
- Min: ${min.toFixed(2)}ms
- Max: ${max.toFixed(2)}ms
- Iterations: ${iterations}
  `)

  return { average, min, max, times }
}

/**
 * Mock slow API responses for performance testing
 */
export const mockSlowAPI = (delay = 2000) => {
  return vi.fn().mockImplementation(() =>
    new Promise((resolve) => {
      setTimeout(() => resolve({ data: 'slow response' }), delay)
    })
  )
}

/**
 * Simulate network conditions
 */
export const simulateNetworkConditions = (type: 'fast' | 'slow' | '3g' | 'offline') => {
  const conditions = {
    fast: { delay: 50, throughput: Infinity },
    slow: { delay: 2000, throughput: 50000 },
    '3g': { delay: 500, throughput: 200000 },
    offline: { delay: Infinity, throughput: 0 }
  }

  const condition = conditions[type]

  // Mock fetch with delay
  global.fetch = vi.fn().mockImplementation((url) =>
    new Promise((resolve, reject) => {
      if (condition.delay === Infinity) {
        reject(new Error('Network offline'))
      } else {
        setTimeout(() => {
          resolve({
            ok: true,
            json: async () => ({ data: 'response' })
          })
        }, condition.delay)
      }
    })
  )

  return condition
}

/**
 * Memory usage tracking
 */
export const trackMemoryUsage = () => {
  if ('memory' in performance) {
    const memory = (performance as any).memory
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit
    }
  }
  return null
}

/**
 * Throttle function execution for testing
 */
export const createThrottledTest = (fn: Function, delay: number) => {
  let lastCall = 0

  return (...args: any[]) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      return fn(...args)
    }
  }
}

/**
 * Test render performance
 */
export const measureRenderPerformance = async (
  component: React.ComponentType,
  props: any = {}
) => {
  const { render } = await import('@testing-library/react')

  const start = performance.now()
  const { container } = render(component, props)
  const end = performance.now()

  const renderTime = end - start
  const domNodes = container.querySelectorAll('*').length

  console.log(`
Render Performance:
- Render time: ${renderTime.toFixed(2)}ms
- DOM nodes: ${domNodes}
- Nodes per ms: ${(domNodes / renderTime).toFixed(2)}
  `)

  return { renderTime, domNodes }
}

/**
 * Test re-render performance
 */
export const measureReRenderPerformance = async (
  component: React.ComponentType,
  props: any = {},
  updateProps: any = {},
  rerenders = 10
) => {
  const { render, rerender } = await import('@testing-library/react')

  const { container } = render(component, props)

  const times: number[] = []

  for (let i = 0; i < rerenders; i++) {
    const start = performance.now()
    rerender(component, { ...props, ...updateProps, key: i })
    const end = performance.now()
    times.push(end - start)
  }

  const average = times.reduce((a, b) => a + b, 0) / times.length

  console.log(`
Re-render Performance:
- Average re-render time: ${average.toFixed(2)}ms
- Total re-renders: ${rerenders}
  `)

  return { average, times }
}

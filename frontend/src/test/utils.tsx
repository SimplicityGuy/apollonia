/* eslint-disable react-refresh/only-export-components */
import React from 'react'
import { render, RenderOptions, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

// ============================================================================
// Test Query Client Configuration
// ============================================================================

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    // Disable error logging in tests
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })

// ============================================================================
// Wrapper Components
// ============================================================================

interface WrapperProps {
  children: React.ReactNode
}

export const AllTheProviders: React.FC<WrapperProps> = ({ children }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

interface MemoryRouterWrapperProps extends WrapperProps {
  initialEntries?: string[]
  initialIndex?: number
}

export const MemoryRouterWrapper: React.FC<MemoryRouterWrapperProps> = ({
  children,
  initialEntries = ['/'],
  initialIndex,
}) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

// ============================================================================
// Custom Render Functions
// ============================================================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string
  initialEntries?: string[]
  wrapper?: React.ComponentType<any>
}

export const customRender = (
  ui: React.ReactElement,
  options?: CustomRenderOptions
) => {
  const { route = '/', initialEntries, wrapper: Wrapper, ...renderOptions } = options || {}

  if (Wrapper) {
    return render(ui, { wrapper: Wrapper, ...renderOptions })
  }

  if (initialEntries) {
    return render(ui, {
      wrapper: ({ children }) => (
        <MemoryRouterWrapper initialEntries={initialEntries}>
          {children}
        </MemoryRouterWrapper>
      ),
      ...renderOptions,
    })
  }

  window.history.pushState({}, 'Test page', route)

  return render(ui, {
    wrapper: AllTheProviders,
    ...renderOptions,
  })
}

// Re-export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }

// ============================================================================
// User Event Setup
// ============================================================================

export const setupUser = () => userEvent.setup()

// ============================================================================
// Custom Matchers and Assertions
// ============================================================================

export const expectToHaveBeenCalledWithDeep = (
  mock: any,
  expectedArgs: any[]
) => {
  expect(mock).toHaveBeenCalled()
  const calls = mock.mock.calls
  const match = calls.some((call: any[]) =>
    JSON.stringify(call) === JSON.stringify(expectedArgs)
  )
  expect(match).toBe(true)
}

// ============================================================================
// Mock Factories
// ============================================================================

export const createMockMediaFile = (overrides = {}) => ({
  id: '1',
  filename: 'test-file.mp4',
  file_path: '/uploads/test-file.mp4',
  media_type: 'video/mp4',
  file_size: 1048576,
  status: 'completed',
  processing_status: 'completed',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
})

export const createMockUser = (overrides = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  role: 'user',
  ...overrides,
})

export const createMockCatalog = (overrides = {}) => ({
  id: '1',
  name: 'Test Catalog',
  description: 'Test catalog description',
  file_count: 10,
  total_size: 10485760,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
})

// ============================================================================
// Mock API Responses
// ============================================================================

export const mockApiResponse = <T,>(data: T, delay = 0) => {
  return new Promise<{ data: T }>((resolve) => {
    setTimeout(() => resolve({ data }), delay)
  })
}

export const mockApiError = (message = 'API Error', delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error(message)), delay)
  })
}

// ============================================================================
// Wait Utilities
// ============================================================================

export const waitForLoadingToFinish = async () => {
  await waitFor(() => {
    const loadingElements = document.querySelectorAll('[aria-busy="true"]')
    expect(loadingElements.length).toBe(0)
  })
}

export const waitForElementToBeRemoved = async (callback: () => HTMLElement | null) => {
  await waitFor(() => {
    expect(callback()).not.toBeInTheDocument()
  })
}

// ============================================================================
// Form Utilities
// ============================================================================

export const fillForm = async (fields: Record<string, string>) => {
  const user = setupUser()

  for (const [label, value] of Object.entries(fields)) {
    const input = screen.getByLabelText(label)
    await user.clear(input)
    await user.type(input, value)
  }
}

export const submitForm = async (buttonText = 'Submit') => {
  const user = setupUser()
  const submitButton = screen.getByRole('button', { name: buttonText })
  await user.click(submitButton)
}

// ============================================================================
// Table Utilities
// ============================================================================

export const getTableData = (container: HTMLElement) => {
  const rows = container.querySelectorAll('tbody tr')
  return Array.from(rows).map(row => {
    const cells = row.querySelectorAll('td')
    return Array.from(cells).map(cell => cell.textContent?.trim() || '')
  })
}

export const getTableHeaders = (container: HTMLElement) => {
  const headers = container.querySelectorAll('thead th')
  return Array.from(headers).map(header => header.textContent?.trim() || '')
}

// ============================================================================
// Navigation Utilities
// ============================================================================

export const expectNavigation = (href: string) => {
  expect(window.location.pathname).toBe(href)
}

export const renderWithRouter = (
  ui: React.ReactElement,
  { route = '/', path = '*' }: { route?: string; path?: string } = {}
) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path={path} element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

// ============================================================================
// Mock Store Utilities
// ============================================================================

export const createMockAuthStore = (overrides = {}) => ({
  user: createMockUser(),
  isAuthenticated: true,
  login: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn(),
  loading: false,
  error: null,
  ...overrides,
})

// ============================================================================
// Accessibility Utilities
// ============================================================================

export const expectToBeAccessible = async (container: HTMLElement) => {
  // Check for common accessibility issues

  // All images should have alt text
  const images = container.querySelectorAll('img')
  images.forEach(img => {
    expect(img).toHaveAttribute('alt')
  })

  // All form inputs should have labels
  const inputs = container.querySelectorAll('input, select, textarea')
  inputs.forEach(input => {
    const label = container.querySelector(`label[for="${input.id}"]`)
    expect(label).toBeInTheDocument()
  })

  // All buttons should have accessible text
  const buttons = container.querySelectorAll('button')
  buttons.forEach(button => {
    expect(button.textContent || button.getAttribute('aria-label')).toBeTruthy()
  })
}

// ============================================================================
// Debug Utilities
// ============================================================================

export const debugState = (component: any) => {
  console.log('Component state:', component)
  screen.debug()
}

// ============================================================================
// Style Testing Utilities
// ============================================================================

export const expectToHaveClasses = (element: HTMLElement, ...classes: string[]) => {
  classes.forEach(className => {
    expect(element).toHaveClass(className)
  })
}

export const expectNotToHaveClasses = (element: HTMLElement, ...classes: string[]) => {
  classes.forEach(className => {
    expect(element).not.toHaveClass(className)
  })
}

// ============================================================================
// Date Utilities
// ============================================================================

export const mockDate = (dateString: string) => {
  const date = new Date(dateString)
  vi.useFakeTimers()
  vi.setSystemTime(date)
  return () => vi.useRealTimers()
}

// ============================================================================
// Local Storage Utilities
// ============================================================================

export const mockLocalStorage = () => {
  const storage: Record<string, string> = {}

  const localStorageMock = {
    getItem: (key: string) => storage[key] || null,
    setItem: (key: string, value: string) => {
      storage[key] = value
    },
    removeItem: (key: string) => {
      delete storage[key]
    },
    clear: () => {
      Object.keys(storage).forEach(key => delete storage[key])
    },
  }

  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true,
  })

  return localStorageMock
}

// ============================================================================
// Event Utilities
// ============================================================================

export const fireClickOutside = (_element: HTMLElement) => {
  const clickEvent = new MouseEvent('click', {
    bubbles: true,
    cancelable: true,
  })
  document.body.dispatchEvent(clickEvent)
}

export const fireEscapeKey = () => {
  const escapeEvent = new KeyboardEvent('keydown', {
    key: 'Escape',
    code: 'Escape',
    keyCode: 27,
    bubbles: true,
  })
  document.dispatchEvent(escapeEvent)
}

// ============================================================================
// Type Guards
// ============================================================================

export const isHTMLElement = (element: any): element is HTMLElement => {
  return element instanceof HTMLElement
}

export const isInputElement = (element: any): element is HTMLInputElement => {
  return element instanceof HTMLInputElement
}

// Import necessary types from testing library
import { screen } from '@testing-library/react'

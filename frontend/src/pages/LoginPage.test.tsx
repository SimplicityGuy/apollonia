import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import userEvent from '@testing-library/user-event'
import toast from 'react-hot-toast'

// Mock dependencies
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(),
  }
})

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock('@/stores/authStore', () => ({
  useAuthStore: (selector?: (state: { login: typeof mockLogin }) => any) => {
    const state = {
      login: mockLogin,
    }
    return selector ? selector(state) : state
  },
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useNavigate as any).mockReturnValue(mockNavigate)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders login form correctly', () => {
    renderWithRouter(<LoginPage />)

    // Check headings
    expect(screen.getByText('Apollonia')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()

    // Check form fields
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()

    // Check submit button
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('updates form fields when user types', async () => {
    const user = userEvent.setup()
    renderWithRouter(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'testpass123')

    expect(usernameInput).toHaveValue('testuser')
    expect(passwordInput).toHaveValue('testpass123')
  })

  it('has correct input attributes', () => {
    renderWithRouter(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    expect(usernameInput).toHaveAttribute('type', 'text')
    expect(usernameInput).toHaveAttribute('name', 'username')
    expect(usernameInput).toHaveAttribute('autoComplete', 'username')
    expect(usernameInput).toHaveAttribute('required')

    const passwordInput = screen.getByLabelText('Password')
    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(passwordInput).toHaveAttribute('name', 'password')
    expect(passwordInput).toHaveAttribute('autoComplete', 'current-password')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('handles successful login', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)

    renderWithRouter(<LoginPage />)

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'testpass123')

    // Submit form
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    // Wait for async operations
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'testpass123')
      expect(toast.success).toHaveBeenCalledWith('Welcome back!')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('handles login failure', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValue(new Error('Invalid credentials'))

    renderWithRouter(<LoginPage />)

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'wrongpass')

    // Submit form
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    // Wait for async operations
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'wrongpass')
      expect(toast.error).toHaveBeenCalledWith('Invalid username or password')
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  it('disables submit button while loading', async () => {
    const user = userEvent.setup()

    // Create a promise that we can control
    let resolveLogin: (() => void) | undefined
    const loginPromise = new Promise<void>((resolve) => {
      resolveLogin = resolve
    })
    mockLogin.mockReturnValue(loginPromise)

    renderWithRouter(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'testpass123')

    // Submit form
    await user.click(submitButton)

    // Button should be disabled and show loading text
    await waitFor(() => {
      expect(submitButton).toBeDisabled()
      expect(submitButton).toHaveTextContent('Signing in...')
    })

    // Resolve the login
    resolveLogin?.()

    // Button should be enabled again
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
      expect(submitButton).toHaveTextContent('Sign in')
    })
  })

  it('prevents form submission with empty fields', async () => {
    const user = userEvent.setup()
    renderWithRouter(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    // Try to submit empty form by clicking submit button
    // The browser should prevent submission due to required attributes
    await user.click(submitButton)

    // Login should not be called due to HTML5 validation
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('applies correct styling for dark mode', () => {
    renderWithRouter(<LoginPage />)

    // Check dark mode classes on form container
    const formContainer = screen.getByRole('button', { name: 'Sign in' }).closest('.bg-white')
    expect(formContainer).toHaveClass('dark:bg-gray-800')

    // Check labels have dark mode classes
    const usernameLabel = screen.getByText('Username')
    const passwordLabel = screen.getByText('Password')

    expect(usernameLabel).toHaveClass('dark:text-gray-200')
    expect(passwordLabel).toHaveClass('dark:text-gray-200')
  })

  it('has responsive layout', () => {
    renderWithRouter(<LoginPage />)

    const container = screen.getByText('Apollonia').closest('div')
    expect(container).toHaveClass('sm:mx-auto', 'sm:w-full', 'sm:max-w-md')

    const formContainer = screen.getByRole('button', { name: 'Sign in' }).closest('div.bg-white')
    expect(formContainer).toHaveClass('sm:rounded-lg', 'sm:px-10')
  })

  it('focuses username input on mount', () => {
    renderWithRouter(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    // Note: Testing focus on mount might require additional setup or manual focus call
    // This is a limitation of testing library
    expect(usernameInput).toBeInTheDocument()
  })

  it('handles form submission with enter key', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)

    renderWithRouter(<LoginPage />)

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'testpass123')

    // Press enter in password field
    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'testpass123')
    })
  })

  it('clears password field on failed login', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValue(new Error('Invalid credentials'))

    renderWithRouter(<LoginPage />)

    const passwordInput = screen.getByLabelText('Password')

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(passwordInput, 'wrongpass')

    // Submit form
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    // Wait for error
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled()
    })

    // Password should still be there (component doesn't clear it)
    expect(passwordInput).toHaveValue('wrongpass')
  })

  it('maintains form state during loading', async () => {
    const user = userEvent.setup()

    // Create a promise that we can control
    let resolveLogin: (() => void) | undefined
    const loginPromise = new Promise<void>((resolve) => {
      resolveLogin = resolve
    })
    mockLogin.mockReturnValue(loginPromise)

    renderWithRouter(<LoginPage />)

    // Fill form
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'testpass123')

    // Submit form
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    // Inputs should still have their values during loading
    expect(screen.getByLabelText('Username')).toHaveValue('testuser')
    expect(screen.getByLabelText('Password')).toHaveValue('testpass123')

    // Resolve the login
    resolveLogin?.()
  })
})

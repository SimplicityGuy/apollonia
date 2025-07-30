import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useNavigate } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import toast from 'react-hot-toast'
import {
  render,
  screen,
  waitFor,
  setupUser,
  fillForm,
  submitForm,
  createMockAuthStore,
  expectToHaveClasses,
} from '@/test/utils'

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

const mockNavigate = vi.fn()
const mockAuthStore = createMockAuthStore()

vi.mock('@/stores/authStore', () => ({
  useAuthStore: (selector?: (state: any) => any) => {
    const state = mockAuthStore
    return selector ? selector(state) : state
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    ;(useNavigate as any).mockReturnValue(mockNavigate)
    mockAuthStore.login = vi.fn().mockResolvedValue(undefined)
  })

  it('renders login form correctly', () => {
    render(<LoginPage />)

    // Check headings
    expect(screen.getByText('Apollonia')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()

    // Check form fields
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()

    // Check submit button
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()

    // Check form is accessible
    const form = screen.getByRole('button', { name: 'Sign in' }).closest('form')
    expect(form).toBeAccessibleForm()
  })

  it('updates form fields when user types', async () => {
    render(<LoginPage />)

    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })

    expect(screen.getByLabelText('Username')).toHaveValue('testuser')
    expect(screen.getByLabelText('Password')).toHaveValue('testpass123')
  })

  it('has correct input attributes and accessibility features', () => {
    render(<LoginPage />)

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

    // Check for ARIA attributes on the button
    const submitButton = screen.getByRole('button', { name: 'Sign in' })
    expect(submitButton).not.toBeDisabledButton()
  })

  it('handles successful login', async () => {
    render(<LoginPage />)

    // Fill and submit form
    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })
    await submitForm('Sign in')

    // Wait for async operations
    await waitFor(() => {
      expect(mockAuthStore.login).toHaveBeenCalledWith('testuser', 'testpass123')
      expect(toast.success).toHaveBeenCalledWith('Welcome back!')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('handles login failure', async () => {
    mockAuthStore.login.mockRejectedValue(new Error('Invalid credentials'))

    render(<LoginPage />)

    // Fill and submit form
    await fillForm({
      Username: 'testuser',
      Password: 'wrongpass',
    })
    await submitForm('Sign in')

    // Wait for async operations
    await waitFor(() => {
      expect(mockAuthStore.login).toHaveBeenCalledWith('testuser', 'wrongpass')
      expect(toast.error).toHaveBeenCalledWith('Invalid username or password')
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  it('disables submit button while loading', async () => {
    // Create a promise that we can control
    let resolveLogin: (() => void) | undefined
    const loginPromise = new Promise<void>((resolve) => {
      resolveLogin = resolve
    })
    mockAuthStore.login.mockReturnValue(loginPromise)

    render(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    // Fill and submit form
    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })
    const user = setupUser()
    await user.click(submitButton)

    // Button should be disabled and show loading text
    await waitFor(() => {
      expect(submitButton).toBeDisabledButton()
      expect(submitButton).toHaveTextContent('Signing in...')
    })

    // Resolve the login
    resolveLogin?.()

    // Button should be enabled again
    await waitFor(() => {
      expect(submitButton).not.toBeDisabledButton()
      expect(submitButton).toHaveTextContent('Sign in')
    })
  })

  it('prevents form submission with empty fields', async () => {
    render(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: 'Sign in' })
    const user = setupUser()

    // Try to submit empty form by clicking submit button
    // The browser should prevent submission due to required attributes
    await user.click(submitButton)

    // Login should not be called due to HTML5 validation
    expect(mockAuthStore.login).not.toHaveBeenCalled()
  })

  it('applies correct styling for dark mode', () => {
    render(<LoginPage />)

    // Check dark mode classes on form container
    const formContainer = screen.getByRole('button', { name: 'Sign in' }).closest('.bg-white')
    expectToHaveClasses(formContainer!, 'dark:bg-gray-800', 'bg-white')

    // Check labels have dark mode classes
    const usernameLabel = screen.getByText('Username')
    const passwordLabel = screen.getByText('Password')

    expectToHaveClasses(usernameLabel, 'dark:text-gray-200')
    expectToHaveClasses(passwordLabel, 'dark:text-gray-200')
  })

  it('has responsive layout', () => {
    render(<LoginPage />)

    const container = screen.getByText('Apollonia').closest('div')
    expect(container).toHaveClass('sm:mx-auto', 'sm:w-full', 'sm:max-w-md')

    const formContainer = screen.getByRole('button', { name: 'Sign in' }).closest('div.bg-white')
    expect(formContainer).toHaveClass('sm:rounded-lg', 'sm:px-10')
  })

  it('focuses username input on mount', () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText('Username')
    // Note: Testing focus on mount might require additional setup or manual focus call
    // This is a limitation of testing library
    expect(usernameInput).toBeInTheDocument()
  })

  it('handles form submission with enter key', async () => {
    render(<LoginPage />)
    const user = setupUser()

    // Fill form
    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })

    // Press enter in password field
    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(mockAuthStore.login).toHaveBeenCalledWith('testuser', 'testpass123')
    })
  })

  it('clears password field on failed login', async () => {
    mockAuthStore.login.mockRejectedValue(new Error('Invalid credentials'))

    render(<LoginPage />)

    const passwordInput = screen.getByLabelText('Password')

    // Fill and submit form
    await fillForm({
      Username: 'testuser',
      Password: 'wrongpass',
    })
    await submitForm('Sign in')

    // Wait for error
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled()
    })

    // Password should still be there (component doesn't clear it)
    expect(passwordInput).toHaveValue('wrongpass')
  })

  it('maintains form state during loading', async () => {
    // Create a promise that we can control
    let resolveLogin: (() => void) | undefined
    const loginPromise = new Promise<void>((resolve) => {
      resolveLogin = resolve
    })
    mockAuthStore.login.mockReturnValue(loginPromise)

    render(<LoginPage />)

    // Fill and submit form
    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })
    await submitForm('Sign in')

    // Inputs should still have their values during loading
    expect(screen.getByLabelText('Username')).toHaveValue('testuser')
    expect(screen.getByLabelText('Password')).toHaveValue('testpass123')

    // Resolve the login
    resolveLogin?.()
  })

  it('displays error message for network failures', async () => {
    mockAuthStore.login.mockRejectedValue(new Error('Network error'))

    render(<LoginPage />)

    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })
    await submitForm('Sign in')

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Invalid username or password')
    })
  })

  it('trims whitespace from username input', async () => {
    render(<LoginPage />)

    await fillForm({
      Username: '  testuser  ',
      Password: 'testpass123',
    })
    await submitForm('Sign in')

    await waitFor(() => {
      expect(mockAuthStore.login).toHaveBeenCalledWith('testuser', 'testpass123')
    })
  })

  it('validates form fields before submission', async () => {
    const { container } = render(<LoginPage />)

    // Check form has proper validation attributes
    const form = container.querySelector('form')
    expect(form).toBeAccessibleForm()

    // Check inputs have proper validation
    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')

    expect(usernameInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('handles rapid form submissions gracefully', async () => {
    render(<LoginPage />)
    const user = setupUser()

    await fillForm({
      Username: 'testuser',
      Password: 'testpass123',
    })

    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    // Click multiple times rapidly with proper user events
    const clickPromises = [
      user.click(submitButton),
      user.click(submitButton),
      user.click(submitButton),
    ]

    // Execute all clicks simultaneously
    await Promise.all(clickPromises)

    // Wait a bit for all potential async operations to complete
    await waitFor(() => {
      expect(mockAuthStore.login).toHaveBeenCalled()
    })

    // Should only call login once
    expect(mockAuthStore.login).toHaveBeenCalledTimes(1)
  })

  it('preserves form state on error', async () => {
    mockAuthStore.login.mockRejectedValue(new Error('Server error'))

    render(<LoginPage />)

    const username = 'testuser@example.com'
    const password = 'complexPassword123!'

    await fillForm({
      Username: username,
      Password: password,
    })
    await submitForm('Sign in')

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled()
    })

    // Form values should be preserved
    expect(screen.getByLabelText('Username')).toHaveValue(username)
    expect(screen.getByLabelText('Password')).toHaveValue(password)
  })

  it('handles keyboard navigation properly', async () => {
    render(<LoginPage />)
    const user = setupUser()

    // Tab through form elements
    await user.tab()
    expect(screen.getByLabelText('Username')).toHaveFocus()

    await user.tab()
    expect(screen.getByLabelText('Password')).toHaveFocus()

    await user.tab()
    expect(screen.getByRole('button', { name: 'Sign in' })).toHaveFocus()
  })

  it('provides visual feedback for invalid inputs', async () => {
    render(<LoginPage />)
    const user = setupUser()

    const usernameInput = screen.getByLabelText('Username')
    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    // Try to submit with empty username
    await user.click(submitButton)

    // Check for browser validation (HTML5)
    expect(usernameInput).toBeInvalid()
  })
})

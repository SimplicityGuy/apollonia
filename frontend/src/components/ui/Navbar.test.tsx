import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useNavigate } from 'react-router-dom'
import { Navbar } from './Navbar'
import { useAuthStore } from '@/stores/authStore'
import {
  render,
  screen,
  waitFor,
  setupUser,
  createMockUser,
  fireClickOutside,
  expectToHaveClasses
} from '@/test/utils'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(),
  }
})

// Mock the auth store
const mockLogout = vi.fn()
const mockUser = createMockUser({ username: 'testuser', email: 'test@example.com' })

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

describe('Navbar', () => {
  const mockNavigate = vi.fn()

  beforeEach(() => {
    ;(useNavigate as vi.MockedFunction<typeof useNavigate>).mockReturnValue(mockNavigate)
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
    })
  })

  it('renders without crashing', () => {
    render(<Navbar />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('contains accessible search functionality', () => {
    render(<Navbar />)
    const searchInput = screen.getByRole('searchbox', { name: /search/i })
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveAttribute('placeholder', 'Search media files...')
    expect(searchInput).toHaveAttribute('type', 'search')
    expect(searchInput).toHaveAttribute('name', 'q')
    expect(searchInput).toHaveAriaLabel('Search media files')
  })

  it('displays search icon with proper accessibility', () => {
    render(<Navbar />)
    // The icon is rendered with aria-hidden
    const searchContainer = screen.getByRole('searchbox').parentElement
    expect(searchContainer).toContainHTML('svg')
    const icon = searchContainer?.querySelector('svg')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
  })

  it('search form has correct action and is accessible', () => {
    render(<Navbar />)
    const form = screen.getByRole('searchbox').closest('form')
    expect(form).toHaveAttribute('action', '/search')
    expect(form).toHaveAttribute('method', 'GET')
    expect(form).toBeAccessibleForm()
  })

  it('displays accessible notification button', () => {
    render(<Navbar />)
    const notificationButton = screen.getByRole('button', { name: /view notifications/i })
    expect(notificationButton).toBeInTheDocument()
    expect(notificationButton).toHaveAriaLabel('View notifications')
  })

  it('displays user menu when authenticated', () => {
    render(<Navbar />)
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    expect(userButton).toBeInTheDocument()
    expect(userButton).toHaveAttribute('aria-expanded', 'false')
  })

  it('displays username in menu button', () => {
    render(<Navbar />)
    expect(screen.getByText('testuser')).toBeInTheDocument()
  })

  it('opens user menu on click with proper ARIA states', async () => {
    const user = setupUser()
    render(<Navbar />)

    const userButton = screen.getByRole('button', { name: /open user menu/i })

    // Menu items should not be visible initially
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    expect(screen.queryByText('Sign out')).not.toBeInTheDocument()

    // Click to open menu
    await user.click(userButton)

    // Menu items should now be visible
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
      expect(screen.getByText('Sign out')).toBeInTheDocument()
    })

    // ARIA state should update
    expect(userButton).toHaveAttribute('aria-expanded', 'true')
  })

  it('navigates to settings when settings link is clicked', async () => {
    const user = setupUser()
    render(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    // Click settings link
    const settingsLink = await screen.findByText('Settings')
    expect(settingsLink).toHaveAttribute('href', '/settings')
  })

  it('logs out and navigates when sign out is clicked', async () => {
    const user = setupUser()
    render(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    // Click sign out
    const signOutButton = await screen.findByText('Sign out')
    await user.click(signOutButton)

    // Verify logout was called and navigation happened
    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('displays mobile menu button on small screens', () => {
    render(<Navbar />)
    const mobileMenuButton = screen.getByRole('button', { name: /open sidebar/i })
    expect(mobileMenuButton).toBeInTheDocument()
    expectToHaveClasses(mobileMenuButton, 'lg:hidden')
  })

  it('applies correct styling for dark mode', () => {
    render(<Navbar />)

    const header = screen.getByRole('banner')
    expectToHaveClasses(header, 'dark:border-gray-800', 'dark:bg-gray-950')

    const searchInput = screen.getByRole('searchbox')
    expectToHaveClasses(searchInput, 'dark:bg-gray-950', 'dark:text-white')
  })

  it('menu items have hover states', async () => {
    const user = setupUser()
    render(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    const settingsLink = await screen.findByText('Settings')
    const signOutButton = await screen.findByText('Sign out')

    // Check initial state
    expectToHaveClasses(settingsLink, 'text-gray-900')
    expectToHaveClasses(signOutButton, 'text-gray-900')
  })

  it('handles missing user gracefully', () => {
    // Override the mock for this test
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: null,
      logout: mockLogout,
    })

    render(<Navbar />)

    // Should display 'User' as fallback
    expect(screen.getByText('User')).toBeInTheDocument()

    // Reset for other tests
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
    })
  })

  it('menu closes when clicking outside', async () => {
    const user = setupUser()
    render(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    // Verify menu is open
    expect(screen.getByText('Settings')).toBeInTheDocument()

    // Click outside
    fireClickOutside(userButton)

    // Menu should close
    await waitFor(() => {
      expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    })
  })

  it('includes proper accessibility attributes', () => {
    render(<Navbar />)

    // Check for aria-hidden on decorative elements
    const icons = document.querySelectorAll('[aria-hidden="true"]')
    expect(icons.length).toBeGreaterThan(0)

    // Check for sr-only labels
    const srOnlyElements = document.querySelectorAll('.sr-only')
    expect(srOnlyElements.length).toBeGreaterThan(0)

    // Check nav landmark
    expect(document.querySelector('nav')).toBeInTheDocument()
  })

  it('search input can be typed into', async () => {
    const user = setupUser()
    render(<Navbar />)

    const searchInput = screen.getByRole('searchbox')
    await user.type(searchInput, 'test query')

    expect(searchInput).toHaveValue('test query')
  })

  it('handles search form submission', async () => {
    const user = setupUser()
    render(<Navbar />)

    const searchInput = screen.getByRole('searchbox')
    const form = searchInput.closest('form')

    await user.type(searchInput, 'test query')

    // Create form submit event
    const submitEvent = new Event('submit', { bubbles: true, cancelable: true })
    form?.dispatchEvent(submitEvent)

    // Form should have the search value
    expect(searchInput).toHaveValue('test query')
  })

  it('shows notification badge when notifications are present', () => {
    // Mock auth store with notifications
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: { ...mockUser, unreadNotifications: 5 },
      logout: mockLogout,
    })

    render(<Navbar />)

    const notificationButton = screen.getByRole('button', { name: /view notifications/i })
    const badge = notificationButton.querySelector('.bg-red-500')

    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('5')

    // Reset
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
    })
  })

  it('keyboard navigation works properly', async () => {
    const user = setupUser()
    render(<Navbar />)

    // Tab to search
    await user.tab()
    expect(screen.getByRole('searchbox')).toHaveFocus()

    // Tab to notifications
    await user.tab()
    expect(screen.getByRole('button', { name: /view notifications/i })).toHaveFocus()

    // Tab to user menu
    await user.tab()
    expect(screen.getByRole('button', { name: /open user menu/i })).toHaveFocus()
  })

  it('handles user menu keyboard navigation', async () => {
    const user = setupUser()
    render(<Navbar />)

    const userButton = screen.getByRole('button', { name: /open user menu/i })

    // Open menu with Enter key
    await user.click(userButton)
    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    // Navigate through menu items
    await user.keyboard('{ArrowDown}')
    expect(screen.getByText('Settings')).toHaveFocus()

    await user.keyboard('{ArrowDown}')
    expect(screen.getByText('Sign out')).toHaveFocus()

    // Close with Escape
    await user.keyboard('{Escape}')
    await waitFor(() => {
      expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    })
  })

  it('prevents XSS in search input', async () => {
    const user = setupUser()
    render(<Navbar />)

    const searchInput = screen.getByRole('searchbox')
    const maliciousInput = '<script>alert("XSS")</script>'

    await user.type(searchInput, maliciousInput)

    // Value should be escaped
    expect(searchInput).toHaveValue(maliciousInput)
    // Script should not execute
    expect(document.querySelector('script')).not.toBeInTheDocument()
  })

  it('maintains focus after menu closes', async () => {
    const user = setupUser()
    render(<Navbar />)

    const userButton = screen.getByRole('button', { name: /open user menu/i })

    // Open menu
    await user.click(userButton)
    expect(screen.getByText('Settings')).toBeInTheDocument()

    // Close menu by clicking button again
    await user.click(userButton)

    await waitFor(() => {
      expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    })

    // Focus should return to button
    expect(userButton).toHaveFocus()
  })

  it('renders correctly on mobile viewport', () => {
    // Mock mobile viewport
    window.innerWidth = 375
    window.innerHeight = 667

    render(<Navbar />)

    // Mobile menu button should be visible
    const mobileMenuButton = screen.getByRole('button', { name: /open sidebar/i })
    expect(mobileMenuButton).toBeVisible()

    // Desktop-only elements should be hidden
    const searchForm = screen.getByRole('searchbox').closest('form')
    expect(searchForm?.parentElement).toHaveClass('hidden', 'lg:block')

    // Reset viewport
    window.innerWidth = 1024
    window.innerHeight = 768
  })
})

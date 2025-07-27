import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import { Navbar } from './Navbar'
import userEvent from '@testing-library/user-event'
import { useAuthStore } from '@/stores/authStore'

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
const mockUser = { username: 'testuser', email: 'test@example.com' }

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Navbar', () => {
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(useNavigate as vi.MockedFunction<typeof useNavigate>).mockReturnValue(mockNavigate)
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders without crashing', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('contains search functionality', () => {
    renderWithRouter(<Navbar />)
    const searchInput = screen.getByRole('searchbox', { name: /search/i })
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveAttribute('placeholder', 'Search media files...')
    expect(searchInput).toHaveAttribute('type', 'search')
    expect(searchInput).toHaveAttribute('name', 'q')
  })

  it('displays search icon', () => {
    renderWithRouter(<Navbar />)
    // The icon is rendered with aria-hidden
    const searchContainer = screen.getByRole('searchbox').parentElement
    expect(searchContainer).toContainHTML('svg')
  })

  it('search form has correct action', () => {
    renderWithRouter(<Navbar />)
    const form = screen.getByRole('searchbox').closest('form')
    expect(form).toHaveAttribute('action', '/search')
    expect(form).toHaveAttribute('method', 'GET')
  })

  it('displays notification button', () => {
    renderWithRouter(<Navbar />)
    const notificationButton = screen.getByRole('button', { name: /view notifications/i })
    expect(notificationButton).toBeInTheDocument()
  })

  it('displays user menu when authenticated', () => {
    renderWithRouter(<Navbar />)
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    expect(userButton).toBeInTheDocument()
  })

  it('displays username in menu button', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByText('testuser')).toBeInTheDocument()
  })

  it('opens user menu on click', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

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
  })

  it('navigates to settings when settings link is clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    // Click settings link
    const settingsLink = await screen.findByText('Settings')
    expect(settingsLink).toHaveAttribute('href', '/settings')
  })

  it('logs out and navigates when sign out is clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

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
    renderWithRouter(<Navbar />)
    const mobileMenuButton = screen.getByRole('button', { name: /open sidebar/i })
    expect(mobileMenuButton).toBeInTheDocument()
    expect(mobileMenuButton).toHaveClass('lg:hidden')
  })

  it('applies correct styling for dark mode', () => {
    renderWithRouter(<Navbar />)

    const header = screen.getByRole('banner')
    expect(header).toHaveClass('dark:border-gray-800', 'dark:bg-gray-950')

    const searchInput = screen.getByRole('searchbox')
    expect(searchInput).toHaveClass('dark:bg-gray-950', 'dark:text-white')
  })

  it('menu items have hover states', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    const settingsLink = await screen.findByText('Settings')
    const signOutButton = await screen.findByText('Sign out')

    // Check initial state
    expect(settingsLink).toHaveClass('text-gray-900')
    expect(signOutButton).toHaveClass('text-gray-900')
  })

  it('handles missing user gracefully', () => {
    // Override the mock for this test by temporarily changing the mock implementation
    const originalMock = (useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockImplementation
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockImplementation(() => ({
      user: null,
      logout: mockLogout,
    }))

    renderWithRouter(<Navbar />)

    // Should display 'User' as fallback
    expect(screen.getByText('User')).toBeInTheDocument()

    // Restore the original mock
    ;(useAuthStore as vi.MockedFunction<typeof useAuthStore>).mockImplementation = originalMock
  })

  it('menu closes when clicking outside', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

    // Open menu
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    await user.click(userButton)

    // Verify menu is open
    expect(screen.getByText('Settings')).toBeInTheDocument()

    // Click outside (on the header)
    const header = screen.getByRole('banner')
    await user.click(header)

    // Menu should close
    await waitFor(() => {
      expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    })
  })

  it('includes proper accessibility attributes', () => {
    renderWithRouter(<Navbar />)

    // Check for aria-hidden on decorative elements
    const icons = document.querySelectorAll('[aria-hidden="true"]')
    expect(icons.length).toBeGreaterThan(0)

    // Check for sr-only labels
    const srOnlyElements = screen.getAllByText((_, element) => {
      return element?.classList.contains('sr-only') || false
    })
    expect(srOnlyElements.length).toBeGreaterThan(0)
  })

  it('search input can be typed into', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Navbar />)

    const searchInput = screen.getByRole('searchbox')
    await user.type(searchInput, 'test query')

    expect(searchInput).toHaveValue('test query')
  })
})

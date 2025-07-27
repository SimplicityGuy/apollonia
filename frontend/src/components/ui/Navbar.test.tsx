import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { Navbar } from './Navbar'

// Mock the auth store
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    user: { name: 'Test User', email: 'test@example.com' },
    logout: vi.fn(),
  }),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('contains search functionality', () => {
    renderWithRouter(<Navbar />)
    const searchInput = screen.getByRole('searchbox', { name: /search/i })
    expect(searchInput).toBeInTheDocument()
  })

  it('displays user menu when authenticated', () => {
    renderWithRouter(<Navbar />)
    const userButton = screen.getByRole('button', { name: /open user menu/i })
    expect(userButton).toBeInTheDocument()
  })
})

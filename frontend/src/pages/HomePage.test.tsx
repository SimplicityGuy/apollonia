import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from './HomePage'

// Mock the API service
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const renderWithQueryClient = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(<QueryClientProvider client={testQueryClient}>{component}</QueryClientProvider>)
}

describe('HomePage', () => {
  it('renders without crashing', () => {
    renderWithQueryClient(<HomePage />)
    expect(screen.getByText('Total Media Files')).toBeInTheDocument()
  })

  it('displays statistics', () => {
    renderWithQueryClient(<HomePage />)
    expect(screen.getByText('Analyzed Files')).toBeInTheDocument()
    expect(screen.getByText('Processing Queue')).toBeInTheDocument()
    expect(screen.getByText('Storage Used')).toBeInTheDocument()
  })

  it('shows dashboard heading', () => {
    renderWithQueryClient(<HomePage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})

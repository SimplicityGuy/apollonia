import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HomePage } from './HomePage'
import type { MediaFilesResponse } from '@/types/media'
import { api } from '@/services/api'

// Mock the API service
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

const mockMediaFiles: MediaFilesResponse = {
  items: [
    {
      id: '1',
      filename: 'video.mp4',
      media_type: 'video/mp4',
      file_size: 1048576,
      processing_status: 'completed',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      filename: 'image.jpg',
      media_type: 'image/jpeg',
      file_size: 524288,
      processing_status: 'processing',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
    {
      id: '3',
      filename: 'document.pdf',
      media_type: 'application/pdf',
      file_size: 2097152,
      processing_status: 'pending',
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    },
  ],
  total: 3,
  page: 1,
  page_size: 10,
}

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

const renderWithQueryClient = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(<QueryClientProvider client={testQueryClient}>{component}</QueryClientProvider>)
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.get).mockResolvedValue({ data: mockMediaFiles })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders without crashing', () => {
    renderWithQueryClient(<HomePage />)
    expect(screen.getByText('Total Media Files')).toBeInTheDocument()
  })

  it('displays all statistics cards', () => {
    renderWithQueryClient(<HomePage />)
    const statNames = ['Total Media Files', 'Analyzed Files', 'Processing Queue', 'Storage Used']

    statNames.forEach(name => {
      expect(screen.getByText(name)).toBeInTheDocument()
    })

    // Check stat values
    expect(screen.getByText('71,897')).toBeInTheDocument()
    expect(screen.getByText('58,234')).toBeInTheDocument()
    expect(screen.getByText('24')).toBeInTheDocument()
    expect(screen.getByText('2.4 TB')).toBeInTheDocument()
  })

  it('displays stat changes with correct styling', () => {
    renderWithQueryClient(<HomePage />)

    // Check increase indicators
    const increaseIndicators = screen.getAllByText(/1.34%|2.94%|4.35%/)
    increaseIndicators.forEach(indicator => {
      expect(indicator).toHaveClass('text-green-600')
    })

    // Check decrease indicator
    const decreaseIndicator = screen.getByText('14.29%')
    expect(decreaseIndicator).toHaveClass('text-red-600')
  })

  it('shows dashboard heading', () => {
    renderWithQueryClient(<HomePage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Dashboard')
  })

  it('displays recent files section', async () => {
    renderWithQueryClient(<HomePage />)

    expect(screen.getByText('Recent Files')).toBeInTheDocument()

    // Wait for the API call to complete
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/media/files', {
        params: { limit: 10, sort: '-created_at' },
      })
    })
  })

  it('renders recent files table with data', async () => {
    renderWithQueryClient(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('video.mp4')).toBeInTheDocument()
      expect(screen.getByText('image.jpg')).toBeInTheDocument()
      expect(screen.getByText('document.pdf')).toBeInTheDocument()
    })

    // Check media types
    expect(screen.getByText('video/mp4')).toBeInTheDocument()
    expect(screen.getByText('image/jpeg')).toBeInTheDocument()
    expect(screen.getByText('application/pdf')).toBeInTheDocument()

    // Check file sizes are formatted
    expect(screen.getByText('1 MB')).toBeInTheDocument() // 1048576 bytes
    expect(screen.getByText('512 KB')).toBeInTheDocument() // 524288 bytes
    expect(screen.getByText('2 MB')).toBeInTheDocument() // 2097152 bytes
  })

  it('displays processing status with correct styling', async () => {
    renderWithQueryClient(<HomePage />)

    await waitFor(() => {
      const completedStatus = screen.getByText('completed')
      expect(completedStatus).toHaveClass('bg-green-100', 'text-green-800')

      const processingStatus = screen.getByText('processing')
      expect(processingStatus).toHaveClass('bg-yellow-100', 'text-yellow-800')

      const pendingStatus = screen.getByText('pending')
      expect(pendingStatus).toHaveClass('bg-gray-100', 'text-gray-800')
    })
  })

  it('renders table headers correctly', async () => {
    renderWithQueryClient(<HomePage />)

    const headers = ['Name', 'Type', 'Size', 'Status']
    headers.forEach(header => {
      expect(screen.getByText(header)).toBeInTheDocument()
    })
  })

  it('renders view links for each file', async () => {
    renderWithQueryClient(<HomePage />)

    await waitFor(() => {
      const viewLinks = screen.getAllByText('View')
      expect(viewLinks).toHaveLength(3)

      viewLinks.forEach((link, index) => {
        expect(link).toHaveAttribute('href', `/files/${mockMediaFiles.items[index].id}`)
      })
    })
  })

  it('handles empty recent files gracefully', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { items: [], total: 0, page: 1, page_size: 10 } })

    renderWithQueryClient(<HomePage />)

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled()
    })

    // Table should still render but with no data rows
    expect(screen.getByText('Recent Files')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('API Error'))

    renderWithQueryClient(<HomePage />)

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled()
    })

    // Stats should still be displayed
    expect(screen.getByText('Total Media Files')).toBeInTheDocument()
  })

  it('includes accessibility attributes', () => {
    renderWithQueryClient(<HomePage />)

    // Check for screen reader only text
    const srOnlyElements = screen.getAllByText(/Increased by|Decreased by/)
    expect(srOnlyElements.length).toBeGreaterThan(0)

    srOnlyElements.forEach(element => {
      expect(element).toHaveClass('sr-only')
    })
  })

  it('renders view all links for stats', () => {
    renderWithQueryClient(<HomePage />)

    const viewAllLinks = screen.getAllByText('View all')
    expect(viewAllLinks).toHaveLength(4) // One for each stat card
  })

  it('uses correct icon for stat changes', () => {
    renderWithQueryClient(<HomePage />)

    // Check for arrow icons (they have specific classes)
    const upArrows = document.querySelectorAll('.text-green-500')
    const downArrows = document.querySelectorAll('.text-red-500')

    expect(upArrows.length).toBe(3) // 3 increases
    expect(downArrows.length).toBe(1) // 1 decrease
  })
})

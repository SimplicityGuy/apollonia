import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HomePage } from './HomePage'
import { api } from '@/services/api'
import {
  render,
  screen,
  waitFor,
  createMockMediaFilesResponse,
  getTableData,
  getTableHeaders,
  expectToHaveClasses,
  setupUser,
  waitForLoadingToFinish
} from '@/test/utils'

// Mock the API service
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

const mockMediaFiles = createMockMediaFilesResponse(3)

describe('HomePage', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockResolvedValue({ data: mockMediaFiles })
  })

  it('renders without crashing', () => {
    render(<HomePage />)
    expect(screen.getByText('Total Media Files')).toBeInTheDocument()
  })

  it('displays all statistics cards with correct values', () => {
    render(<HomePage />)
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

  it('displays stat changes with correct styling and semantic meaning', () => {
    render(<HomePage />)

    // Check increase indicators
    const increaseIndicators = screen.getAllByText(/1.34%|2.94%|4.35%/)
    increaseIndicators.forEach(indicator => {
      expect(indicator).toHaveClass('text-green-600')
    })

    // Check decrease indicator
    const decreaseIndicator = screen.getByText('14.29%')
    expect(decreaseIndicator).toHaveClass('text-red-600')

    // Check for screen reader text
    expect(screen.getAllByText(/Increased by/)).toHaveLength(3)
    expect(screen.getByText(/Decreased by/)).toBeInTheDocument()
  })

  it('shows dashboard heading with proper hierarchy', () => {
    render(<HomePage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContentTrimmed('Dashboard')
  })

  it('displays recent files section and fetches data', async () => {
    render(<HomePage />)

    expect(screen.getByText('Recent Files')).toBeInTheDocument()

    // Wait for the API call to complete
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/media/files', {
        params: { limit: 10, sort: '-created_at' },
      })
    })
  })

  it('renders recent files table with properly formatted data', async () => {
    const { container } = render(<HomePage />)

    await waitFor(() => {
      // Check filenames are displayed
      mockMediaFiles.items.forEach(file => {
        expect(screen.getByText(file.filename)).toBeInTheDocument()
      })
    })

    // Check table structure
    const headers = getTableHeaders(container)
    expect(headers).toEqual(['Name', 'Type', 'Size', 'Status', 'View'])

    // Check file data is properly formatted
    const tableData = getTableData(container)
    expect(tableData).toHaveLength(mockMediaFiles.items.length)
  })

  it('displays processing status badges with semantic colors', async () => {
    // Create specific test data with different statuses
    const testFiles = createMockMediaFilesResponse(3)
    testFiles.items[0].processing_status = 'completed'
    testFiles.items[1].processing_status = 'processing'
    testFiles.items[2].processing_status = 'pending'

    vi.mocked(api.get).mockResolvedValue({ data: testFiles })

    render(<HomePage />)

    await waitFor(() => {
      const completedStatus = screen.getByText('completed')
      expectToHaveClasses(completedStatus, 'bg-green-100', 'text-green-800')

      const processingStatus = screen.getByText('processing')
      expectToHaveClasses(processingStatus, 'bg-yellow-100', 'text-yellow-800')

      const pendingStatus = screen.getByText('pending')
      expectToHaveClasses(pendingStatus, 'bg-gray-100', 'text-gray-800')
    })
  })

  it('renders accessible table structure', async () => {
    const { container } = render(<HomePage />)

    // Check table has proper structure
    const table = container.querySelector('table')
    expect(table).toBeInTheDocument()

    // Check headers
    const headers = getTableHeaders(container)
    expect(headers).toEqual(['Name', 'Type', 'Size', 'Status', 'View'])

    // Check table is accessible
    const tableHeaders = container.querySelectorAll('th')
    tableHeaders.forEach(header => {
      expect(header).toHaveAttribute('scope', 'col')
    })
  })

  it('renders accessible view links for each file', async () => {
    render(<HomePage />)

    await waitFor(() => {
      // Get links that have href attributes pointing to files
      const viewLinks = screen.getAllByRole('link').filter(link =>
        link.getAttribute('href')?.startsWith('/files/')
      )
      expect(viewLinks).toHaveLength(mockMediaFiles.items.length)

      viewLinks.forEach((link, index) => {
        expect(link).toHaveAttribute('href', `/files/${mockMediaFiles.items[index].id}`)
        expect(link).toHaveTextContent('View')
        // Check accessibility
        expect(link).toHaveAttribute('aria-label', expect.stringContaining(mockMediaFiles.items[index].filename))
      })
    })
  })

  it('handles empty recent files with appropriate messaging', async () => {
    const emptyResponse = createMockMediaFilesResponse(0)
    vi.mocked(api.get).mockResolvedValue({ data: emptyResponse })

    render(<HomePage />)

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled()
    })

    // Should show empty state
    expect(screen.getByText('Recent Files')).toBeInTheDocument()
    expect(screen.getByText('No files found')).toBeInTheDocument()
  })

  it('handles API errors with error boundary', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(api.get).mockRejectedValue(new Error('Network Error'))

    render(<HomePage />)

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled()
    })

    // Stats should still be displayed
    expect(screen.getByText('Total Media Files')).toBeInTheDocument()

    // Error message should be shown
    expect(screen.getByText(/Failed to load recent files/)).toBeInTheDocument()

    consoleError.mockRestore()
  })

  it('provides comprehensive accessibility features', async () => {
    const { container } = render(<HomePage />)

    // Check for screen reader only text
    const srOnlyElements = screen.getAllByText(/Increased by|Decreased by/)
    expect(srOnlyElements.length).toBeGreaterThan(0)
    srOnlyElements.forEach(element => {
      expect(element).toHaveClass('sr-only')
    })

    // Check ARIA labels on interactive elements
    const viewAllLinks = screen.getAllByText('View all')
    viewAllLinks.forEach(link => {
      expect(link.closest('a')).toHaveAttribute('aria-label')
    })

    // Check page has proper landmarks
    expect(container.querySelector('main')).toBeInTheDocument()
  })

  it('renders interactive stat cards with navigation', () => {
    render(<HomePage />)

    const viewAllLinks = screen.getAllByText('View all')
    expect(viewAllLinks).toHaveLength(4) // One for each stat card

    // Check each link has proper href
    const expectedPaths = ['/files', '/analytics', '/processing', '/storage']
    viewAllLinks.forEach((link, index) => {
      const anchor = link.closest('a')
      expect(anchor).toHaveAttribute('href', expectedPaths[index])
    })
  })

  it('displays trend indicators with semantic meaning', () => {
    const { container } = render(<HomePage />)

    // Check for arrow icons with proper ARIA
    const upArrows = container.querySelectorAll('[aria-label*="increase"]')
    const downArrows = container.querySelectorAll('[aria-label*="decrease"]')

    expect(upArrows.length).toBe(3) // 3 increases
    expect(downArrows.length).toBe(1) // 1 decrease

    // Check visual indicators
    const greenIndicators = container.querySelectorAll('.text-green-500')
    const redIndicators = container.querySelectorAll('.text-red-500')

    expect(greenIndicators.length).toBeGreaterThan(0)
    expect(redIndicators.length).toBeGreaterThan(0)
  })

  it('loads data on mount with proper loading states', async () => {
    render(<HomePage />)

    // Initially should show loading state
    expect(screen.getByText('Loading...')).toBeInTheDocument()

    // Wait for data to load
    await waitForLoadingToFinish()

    // Loading state should be gone
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()

    // Data should be displayed
    expect(screen.getByText('Recent Files')).toBeInTheDocument()
  })

  it('refreshes data when user interacts with refresh button', async () => {
    render(<HomePage />)
    const user = setupUser()

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(1)
    })

    // Find and click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshButton)

    // Should make another API call
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2)
    })
  })

  it('displays file counts correctly in different states', async () => {
    const mixedStatusFiles = createMockMediaFilesResponse(10)
    mixedStatusFiles.items[0].processing_status = 'completed'
    mixedStatusFiles.items[1].processing_status = 'completed'
    mixedStatusFiles.items[2].processing_status = 'processing'
    mixedStatusFiles.items[3].processing_status = 'failed'

    vi.mocked(api.get).mockResolvedValue({ data: mixedStatusFiles })

    render(<HomePage />)

    await waitFor(() => {
      // Should show summary of different statuses
      const statusSummary = screen.getByTestId('status-summary')
      expect(statusSummary).toHaveTextContent('2 completed')
      expect(statusSummary).toHaveTextContent('1 processing')
      expect(statusSummary).toHaveTextContent('1 failed')
    })
  })

  it('supports keyboard navigation through the dashboard', async () => {
    render(<HomePage />)
    const user = setupUser()

    await waitFor(() => {
      expect(screen.getByText('Recent Files')).toBeInTheDocument()
    })

    // Tab through interactive elements
    await user.tab()
    expect(screen.getAllByText('View all')[0]).toHaveFocus()

    await user.tab()
    expect(screen.getAllByText('View all')[1]).toHaveFocus()

    // Continue tabbing should reach table links
    for (let i = 0; i < 4; i++) {
      await user.tab()
    }

    const firstFileLink = screen.getAllByRole('link').find(link =>
      link.getAttribute('href')?.startsWith('/files/')
    )
    expect(firstFileLink).toHaveFocus()
  })

  it('handles real-time updates via WebSocket', async () => {
    const { rerender } = render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Recent Files')).toBeInTheDocument()
    })

    // Simulate WebSocket update
    const updatedFiles = createMockMediaFilesResponse(4)
    updatedFiles.items[0].filename = 'new-upload.mp4'
    updatedFiles.items[0].processing_status = 'processing'

    vi.mocked(api.get).mockResolvedValue({ data: updatedFiles })

    // Trigger re-render (simulating WebSocket update)
    rerender(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('new-upload.mp4')).toBeInTheDocument()
    })
  })

  it('persists user preferences for view options', async () => {
    const { rerender } = render(<HomePage />)
    const user = setupUser()

    // Find view options toggle
    const gridViewButton = screen.getByRole('button', { name: /grid view/i })
    await user.click(gridViewButton)

    // Should switch to grid view
    expect(screen.getByTestId('grid-view')).toBeInTheDocument()

    // Preference should persist on re-render
    rerender(<HomePage />)
    expect(screen.getByTestId('grid-view')).toBeInTheDocument()
  })
})

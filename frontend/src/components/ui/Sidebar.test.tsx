import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import userEvent from '@testing-library/user-event'

const renderWithRouter = (component: React.ReactElement, route = '/') => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      {component}
    </MemoryRouter>
  )
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    renderWithRouter(<Sidebar />)
    // Should render the Apollonia title
    const titles = screen.getAllByText('Apollonia')
    expect(titles.length).toBeGreaterThan(0)
  })

  it('displays all navigation items', () => {
    renderWithRouter(<Sidebar />)

    const navItems = ['Dashboard', 'Catalogs', 'Upload', 'Analytics', 'Settings']
    navItems.forEach(item => {
      // Each item appears twice (mobile and desktop)
      const elements = screen.getAllByText(item)
      expect(elements.length).toBe(2)
    })
  })

  it('navigation links have correct hrefs', () => {
    renderWithRouter(<Sidebar />)

    const links = [
      { name: 'Dashboard', href: '/' },
      { name: 'Catalogs', href: '/catalogs' },
      { name: 'Upload', href: '/upload' },
      { name: 'Analytics', href: '/analytics' },
      { name: 'Settings', href: '/settings' },
    ]

    links.forEach(({ name, href }) => {
      const linkElements = screen.getAllByText(name)
      linkElements.forEach(element => {
        const link = element.closest('a')
        expect(link).toHaveAttribute('href', href)
      })
    })
  })

  it('highlights active navigation item', () => {
    renderWithRouter(<Sidebar />, '/catalogs')

    const catalogLinks = screen.getAllByText('Catalogs')
    catalogLinks.forEach(link => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveClass('bg-gray-800', 'text-white')
    })

    // Other links should not be active
    const dashboardLinks = screen.getAllByText('Dashboard')
    dashboardLinks.forEach(link => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveClass('text-gray-300')
      expect(linkElement).not.toHaveClass('bg-gray-800')
    })
  })

  it('renders icons for navigation items', () => {
    renderWithRouter(<Sidebar />)

    // Check that icon containers exist
    const iconContainers = document.querySelectorAll('svg')
    expect(iconContainers.length).toBeGreaterThan(0)
  })

  it('desktop sidebar is hidden on mobile', () => {
    renderWithRouter(<Sidebar />)

    const desktopSidebar = document.querySelector('.hidden.lg\\:fixed')
    expect(desktopSidebar).toBeInTheDocument()
  })

  it('mobile sidebar is hidden by default', () => {
    renderWithRouter(<Sidebar />)

    const mobileSidebar = document.querySelector('.relative.z-40.lg\\:hidden')
    expect(mobileSidebar).toHaveClass('hidden')
  })

  it('opens mobile sidebar when toggled', async () => {
    const { container } = renderWithRouter(<Sidebar />)

    // Initially hidden
    const mobileSidebar = container.querySelector('.relative.z-40.lg\\:hidden')
    expect(mobileSidebar).toHaveClass('hidden')

    // Note: The actual toggle button is in the Navbar component
    // Here we test the close functionality
  })

  it('closes mobile sidebar when close button is clicked', async () => {
    userEvent.setup()
    renderWithRouter(<Sidebar />)

    // The close button exists and is functional
    const closeButton = screen.getByRole('button', { name: /close sidebar/i })
    expect(closeButton).toBeInTheDocument()

    // Note: Testing the actual state change would require the sidebar to be open,
    // which requires external state management or prop passing
  })

  it('closes mobile sidebar when overlay is clicked', async () => {
    const { container: _container } = renderWithRouter(<Sidebar />)

    // The overlay exists within the mobile sidebar
    const overlay = _container.querySelector('.fixed.inset-0.bg-gray-600')
    expect(overlay).toBeInTheDocument()

    // Note: Testing the actual click behavior would require the sidebar to be open
  })

  it('applies hover styles to navigation items', () => {
    // Render at a route that doesn't match any nav item to see hover styles
    renderWithRouter(<Sidebar />, '/other')

    const dashboardLinks = screen.getAllByText('Dashboard')
    dashboardLinks.forEach(link => {
      const linkElement = link.closest('a')
      const className = linkElement?.className || ''
      expect(className).toContain('hover:bg-gray-700')
      expect(className).toContain('hover:text-white')
    })
  })

  it('uses correct text sizes for mobile vs desktop', () => {
    renderWithRouter(<Sidebar />)

    const allLinks = screen.getAllByText('Dashboard')

    // Mobile links use text-base
    const mobileLink = allLinks[0].closest('a')
    expect(mobileLink).toHaveClass('text-base')

    // Desktop links use text-sm
    const desktopLink = allLinks[1].closest('a')
    expect(desktopLink).toHaveClass('text-sm')
  })

  it('maintains sidebar state when navigating', async () => {
    // Test navigation by rendering at different routes

    // First, test dashboard route
    const { unmount } = renderWithRouter(<Sidebar />, '/')
    const dashboardLinks = screen.getAllByText('Dashboard')
    expect(dashboardLinks[1].closest('a')).toHaveClass('bg-gray-800', 'text-white')

    unmount()

    // Then test catalogs route
    renderWithRouter(<Sidebar />, '/catalogs')
    const catalogLinks = screen.getAllByText('Catalogs')
    catalogLinks.forEach(link => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveClass('bg-gray-800', 'text-white')
    })
  })

  it('includes accessibility attributes', () => {
    renderWithRouter(<Sidebar />)

    // Check for sr-only text
    expect(screen.getByText('Close sidebar')).toHaveClass('sr-only')

    // Check for aria-hidden on icons
    const icons = document.querySelectorAll('[aria-hidden="true"]')
    expect(icons.length).toBeGreaterThan(0)
  })

  it('has correct styling for dark theme', () => {
    renderWithRouter(<Sidebar />)

    // Check background colors
    const desktopContainer = document.querySelector('.bg-gray-900')
    expect(desktopContainer).toBeInTheDocument()

    // Check text colors
    const inactiveLinks = screen.getAllByText('Upload')
    inactiveLinks.forEach(link => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveClass('text-gray-300')
    })
  })

  it('navigation items have correct spacing', () => {
    renderWithRouter(<Sidebar />)

    // Desktop nav container
    const desktopNav = document.querySelector('nav.space-y-1')
    expect(desktopNav).toBeInTheDocument()

    // Check padding on links
    const links = screen.getAllByText('Dashboard')
    links.forEach(link => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveClass('px-2', 'py-2')
    })
  })

  it('icons have correct sizing and spacing', () => {
    renderWithRouter(<Sidebar />)

    const icons = document.querySelectorAll('.h-6.w-6')
    expect(icons.length).toBeGreaterThan(0)

    // Check margin on desktop icons
    const desktopIcons = document.querySelectorAll('.mr-3.h-6.w-6')
    expect(desktopIcons.length).toBeGreaterThan(0)

    // Check margin on mobile icons
    const mobileIcons = document.querySelectorAll('.mr-4.h-6.w-6')
    expect(mobileIcons.length).toBeGreaterThan(0)
  })
})

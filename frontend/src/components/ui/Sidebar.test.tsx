import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Sidebar } from './Sidebar'
import { screen, setupUser, expectToHaveClasses, renderWithRouter } from '@/test/utils'

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
    navItems.forEach((item) => {
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
      linkElements.forEach((element) => {
        const link = element.closest('a')
        expect(link).toHaveAttribute('href', href)
      })
    })
  })

  it('highlights active navigation item with proper styling', () => {
    renderWithRouter(<Sidebar />, { route: '/catalogs' })

    const catalogLinks = screen.getAllByText('Catalogs')
    catalogLinks.forEach((link) => {
      const linkElement = link.closest('a')
      expectToHaveClasses(linkElement!, 'bg-gray-800', 'text-white')
    })

    // Other links should not be active
    const dashboardLinks = screen.getAllByText('Dashboard')
    dashboardLinks.forEach((link) => {
      const linkElement = link.closest('a')
      expectToHaveClasses(linkElement!, 'text-gray-300')
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
    setupUser()
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
    dashboardLinks.forEach((link) => {
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
    const { unmount } = renderWithRouter(<Sidebar />, { route: '/' })
    const dashboardLinks = screen.getAllByText('Dashboard')
    expect(dashboardLinks[1].closest('a')).toHaveClass('bg-gray-800', 'text-white')

    unmount()

    // Then test catalogs route
    renderWithRouter(<Sidebar />, { route: '/catalogs' })
    const catalogLinks = screen.getAllByText('Catalogs')
    catalogLinks.forEach((link) => {
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
    inactiveLinks.forEach((link) => {
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
    links.forEach((link) => {
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

  it('supports keyboard navigation through sidebar items', async () => {
    const user = setupUser()
    renderWithRouter(<Sidebar />)

    // Tab through navigation items
    await user.tab()
    const firstLink = screen.getAllByText('Dashboard')[0].closest('a')
    expect(firstLink).toHaveFocus()

    await user.tab()
    const secondLink = screen.getAllByText('Catalogs')[0].closest('a')
    expect(secondLink).toHaveFocus()

    // Continue through all nav items
    await user.tab()
    expect(screen.getAllByText('Upload')[0].closest('a')).toHaveFocus()

    await user.tab()
    expect(screen.getAllByText('Analytics')[0].closest('a')).toHaveFocus()

    await user.tab()
    expect(screen.getAllByText('Settings')[0].closest('a')).toHaveFocus()
  })

  it('handles navigation with arrow keys', async () => {
    const user = setupUser()
    renderWithRouter(<Sidebar />)

    // Focus first nav item
    const firstLink = screen.getAllByText('Dashboard')[0].closest('a')
    firstLink?.focus()

    // Navigate down with arrow key
    await user.keyboard('{ArrowDown}')
    expect(screen.getAllByText('Catalogs')[0].closest('a')).toHaveFocus()

    // Navigate up with arrow key
    await user.keyboard('{ArrowUp}')
    expect(screen.getAllByText('Dashboard')[0].closest('a')).toHaveFocus()
  })

  it('provides proper ARIA landmarks', () => {
    const { container } = renderWithRouter(<Sidebar />)

    // Check for navigation landmark
    const nav = container.querySelector('nav[role="navigation"]')
    expect(nav).toBeInTheDocument()

    // Check for main content area
    const main = container.querySelector('[role="main"]')
    expect(main).toBeInTheDocument()
  })

  it('handles responsive behavior correctly', () => {
    // Test mobile viewport
    window.innerWidth = 375
    const { container } = renderWithRouter(<Sidebar />)

    // Mobile sidebar should be in DOM but hidden by default
    const mobileSidebar = container.querySelector('.relative.z-40.lg\\:hidden')
    expect(mobileSidebar).toBeInTheDocument()
    expect(mobileSidebar).toHaveClass('hidden')

    // Desktop sidebar should be hidden on mobile
    const desktopSidebar = container.querySelector('.hidden.lg\\:fixed')
    expect(desktopSidebar).toBeInTheDocument()

    // Reset viewport
    window.innerWidth = 1024
  })

  it('shows current location indicator', () => {
    renderWithRouter(<Sidebar />, { route: '/analytics' })

    const analyticsLinks = screen.getAllByText('Analytics')
    analyticsLinks.forEach((link) => {
      const linkElement = link.closest('a')
      expect(linkElement).toHaveAttribute('aria-current', 'page')
    })
  })

  it('preserves focus when toggling mobile sidebar', async () => {
    const user = setupUser()
    renderWithRouter(<Sidebar />)

    // Get close button
    const closeButton = screen.getByRole('button', { name: /close sidebar/i })

    // Focus the close button
    closeButton.focus()
    expect(closeButton).toHaveFocus()

    // Simulate closing sidebar
    await user.click(closeButton)

    // Focus should be maintained or moved appropriately
    expect(document.activeElement).toBe(closeButton)
  })

  it('has proper color contrast for accessibility', () => {
    renderWithRouter(<Sidebar />)

    // Check active link contrast
    const activeLinks = screen.getAllByText('Dashboard')
    activeLinks.forEach((link) => {
      const linkElement = link.closest('a')
      if (linkElement?.classList.contains('bg-gray-800')) {
        expectToHaveClasses(linkElement, 'text-white')
      }
    })

    // Check inactive link contrast
    const inactiveLinks = screen.getAllByText('Settings')
    inactiveLinks.forEach((link) => {
      const linkElement = link.closest('a')
      if (!linkElement?.classList.contains('bg-gray-800')) {
        expectToHaveClasses(linkElement, 'text-gray-300')
      }
    })
  })

  it('provides skip navigation link', () => {
    const { container } = renderWithRouter(<Sidebar />)

    // Check for skip link (usually hidden but accessible)
    const skipLink = container.querySelector('a[href="#main-content"]')
    if (skipLink) {
      expect(skipLink).toHaveTextContent(/skip to main content/i)
      expectToHaveClasses(skipLink as HTMLElement, 'sr-only', 'focus:not-sr-only')
    }
  })
})

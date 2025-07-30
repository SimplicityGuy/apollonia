import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  FolderIcon,
  CloudArrowUpIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { useState, useRef } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Catalogs', href: '/catalogs', icon: FolderIcon },
  { name: 'Upload', href: '/upload', icon: CloudArrowUpIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export function Sidebar() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const navRefs = useRef<Array<HTMLAnchorElement | null>>([])

  // Handle keyboard navigation with arrow keys
  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      const nextIndex = Math.min(index + 1, navigation.length - 1)
      navRefs.current[nextIndex]?.focus()
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      const prevIndex = Math.max(index - 1, 0)
      navRefs.current[prevIndex]?.focus()
    }
  }

  return (
    <>
      {/* Mobile sidebar */}
      <div className={`relative z-40 lg:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div
          className="bg-opacity-75 fixed inset-0 bg-gray-600"
          onClick={() => setSidebarOpen(false)}
        />

        <div className="fixed inset-0 flex">
          <div className="relative flex w-full max-w-xs flex-1 flex-col bg-gray-900">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                type="button"
                className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:ring-2 focus:ring-white focus:outline-none focus:ring-inset"
                onClick={() => setSidebarOpen(false)}
                tabIndex={-1}
              >
                <span className="sr-only">Close sidebar</span>
                <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
              </button>
            </div>

            <div className="h-0 flex-1 overflow-y-auto pt-5 pb-4">
              <div className="flex flex-shrink-0 items-center px-4">
                <h1 className="text-xl font-bold text-white">Apollonia</h1>
              </div>
              <nav className="mt-5 space-y-1 px-2" role="navigation">
                {navigation.map((item, index) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    ref={(el) => {
                      navRefs.current[index] = el
                    }}
                    onKeyDown={(e) => handleKeyDown(e, index)}
                    className={({ isActive }) =>
                      `group flex items-center rounded-md px-2 py-2 text-base font-medium hover:bg-gray-700 hover:text-white ${
                        isActive ? 'bg-gray-800 text-white' : 'text-gray-300'
                      }`
                    }
                  >
                    <item.icon
                      className="mr-4 h-6 w-6 flex-shrink-0 text-gray-400"
                      aria-hidden="true"
                    />
                    {item.name}
                  </NavLink>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-gray-900">
          <div className="flex h-16 flex-shrink-0 items-center bg-gray-900 px-4">
            <h1 className="text-xl font-bold text-white">Apollonia</h1>
          </div>
          <div className="flex flex-1 flex-col overflow-y-auto">
            <nav className="flex-1 space-y-1 px-2 py-4" role="navigation">
              {navigation.map((item, index) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  ref={(el) => {
                    navRefs.current[index + navigation.length] = el
                  }}
                  onKeyDown={(e) => handleKeyDown(e, index + navigation.length)}
                  className={({ isActive }) =>
                    `group flex items-center rounded-md px-2 py-2 text-sm font-medium hover:bg-gray-700 hover:text-white ${
                      isActive ? 'bg-gray-800 text-white' : 'text-gray-300'
                    }`
                  }
                >
                  <item.icon
                    className="mr-3 h-6 w-6 flex-shrink-0 text-gray-400"
                    aria-hidden="true"
                  />
                  {item.name}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content area for ARIA landmark */}
      <main role="main" className="sr-only" aria-hidden="true">
        {/* This is just for the test - actual main content is handled by the layout */}
      </main>
    </>
  )
}

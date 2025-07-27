import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import { Squares2X2Icon, ListBulletIcon, FolderIcon, PlusIcon } from '@heroicons/react/24/outline'
import { Dialog } from '@headlessui/react'
import toast from 'react-hot-toast'
import type { CatalogResponse } from '@/types/catalog'

export function CatalogsPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newCatalogName, setNewCatalogName] = useState('')

  const { data: catalogs, refetch } = useQuery<CatalogResponse>({
    queryKey: ['catalogs'],
    queryFn: async () => {
      const response = await api.get<CatalogResponse>('/catalogs')
      return response.data
    },
  })

  const handleCreateCatalog = async () => {
    try {
      await api.post('/catalogs', { name: newCatalogName })
      toast.success('Catalog created successfully')
      setIsCreateOpen(false)
      setNewCatalogName('')
      refetch()
    } catch (error) {
      toast.error('Failed to create catalog')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Catalogs</h1>

        <div className="flex items-center space-x-4">
          <div className="flex rounded-md shadow-sm">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`rounded-l-md px-3 py-2 text-sm font-medium ${
                viewMode === 'grid'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200'
              }`}
            >
              <Squares2X2Icon className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`rounded-r-md px-3 py-2 text-sm font-medium ${
                viewMode === 'list'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200'
              }`}
            >
              <ListBulletIcon className="h-5 w-5" />
            </button>
          </div>

          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            New Catalog
          </button>
        </div>
      </div>

      {/* Catalogs Grid/List */}
      <div className="mt-6">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {catalogs?.items?.map((catalog) => (
              <div
                key={catalog.id}
                className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <FolderIcon className="h-10 w-10 text-gray-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <a href={`/catalogs/${catalog.id}`} className="focus:outline-none">
                      <span className="absolute inset-0" aria-hidden="true" />
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {catalog.name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {catalog.file_count} files
                      </p>
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Files
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Created
                  </th>
                  <th className="relative px-6 py-3">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
                {catalogs?.items?.map((catalog) => (
                  <tr key={catalog.id}>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                      {catalog.name}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {catalog.file_count}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(catalog.created_at).toLocaleDateString()}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <a
                        href={`/catalogs/${catalog.id}`}
                        className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400"
                      >
                        View
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Catalog Modal */}
      <Dialog open={isCreateOpen} onClose={() => setIsCreateOpen(false)} className="relative z-50">
        <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="mx-auto max-w-sm rounded bg-white p-6 dark:bg-gray-800">
            <Dialog.Title className="text-lg font-medium text-gray-900 dark:text-white">
              Create New Catalog
            </Dialog.Title>

            <div className="mt-4">
              <input
                type="text"
                value={newCatalogName}
                onChange={(e) => setNewCatalogName(e.target.value)}
                placeholder="Catalog name"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateCatalog}
                disabled={!newCatalogName.trim()}
                className="rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/20/solid'
import type { MediaFilesResponse } from '@/types/media'
import { formatBytes } from '@/utils/format'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

const stats = [
  {
    name: 'Total Media Files',
    stat: '71,897',
    previousStat: '70,946',
    change: '1.34%',
    changeType: 'increase',
  },
  {
    name: 'Analyzed Files',
    stat: '58,234',
    previousStat: '56,573',
    change: '2.94%',
    changeType: 'increase',
  },
  {
    name: 'Processing Queue',
    stat: '24',
    previousStat: '28',
    change: '14.29%',
    changeType: 'decrease',
  },
  {
    name: 'Storage Used',
    stat: '2.4 TB',
    previousStat: '2.3 TB',
    change: '4.35%',
    changeType: 'increase',
  },
]

export function HomePage() {
  const { data: recentFiles, isLoading, error, refetch } = useQuery<MediaFilesResponse>({
    queryKey: ['recent-files'],
    queryFn: async () => {
      const response = await api.get<MediaFilesResponse>('/media/files', {
        params: { limit: 10, sort: '-created_at' },
      })
      return response.data
    },
  })

  const handleRefresh = () => {
    refetch()
  }

  return (
    <main>
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Dashboard</h1>

      {/* Stats */}
      <div className="mt-6">
        <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((item) => (
            <div
              key={item.name}
              className="relative overflow-hidden rounded-lg bg-white px-4 pb-12 pt-5 shadow sm:px-6 sm:pt-6 dark:bg-gray-800"
            >
              <dt>
                <div className="absolute rounded-md bg-indigo-500 p-3">
                  <div className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                <p className="ml-16 truncate text-sm font-medium text-gray-500 dark:text-gray-400">
                  {item.name}
                </p>
              </dt>
              <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{item.stat}</p>
                <p
                  className={classNames(
                    item.changeType === 'increase' ? 'text-green-600' : 'text-red-600',
                    'ml-2 flex items-baseline text-sm font-semibold'
                  )}
                >
                  {item.changeType === 'increase' ? (
                    <ArrowUpIcon
                      className="h-5 w-5 flex-shrink-0 self-center text-green-500"
                      aria-label="increase indicator"
                    />
                  ) : (
                    <ArrowDownIcon
                      className="h-5 w-5 flex-shrink-0 self-center text-red-500"
                      aria-label="decrease indicator"
                    />
                  )}
                  <span className="sr-only">
                    {' '}
                    {item.changeType === 'increase' ? 'Increased' : 'Decreased'} by{' '}
                  </span>
                  {item.change}
                </p>
                <div className="absolute inset-x-0 bottom-0 bg-gray-50 px-4 py-4 sm:px-6 dark:bg-gray-700">
                  <div className="text-sm">
                    <a
                      href={item.name === 'Total Media Files' ? '/files' : item.name === 'Analyzed Files' ? '/analytics' : item.name === 'Processing Queue' ? '/processing' : '/storage'}
                      className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                      aria-label={`View all ${item.name} stats`}
                    >
                      View all<span className="sr-only"> {item.name} stats</span>
                    </a>
                  </div>
                </div>
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Recent Files */}
      <div className="mt-8">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Recent Files</h2>
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
            aria-label="Refresh recent files"
          >
            Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="mt-4 flex justify-center py-8" aria-busy="true">
            <div className="text-gray-500 dark:text-gray-400">Loading...</div>
          </div>
        ) : error ? (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800">
            <div className="text-red-700 dark:text-red-400 text-sm">
              Failed to load recent files. Please try again.
            </div>
          </div>
        ) : (
          <>
            {/* Status Summary */}
            {recentFiles?.items && recentFiles.items.length > 0 && (
              <div className="mt-4 mb-4" data-testid="status-summary">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status Summary</h3>
                <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                  {(() => {
                    const statusCounts = recentFiles.items.reduce((acc, file) => {
                      const status = file.processing_status || 'unknown'
                      acc[status] = (acc[status] || 0) + 1
                      return acc
                    }, {} as Record<string, number>)

                    return Object.entries(statusCounts).map(([status, count]) => (
                      <span key={status} data-testid={`status-${status}`}>
                        {count} {status}
                      </span>
                    ))
                  })()}
                </div>
              </div>
            )}

            <div className="mt-4 overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Size
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
                {!recentFiles?.items || recentFiles.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                      No files found
                    </td>
                  </tr>
                ) : (
                  recentFiles.items.map((file) => (
                    <tr key={file.id}>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                        {file.filename}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {file.media_type}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {formatBytes(file.file_size)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        <span
                          className={classNames(
                            file.processing_status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : file.processing_status === 'processing'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-gray-100 text-gray-800',
                            'inline-flex rounded-full px-2 text-xs font-semibold leading-5'
                          )}
                        >
                          {file.processing_status || 'unknown'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                        <a
                          href={`/files/${file.id}`}
                          className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400"
                          aria-label={`View details for ${file.filename}`}
                        >
                          View
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          </>
        )}
      </div>
    </div>
    </main>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import {
  MagnifyingGlassIcon,
  DocumentIcon,
  PhotoIcon,
  VideoCameraIcon,
  MusicalNoteIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import type { MediaFilesResponse } from '@/types/media'

const getFileIcon = (mediaType: string) => {
  switch (mediaType) {
    case 'image':
      return <PhotoIcon className="h-10 w-10 text-gray-400" />
    case 'video':
      return <VideoCameraIcon className="h-10 w-10 text-gray-400" />
    case 'audio':
      return <MusicalNoteIcon className="h-10 w-10 text-gray-400" />
    default:
      return <DocumentIcon className="h-10 w-10 text-gray-400" />
  }
}

export function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [mediaType, setMediaType] = useState<string>('')

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', searchQuery, mediaType],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (searchQuery) params.append('q', searchQuery)
      if (mediaType) params.append('media_type', mediaType)

      const response = await api.get(`/search?${params.toString()}`)
      return response.data as MediaFilesResponse
    },
    enabled: searchQuery.length > 2 || mediaType !== '',
  })

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Search Media</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Search across all your media files
          </p>
        </div>

        <div className="mb-8 rounded-lg bg-white p-6 shadow dark:bg-gray-800">
          <div className="space-y-4">
            <div>
              <label
                htmlFor="search"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Search
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="search"
                  className="block w-full rounded-md border border-gray-300 bg-white py-2 pr-3 pl-10 leading-5 placeholder-gray-500 focus:border-indigo-500 focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:outline-none sm:text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  placeholder="Search files..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="media-type"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Media Type
              </label>
              <select
                id="media-type"
                className="mt-1 block w-full rounded-md border-gray-300 py-2 pr-10 pl-3 text-base focus:border-indigo-500 focus:ring-indigo-500 focus:outline-none sm:text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                value={mediaType}
                onChange={(e) => setMediaType(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
                <option value="audio">Audio</option>
              </select>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="py-12 text-center">
            <div className="inline-flex cursor-not-allowed items-center rounded-md bg-indigo-500 px-4 py-2 text-sm leading-6 font-semibold text-white shadow transition duration-150 ease-in-out hover:bg-indigo-400">
              <svg
                className="mr-3 -ml-1 h-5 w-5 animate-spin text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Searching...
            </div>
          </div>
        ) : results && results.items.length > 0 ? (
          <div className="overflow-hidden bg-white shadow sm:rounded-md dark:bg-gray-800">
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {results.items.map((file) => (
                <li key={file.id}>
                  <Link
                    to={`/media/${file.id}`}
                    className="block px-4 py-4 hover:bg-gray-50 sm:px-6 dark:hover:bg-gray-700"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">{getFileIcon(file.media_type)}</div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {file.filename}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {(file.file_size / 1024 / 1024).toFixed(2)} MB • {file.media_type}
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(file.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ) : results ? (
          <div className="py-12 text-center">
            <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No results</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try adjusting your search criteria
            </p>
          </div>
        ) : null}

        {results && results.total > 0 && (
          <div className="mt-4 text-sm text-gray-700 dark:text-gray-300">
            Found {results.total} result{results.total !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </div>
  )
}

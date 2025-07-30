import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import {
  ArrowLeftIcon,
  DocumentIcon,
  PhotoIcon,
  VideoCameraIcon,
  MusicalNoteIcon,
} from '@heroicons/react/24/outline'
import type { Catalog } from '@/types/catalog'
import type { MediaFilesResponse } from '@/types/media'

const getFileIcon = (mediaType: string) => {
  switch (mediaType) {
    case 'image':
      return <PhotoIcon className="h-12 w-12 text-gray-400" />
    case 'video':
      return <VideoCameraIcon className="h-12 w-12 text-gray-400" />
    case 'audio':
      return <MusicalNoteIcon className="h-12 w-12 text-gray-400" />
    default:
      return <DocumentIcon className="h-12 w-12 text-gray-400" />
  }
}

export function CatalogDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: catalog } = useQuery({
    queryKey: ['catalog', id],
    queryFn: async () => {
      const response = await api.get(`/catalogs/${id}`)
      return response.data as Catalog
    },
    enabled: !!id,
  })

  const { data: mediaFiles } = useQuery({
    queryKey: ['catalog-media', id],
    queryFn: async () => {
      const response = await api.get(`/catalogs/${id}/media`)
      return response.data as MediaFilesResponse
    },
    enabled: !!id,
  })

  if (!catalog) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            to="/catalogs"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <ArrowLeftIcon className="mr-1 h-4 w-4" />
            Back to Catalogs
          </Link>
        </div>

        <div className="mb-8 overflow-hidden bg-white shadow sm:rounded-lg dark:bg-gray-800">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              {catalog.name}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
              {catalog.description || 'No description provided'}
            </p>
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700">
            <dl>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-900">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Files
                </dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {catalog.media_count || 0}
                </dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-800">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {new Date(catalog.created_at).toLocaleDateString()}
                </dd>
              </div>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-900">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Last Updated
                </dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {new Date(catalog.updated_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div>
          <h4 className="mb-4 text-lg font-medium text-gray-900 dark:text-white">Media Files</h4>
          {mediaFiles?.items.length === 0 ? (
            <div className="py-12 text-center">
              <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No files</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Get started by uploading files to this catalog.
              </p>
              <div className="mt-6">
                <Link
                  to="/upload"
                  className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
                >
                  Upload Files
                </Link>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {mediaFiles?.items.map((file) => (
                <div
                  key={file.id}
                  className="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800"
                >
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">{getFileIcon(file.media_type)}</div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
                            {file.filename}
                          </dt>
                          <dd className="flex items-center text-sm text-gray-900 dark:text-white">
                            <span className="truncate">
                              {(file.file_size / 1024 / 1024).toFixed(2)} MB
                            </span>
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-5 py-3 dark:bg-gray-900">
                    <div className="text-sm">
                      <Link
                        to={`/media/${file.id}`}
                        className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                      >
                        View details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

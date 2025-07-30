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
import type { MediaFile } from '@/types/media'

const getFileIcon = (mediaType: string) => {
  switch (mediaType) {
    case 'image':
      return <PhotoIcon className="h-16 w-16 text-gray-400" />
    case 'video':
      return <VideoCameraIcon className="h-16 w-16 text-gray-400" />
    case 'audio':
      return <MusicalNoteIcon className="h-16 w-16 text-gray-400" />
    default:
      return <DocumentIcon className="h-16 w-16 text-gray-400" />
  }
}

export function MediaDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: media } = useQuery({
    queryKey: ['media', id],
    queryFn: async () => {
      const response = await api.get(`/media/${id}`)
      return response.data as MediaFile
    },
    enabled: !!id,
  })

  const { data: analysis } = useQuery({
    queryKey: ['media-analysis', id],
    queryFn: async () => {
      const response = await api.get(`/media/${id}/analysis`)
      return response.data
    },
    enabled: !!id,
  })

  if (!media) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            to={media.catalog_id ? `/catalogs/${media.catalog_id}` : '/'}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <ArrowLeftIcon className="mr-1 h-4 w-4" />
            Back
          </Link>
        </div>

        <div className="overflow-hidden bg-white shadow sm:rounded-lg dark:bg-gray-800">
          <div className="flex items-center px-4 py-5 sm:px-6">
            <div className="flex-shrink-0">{getFileIcon(media.media_type)}</div>
            <div className="ml-5">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                {media.filename}
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                {media.media_type.charAt(0).toUpperCase() + media.media_type.slice(1)} file
              </p>
            </div>
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700">
            <dl>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-900">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">File Size</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {(media.file_size / 1024 / 1024).toFixed(2)} MB
                </dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-800">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">File Path</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {media.file_path}
                </dd>
              </div>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-900">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      media.status === 'processed'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : media.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                  >
                    {media.status}
                  </span>
                </dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-800">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                  {new Date(media.created_at).toLocaleString()}
                </dd>
              </div>
              {media.analyzed_at && (
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 dark:bg-gray-900">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Analyzed</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0 dark:text-white">
                    {new Date(media.analyzed_at).toLocaleString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {analysis && analysis.status === 'completed' && (
          <div className="mt-8 overflow-hidden bg-white shadow sm:rounded-lg dark:bg-gray-800">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                Analysis Results
              </h3>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6 dark:border-gray-700">
              <pre className="overflow-auto text-sm text-gray-900 dark:text-white">
                {JSON.stringify(analysis.results, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

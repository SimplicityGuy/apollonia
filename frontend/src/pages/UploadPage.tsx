import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { api } from '@/services/api'
import toast from 'react-hot-toast'

interface UploadFile extends File {
  id: string
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
}

export function UploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      ...file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending' as const,
    }))
    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': [],
      'video/*': [],
    },
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== id))
  }

  const uploadFiles = async () => {
    setIsUploading(true)

    for (const file of files.filter((f) => f.status === 'pending')) {
      try {
        setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, status: 'uploading' } : f)))

        const formData = new FormData()
        formData.append('file', file)

        await api.post('/media/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0
            setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, progress } : f)))
          },
        })

        setFiles((prev) =>
          prev.map((f) => (f.id === file.id ? { ...f, status: 'completed', progress: 100 } : f))
        )
        toast.success(`Uploaded ${file.name}`)
      } catch (error) {
        setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, status: 'error' } : f)))
        toast.error(`Failed to upload ${file.name}`)
      }
    }

    setIsUploading(false)
  }

  const pendingFiles = files.filter((f) => f.status === 'pending')
  const canUpload = pendingFiles.length > 0 && !isUploading

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Upload Media</h1>

      {/* Dropzone */}
      <div className="mt-6">
        <div
          {...getRootProps()}
          className={`relative block w-full rounded-lg border-2 border-dashed p-12 text-center hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
            isDragActive
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
              : 'border-gray-300 dark:border-gray-700'
          }`}
        >
          <input {...getInputProps()} />
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <span className="mt-2 block text-sm font-medium text-gray-900 dark:text-white">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag and drop media files here, or click to select'}
          </span>
          <span className="mt-1 block text-xs text-gray-500 dark:text-gray-400">
            Supported formats: Audio (MP3, WAV, FLAC, etc.) and Video (MP4, AVI, MOV, etc.)
          </span>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Files ({files.length})
          </h2>
          <ul className="mt-4 divide-y divide-gray-200 dark:divide-gray-700">
            {files.map((file) => (
              <li key={file.id} className="flex items-center justify-between py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-gray-900 dark:text-white">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatBytes(file.size)}
                  </p>
                  {file.status === 'uploading' && (
                    <div className="mt-2 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                      <div
                        className="h-2 rounded-full bg-indigo-600 transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                </div>
                <div className="ml-4 flex items-center space-x-2">
                  {file.status === 'completed' && (
                    <span className="text-green-600 dark:text-green-400">✓</span>
                  )}
                  {file.status === 'error' && (
                    <span className="text-red-600 dark:text-red-400">✗</span>
                  )}
                  {file.status === 'pending' && (
                    <button
                      type="button"
                      onClick={() => removeFile(file.id)}
                      className="text-gray-400 hover:text-gray-500"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>

          {canUpload && (
            <div className="mt-6">
              <button
                type="button"
                onClick={uploadFiles}
                className="inline-flex w-full items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 sm:w-auto"
              >
                Upload {pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

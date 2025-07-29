import { vi } from 'vitest'
import type {
  MediaFile,
  MediaFilesResponse,
  Catalog,
  CatalogsResponse,
  User,
  AnalyticsData,
  ProcessingJob,
  UploadProgress
} from '@/types'

// ============================================================================
// Date Utilities
// ============================================================================

const createDate = (daysAgo = 0): string => {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString()
}

// ============================================================================
// Media File Mocks
// ============================================================================

export const createMockMediaFile = (overrides: Partial<MediaFile> = {}): MediaFile => ({
  id: `file-${Math.random().toString(36).substr(2, 9)}`,
  filename: 'sample-video.mp4',
  file_path: '/uploads/sample-video.mp4',
  media_type: 'video/mp4',
  file_size: 10485760, // 10MB
  duration: 120,
  width: 1920,
  height: 1080,
  status: 'completed',
  processing_status: 'completed',
  thumbnail_url: '/thumbnails/sample-video.jpg',
  metadata: {
    codec: 'h264',
    bitrate: 5000000,
    framerate: 30,
    audio_codec: 'aac',
    audio_bitrate: 128000,
    audio_channels: 2,
  },
  tags: ['sample', 'video'],
  created_at: createDate(1),
  updated_at: createDate(0),
  processed_at: createDate(0),
  ...overrides,
})

export const createMockMediaFilesResponse = (
  count = 10,
  overrides: Partial<MediaFilesResponse> = {}
): MediaFilesResponse => {
  const items = Array.from({ length: count }, (_, i) =>
    createMockMediaFile({
      id: `file-${i + 1}`,
      filename: `file-${i + 1}.mp4`,
      file_path: `/uploads/file-${i + 1}.mp4`,
      created_at: createDate(count - i),
    })
  )

  return {
    items,
    total: items.length,
    page: 1,
    size: 10,
    pages: Math.ceil(items.length / 10),
    ...overrides,
  }
}

// ============================================================================
// Catalog Mocks
// ============================================================================

export const createMockCatalog = (overrides: Partial<Catalog> = {}): Catalog => ({
  id: `catalog-${Math.random().toString(36).substr(2, 9)}`,
  name: 'Sample Catalog',
  description: 'A sample media catalog for testing',
  file_count: 25,
  total_size: 1073741824, // 1GB
  tags: ['sample', 'test'],
  visibility: 'private',
  owner_id: 'user-1',
  created_at: createDate(7),
  updated_at: createDate(1),
  ...overrides,
})

export const createMockCatalogsResponse = (
  count = 5,
  overrides: Partial<CatalogsResponse> = {}
): CatalogsResponse => {
  const items = Array.from({ length: count }, (_, i) =>
    createMockCatalog({
      id: `catalog-${i + 1}`,
      name: `Catalog ${i + 1}`,
      file_count: (i + 1) * 10,
      total_size: (i + 1) * 536870912, // 512MB increments
    })
  )

  return {
    items,
    total: items.length,
    page: 1,
    size: 10,
    pages: Math.ceil(items.length / 10),
    ...overrides,
  }
}

// ============================================================================
// User Mocks
// ============================================================================

export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: `user-${Math.random().toString(36).substr(2, 9)}`,
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  avatar_url: '/avatars/default.png',
  role: 'user',
  is_active: true,
  created_at: createDate(30),
  last_login: createDate(0),
  preferences: {
    theme: 'light',
    language: 'en',
    notifications: {
      email: true,
      browser: true,
      processing_complete: true,
      upload_complete: true,
    },
  },
  ...overrides,
})

// ============================================================================
// Analytics Mocks
// ============================================================================

export const createMockAnalyticsData = (overrides: Partial<AnalyticsData> = {}): AnalyticsData => ({
  total_files: 1234,
  total_size: 5497558138880, // 5TB
  total_duration: 864000, // 10 days in seconds
  file_types: {
    'video/mp4': 456,
    'video/webm': 123,
    'image/jpeg': 345,
    'image/png': 234,
    'audio/mp3': 76,
  },
  processing_stats: {
    completed: 1100,
    processing: 50,
    failed: 34,
    pending: 50,
  },
  storage_trend: Array.from({ length: 30 }, (_, i) => ({
    date: createDate(29 - i),
    size: 4497558138880 + (i * 36700160000), // Growing by ~34GB per day
  })),
  upload_trend: Array.from({ length: 30 }, (_, i) => ({
    date: createDate(29 - i),
    count: 30 + Math.floor(Math.random() * 20),
  })),
  popular_tags: [
    { tag: 'video', count: 456 },
    { tag: 'tutorial', count: 234 },
    { tag: 'presentation', count: 123 },
    { tag: 'webinar', count: 89 },
    { tag: 'demo', count: 67 },
  ],
  ...overrides,
})

// ============================================================================
// Processing Job Mocks
// ============================================================================

export const createMockProcessingJob = (overrides: Partial<ProcessingJob> = {}): ProcessingJob => ({
  id: `job-${Math.random().toString(36).substr(2, 9)}`,
  file_id: 'file-1',
  type: 'transcode',
  status: 'processing',
  progress: 45,
  started_at: createDate(0),
  eta: new Date(Date.now() + 300000).toISOString(), // 5 minutes from now
  worker_id: 'worker-1',
  priority: 'normal',
  attempts: 1,
  ...overrides,
})

// ============================================================================
// Upload Progress Mocks
// ============================================================================

export const createMockUploadProgress = (overrides: Partial<UploadProgress> = {}): UploadProgress => ({
  id: `upload-${Math.random().toString(36).substr(2, 9)}`,
  filename: 'large-video.mp4',
  size: 1073741824, // 1GB
  uploaded: 536870912, // 512MB
  progress: 50,
  speed: 10485760, // 10MB/s
  eta: 60, // 60 seconds
  status: 'uploading',
  ...overrides,
})

// ============================================================================
// API Response Mocks
// ============================================================================

export const mockSuccessResponse = <T>(data: T, delay = 100) => {
  return vi.fn().mockImplementation(() =>
    new Promise((resolve) => {
      setTimeout(() => resolve({ data }), delay)
    })
  )
}

export const mockErrorResponse = (message = 'API Error', status = 500, delay = 100) => {
  return vi.fn().mockImplementation(() =>
    new Promise((_, reject) => {
      setTimeout(() => reject({
        response: {
          status,
          data: { message },
        },
      }), delay)
    })
  )
}

export const mockPaginatedResponse = <T>(
  items: T[],
  page = 1,
  size = 10
) => {
  const start = (page - 1) * size
  const end = start + size
  const paginatedItems = items.slice(start, end)

  return {
    items: paginatedItems,
    total: items.length,
    page,
    size,
    pages: Math.ceil(items.length / size),
  }
}

// ============================================================================
// Store Mocks
// ============================================================================

export const createMockAuthStore = (overrides = {}) => ({
  user: createMockUser(),
  token: 'mock-jwt-token',
  isAuthenticated: true,
  loading: false,
  error: null,
  login: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn(),
  register: vi.fn().mockResolvedValue(undefined),
  refreshToken: vi.fn().mockResolvedValue(undefined),
  updateProfile: vi.fn().mockResolvedValue(undefined),
  ...overrides,
})

export const createMockMediaStore = (overrides = {}) => ({
  files: createMockMediaFilesResponse().items,
  selectedFile: null,
  loading: false,
  error: null,
  filters: {
    search: '',
    type: 'all',
    status: 'all',
    tags: [],
  },
  sortBy: 'created_at',
  sortOrder: 'desc',
  fetchFiles: vi.fn().mockResolvedValue(undefined),
  selectFile: vi.fn(),
  updateFilters: vi.fn(),
  deleteFile: vi.fn().mockResolvedValue(undefined),
  updateFile: vi.fn().mockResolvedValue(undefined),
  ...overrides,
})

export const createMockUploadStore = (overrides = {}) => ({
  uploads: [],
  activeUploads: 0,
  totalProgress: 0,
  addUpload: vi.fn(),
  updateProgress: vi.fn(),
  completeUpload: vi.fn(),
  failUpload: vi.fn(),
  removeUpload: vi.fn(),
  clearCompleted: vi.fn(),
  ...overrides,
})

// ============================================================================
// WebSocket Mocks
// ============================================================================

export class MockWebSocket {
  url: string
  readyState: number = WebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 100)
  }

  send(data: string) {
    // Mock send implementation
  }

  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }
}

// ============================================================================
// Browser API Mocks
// ============================================================================

export const mockFileReader = () => {
  const FileReaderMock = vi.fn(() => ({
    readAsDataURL: vi.fn(),
    readAsText: vi.fn(),
    readAsArrayBuffer: vi.fn(),
    result: 'data:image/png;base64,mock-data',
    onload: null,
    onerror: null,
  }))

  Object.defineProperty(window, 'FileReader', {
    writable: true,
    value: FileReaderMock,
  })

  return FileReaderMock
}

export const mockNotificationAPI = () => {
  const NotificationMock = vi.fn()
  NotificationMock.permission = 'granted'
  NotificationMock.requestPermission = vi.fn().mockResolvedValue('granted')

  Object.defineProperty(window, 'Notification', {
    writable: true,
    value: NotificationMock,
  })

  return NotificationMock
}

// Re-export all types from individual files
export * from './media'
export * from './catalog'

// Common types used across the application
export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  created_at: string
  last_login?: string
  preferences?: UserPreferences
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  notifications: NotificationPreferences
}

export interface NotificationPreferences {
  email: boolean
  browser: boolean
  processing_complete: boolean
  upload_complete: boolean
}

export interface AnalyticsData {
  total_files: number
  total_size: number
  total_duration: number
  file_types: Record<string, number>
  processing_stats: ProcessingStats
  storage_trend: StorageTrendData[]
  upload_trend: UploadTrendData[]
  popular_tags: TagCount[]
}

export interface ProcessingStats {
  completed: number
  processing: number
  failed: number
  pending: number
}

export interface StorageTrendData {
  date: string
  size: number
}

export interface UploadTrendData {
  date: string
  count: number
}

export interface TagCount {
  tag: string
  count: number
}

export interface ProcessingJob {
  id: string
  file_id: string
  type: 'transcode' | 'analyze' | 'thumbnail' | 'extract_metadata'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  started_at?: string
  completed_at?: string
  eta?: string
  error?: string
  worker_id?: string
  priority: 'low' | 'normal' | 'high'
  attempts: number
  result?: any
}

export interface UploadProgress {
  id: string
  filename: string
  size: number
  uploaded: number
  progress: number
  speed: number
  eta: number
  status: 'preparing' | 'uploading' | 'completed' | 'failed' | 'cancelled'
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ApiError {
  message: string
  code?: string
  details?: Record<string, any>
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface SearchFilters {
  search?: string
  type?: string
  status?: string
  tags?: string[]
  date_from?: string
  date_to?: string
  size_min?: number
  size_max?: number
}

export interface SortOptions {
  field: 'created_at' | 'updated_at' | 'filename' | 'file_size' | 'duration'
  order: 'asc' | 'desc'
}

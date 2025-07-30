export interface MediaFile {
  id: string
  filename: string
  file_path: string
  file_size: number
  media_type: string
  status: string
  created_at: string
  updated_at: string
  analyzed_at?: string
  catalog_id?: string
  processing_status?: string // Optional for backward compatibility
}

export interface MediaFilesResponse {
  items: MediaFile[]
  total: number
  page: number
  size: number
}

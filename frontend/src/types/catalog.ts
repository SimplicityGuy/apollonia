export interface Catalog {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  media_count: number
  file_count?: number // Optional for backward compatibility
}

export interface CatalogResponse {
  items: Catalog[]
  total: number
  page: number
  size: number
}

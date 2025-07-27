/**
 * Format bytes into human readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ${hours % 24}h`
  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`
  return `${seconds}s`
}

/**
 * Truncate text to specified length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Format file name for display
 */
export function formatFileName(fileName: string, maxLength = 30): string {
  if (fileName.length <= maxLength) return fileName

  const ext = fileName.split('.').pop()
  const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')

  if (!ext || ext === fileName) {
    // No extension
    return nameWithoutExt.substring(0, maxLength - 3) + '...'
  }

  // With extension: leave room for "..." + extension
  const availableLength = maxLength - ext.length - 3
  const truncatedName = nameWithoutExt.substring(0, availableLength)
  return `${truncatedName}...${ext}`
}

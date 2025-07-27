/**
 * Format bytes into human readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const isNegative = bytes < 0
  const absBytes = Math.abs(bytes)

  const i = Math.floor(Math.log(absBytes) / Math.log(k))

  const result = parseFloat((absBytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
  return isNegative ? '-' + result : result
}

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(ms: number): string {
  const isNegative = ms < 0
  const absMs = Math.abs(ms)

  const seconds = Math.floor(absMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  let result: string
  if (days > 0) {
    const h = hours % 24
    result = h > 0 ? `${days}d ${h}h` : `${days}d`
  } else if (hours > 0) {
    const m = minutes % 60
    result = m > 0 ? `${hours}h ${m}m` : `${hours}h`
  } else if (minutes > 0) {
    const s = seconds % 60
    result = s > 0 ? `${minutes}m ${s}s` : `${minutes}m`
  } else {
    result = `${seconds}s`
  }

  return isNegative ? '-' + result : result
}

/**
 * Truncate text to specified length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  if (maxLength <= 0) return '...'
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Format file name for display
 */
export function formatFileName(fileName: string, maxLength = 50): string {
  if (!fileName) return ''
  if (fileName.length <= maxLength) return fileName

  const lastDotIndex = fileName.lastIndexOf('.')
  const hasExtension = lastDotIndex > 0 && lastDotIndex < fileName.length - 1

  if (!hasExtension) {
    // No extension
    return fileName.substring(0, maxLength - 3) + '...'
  }

  const ext = fileName.substring(lastDotIndex + 1)
  const nameWithoutExt = fileName.substring(0, lastDotIndex)

  // If extension is too long, just truncate the whole thing
  if (ext.length + 3 >= maxLength) {
    return '...' + fileName.substring(fileName.length - (maxLength - 3))
  }

  // With extension: leave room for "..." + extension
  const availableLength = maxLength - ext.length - 3
  const truncatedName = nameWithoutExt.substring(0, availableLength)
  return `${truncatedName}...${ext}`
}

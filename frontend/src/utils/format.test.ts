import { describe, it, expect } from 'vitest'
import { formatBytes, formatDuration, truncateText, formatFileName } from './format'

describe('formatBytes', () => {
  it('formats bytes correctly', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(1048576)).toBe('1 MB')
    expect(formatBytes(1073741824)).toBe('1 GB')
  })

  it('handles decimal places', () => {
    expect(formatBytes(1536, 0)).toBe('2 KB')
    expect(formatBytes(1536, 1)).toBe('1.5 KB')
    expect(formatBytes(1536, 3)).toBe('1.5 KB') // parseFloat removes trailing zeros
  })
})

describe('formatDuration', () => {
  it('formats duration correctly', () => {
    expect(formatDuration(1000)).toBe('1s')
    expect(formatDuration(61000)).toBe('1m 1s')
    expect(formatDuration(3661000)).toBe('1h 1m')
    expect(formatDuration(90061000)).toBe('1d 1h')
  })

  it('handles edge cases', () => {
    expect(formatDuration(0)).toBe('0s')
    expect(formatDuration(999)).toBe('0s')
  })
})

describe('truncateText', () => {
  it('truncates text correctly', () => {
    expect(truncateText('Hello world', 5)).toBe('Hello...')
    expect(truncateText('Short', 10)).toBe('Short')
    expect(truncateText('', 5)).toBe('')
  })
})

describe('formatFileName', () => {
  it('formats file names correctly', () => {
    expect(formatFileName('short.txt')).toBe('short.txt')
    // maxLength(20) - ext.length(3) - 3 = 14 chars for name
    expect(formatFileName('very-long-file-name-that-should-be-truncated.txt', 20)).toBe(
      'very-long-file...txt'
    )
    expect(formatFileName('file-without-extension-that-is-very-long', 20)).toBe(
      'file-without-exte...'
    )
  })

  it('handles edge cases', () => {
    expect(formatFileName('')).toBe('')
    expect(formatFileName('a.txt')).toBe('a.txt')
  })
})

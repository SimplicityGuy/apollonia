import { describe, it, expect } from 'vitest'
import { formatBytes, formatDuration, truncateText, formatFileName } from './format'

describe('formatBytes', () => {
  it('formats bytes correctly', () => {
    expect(formatBytes(0)).toBe('0 Bytes')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(1048576)).toBe('1 MB')
    expect(formatBytes(1073741824)).toBe('1 GB')
    expect(formatBytes(1099511627776)).toBe('1 TB')
    expect(formatBytes(1125899906842624)).toBe('1 PB')
  })

  it('handles decimal places', () => {
    expect(formatBytes(1536, 0)).toBe('2 KB')
    expect(formatBytes(1536, 1)).toBe('1.5 KB')
    expect(formatBytes(1536, 3)).toBe('1.5 KB') // parseFloat removes trailing zeros
    expect(formatBytes(1234567, 2)).toBe('1.18 MB')
    expect(formatBytes(1234567890, 3)).toBe('1.15 GB')
  })

  it('handles negative numbers', () => {
    expect(formatBytes(-1024)).toBe('-1 KB')
    expect(formatBytes(-1536)).toBe('-1.5 KB')
  })

  it('handles very small numbers', () => {
    expect(formatBytes(1)).toBe('1 Bytes')
    expect(formatBytes(10)).toBe('10 Bytes')
    expect(formatBytes(100)).toBe('100 Bytes')
    expect(formatBytes(1023)).toBe('1023 Bytes')
  })

  it('handles very large numbers', () => {
    expect(formatBytes(Number.MAX_SAFE_INTEGER)).toMatch(/PB$/)
  })

  it('uses default decimal places of 2', () => {
    expect(formatBytes(1536)).toBe('1.5 KB')
    expect(formatBytes(1234567)).toBe('1.18 MB')
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
    expect(formatDuration(500)).toBe('0s')
  })

  it('handles complex durations', () => {
    expect(formatDuration(59000)).toBe('59s')
    expect(formatDuration(60000)).toBe('1m')
    expect(formatDuration(3600000)).toBe('1h')
    expect(formatDuration(86400000)).toBe('1d')
    expect(formatDuration(90000000)).toBe('1d 1h')
    expect(formatDuration(93784000)).toBe('1d 2h')
  })

  it('handles multiple units', () => {
    expect(formatDuration(3723000)).toBe('1h 2m') // 1h 2m 3s -> shows only 2 largest
    expect(formatDuration(90123000)).toBe('1d 1h') // 1d 1h 2m 3s -> shows only 2 largest
    expect(formatDuration(123000)).toBe('2m 3s')
  })

  it('handles negative durations', () => {
    expect(formatDuration(-1000)).toBe('-1s')
    expect(formatDuration(-61000)).toBe('-1m 1s')
  })

  it('rounds down to seconds', () => {
    expect(formatDuration(1999)).toBe('1s')
    expect(formatDuration(2000)).toBe('2s')
  })
})

describe('truncateText', () => {
  it('truncates text correctly', () => {
    expect(truncateText('Hello world', 5)).toBe('Hello...')
    expect(truncateText('Short', 10)).toBe('Short')
    expect(truncateText('', 5)).toBe('')
  })

  it('handles exact length', () => {
    expect(truncateText('Hello', 5)).toBe('Hello')
    expect(truncateText('Test', 4)).toBe('Test')
  })

  it('handles very short maxLength', () => {
    expect(truncateText('Hello', 1)).toBe('H...')
    expect(truncateText('Hello', 2)).toBe('He...')
    expect(truncateText('Hello', 3)).toBe('Hel...')
  })

  it('handles unicode characters', () => {
    expect(truncateText('Hello 👋 World', 7)).toBe('Hello 👋...')
    expect(truncateText('测试文本很长', 3)).toBe('测试文...')
  })

  it('handles null or undefined gracefully', () => {
    expect(truncateText(null as any, 5)).toBe('')
    expect(truncateText(undefined as any, 5)).toBe('')
  })

  it('handles zero or negative maxLength', () => {
    expect(truncateText('Hello', 0)).toBe('...')
    expect(truncateText('Hello', -1)).toBe('...')
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
    expect(formatFileName('.hidden')).toBe('.hidden')
    expect(formatFileName('.')).toBe('.')
  })

  it('handles multiple dots in filename', () => {
    expect(formatFileName('file.name.with.dots.txt', 20)).toBe('file.name.with...txt')
    expect(formatFileName('archive.tar.gz', 15)).toBe('archive.tar.gz') // fits within limit
    expect(formatFileName('very.long.archive.name.tar.gz', 20)).toBe('very.long.arch...gz')
  })

  it('handles files without extensions', () => {
    expect(formatFileName('README')).toBe('README')
    expect(formatFileName('very-long-readme-file-without-extension', 15)).toBe('very-long-re...')
  })

  it('handles very long extensions', () => {
    expect(formatFileName('file.verylongextension', 15)).toBe('fi...xtension')
    expect(formatFileName('a.verylongextension', 10)).toBe('a...nsion')
  })

  it('uses default maxLength of 50', () => {
    const longName = 'a'.repeat(60) + '.txt'
    const result = formatFileName(longName)
    expect(result).toHaveLength(50)
    expect(result).toMatch(/^a+\.\.\.txt$/)
  })

  it('handles special characters in filenames', () => {
    expect(formatFileName('file name with spaces.txt', 20)).toBe('file name with...txt')
    expect(formatFileName('file-with-dashes.txt', 20)).toBe('file-with-dash...txt')
    expect(formatFileName('file_with_underscores.txt', 25)).toBe('file_with_underscor...txt')
  })

  it('handles unicode filenames', () => {
    expect(formatFileName('很长的中文文件名.txt', 15)).toBe('很长的中文文...txt')
    expect(formatFileName('файл.документ', 10)).toBe('файл...нт')
  })

  it('handles edge case where maxLength is less than extension length', () => {
    expect(formatFileName('file.txt', 3)).toBe('...')
    expect(formatFileName('test.jpeg', 5)).toBe('...eg')
  })
})

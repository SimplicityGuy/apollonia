import { expect } from 'vitest'

// Extend Vitest's expect with custom matchers
declare module 'vitest' {
  interface Assertion<T = any> {
    toBeDisabledButton(): T
    toHaveAriaLabel(label: string): T
    toHaveTextContentTrimmed(text: string): T
    toBeAccessibleForm(): T
    toHaveValidationError(message: string): T
    toBeVisibleInViewport(): T
    toHaveNoAxeViolations(): T
  }
}

// Custom matcher to check if a button is properly disabled
expect.extend({
  toBeDisabledButton(received: HTMLElement) {
    const pass =
      received.tagName === 'BUTTON' &&
      (received.hasAttribute('disabled') || received.getAttribute('aria-disabled') === 'true')

    return {
      pass,
      message: () =>
        pass ? `expected button not to be disabled` : `expected button to be disabled`,
      actual: received,
    }
  },
})

// Custom matcher for aria-label
expect.extend({
  toHaveAriaLabel(received: HTMLElement, label: string) {
    const actualLabel = received.getAttribute('aria-label')
    const pass = actualLabel === label

    return {
      pass,
      message: () =>
        pass
          ? `expected element not to have aria-label "${label}"`
          : `expected element to have aria-label "${label}", but got "${actualLabel}"`,
      actual: actualLabel,
      expected: label,
    }
  },
})

// Custom matcher for trimmed text content
expect.extend({
  toHaveTextContentTrimmed(received: HTMLElement, text: string) {
    const actualText = received.textContent?.trim() || ''
    const pass = actualText === text

    return {
      pass,
      message: () =>
        pass
          ? `expected element not to have text content "${text}"`
          : `expected element to have text content "${text}", but got "${actualText}"`,
      actual: actualText,
      expected: text,
    }
  },
})

// Custom matcher for accessible forms
expect.extend({
  toBeAccessibleForm(received: HTMLFormElement) {
    const issues: string[] = []

    // Check all inputs have labels
    const inputs = received.querySelectorAll('input, select, textarea')
    inputs.forEach((input) => {
      if (!input.id) {
        issues.push(`Input of type "${input.getAttribute('type')}" has no id`)
        return
      }

      const label = received.querySelector(`label[for="${input.id}"]`)
      if (!label && !input.getAttribute('aria-label')) {
        issues.push(`Input with id "${input.id}" has no label or aria-label`)
      }
    })

    // Check required fields have required attribute or aria-required
    const requiredFields = received.querySelectorAll('[aria-required="true"], [required]')
    if (requiredFields.length === 0) {
      issues.push('Form has no fields marked as required')
    }

    // Check submit button exists
    const submitButton = received.querySelector(
      'button[type="submit"], button:not([type="button"])'
    )
    if (!submitButton) {
      issues.push('Form has no submit button')
    }

    const pass = issues.length === 0

    return {
      pass,
      message: () =>
        pass
          ? 'expected form not to be accessible'
          : `expected form to be accessible, but found issues:\n${issues.join('\n')}`,
      actual: received,
    }
  },
})

// Custom matcher for validation errors
expect.extend({
  toHaveValidationError(received: HTMLElement, message: string) {
    // Check for aria-invalid
    const isInvalid = received.getAttribute('aria-invalid') === 'true'

    // Check for error message
    const errorId = received.getAttribute('aria-describedby')
    let errorElement: HTMLElement | null = null
    let errorText = ''

    if (errorId) {
      errorElement = document.getElementById(errorId)
      errorText = errorElement?.textContent || ''
    }

    const pass = isInvalid && errorText.includes(message)

    return {
      pass,
      message: () =>
        pass
          ? `expected element not to have validation error "${message}"`
          : `expected element to have validation error "${message}", but got "${errorText}"`,
      actual: errorText,
      expected: message,
    }
  },
})

// Custom matcher to check if element is visible in viewport
expect.extend({
  toBeVisibleInViewport(received: HTMLElement) {
    const rect = received.getBoundingClientRect()
    const isVisible =
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth) &&
      rect.width > 0 &&
      rect.height > 0

    return {
      pass: isVisible,
      message: () =>
        isVisible
          ? 'expected element not to be visible in viewport'
          : 'expected element to be visible in viewport',
      actual: received,
    }
  },
})

// Placeholder for axe-core integration (requires additional setup)
expect.extend({
  async toHaveNoAxeViolations(received: HTMLElement) {
    // This would require axe-core to be installed and configured
    // For now, we'll do basic accessibility checks
    const issues: string[] = []

    // Check images have alt text
    const images = received.querySelectorAll('img')
    images.forEach((img) => {
      if (!img.hasAttribute('alt')) {
        issues.push(`Image with src "${img.src}" has no alt text`)
      }
    })

    // Check headings are in order
    const headings = received.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let lastLevel = 0
    headings.forEach((heading) => {
      const level = parseInt(heading.tagName[1])
      if (level > lastLevel + 1) {
        issues.push(`Heading level jumped from h${lastLevel} to h${level}`)
      }
      lastLevel = level
    })

    const pass = issues.length === 0

    return {
      pass,
      message: () =>
        pass
          ? 'expected element to have accessibility violations'
          : `expected element to have no accessibility violations, but found:\n${issues.join('\n')}`,
      actual: received,
    }
  },
})

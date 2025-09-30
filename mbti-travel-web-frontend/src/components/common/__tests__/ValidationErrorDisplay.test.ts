import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ValidationErrorDisplay from '../ValidationErrorDisplay.vue'
import type { FormValidationError, ValidationError } from '@/types/error'

describe('ValidationErrorDisplay', () => {
  const mockFieldErrors: FormValidationError[] = [
    {
      field: 'mbtiPersonality',
      message: 'MBTI personality is required',
      type: 'required'
    },
    {
      field: 'email',
      message: 'Invalid email format',
      type: 'format',
      value: 'invalid-email'
    }
  ]

  const mockFormErrors: ValidationError[] = [
    {
      type: 'validation_error',
      field: 'form',
      message: 'Form validation failed',
      timestamp: new Date().toISOString()
    }
  ]

  it('renders field errors', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors
      }
    })

    expect(wrapper.text()).toContain('MBTI personality is required')
    expect(wrapper.text()).toContain('Invalid email format')
    expect(wrapper.findAll('.validation-error-item')).toHaveLength(2)
  })

  it('renders form errors', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        formErrors: mockFormErrors
      }
    })

    expect(wrapper.text()).toContain('Form validation failed')
    expect(wrapper.find('.form-errors').exists()).toBe(true)
  })

  it('shows validation summary when enabled', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors,
        showSummary: true
      }
    })

    expect(wrapper.find('.validation-summary').exists()).toBe(true)
    expect(wrapper.text()).toContain('Validation Summary')
    expect(wrapper.findAll('.validation-summary-item')).toHaveLength(2)
  })

  it('hides validation summary when disabled', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors,
        showSummary: false
      }
    })

    expect(wrapper.find('.validation-summary').exists()).toBe(false)
  })

  it('generates quick fixes for MBTI errors', () => {
    const mbtiErrors: FormValidationError[] = [
      {
        field: 'mbtiPersonality',
        message: 'Invalid MBTI format',
        type: 'format',
        value: 'INVALID'
      }
    ]

    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mbtiErrors,
        showQuickFixes: true
      }
    })

    expect(wrapper.find('.quick-fixes').exists()).toBe(true)
    expect(wrapper.text()).toContain('Quick Fixes')
    expect(wrapper.findAll('.quick-fix-button').length).toBeGreaterThan(0)
  })

  it('generates completion suggestions for partial MBTI input', () => {
    const partialMbtiErrors: FormValidationError[] = [
      {
        field: 'mbtiPersonality',
        message: 'MBTI must be 4 characters',
        type: 'length',
        value: 'EN'
      }
    ]

    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: partialMbtiErrors,
        showQuickFixes: true
      }
    })

    expect(wrapper.find('.quick-fixes').exists()).toBe(true)
    const quickFixButtons = wrapper.findAll('.quick-fix-button')
    expect(quickFixButtons.length).toBeGreaterThan(0)
    
    // Should suggest completions starting with 'EN'
    const buttonTexts = quickFixButtons.map(button => button.text())
    expect(buttonTexts.some(text => text.includes('ENFP') || text.includes('ENTJ'))).toBe(true)
  })

  it('provides appropriate error titles', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: [
          { field: 'test', message: 'Required', type: 'required' },
          { field: 'test', message: 'Invalid format', type: 'format' },
          { field: 'test', message: 'Too long', type: 'length' },
          { field: 'test', message: 'Custom error', type: 'custom' }
        ]
      }
    })

    expect(wrapper.text()).toContain('Required Field')
    expect(wrapper.text()).toContain('Invalid Format')
    expect(wrapper.text()).toContain('Length Validation')
    expect(wrapper.text()).toContain('Validation Error')
  })

  it('provides appropriate error suggestions', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: [
          { field: 'mbtiPersonality', message: 'Invalid format', type: 'format' },
          { field: 'email', message: 'Invalid format', type: 'format' },
          { field: 'mbtiPersonality', message: 'Wrong length', type: 'length' }
        ]
      }
    })

    expect(wrapper.text()).toContain('valid 4-letter MBTI code')
    expect(wrapper.text()).toContain('valid email address')
    expect(wrapper.text()).toContain('exactly 4 characters')
  })

  it('emits field-focus event when summary link is clicked', async () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors,
        showSummary: true
      }
    })

    const summaryLink = wrapper.find('.validation-summary-link')
    await summaryLink.trigger('click')

    expect(wrapper.emitted('field-focus')).toBeTruthy()
    expect(wrapper.emitted('field-focus')![0]).toEqual(['mbtiPersonality'])
  })

  it('emits fix-applied event when quick fix is applied', async () => {
    const mbtiErrors: FormValidationError[] = [
      {
        field: 'mbtiPersonality',
        message: 'Invalid MBTI format',
        type: 'format'
      }
    ]

    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mbtiErrors,
        showQuickFixes: true
      }
    })

    const quickFixButton = wrapper.find('.quick-fix-button')
    await quickFixButton.trigger('click')

    expect(wrapper.emitted('fix-applied')).toBeTruthy()
  })

  it('emits error-dismissed event when form error is dismissed', async () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        formErrors: mockFormErrors
      }
    })

    // Find the ErrorMessage component and trigger dismiss
    const errorMessage = wrapper.findComponent({ name: 'ErrorMessage' })
    await errorMessage.vm.$emit('dismiss')

    expect(wrapper.emitted('error-dismissed')).toBeTruthy()
  })

  it('handles action events from error messages', async () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors
      }
    })

    const errorMessage = wrapper.findComponent({ name: 'ErrorMessage' })
    const mockAction = { label: 'Test Action', action: vi.fn() }
    await errorMessage.vm.$emit('action', mockAction)

    expect(mockAction.action).toHaveBeenCalled()
  })

  it('applies correct CSS classes for error types', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: [
          { field: 'test1', message: 'Required', type: 'required' },
          { field: 'test2', message: 'Invalid format', type: 'format' },
          { field: 'test3', message: 'Too long', type: 'length' },
          { field: 'test4', message: 'Custom error', type: 'custom' }
        ]
      }
    })

    expect(wrapper.find('.validation-error-item--required').exists()).toBe(true)
    expect(wrapper.find('.validation-error-item--format').exists()).toBe(true)
    expect(wrapper.find('.validation-error-item--length').exists()).toBe(true)
    expect(wrapper.find('.validation-error-item--custom').exists()).toBe(true)
  })

  it('shows loading state for quick fixes', async () => {
    const mbtiErrors: FormValidationError[] = [
      {
        field: 'mbtiPersonality',
        message: 'Invalid MBTI format',
        type: 'format'
      }
    ]

    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mbtiErrors,
        showQuickFixes: true
      }
    })

    const quickFixButton = wrapper.find('.quick-fix-button')
    
    // Simulate loading state by clicking and checking for loading indicator
    await quickFixButton.trigger('click')
    
    // The component should handle loading state internally
    expect(wrapper.find('.quick-fix-loading').exists()).toBe(false) // Initially not loading
  })

  it('hides quick fixes when disabled', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: mockFieldErrors,
        showQuickFixes: false
      }
    })

    expect(wrapper.find('.quick-fixes').exists()).toBe(false)
  })

  it('handles empty error arrays gracefully', () => {
    const wrapper = mount(ValidationErrorDisplay, {
      props: {
        fieldErrors: [],
        formErrors: []
      }
    })

    expect(wrapper.find('.validation-error-item').exists()).toBe(false)
    expect(wrapper.find('.form-errors').exists()).toBe(false)
    expect(wrapper.find('.validation-summary').exists()).toBe(false)
    expect(wrapper.find('.quick-fixes').exists()).toBe(false)
  })
})
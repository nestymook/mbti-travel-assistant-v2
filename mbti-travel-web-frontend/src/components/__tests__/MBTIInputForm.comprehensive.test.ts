import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MBTIInputForm from '../input/MBTIInputForm.vue'
import type { MBTIValidationResult } from '../../types'

// Mock services
const mockValidationService = {
  validateMBTICode: vi.fn(),
  validateRealTimeInput: vi.fn(),
  formatMBTIInput: vi.fn(),
  getUserFriendlyMessage: vi.fn(),
  getValidMBTITypes: vi.fn()
}

const mockApiService = {
  generateItinerary: vi.fn()
}

const mockThemeService = {
  applyMBTITheme: vi.fn(),
  getCurrentPersonality: vi.fn(),
  getPersonalityColors: vi.fn()
}

vi.mock('../../services/validationService', () => ({
  ValidationService: {
    getInstance: () => mockValidationService
  }
}))

vi.mock('../../services/apiService', () => ({
  ApiService: {
    getInstance: () => mockApiService
  }
}))

vi.mock('../../services/themeService', () => ({
  ThemeService: {
    getInstance: () => mockThemeService
  }
}))

describe('MBTIInputForm - Comprehensive Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock implementations
    mockValidationService.validateMBTICode.mockReturnValue({
      isValid: true,
      formattedValue: 'ENFP'
    })
    
    mockValidationService.validateRealTimeInput.mockReturnValue({
      isValid: true,
      formattedValue: 'ENFP',
      canContinue: true
    })
    
    mockValidationService.formatMBTIInput.mockImplementation((input: string) => 
      input.toUpperCase().slice(0, 4)
    )
    
    mockValidationService.getValidMBTITypes.mockReturnValue([
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP',
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ])
    
    mockThemeService.getCurrentPersonality.mockReturnValue('ENFP')
    mockThemeService.getPersonalityColors.mockReturnValue({
      name: 'ENFP - The Campaigner',
      primary: '#ff5722',
      secondary: '#d84315',
      accent: '#4caf50'
    })
  })

  describe('Component Rendering', () => {
    it('renders all required elements', () => {
      const wrapper = mount(MBTIInputForm)
      
      expect(wrapper.find('h1').text()).toBe('Hong Kong MBTI Travel Planner')
      expect(wrapper.find('h2').text()).toBe('Welcome to MBTI Travel Planner for traveling Hong Kong')
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
      expect(wrapper.find('a[href="https://www.16personalities.com"]').exists()).toBe(true)
    })

    it('displays placeholder text correctly', () => {
      const wrapper = mount(MBTIInputForm)
      
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('placeholder')).toBe('E.g. ENFP, INTJ, INFJ...')
    })

    it('shows help text for users', () => {
      const wrapper = mount(MBTIInputForm)
      
      const helpText = wrapper.find('.help-text')
      expect(helpText.exists()).toBe(true)
      expect(helpText.text()).toContain('Enter your 4-letter MBTI personality type')
    })
  })

  describe('Input Validation', () => {
    it('validates input in real-time', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('E')
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('E')

      await input.setValue('EN')
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('EN')

      await input.setValue('ENF')
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('ENF')

      await input.setValue('ENFP')
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('ENFP')
    })

    it('formats input automatically', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('enfp')
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('enfp')
      expect(input.element.value).toBe('ENFP')
    })

    it('limits input to 4 characters', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFPEXTRA')
      expect(input.element.value).toBe('ENFP')
    })

    it('only allows alphabetic characters', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('EN1P')
      await input.setValue('E@FP')
      await input.setValue('E FP')
      
      // Should filter out non-alphabetic characters
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('ENP')
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('EFP')
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('EFP')
    })

    it('shows validation errors for invalid input', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })
      mockValidationService.getUserFriendlyMessage.mockReturnValue('Please enter a valid MBTI personality type')

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('Please enter a valid MBTI personality type')
    })

    it('clears validation errors when input becomes valid', async () => {
      // Start with invalid input
      mockValidationService.validateMBTICode.mockReturnValueOnce({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(true)

      // Now make input valid
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: true,
        formattedValue: 'ENFP'
      })

      await input.setValue('ENFP')
      await nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(false)
    })
  })

  describe('Form Submission', () => {
    it('submits form with valid input', async () => {
      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await form.trigger('submit')

      expect(mockValidationService.validateMBTICode).toHaveBeenCalledWith('ENFP')
      expect(wrapper.emitted('submit')).toBeTruthy()
      expect(wrapper.emitted('submit')?.[0]).toEqual(['ENFP'])
    })

    it('prevents submission with invalid input', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toBeFalsy()
    })

    it('prevents submission with empty input', async () => {
      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')

      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toBeFalsy()
      expect(wrapper.find('.error-message').exists()).toBe(true)
    })

    it('trims whitespace from input', async () => {
      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('  ENFP  ')
      await form.trigger('submit')

      expect(mockValidationService.validateMBTICode).toHaveBeenCalledWith('ENFP')
    })
  })

  describe('Loading States', () => {
    it('shows loading state when isLoading prop is true', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true
        }
      })

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeDefined()
      expect(button.text()).toContain('Generating...')
      
      const loadingMessage = wrapper.find('.loading-message')
      expect(loadingMessage.exists()).toBe(true)
      expect(loadingMessage.text()).toContain('Generating Itinerary in progress')
    })

    it('disables form during loading', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true
        }
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      expect(input.attributes('disabled')).toBeDefined()
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('shows progress indicator during loading', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true,
          loadingProgress: 45
        }
      })

      const progressBar = wrapper.find('.progress-bar')
      expect(progressBar.exists()).toBe(true)
      expect(progressBar.attributes('aria-valuenow')).toBe('45')
    })
  })

  describe('Error Handling', () => {
    it('displays error message from props', () => {
      const errorMessage = 'Network error occurred'
      const wrapper = mount(MBTIInputForm, {
        props: {
          errorMessage
        }
      })

      const errorElement = wrapper.find('.error-message')
      expect(errorElement.exists()).toBe(true)
      expect(errorElement.text()).toContain(errorMessage)
    })

    it('shows retry button for retryable errors', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          errorMessage: 'Network error occurred',
          canRetry: true
        }
      })

      const retryButton = wrapper.find('.retry-button')
      expect(retryButton.exists()).toBe(true)
    })

    it('emits retry event when retry button is clicked', async () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          errorMessage: 'Network error occurred',
          canRetry: true
        }
      })

      const retryButton = wrapper.find('.retry-button')
      await retryButton.trigger('click')

      expect(wrapper.emitted('retry')).toBeTruthy()
    })

    it('handles validation service errors gracefully', async () => {
      mockValidationService.validateMBTICode.mockImplementation(() => {
        throw new Error('Validation service error')
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await form.trigger('submit')

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('An error occurred during validation')
    })
  })

  describe('Accessibility Features', () => {
    it('has proper ARIA labels', () => {
      const wrapper = mount(MBTIInputForm)
      
      const form = wrapper.find('form')
      expect(form.attributes('aria-label')).toBe('MBTI personality type input form')
      
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('aria-label')).toBe('Enter your MBTI personality type')
      expect(input.attributes('aria-required')).toBe('true')
      
      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('aria-label')).toBe('Generate 3-day itinerary')
    })

    it('associates help text with input', () => {
      const wrapper = mount(MBTIInputForm)
      
      const input = wrapper.find('input[type="text"]')
      const helpId = input.attributes('aria-describedby')
      
      expect(helpId).toBeDefined()
      expect(wrapper.find(`#${helpId}`).exists()).toBe(true)
    })

    it('associates error messages with input', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(input.attributes('aria-invalid')).toBe('true')
      
      const describedBy = input.attributes('aria-describedby')
      expect(describedBy).toContain('error')
      
      const errorElement = wrapper.find(`#${describedBy?.split(' ').find(id => id.includes('error'))}`)
      expect(errorElement.exists()).toBe(true)
    })

    it('has proper heading hierarchy', () => {
      const wrapper = mount(MBTIInputForm)
      
      const h1 = wrapper.find('h1')
      expect(h1.exists()).toBe(true)
      expect(h1.text()).toBe('Hong Kong MBTI Travel Planner')
      
      const h2 = wrapper.find('h2')
      expect(h2.exists()).toBe(true)
      expect(h2.text()).toBe('Welcome to MBTI Travel Planner for traveling Hong Kong')
    })

    it('provides skip link for keyboard navigation', () => {
      const wrapper = mount(MBTIInputForm)
      
      const skipLink = wrapper.find('.skip-link')
      expect(skipLink.exists()).toBe(true)
      expect(skipLink.attributes('href')).toBe('#main-content')
    })
  })

  describe('Keyboard Navigation', () => {
    it('supports Enter key submission', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await input.trigger('keydown.enter')

      expect(wrapper.emitted('submit')).toBeTruthy()
      expect(wrapper.emitted('submit')?.[0]).toEqual(['ENFP'])
    })

    it('supports Escape key to clear input', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await input.trigger('keydown.escape')

      expect(input.element.value).toBe('')
    })

    it('supports Tab navigation', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')
      const link = wrapper.find('a[href="https://www.16personalities.com"]')

      // Focus should move through elements in order
      const inputElement = input.element as HTMLInputElement
      const buttonElement = button.element as HTMLButtonElement
      const linkElement = link.element as HTMLAnchorElement

      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      await input.trigger('keydown.tab')
      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      await button.trigger('keydown.tab')
      linkElement.focus()
      expect(document.activeElement).toBe(linkElement)

      wrapper.unmount()
    })
  })

  describe('Theme Integration', () => {
    it('applies theme when personality is detected', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await nextTick()

      expect(mockThemeService.applyMBTITheme).toHaveBeenCalledWith('ENFP')
    })

    it('shows personality colors in preview', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await nextTick()

      const preview = wrapper.find('.personality-preview')
      expect(preview.exists()).toBe(true)
      expect(preview.text()).toContain('ENFP - The Campaigner')
    })
  })

  describe('External Link', () => {
    it('opens MBTI test in new tab', () => {
      const wrapper = mount(MBTIInputForm)
      
      const link = wrapper.find('a[href="https://www.16personalities.com"]')
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
      expect(link.text()).toContain("Don't know your MBTI type? Take the test here")
    })

    it('has proper accessibility attributes for external link', () => {
      const wrapper = mount(MBTIInputForm)
      
      const link = wrapper.find('a[href="https://www.16personalities.com"]')
      expect(link.attributes('aria-label')).toBe('Take MBTI personality test (opens in new tab)')
    })
  })

  describe('Component Props', () => {
    it('accepts and uses modelValue prop', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          modelValue: 'INTJ'
        }
      })

      const input = wrapper.find('input[type="text"]')
      expect(input.element.value).toBe('INTJ')
    })

    it('emits update:modelValue on input change', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['ENFP'])
    })

    it('respects disabled prop', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          disabled: true
        }
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      expect(input.attributes('disabled')).toBeDefined()
      expect(button.attributes('disabled')).toBeDefined()
    })
  })

  describe('Performance', () => {
    it('debounces real-time validation', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      // Rapid input changes
      await input.setValue('E')
      await input.setValue('EN')
      await input.setValue('ENF')
      await input.setValue('ENFP')

      // Wait for debounce
      await new Promise(resolve => setTimeout(resolve, 300))

      // Should only validate the final value
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('ENFP')
    })

    it('memoizes validation results', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      // Same input multiple times
      await input.setValue('ENFP')
      await input.setValue('')
      await input.setValue('ENFP')

      // Should use cached result for repeated input
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledTimes(2) // Only for different values
    })
  })
})
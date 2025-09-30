import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MBTIInputForm from '../MBTIInputForm.vue'

// Mock the validation service
const mockValidationService = {
  validateMBTICode: vi.fn(),
  validateRealTimeInput: vi.fn(),
  formatMBTIInput: vi.fn(),
  getUserFriendlyMessage: vi.fn()
}

vi.mock('@/services/validationService', () => ({
  ValidationService: {
    getInstance: () => mockValidationService
  }
}))

describe('MBTIInputForm', () => {
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
    
    mockValidationService.getUserFriendlyMessage.mockReturnValue('Valid MBTI type')
  })

  describe('Component Rendering', () => {
    it('renders the form with all required elements', () => {
      const wrapper = mount(MBTIInputForm)

      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
      expect(wrapper.find('a[href="https://www.16personalities.com"]').exists()).toBe(true)
    })

    it('displays the correct header text', () => {
      const wrapper = mount(MBTIInputForm)

      expect(wrapper.text()).toContain('Hong Kong MBTI Travel Planner')
      expect(wrapper.text()).toContain('Welcome to MBTI Travel Planner for traveling Hong Kong')
    })

    it('shows the correct placeholder text', () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      expect(input.attributes('placeholder')).toBe('E.g. ENFP, INTJ, INFJ...')
    })

    it('displays the submit button with correct text', () => {
      const wrapper = mount(MBTIInputForm)
      const button = wrapper.find('button[type="submit"]')

      expect(button.text()).toBe('Get my 3 days itinerary!')
    })

    it('shows the external MBTI test link', () => {
      const wrapper = mount(MBTIInputForm)
      const link = wrapper.find('a[href="https://www.16personalities.com"]')

      expect(link.text()).toContain("Don't know your MBTI type? Take the test here")
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    })
  })

  describe('Input Handling', () => {
    it('updates input value on user typing', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('enfp')
      
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('enfp')
    })

    it('formats input using validation service', async () => {
      mockValidationService.formatMBTIInput.mockReturnValue('ENFP')
      
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('enfp')
      
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('enfp')
    })

    it('limits input to 4 characters', async () => {
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: false,
        formattedValue: 'ENFP',
        canContinue: false,
        message: 'Maximum 4 characters allowed'
      })

      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFPX')
      await nextTick()

      expect(input.element.value).toBe('ENFP')
    })

    it('converts input to uppercase', async () => {
      mockValidationService.formatMBTIInput.mockReturnValue('ENFP')
      
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('enfp')
      await nextTick()

      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('enfp')
    })
  })

  describe('Real-time Validation', () => {
    it('shows validation message during typing', async () => {
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: false,
        formattedValue: 'EN',
        canContinue: true,
        message: 'Continue typing... (4 possible matches)'
      })

      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('EN')
      await nextTick()

      expect(wrapper.text()).toContain('Continue typing... (4 possible matches)')
    })

    it('shows error for invalid characters', async () => {
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: false,
        formattedValue: 'EN',
        canContinue: true,
        message: 'Only letters A-Z are allowed'
      })

      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('EN1P')
      await nextTick()

      expect(wrapper.text()).toContain('Only letters A-Z are allowed')
    })

    it('clears validation message for valid input', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      // First, set invalid input
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: false,
        formattedValue: 'EN',
        canContinue: true,
        message: 'Continue typing...'
      })

      await input.setValue('EN')
      await nextTick()
      expect(wrapper.text()).toContain('Continue typing...')

      // Then, set valid input
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: true,
        formattedValue: 'ENFP',
        canContinue: true
      })

      await input.setValue('ENFP')
      await nextTick()
      expect(wrapper.text()).not.toContain('Continue typing...')
    })
  })

  describe('Form Submission', () => {
    it('validates input on form submission', async () => {
      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await form.trigger('submit')

      expect(mockValidationService.validateMBTICode).toHaveBeenCalledWith('ENFP')
    })

    it('emits submit event with valid MBTI code', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: true,
        formattedValue: 'ENFP',
        detectedType: 'ENFP'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toHaveLength(1)
      expect(wrapper.emitted('submit')?.[0]).toEqual(['ENFP'])
    })

    it('shows error message for invalid MBTI code', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Please input correct MBTI Personality!',
        formattedValue: 'XXXX'
      })

      mockValidationService.getUserFriendlyMessage.mockReturnValue(
        'Please input correct MBTI Personality!'
      )

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toBeUndefined()
      expect(wrapper.text()).toContain('Please input correct MBTI Personality!')
    })

    it('prevents submission with empty input', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Please enter your MBTI personality type',
        errorCode: 'REQUIRED'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')

      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toBeUndefined()
      expect(mockValidationService.validateMBTICode).toHaveBeenCalledWith('')
    })
  })

  describe('Loading State', () => {
    it('shows loading state when isLoading prop is true', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true
        }
      })

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeDefined()
      expect(wrapper.text()).toContain('Generating Itinerary in progress...')
    })

    it('disables form elements during loading', () => {
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

    it('enables form elements when not loading', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: false
        }
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      expect(input.attributes('disabled')).toBeUndefined()
      expect(button.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Error Display', () => {
    it('displays error message from props', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          errorMessage: 'API connection failed'
        }
      })

      expect(wrapper.text()).toContain('API connection failed')
    })

    it('prioritizes validation errors over prop errors', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type'
      })

      mockValidationService.getUserFriendlyMessage.mockReturnValue('Invalid MBTI type')

      const wrapper = mount(MBTIInputForm, {
        props: {
          errorMessage: 'API connection failed'
        }
      })

      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')

      expect(wrapper.text()).toContain('Invalid MBTI type')
      expect(wrapper.text()).not.toContain('API connection failed')
    })

    it('clears validation error when input becomes valid', async () => {
      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      // First, trigger validation error
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type'
      })
      mockValidationService.getUserFriendlyMessage.mockReturnValue('Invalid MBTI type')

      await input.setValue('XXXX')
      await form.trigger('submit')
      expect(wrapper.text()).toContain('Invalid MBTI type')

      // Then, make input valid
      mockValidationService.validateRealTimeInput.mockReturnValue({
        isValid: true,
        formattedValue: 'ENFP',
        canContinue: true
      })

      await input.setValue('ENFP')
      await nextTick()

      expect(wrapper.text()).not.toContain('Invalid MBTI type')
    })
  })

  describe('Accessibility', () => {
    it('has proper form labels and ARIA attributes', () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      expect(input.attributes('aria-label')).toBe('Enter your MBTI personality type')
      expect(input.attributes('aria-required')).toBe('true')
    })

    it('associates error messages with input using aria-describedby', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type'
      })
      mockValidationService.getUserFriendlyMessage.mockReturnValue('Invalid MBTI type')

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(input.attributes('aria-describedby')).toContain('mbti-error')
      expect(wrapper.find('#mbti-error').exists()).toBe(true)
    })

    it('has proper button accessibility attributes', () => {
      const wrapper = mount(MBTIInputForm)
      const button = wrapper.find('button[type="submit"]')

      expect(button.attributes('aria-label')).toBe('Generate 3-day itinerary')
    })

    it('has proper link accessibility attributes', () => {
      const wrapper = mount(MBTIInputForm)
      const link = wrapper.find('a[href="https://www.16personalities.com"]')

      expect(link.attributes('aria-label')).toBe('Take MBTI personality test (opens in new tab)')
    })
  })

  describe('Keyboard Navigation', () => {
    it('submits form on Enter key press', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: true,
        formattedValue: 'ENFP',
        detectedType: 'ENFP'
      })

      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await input.trigger('keydown.enter')

      expect(wrapper.emitted('submit')).toHaveLength(1)
      expect(wrapper.emitted('submit')?.[0]).toEqual(['ENFP'])
    })

    it('focuses input on component mount', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      await nextTick()

      const input = wrapper.find('input[type="text"]')
      expect(document.activeElement).toBe(input.element)

      wrapper.unmount()
    })
  })

  describe('Suggestions Display', () => {
    it('shows suggestions for invalid input', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        suggestions: ['ENFP', 'INFP', 'ENTP'],
        suggestedValue: 'ENFP'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(wrapper.text()).toContain('Did you mean:')
      expect(wrapper.text()).toContain('ENFP')
    })

    it('allows clicking on suggestions to select them', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        suggestions: ['ENFP', 'INFP', 'ENTP'],
        suggestedValue: 'ENFP'
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      const suggestionButton = wrapper.find('[data-testid="suggestion-ENFP"]')
      expect(suggestionButton.exists()).toBe(true)

      await suggestionButton.trigger('click')
      await nextTick()

      expect(input.element.value).toBe('ENFP')
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
      const wrapper = mount(MBTIInputForm, {
        props: {
          modelValue: ''
        }
      })

      const input = wrapper.find('input[type="text"]')
      await input.setValue('ENFP')

      expect(wrapper.emitted('update:modelValue')).toHaveLength(1)
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['ENFP'])
    })
  })

  describe('Edge Cases', () => {
    it('handles validation service errors gracefully', async () => {
      mockValidationService.validateMBTICode.mockImplementation(() => {
        throw new Error('Validation service error')
      })

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      
      // Should not throw error
      expect(async () => {
        await form.trigger('submit')
      }).not.toThrow()

      expect(wrapper.emitted('submit')).toBeUndefined()
    })

    it('handles empty validation result', async () => {
      mockValidationService.validateMBTICode.mockReturnValue(null)

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await form.trigger('submit')

      expect(wrapper.emitted('submit')).toBeUndefined()
    })
  })
})
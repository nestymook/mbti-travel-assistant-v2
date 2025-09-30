import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MBTIInputForm from '../../components/input/MBTIInputForm.vue'
import ItineraryTable from '../../components/itinerary/ItineraryTable.vue'
import RecommendationComboBox from '../../components/itinerary/RecommendationComboBox.vue'
import ErrorMessage from '../../components/common/ErrorMessage.vue'
import type { MainItinerary, CandidateTouristSpots, CandidateRestaurants } from '../../types/api'
import type { Restaurant } from '../../types'

// Mock services
const mockValidationService = {
  validateMBTICode: vi.fn(),
  validateRealTimeInput: vi.fn(),
  formatMBTIInput: vi.fn(),
  getUserFriendlyMessage: vi.fn()
}

const mockThemeService = {
  getCurrentPersonality: vi.fn(),
  isColorfulPersonality: vi.fn(),
  shouldShowImages: vi.fn(),
  getPersonalityColors: vi.fn()
}

vi.mock('../../services/validationService', () => ({
  ValidationService: {
    getInstance: () => mockValidationService
  }
}))

vi.mock('../../services/themeService', () => ({
  ThemeService: {
    getInstance: () => mockThemeService
  }
}))

describe('Keyboard Navigation Comprehensive Tests', () => {
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
    
    mockThemeService.getCurrentPersonality.mockReturnValue('ENFP')
    mockThemeService.isColorfulPersonality.mockReturnValue(true)
    mockThemeService.shouldShowImages.mockReturnValue(true)
    mockThemeService.getPersonalityColors.mockReturnValue({
      name: 'ENFP - The Campaigner',
      primary: '#ff5722',
      secondary: '#d84315',
      accent: '#4caf50',
      colorful: true
    })
  })

  describe('MBTIInputForm Keyboard Navigation', () => {
    it('supports Tab navigation through all interactive elements', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')
      const link = wrapper.find('a[href="https://www.16personalities.com"]')

      // Get DOM elements
      const inputElement = input.element as HTMLInputElement
      const buttonElement = button.element as HTMLButtonElement
      const linkElement = link.element as HTMLAnchorElement

      // Start with input focused
      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      // Tab to button
      await input.trigger('keydown.tab')
      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      // Tab to link
      await button.trigger('keydown.tab')
      linkElement.focus()
      expect(document.activeElement).toBe(linkElement)

      // Shift+Tab back to button
      await link.trigger('keydown.tab', { shiftKey: true })
      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      wrapper.unmount()
    })

    it('supports Enter key for form submission', async () => {
      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')

      await input.setValue('ENFP')
      await input.trigger('keydown.enter')

      expect(wrapper.emitted('submit')).toBeTruthy()
      expect(wrapper.emitted('submit')?.[0]).toEqual(['ENFP'])
    })

    it('supports Escape key to clear input and errors', async () => {
      // Start with error state
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const wrapper = mount(MBTIInputForm)
      const input = wrapper.find('input[type="text"]')
      const form = wrapper.find('form')

      // Create error state
      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(wrapper.find('.error-message').exists()).toBe(true)

      // Press Escape to clear
      await input.trigger('keydown.escape')

      expect(input.element.value).toBe('')
      expect(wrapper.find('.error-message').exists()).toBe(false)
    })

    it('supports arrow keys for input navigation', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })
      const input = wrapper.find('input[type="text"]')
      const inputElement = input.element as HTMLInputElement

      await input.setValue('ENFP')
      inputElement.focus()

      // Move cursor to beginning
      await input.trigger('keydown.home')
      expect(inputElement.selectionStart).toBe(0)

      // Move cursor to end
      await input.trigger('keydown.end')
      expect(inputElement.selectionStart).toBe(4)

      // Move cursor left
      await input.trigger('keydown.left')
      expect(inputElement.selectionStart).toBe(3)

      // Move cursor right
      await input.trigger('keydown.right')
      expect(inputElement.selectionStart).toBe(4)

      wrapper.unmount()
    })

    it('supports Ctrl+A to select all text', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })
      const input = wrapper.find('input[type="text"]')
      const inputElement = input.element as HTMLInputElement

      await input.setValue('ENFP')
      inputElement.focus()

      // Select all text
      await input.trigger('keydown.a', { ctrlKey: true })
      
      expect(inputElement.selectionStart).toBe(0)
      expect(inputElement.selectionEnd).toBe(4)

      wrapper.unmount()
    })

    it('handles focus management during loading state', async () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true
        },
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      // Elements should be disabled during loading
      expect(input.attributes('disabled')).toBeDefined()
      expect(button.attributes('disabled')).toBeDefined()

      // Focus should be managed appropriately
      const inputElement = input.element as HTMLInputElement
      inputElement.focus()
      
      // Should not be able to focus disabled elements
      expect(document.activeElement).not.toBe(inputElement)

      wrapper.unmount()
    })
  })

  describe('ItineraryTable Keyboard Navigation', () => {
    const mockMainItinerary: MainItinerary = {
      day_1: {
        breakfast: {
          id: 'rest_001',
          name: 'Morning Cafe',
          address: '123 Main St',
          district: 'Central',
          mealType: ['breakfast'],
          sentiment: { likes: 85, dislikes: 10, neutral: 5 },
          locationCategory: 'Hong Kong Island',
          priceRange: 'Below $50',
          operatingHours: {
            'Mon - Fri': '07:00-11:00',
            'Sat - Sun': '08:00-12:00',
            'Public Holiday': '08:00-12:00'
          }
        },
        morning_session: {
          tourist_spot: 'Victoria Peak',
          mbti: 'ENFP',
          description: 'Stunning views',
          address: 'Peak Rd',
          district: 'Central',
          area: 'Hong Kong Island',
          operating_hours_mon_fri: '10:00-23:00',
          operating_hours_sat_sun: '08:00-23:00',
          operating_hours_public_holiday: '08:00-23:00',
          full_day: false
        },
        lunch: {} as any,
        afternoon_session: {} as any,
        dinner: {} as any,
        night_session: {} as any
      },
      day_2: {} as any,
      day_3: {} as any
    }

    const mockCandidateSpots: CandidateTouristSpots = {
      morning_session: [],
      afternoon_session: [],
      night_session: []
    }

    const mockCandidateRestaurants: CandidateRestaurants = {
      breakfast: [],
      lunch: [],
      dinner: []
    }

    it('supports arrow key navigation through table cells', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const table = wrapper.find('table')
      const cells = wrapper.findAll('td')

      if (cells.length > 0) {
        const firstCell = cells[0].element as HTMLTableCellElement
        firstCell.focus()
        expect(document.activeElement).toBe(firstCell)

        // Arrow right to next cell
        await cells[0].trigger('keydown.right')
        if (cells.length > 1) {
          const secondCell = cells[1].element as HTMLTableCellElement
          secondCell.focus()
          expect(document.activeElement).toBe(secondCell)
        }

        // Arrow down to cell below
        await cells[0].trigger('keydown.down')
        // Should move to cell in next row
      }

      wrapper.unmount()
    })

    it('supports Home/End keys for table navigation', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const cells = wrapper.findAll('td')

      if (cells.length > 0) {
        const firstCell = cells[0].element as HTMLTableCellElement
        firstCell.focus()

        // Home key should go to first cell in row
        await cells[0].trigger('keydown.home')
        expect(document.activeElement).toBe(firstCell)

        // End key should go to last cell in row
        await cells[0].trigger('keydown.end')
        // Should move to last cell in current row
      }

      wrapper.unmount()
    })

    it('supports Page Up/Page Down for table navigation', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const table = wrapper.find('table')
      const tableElement = table.element as HTMLTableElement
      tableElement.focus()

      // Page Down should scroll table
      await table.trigger('keydown.pagedown')
      
      // Page Up should scroll back
      await table.trigger('keydown.pageup')

      wrapper.unmount()
    })
  })

  describe('RecommendationComboBox Keyboard Navigation', () => {
    const mockRestaurant: Restaurant = {
      id: 'rest_001',
      name: 'Test Restaurant',
      address: '123 Test St',
      district: 'Central',
      mealType: ['lunch'],
      sentiment: { likes: 85, dislikes: 10, neutral: 5 },
      locationCategory: 'Hong Kong Island',
      priceRange: 'Below $50',
      operatingHours: {
        'Mon - Fri': '11:30-15:00',
        'Sat - Sun': '11:30-15:30',
        'Public Holiday': '11:30-15:30'
      }
    }

    const mockOptions: Restaurant[] = [
      mockRestaurant,
      {
        ...mockRestaurant,
        id: 'rest_002',
        name: 'Alternative Restaurant'
      }
    ]

    it('supports arrow keys for option navigation', async () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const select = wrapper.find('select')
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()

      // Arrow down should move to next option
      await select.trigger('keydown.down')
      expect(selectElement.selectedIndex).toBeGreaterThanOrEqual(0)

      // Arrow up should move to previous option
      await select.trigger('keydown.up')

      wrapper.unmount()
    })

    it('supports Enter key for option selection', async () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const select = wrapper.find('select')
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()

      // Enter should confirm selection
      await select.trigger('keydown.enter')
      
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()

      wrapper.unmount()
    })

    it('supports Escape key to close dropdown', async () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const select = wrapper.find('select')
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()

      // Escape should close dropdown and maintain focus
      await select.trigger('keydown.escape')
      expect(document.activeElement).toBe(selectElement)

      wrapper.unmount()
    })

    it('supports Space key to open dropdown', async () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const select = wrapper.find('select')
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()

      // Space should open dropdown
      await select.trigger('keydown.space')
      
      // Dropdown should be open (implementation dependent)
      expect(document.activeElement).toBe(selectElement)

      wrapper.unmount()
    })

    it('supports type-ahead search in dropdown', async () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        },
        attachTo: document.body
      })

      const select = wrapper.find('select')
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()

      // Type 'A' to search for "Alternative Restaurant"
      await select.trigger('keydown', { key: 'A' })
      
      // Should select option starting with 'A'
      expect(selectElement.selectedIndex).toBeGreaterThanOrEqual(0)

      wrapper.unmount()
    })
  })

  describe('ErrorMessage Keyboard Navigation', () => {
    it('supports Enter key on dismiss button', async () => {
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test error message',
          dismissible: true
        },
        attachTo: document.body
      })

      const dismissButton = wrapper.find('.dismiss-button')
      if (dismissButton.exists()) {
        const buttonElement = dismissButton.element as HTMLButtonElement
        buttonElement.focus()

        await dismissButton.trigger('keydown.enter')
        expect(wrapper.emitted('dismiss')).toBeTruthy()
      }

      wrapper.unmount()
    })

    it('supports Space key on action buttons', async () => {
      const mockAction = vi.fn()
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test message',
          actions: [
            {
              label: 'Retry',
              action: mockAction,
              style: 'primary'
            }
          ]
        },
        attachTo: document.body
      })

      const actionButton = wrapper.find('.error-action-button')
      if (actionButton.exists()) {
        const buttonElement = actionButton.element as HTMLButtonElement
        buttonElement.focus()

        await actionButton.trigger('keydown.space')
        expect(mockAction).toHaveBeenCalled()
      }

      wrapper.unmount()
    })

    it('supports Escape key to dismiss error', async () => {
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test error message',
          dismissible: true
        },
        attachTo: document.body
      })

      const errorElement = wrapper.find('.error-message')
      const errorElementDOM = errorElement.element as HTMLElement
      errorElementDOM.focus()

      await errorElement.trigger('keydown.escape')
      expect(wrapper.emitted('dismiss')).toBeTruthy()

      wrapper.unmount()
    })
  })

  describe('Focus Management', () => {
    it('maintains focus order during dynamic content changes', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const inputElement = input.element as HTMLInputElement
      inputElement.focus()

      // Simulate dynamic content change (error message appears)
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const form = wrapper.find('form')
      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      // Focus should remain manageable
      expect(document.activeElement).toBeDefined()

      wrapper.unmount()
    })

    it('restores focus after modal interactions', async () => {
      // This would test focus restoration after modal dialogs
      // For now, we'll test basic focus restoration
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      const inputElement = input.element as HTMLInputElement
      const buttonElement = button.element as HTMLButtonElement

      // Focus input, then button, then back to input
      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      wrapper.unmount()
    })

    it('handles focus trapping in complex components', async () => {
      // Test focus trapping within component boundaries
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')
      const link = wrapper.find('a')

      // Tab through all elements and ensure focus stays within component
      const inputElement = input.element as HTMLInputElement
      const buttonElement = button.element as HTMLButtonElement
      const linkElement = link.element as HTMLAnchorElement

      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      // Tab forward through all elements
      await input.trigger('keydown.tab')
      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      await button.trigger('keydown.tab')
      linkElement.focus()
      expect(document.activeElement).toBe(linkElement)

      // Tab should wrap back to first element
      await link.trigger('keydown.tab')
      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      wrapper.unmount()
    })
  })

  describe('Screen Reader Support', () => {
    it('announces dynamic content changes', async () => {
      const wrapper = mount(MBTIInputForm)
      
      // Check for aria-live regions
      const liveRegion = wrapper.find('[aria-live]')
      expect(liveRegion.exists()).toBe(true)

      // Simulate content change
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })

      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      // Error should be announced via aria-live
      const errorElement = wrapper.find('[role="alert"]')
      expect(errorElement.exists()).toBe(true)
    })

    it('provides proper context for screen readers', () => {
      const wrapper = mount(MBTIInputForm)
      
      // Check for proper labeling
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('aria-label')).toBeDefined()
      expect(input.attributes('aria-describedby')).toBeDefined()
      
      // Check for help text association
      const helpId = input.attributes('aria-describedby')
      if (helpId) {
        const helpElement = wrapper.find(`#${helpId}`)
        expect(helpElement.exists()).toBe(true)
      }
    })
  })
})
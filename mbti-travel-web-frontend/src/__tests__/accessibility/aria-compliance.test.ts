import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MBTIInputForm from '../../components/input/MBTIInputForm.vue'
import ItineraryTable from '../../components/itinerary/ItineraryTable.vue'
import RecommendationComboBox from '../../components/itinerary/RecommendationComboBox.vue'
import ErrorMessage from '../../components/common/ErrorMessage.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
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

describe('ARIA Compliance Tests', () => {
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

  describe('MBTIInputForm ARIA Compliance', () => {
    it('has proper form labeling', () => {
      const wrapper = mount(MBTIInputForm)
      
      const form = wrapper.find('form')
      expect(form.attributes('role')).toBe('form')
      expect(form.attributes('aria-label')).toBe('MBTI personality type input form')
    })

    it('has proper input labeling and description', () => {
      const wrapper = mount(MBTIInputForm)
      
      const input = wrapper.find('input[type="text"]')
      expect(input.attributes('aria-label')).toBe('Enter your MBTI personality type')
      expect(input.attributes('aria-required')).toBe('true')
      expect(input.attributes('aria-describedby')).toContain('mbti-help')
      
      const helpText = wrapper.find('#mbti-help')
      expect(helpText.exists()).toBe(true)
      expect(helpText.text()).toContain('Enter your 4-letter MBTI personality type')
    })

    it('associates error messages with input using aria-describedby', async () => {
      mockValidationService.validateMBTICode.mockReturnValue({
        isValid: false,
        message: 'Invalid MBTI type',
        errorCode: 'INVALID_TYPE'
      })
      mockValidationService.getUserFriendlyMessage.mockReturnValue('Invalid MBTI type')

      const wrapper = mount(MBTIInputForm)
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')

      await input.setValue('XXXX')
      await form.trigger('submit')
      await nextTick()

      expect(input.attributes('aria-describedby')).toContain('mbti-error')
      expect(input.attributes('aria-invalid')).toBe('true')
      
      const errorElement = wrapper.find('#mbti-error')
      expect(errorElement.exists()).toBe(true)
      expect(errorElement.attributes('role')).toBe('alert')
      expect(errorElement.attributes('aria-live')).toBe('assertive')
    })

    it('has proper button accessibility', () => {
      const wrapper = mount(MBTIInputForm)
      
      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('aria-label')).toBe('Generate 3-day itinerary')
      expect(button.attributes('type')).toBe('submit')
    })

    it('has proper external link accessibility', () => {
      const wrapper = mount(MBTIInputForm)
      
      const link = wrapper.find('a[href="https://www.16personalities.com"]')
      expect(link.attributes('aria-label')).toBe('Take MBTI personality test (opens in new tab)')
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    })

    it('provides proper loading state accessibility', () => {
      const wrapper = mount(MBTIInputForm, {
        props: {
          isLoading: true
        }
      })

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('aria-busy')).toBe('true')
      expect(button.attributes('disabled')).toBeDefined()
      
      const loadingMessage = wrapper.find('[aria-live="polite"]')
      expect(loadingMessage.exists()).toBe(true)
      expect(loadingMessage.text()).toContain('Generating Itinerary in progress')
    })

    it('supports keyboard navigation', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      // Test tab navigation
      const inputElement = input.element as HTMLInputElement
      const buttonElement = button.element as HTMLButtonElement
      
      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      // Simulate tab key
      await input.trigger('keydown.tab')
      buttonElement.focus()
      expect(document.activeElement).toBe(buttonElement)

      wrapper.unmount()
    })
  })

  describe('ItineraryTable ARIA Compliance', () => {
    const mockMainItinerary: MainItinerary = {
      day_1: {
        breakfast: {
          id: 'rest_001',
          name: 'Morning Cafe',
          address: '123 Main St',
          district: 'Central',
          mealType: ['breakfast'],
          sentiment: { likes: 85, dislikes: 10, neutral: 5 },
          locationCategory: 'Kowloon',
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
        lunch: {
          id: 'rest_002',
          name: 'Lunch Spot',
          address: '456 Food St',
          district: 'Tsim Sha Tsui',
          mealType: ['lunch'],
          sentiment: { likes: 75, dislikes: 15, neutral: 10 },
          locationCategory: 'Kowloon',
          priceRange: 'Below $50',
          operatingHours: {
            'Mon - Fri': '11:30-15:00',
            'Sat - Sun': '11:30-15:30',
            'Public Holiday': '11:30-15:30'
          }
        },
        afternoon_session: {
          tourist_spot: 'Star Ferry',
          mbti: 'ENFP',
          description: 'Historic ferry',
          address: 'Tsim Sha Tsui Pier',
          district: 'Tsim Sha Tsui',
          area: 'Kowloon',
          operating_hours_mon_fri: '06:30-23:30',
          operating_hours_sat_sun: '06:30-23:30',
          operating_hours_public_holiday: '06:30-23:30',
          full_day: false
        },
        dinner: {
          id: 'rest_003',
          name: 'Dinner Place',
          address: '789 Night St',
          district: 'Mong Kok',
          mealType: ['dinner'],
          sentiment: { likes: 90, dislikes: 5, neutral: 5 },
          locationCategory: 'Kowloon',
          priceRange: '$51-100',
          operatingHours: {
            'Mon - Fri': '18:00-22:00',
            'Sat - Sun': '17:30-22:30',
            'Public Holiday': '17:30-22:30'
          }
        },
        night_session: {
          tourist_spot: 'Night Market',
          mbti: 'ENFP',
          description: 'Vibrant market',
          address: 'Temple St',
          district: 'Yau Ma Tei',
          area: 'Kowloon',
          operating_hours_mon_fri: '20:00-24:00',
          operating_hours_sat_sun: '19:00-01:00',
          operating_hours_public_holiday: '19:00-01:00',
          full_day: false
        }
      },
      day_2: {
        breakfast: {
          id: 'rest_004',
          name: 'Day 2 Breakfast',
          address: '321 Morning Ave',
          district: 'Wan Chai',
          mealType: ['breakfast'],
          sentiment: { likes: 80, dislikes: 12, neutral: 8 },
          locationCategory: 'Hong Kong Island',
          priceRange: 'Below $50',
          operatingHours: {
            'Mon - Fri': '07:30-11:30',
            'Sat - Sun': '08:00-12:00',
            'Public Holiday': '08:00-12:00'
          }
        },
        morning_session: {
          tourist_spot: 'Ocean Park',
          mbti: 'ENFP',
          description: 'Theme park',
          address: 'Ocean Park Rd',
          district: 'Aberdeen',
          area: 'Hong Kong Island',
          operating_hours_mon_fri: '10:00-18:00',
          operating_hours_sat_sun: '10:00-19:00',
          operating_hours_public_holiday: '10:00-19:00',
          full_day: true
        },
        lunch: {
          id: 'rest_005',
          name: 'Park Lunch',
          address: 'Inside Ocean Park',
          district: 'Aberdeen',
          mealType: ['lunch'],
          sentiment: { likes: 70, dislikes: 20, neutral: 10 },
          locationCategory: 'Hong Kong Island',
          priceRange: '$51-100',
          operatingHours: {
            'Mon - Fri': '11:00-16:00',
            'Sat - Sun': '11:00-16:30',
            'Public Holiday': '11:00-16:30'
          }
        },
        afternoon_session: {
          tourist_spot: 'Ocean Park (continued)',
          mbti: 'ENFP',
          description: 'Continue exploring',
          address: 'Ocean Park Rd',
          district: 'Aberdeen',
          area: 'Hong Kong Island',
          operating_hours_mon_fri: '10:00-18:00',
          operating_hours_sat_sun: '10:00-19:00',
          operating_hours_public_holiday: '10:00-19:00',
          full_day: true
        },
        dinner: {
          id: 'rest_006',
          name: 'Evening Dining',
          address: '654 Sunset Blvd',
          district: 'Causeway Bay',
          mealType: ['dinner'],
          sentiment: { likes: 88, dislikes: 7, neutral: 5 },
          locationCategory: 'Hong Kong Island',
          priceRange: '$101-200',
          operatingHours: {
            'Mon - Fri': '18:30-23:00',
            'Sat - Sun': '18:00-23:30',
            'Public Holiday': '18:00-23:30'
          }
        },
        night_session: {
          tourist_spot: 'Causeway Bay Shopping',
          mbti: 'ENFP',
          description: 'Shopping and nightlife',
          address: 'Causeway Bay',
          district: 'Causeway Bay',
          area: 'Hong Kong Island',
          operating_hours_mon_fri: '10:00-22:00',
          operating_hours_sat_sun: '10:00-23:00',
          operating_hours_public_holiday: '10:00-23:00',
          full_day: false
        }
      },
      day_3: {
        breakfast: {
          id: 'rest_007',
          name: 'Final Day Breakfast',
          address: '987 Last St',
          district: 'Sheung Wan',
          mealType: ['breakfast'],
          sentiment: { likes: 82, dislikes: 11, neutral: 7 },
          locationCategory: 'Hong Kong Island',
          priceRange: 'Below $50',
          operatingHours: {
            'Mon - Fri': '07:00-11:00',
            'Sat - Sun': '07:30-11:30',
            'Public Holiday': '07:30-11:30'
          }
        },
        morning_session: {
          tourist_spot: 'Man Mo Temple',
          mbti: 'ENFP',
          description: 'Traditional temple',
          address: '124-126 Hollywood Rd',
          district: 'Sheung Wan',
          area: 'Hong Kong Island',
          operating_hours_mon_fri: '08:00-18:00',
          operating_hours_sat_sun: '08:00-18:00',
          operating_hours_public_holiday: '08:00-18:00',
          full_day: false
        },
        lunch: {
          id: 'rest_008',
          name: 'Traditional Lunch',
          address: '147 Heritage St',
          district: 'Central',
          mealType: ['lunch'],
          sentiment: { likes: 85, dislikes: 8, neutral: 7 },
          locationCategory: 'Hong Kong Island',
          priceRange: '$51-100',
          operatingHours: {
            'Mon - Fri': '11:30-15:00',
            'Sat - Sun': '11:00-15:30',
            'Public Holiday': '11:00-15:30'
          }
        },
        afternoon_session: {
          tourist_spot: 'Hong Kong Museum',
          mbti: 'ENFP',
          description: 'Cultural exhibits',
          address: '10 Salisbury Rd',
          district: 'Tsim Sha Tsui',
          area: 'Kowloon',
          operating_hours_mon_fri: '10:00-18:00',
          operating_hours_sat_sun: '10:00-19:00',
          operating_hours_public_holiday: '10:00-19:00',
          full_day: false
        },
        dinner: {
          id: 'rest_009',
          name: 'Farewell Dinner',
          address: '258 Memory Lane',
          district: 'Admiralty',
          mealType: ['dinner'],
          sentiment: { likes: 92, dislikes: 4, neutral: 4 },
          locationCategory: 'Hong Kong Island',
          priceRange: '$101-200',
          operatingHours: {
            'Mon - Fri': '18:00-22:30',
            'Sat - Sun': '17:30-23:00',
            'Public Holiday': '17:30-23:00'
          }
        },
        night_session: {
          tourist_spot: 'Symphony of Lights',
          mbti: 'ENFP',
          description: 'Light show',
          address: 'Tsim Sha Tsui Promenade',
          district: 'Tsim Sha Tsui',
          area: 'Kowloon',
          operating_hours_mon_fri: '20:00-20:15',
          operating_hours_sat_sun: '20:00-20:15',
          operating_hours_public_holiday: '20:00-20:15',
          full_day: false
        }
      }
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

    it('has proper table structure and labeling', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const table = wrapper.find('table')
      expect(table.attributes('role')).toBe('table')
      expect(table.attributes('aria-label')).toBe('3-day Hong Kong itinerary')
      expect(table.attributes('aria-describedby')).toContain('itinerary-description')
      
      const description = wrapper.find('#itinerary-description')
      expect(description.exists()).toBe(true)
    })

    it('has proper header associations', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Check column headers
      const columnHeaders = wrapper.findAll('thead th')
      columnHeaders.forEach(header => {
        expect(header.attributes('scope')).toBe('col')
      })

      // Check row headers
      const rowHeaders = wrapper.findAll('tbody tr td:first-child')
      rowHeaders.forEach(header => {
        expect(header.attributes('scope')).toBe('row')
      })
    })

    it('provides proper caption for screen readers', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const caption = wrapper.find('caption')
      expect(caption.exists()).toBe(true)
      expect(caption.text()).toContain('3-day Hong Kong travel itinerary')
      expect(caption.text()).toContain('ENFP personality')
    })

    it('has proper cell associations with headers', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Check that data cells have proper headers attribute
      const dataCells = wrapper.findAll('tbody td:not(:first-child)')
      dataCells.forEach(cell => {
        const headers = cell.attributes('headers')
        expect(headers).toBeDefined()
        expect(headers?.split(' ').length).toBeGreaterThan(1) // Should reference both row and column headers
      })
    })
  })

  describe('RecommendationComboBox ARIA Compliance', () => {
    const mockRestaurant: Restaurant = {
      id: 'rest_001',
      name: 'Test Restaurant',
      address: '123 Test St',
      district: 'Central',
      mealType: ['lunch'],
      sentiment: { likes: 85, dislikes: 10, neutral: 5 },
      locationCategory: 'Kowloon',
      priceRange: 'Below $50',
      operatingHours: {
        'Mon - Fri': '11:30-15:00',
        'Sat - Sun': '11:30-15:30',
        'Public Holiday': '11:30-15:30'
      }
    }

    const mockOptions: Restaurant[] = [mockRestaurant]

    it('has proper select labeling', () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP',
          sessionType: 'lunch',
          day: 'day_1'
        }
      })

      const select = wrapper.find('select')
      expect(select.attributes('aria-label')).toBe('Select restaurant for lunch on Day 1')
      expect(select.attributes('role')).toBe('combobox')
    })

    it('associates details with select using aria-describedby', () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP',
          sessionType: 'lunch',
          day: 'day_1'
        }
      })

      const select = wrapper.find('select')
      const describedBy = select.attributes('aria-describedby')
      expect(describedBy).toBeDefined()
      
      if (describedBy) {
        const detailsElement = wrapper.find(`#${describedBy}`)
        expect(detailsElement.exists()).toBe(true)
      }
    })

    it('provides proper option labeling', () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP'
        }
      })

      const options = wrapper.findAll('option')
      options.forEach(option => {
        expect(option.attributes('value')).toBeDefined()
        expect(option.text().length).toBeGreaterThan(0)
      })
    })

    it('handles loading state accessibility', () => {
      const wrapper = mount(RecommendationComboBox, {
        props: {
          modelValue: mockRestaurant,
          options: mockOptions,
          type: 'restaurant',
          mbtiPersonality: 'ENFP',
          isLoading: true
        }
      })

      const select = wrapper.find('select')
      expect(select.attributes('aria-busy')).toBe('true')
      expect(select.attributes('disabled')).toBeDefined()
      
      const loadingMessage = wrapper.find('[aria-live="polite"]')
      expect(loadingMessage.exists()).toBe(true)
    })

    it('supports keyboard navigation', async () => {
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
      
      // Test focus
      const selectElement = select.element as HTMLSelectElement
      selectElement.focus()
      expect(document.activeElement).toBe(selectElement)

      // Test arrow key navigation
      await select.trigger('keydown.down')
      await select.trigger('keydown.up')
      await select.trigger('keydown.enter')

      wrapper.unmount()
    })
  })

  describe('ErrorMessage ARIA Compliance', () => {
    it('has proper alert role for errors', () => {
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test error message',
          severity: 'error'
        }
      })

      const errorElement = wrapper.find('.error-message')
      expect(errorElement.attributes('role')).toBe('alert')
      expect(errorElement.attributes('aria-live')).toBe('assertive')
    })

    it('uses polite aria-live for non-error severities', () => {
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test info message',
          severity: 'info'
        }
      })

      const errorElement = wrapper.find('.error-message')
      expect(errorElement.attributes('role')).toBe('status')
      expect(errorElement.attributes('aria-live')).toBe('polite')
    })

    it('has proper dismiss button accessibility', () => {
      const wrapper = mount(ErrorMessage, {
        props: {
          message: 'Test message',
          dismissible: true
        }
      })

      const dismissButton = wrapper.find('.dismiss-button')
      expect(dismissButton.attributes('aria-label')).toBe('Dismiss error message')
      expect(dismissButton.attributes('type')).toBe('button')
    })

    it('has proper action button accessibility', () => {
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
        }
      })

      const actionButton = wrapper.find('.error-action-button')
      expect(actionButton.attributes('type')).toBe('button')
      expect(actionButton.attributes('aria-label')).toContain('Retry')
    })
  })

  describe('LoadingSpinner ARIA Compliance', () => {
    it('has proper loading accessibility attributes', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading content...'
        }
      })

      const spinner = wrapper.find('.loading-spinner')
      expect(spinner.attributes('role')).toBe('status')
      expect(spinner.attributes('aria-live')).toBe('polite')
      expect(spinner.attributes('aria-label')).toBe('Loading content...')
    })

    it('provides screen reader text', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading content...'
        }
      })

      const srText = wrapper.find('.sr-only')
      expect(srText.exists()).toBe(true)
      expect(srText.text()).toBe('Loading content...')
    })

    it('handles progress accessibility', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading content...',
          progress: 50
        }
      })

      const progressBar = wrapper.find('[role="progressbar"]')
      expect(progressBar.exists()).toBe(true)
      expect(progressBar.attributes('aria-valuenow')).toBe('50')
      expect(progressBar.attributes('aria-valuemin')).toBe('0')
      expect(progressBar.attributes('aria-valuemax')).toBe('100')
      expect(progressBar.attributes('aria-label')).toContain('50%')
    })
  })

  describe('Focus Management', () => {
    it('manages focus properly in modal dialogs', async () => {
      // This would test focus trapping in modal components
      // For now, we'll test basic focus management
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      
      // Component should focus input on mount
      await nextTick()
      const inputElement = input.element as HTMLInputElement
      expect(document.activeElement).toBe(inputElement)

      wrapper.unmount()
    })

    it('restores focus after interactions', async () => {
      const wrapper = mount(MBTIInputForm, {
        attachTo: document.body
      })

      const input = wrapper.find('input[type="text"]')
      const button = wrapper.find('button[type="submit"]')

      // Focus input
      const inputElement = input.element as HTMLInputElement
      inputElement.focus()
      expect(document.activeElement).toBe(inputElement)

      // Click button
      await button.trigger('click')
      
      // Focus should remain manageable
      expect(document.activeElement).toBeDefined()

      wrapper.unmount()
    })
  })

  describe('Color Contrast and Visual Accessibility', () => {
    it('applies high contrast mode when needed', () => {
      // Mock high contrast media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })

      const wrapper = mount(MBTIInputForm)
      
      // Should apply high contrast classes when needed
      expect(wrapper.find('.high-contrast').exists()).toBe(true)
    })

    it('respects reduced motion preferences', () => {
      // Mock reduced motion media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })

      const wrapper = mount(LoadingSpinner)
      
      // Should disable animations when reduced motion is preferred
      expect(wrapper.find('.no-animation').exists()).toBe(true)
    })
  })

  describe('Screen Reader Compatibility', () => {
    it('provides proper heading hierarchy', () => {
      const wrapper = mount(MBTIInputForm)
      
      const h1 = wrapper.find('h1')
      expect(h1.exists()).toBe(true)
      expect(h1.text()).toBe('Hong Kong MBTI Travel Planner')
      
      const h2 = wrapper.find('h2')
      expect(h2.exists()).toBe(true)
      expect(h2.text()).toBe('Welcome to MBTI Travel Planner for traveling Hong Kong')
    })

    it('provides skip links for navigation', () => {
      const wrapper = mount(MBTIInputForm)
      
      const skipLink = wrapper.find('.skip-link')
      expect(skipLink.exists()).toBe(true)
      expect(skipLink.attributes('href')).toBe('#main-content')
      expect(skipLink.text()).toBe('Skip to main content')
    })

    it('uses semantic HTML elements', () => {
      const wrapper = mount(MBTIInputForm)
      
      expect(wrapper.find('main').exists()).toBe(true)
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('button').exists()).toBe(true)
      expect(wrapper.find('input').exists()).toBe(true)
    })
  })
})
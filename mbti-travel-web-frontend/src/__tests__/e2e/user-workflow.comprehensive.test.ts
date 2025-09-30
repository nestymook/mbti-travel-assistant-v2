import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import { nextTick } from 'vue'
import App from '../../App.vue'
import InputPage from '../../views/InputPage.vue'
import ItineraryPage from '../../views/ItineraryPage.vue'
import type { ItineraryResponse } from '../../types'

// Mock services
const mockApiService = {
  generateItinerary: vi.fn()
}

const mockAuthService = {
  isAuthenticated: vi.fn(),
  getToken: vi.fn(),
  validateToken: vi.fn()
}

const mockValidationService = {
  validateMBTICode: vi.fn(),
  validateRealTimeInput: vi.fn(),
  formatMBTIInput: vi.fn(),
  getUserFriendlyMessage: vi.fn()
}

const mockThemeService = {
  applyMBTITheme: vi.fn(),
  getCurrentPersonality: vi.fn(),
  getPersonalityColors: vi.fn(),
  isColorfulPersonality: vi.fn()
}

vi.mock('../../services/apiService', () => ({
  ApiService: { getInstance: () => mockApiService }
}))

vi.mock('../../services/authService', () => ({
  AuthService: { getInstance: () => mockAuthService }
}))

vi.mock('../../services/validationService', () => ({
  ValidationService: { getInstance: () => mockValidationService }
}))

vi.mock('../../services/themeService', () => ({
  ThemeService: { getInstance: () => mockThemeService }
}))

describe('End-to-End User Workflow Tests', () => {
  let router: any
  let pinia: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Create router with all routes
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', name: 'input', component: InputPage },
        { path: '/itinerary', name: 'itinerary', component: ItineraryPage }
      ]
    })

    pinia = createPinia()

    // Setup default mocks
    mockAuthService.isAuthenticated.mockReturnValue(true)
    mockAuthService.getToken.mockReturnValue('valid-token')
    mockAuthService.validateToken.mockResolvedValue(true)

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
    mockThemeService.getPersonalityColors.mockReturnValue({
      name: 'ENFP - The Campaigner',
      primary: '#ff5722',
      secondary: '#d84315',
      accent: '#4caf50'
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Complete User Journey: Input to Itinerary', () => {
    it('completes full workflow from MBTI input to itinerary display', async () => {
      const mockItineraryResponse: ItineraryResponse = {
        main_itinerary: {
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
              description: 'Stunning views of Hong Kong',
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
              priceRange: '$51-100',
              operatingHours: {
                'Mon - Fri': '11:30-15:00',
                'Sat - Sun': '11:30-15:30',
                'Public Holiday': '11:30-15:30'
              }
            },
            afternoon_session: {
              tourist_spot: 'Star Ferry',
              mbti: 'ENFP',
              description: 'Historic ferry ride',
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
              priceRange: '$101-200',
              operatingHours: {
                'Mon - Fri': '18:00-22:00',
                'Sat - Sun': '17:30-22:30',
                'Public Holiday': '17:30-22:30'
              }
            },
            night_session: {
              tourist_spot: 'Night Market',
              mbti: 'ENFP',
              description: 'Vibrant night market',
              address: 'Temple St',
              district: 'Yau Ma Tei',
              area: 'Kowloon',
              operating_hours_mon_fri: '20:00-24:00',
              operating_hours_sat_sun: '19:00-01:00',
              operating_hours_public_holiday: '19:00-01:00',
              full_day: false
            }
          },
          day_2: {} as any,
          day_3: {} as any
        },
        candidate_tourist_spots: {
          morning_session: [
            {
              tourist_spot: 'Alternative Peak',
              mbti: 'ENFP',
              description: 'Another great view',
              address: 'Alt Peak Rd',
              district: 'Central',
              area: 'Hong Kong Island',
              operating_hours_mon_fri: '09:00-22:00',
              operating_hours_sat_sun: '09:00-22:00',
              operating_hours_public_holiday: '09:00-22:00',
              full_day: false
            }
          ],
          afternoon_session: [],
          night_session: []
        },
        candidate_restaurants: {
          breakfast: [
            {
              id: 'rest_alt_001',
              name: 'Alternative Breakfast',
              address: '321 Alt St',
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
            }
          ],
          lunch: [],
          dinner: []
        },
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 2500,
          version: '1.0.0'
        }
      }

      mockApiService.generateItinerary.mockResolvedValue(mockItineraryResponse)

      // Start at input page
      await router.push('/')
      
      const wrapper = mount(App, {
        global: {
          plugins: [router, pinia]
        }
      })

      await nextTick()

      // Step 1: User sees input form
      expect(wrapper.find('h1').text()).toBe('Hong Kong MBTI Travel Planner')
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)

      // Step 2: User enters MBTI type
      const input = wrapper.find('input[type="text"]')
      await input.setValue('ENFP')

      // Verify real-time validation
      expect(mockValidationService.validateRealTimeInput).toHaveBeenCalledWith('ENFP')
      expect(mockValidationService.formatMBTIInput).toHaveBeenCalledWith('ENFP')

      // Step 3: User submits form
      const form = wrapper.find('form')
      await form.trigger('submit')

      // Verify validation and API call
      expect(mockValidationService.validateMBTICode).toHaveBeenCalledWith('ENFP')
      expect(mockApiService.generateItinerary).toHaveBeenCalledWith({
        mbtiPersonality: 'ENFP',
        preferences: {}
      })

      // Step 4: Loading state is shown
      await nextTick()
      expect(wrapper.find('.loading-message').exists()).toBe(true)
      expect(wrapper.find('.loading-message').text()).toContain('Generating Itinerary in progress')

      // Step 5: Navigation to itinerary page
      await router.push('/itinerary')
      await nextTick()

      // Step 6: Itinerary is displayed
      expect(wrapper.find('.itinerary-header').exists()).toBe(true)
      expect(wrapper.text()).toContain('3-Day Itinerary for ENFP Personality')

      // Step 7: Theme is applied
      expect(mockThemeService.applyMBTITheme).toHaveBeenCalledWith('ENFP')

      // Step 8: User can see itinerary content
      expect(wrapper.text()).toContain('Morning Cafe')
      expect(wrapper.text()).toContain('Victoria Peak')
      expect(wrapper.text()).toContain('Lunch Spot')
      expect(wrapper.text()).toContain('Star Ferry')
      expect(wrapper.text()).toContain('Dinner Place')
      expect(wrapper.text()).toContain('Night Market')
    })
  })
})
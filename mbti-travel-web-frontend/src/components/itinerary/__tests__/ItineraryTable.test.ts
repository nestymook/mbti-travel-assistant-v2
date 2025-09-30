import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ItineraryTable from '../ItineraryTable.vue'
import type { MainItinerary, CandidateTouristSpots, CandidateRestaurants } from '@/types/api'
import type { MBTIPersonality } from '@/types/mbti'

// Mock the theme service
const mockThemeService = {
  getCurrentPersonality: vi.fn(),
  isColorfulPersonality: vi.fn(),
  shouldShowImages: vi.fn(),
  getPersonalityColors: vi.fn()
}

vi.mock('@/services/themeService', () => ({
  ThemeService: {
    getInstance: () => mockThemeService
  }
}))

describe('ItineraryTable', () => {
  const mockMainItinerary: MainItinerary = {
    day_1: {
      breakfast: {
        id: 'rest_001',
        name: 'Morning Cafe',
        address: '123 Main St',
        district: 'Central',
        mealType: ['breakfast'],
        sentiment: { likes: 85, dislikes: 10, neutral: 5 },
        locationCategory: 'cafe',
        priceRange: '$',
        operatingHours: {
          'Mon - Fri': '07:00-11:00',
          'Sat - Sun': '08:00-12:00',
          'Public Holiday': '08:00-12:00'
        }
      },
      morning_session: {
        tourist_spot: 'Victoria Peak',
        mbti: 'ENFP',
        description: 'Stunning panoramic views',
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
        locationCategory: 'restaurant',
        priceRange: '$$',
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
        locationCategory: 'restaurant',
        priceRange: '$$$',
        operatingHours: {
          'Mon - Fri': '18:00-22:00',
          'Sat - Sun': '17:30-22:30',
          'Public Holiday': '17:30-22:30'
        }
      },
      night_session: {
        tourist_spot: 'Temple Street Night Market',
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
    day_2: {
      breakfast: {
        id: 'rest_004',
        name: 'Day 2 Breakfast',
        address: '321 Morning Ave',
        district: 'Wan Chai',
        mealType: ['breakfast'],
        sentiment: { likes: 80, dislikes: 12, neutral: 8 },
        locationCategory: 'cafe',
        priceRange: '$',
        operatingHours: {
          'Mon - Fri': '07:30-11:30',
          'Sat - Sun': '08:00-12:00',
          'Public Holiday': '08:00-12:00'
        }
      },
      morning_session: {
        tourist_spot: 'Ocean Park',
        mbti: 'ENFP',
        description: 'Theme park with marine life',
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
        locationCategory: 'food_court',
        priceRange: '$$',
        operatingHours: {
          'Mon - Fri': '11:00-16:00',
          'Sat - Sun': '11:00-16:30',
          'Public Holiday': '11:00-16:30'
        }
      },
      afternoon_session: {
        tourist_spot: 'Ocean Park (continued)',
        mbti: 'ENFP',
        description: 'Continue exploring the park',
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
        locationCategory: 'fine_dining',
        priceRange: '$$$$',
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
        locationCategory: 'bakery',
        priceRange: '$',
        operatingHours: {
          'Mon - Fri': '07:00-11:00',
          'Sat - Sun': '07:30-11:30',
          'Public Holiday': '07:30-11:30'
        }
      },
      morning_session: {
        tourist_spot: 'Man Mo Temple',
        mbti: 'ENFP',
        description: 'Traditional Chinese temple',
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
        locationCategory: 'traditional',
        priceRange: '$$',
        operatingHours: {
          'Mon - Fri': '11:30-15:00',
          'Sat - Sun': '11:00-15:30',
          'Public Holiday': '11:00-15:30'
        }
      },
      afternoon_session: {
        tourist_spot: 'Hong Kong Museum',
        mbti: 'ENFP',
        description: 'Cultural and historical exhibits',
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
        locationCategory: 'fine_dining',
        priceRange: '$$$$',
        operatingHours: {
          'Mon - Fri': '18:00-22:30',
          'Sat - Sun': '17:30-23:00',
          'Public Holiday': '17:30-23:00'
        }
      },
      night_session: {
        tourist_spot: 'Symphony of Lights',
        mbti: 'ENFP',
        description: 'Light show over Victoria Harbour',
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
    morning_session: [
      {
        tourist_spot: 'Alternative Morning Spot',
        mbti: 'ENFP',
        description: 'Alternative morning activity',
        address: 'Alt Morning St',
        district: 'Central',
        area: 'Hong Kong Island',
        operating_hours_mon_fri: '09:00-17:00',
        operating_hours_sat_sun: '09:00-18:00',
        operating_hours_public_holiday: '09:00-18:00',
        full_day: false
      }
    ],
    afternoon_session: [],
    night_session: []
  }

  const mockCandidateRestaurants: CandidateRestaurants = {
    breakfast: [
      {
        id: 'alt_rest_001',
        name: 'Alternative Breakfast',
        address: 'Alt Breakfast St',
        district: 'Central',
        mealType: ['breakfast'],
        sentiment: { likes: 78, dislikes: 12, neutral: 10 },
        locationCategory: 'cafe',
        priceRange: '$',
        operatingHours: {
          'Mon - Fri': '07:00-11:00',
          'Sat - Sun': '08:00-12:00',
          'Public Holiday': '08:00-12:00'
        }
      }
    ],
    lunch: [],
    dinner: []
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
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

  describe('Component Rendering', () => {
    it('renders the table structure correctly', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('table').exists()).toBe(true)
      expect(wrapper.find('thead').exists()).toBe(true)
      expect(wrapper.find('tbody').exists()).toBe(true)
    })

    it('displays correct table headers', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const headers = wrapper.findAll('th')
      expect(headers[0].text()).toBe('')
      expect(headers[1].text()).toBe('Day 1')
      expect(headers[2].text()).toBe('Day 2')
      expect(headers[3].text()).toBe('Day 3')
    })

    it('displays correct row labels', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const rowLabels = wrapper.findAll('tbody tr td:first-child')
      expect(rowLabels[0].text()).toBe('Breakfast')
      expect(rowLabels[1].text()).toBe('Morning Session')
      expect(rowLabels[2].text()).toBe('Lunch')
      expect(rowLabels[3].text()).toBe('Afternoon Session')
      expect(rowLabels[4].text()).toBe('Dinner')
      expect(rowLabels[5].text()).toBe('Night Session')
    })

    it('renders combo boxes for all recommendations', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Should have 18 combo boxes (6 sessions × 3 days)
      const comboBoxes = wrapper.findAll('[data-testid^="combo-box-"]')
      expect(comboBoxes.length).toBe(18)
    })
  })

  describe('Data Display', () => {
    it('displays restaurant information correctly', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Check breakfast restaurant display
      const breakfastCell = wrapper.find('[data-testid="combo-box-breakfast-day_1"]')
      expect(breakfastCell.exists()).toBe(true)
      expect(wrapper.text()).toContain('Morning Cafe')
    })

    it('displays tourist spot information correctly', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Check morning session tourist spot display
      const morningCell = wrapper.find('[data-testid="combo-box-morning_session-day_1"]')
      expect(morningCell.exists()).toBe(true)
      expect(wrapper.text()).toContain('Victoria Peak')
    })

    it('shows operating hours for restaurants', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.text()).toContain('07:00-11:00')
    })

    it('shows sentiment data for restaurants', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.text()).toContain('85 likes')
    })
  })

  describe('Combo Box Functionality', () => {
    it('updates data when combo box selection changes', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const comboBox = wrapper.find('[data-testid="combo-box-breakfast-day_1"]')
      expect(comboBox.exists()).toBe(true)

      // Simulate selection change
      await comboBox.trigger('change')
      
      expect(wrapper.emitted('update:mainItinerary')).toBeDefined()
    })

    it('provides candidate options to combo boxes', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Check that combo boxes receive candidate data
      const morningComboBox = wrapper.find('[data-testid="combo-box-morning_session-day_1"]')
      expect(morningComboBox.exists()).toBe(true)
    })
  })

  describe('Personality-Specific Styling', () => {
    it('applies colorful personality styling', () => {
      mockThemeService.isColorfulPersonality.mockReturnValue(true)
      
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('.itinerary-table--colorful').exists()).toBe(true)
    })

    it('applies standard styling for non-colorful personalities', () => {
      mockThemeService.isColorfulPersonality.mockReturnValue(false)
      
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'INTJ'
        }
      })

      expect(wrapper.find('.itinerary-table--colorful').exists()).toBe(false)
      expect(wrapper.find('.itinerary-table--standard').exists()).toBe(true)
    })

    it('shows image placeholders for personalities that should display images', () => {
      mockThemeService.shouldShowImages.mockReturnValue(true)
      
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.findAll('.image-placeholder').length).toBeGreaterThan(0)
    })
  })

  describe('Responsive Design', () => {
    it('applies responsive classes', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('.itinerary-table--responsive').exists()).toBe(true)
    })

    it('has proper table structure for mobile', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const table = wrapper.find('table')
      expect(table.classes()).toContain('responsive-table')
    })
  })

  describe('Accessibility', () => {
    it('has proper table accessibility attributes', () => {
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

      const headers = wrapper.findAll('th')
      headers.forEach(header => {
        expect(header.attributes('scope')).toBe('col')
      })

      const rowHeaders = wrapper.findAll('tbody tr td:first-child')
      rowHeaders.forEach(header => {
        expect(header.attributes('scope')).toBe('row')
      })
    })

    it('provides descriptive labels for combo boxes', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const breakfastCombo = wrapper.find('[data-testid="combo-box-breakfast-day_1"]')
      expect(breakfastCombo.attributes('aria-label')).toContain('breakfast')
      expect(breakfastCombo.attributes('aria-label')).toContain('Day 1')
    })
  })

  describe('Error Handling', () => {
    it('handles missing itinerary data gracefully', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: {} as MainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('table').exists()).toBe(true)
      expect(wrapper.text()).toContain('No itinerary data available')
    })

    it('handles missing candidate data gracefully', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: {} as CandidateTouristSpots,
          candidateRestaurants: {} as CandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('table').exists()).toBe(true)
      // Should still render with main itinerary data
      expect(wrapper.text()).toContain('Morning Cafe')
    })

    it('handles theme service errors gracefully', () => {
      mockThemeService.isColorfulPersonality.mockImplementation(() => {
        throw new Error('Theme service error')
      })

      expect(() => {
        mount(ItineraryTable, {
          props: {
            mainItinerary: mockMainItinerary,
            candidateSpots: mockCandidateSpots,
            candidateRestaurants: mockCandidateRestaurants,
            mbtiPersonality: 'ENFP'
          }
        })
      }).not.toThrow()
    })
  })

  describe('Performance', () => {
    it('does not re-render unnecessarily when props do not change', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const renderCount = wrapper.vm.$el.querySelectorAll('td').length

      // Update with same props
      await wrapper.setProps({
        mainItinerary: mockMainItinerary,
        candidateSpots: mockCandidateSpots,
        candidateRestaurants: mockCandidateRestaurants,
        mbtiPersonality: 'ENFP'
      })

      const newRenderCount = wrapper.vm.$el.querySelectorAll('td').length
      expect(newRenderCount).toBe(renderCount)
    })
  })

  describe('Data Updates', () => {
    it('emits update events when selections change', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Simulate a combo box selection change
      const comboBox = wrapper.find('[data-testid="combo-box-breakfast-day_1"]')
      await comboBox.trigger('change')

      expect(wrapper.emitted('update:mainItinerary')).toBeDefined()
    })

    it('updates display when main itinerary changes', async () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.text()).toContain('Morning Cafe')

      // Update the itinerary
      const updatedItinerary = {
        ...mockMainItinerary,
        day_1: {
          ...mockMainItinerary.day_1,
          breakfast: {
            ...mockMainItinerary.day_1.breakfast,
            name: 'Updated Breakfast Spot'
          }
        }
      }

      await wrapper.setProps({ mainItinerary: updatedItinerary })
      await nextTick()

      expect(wrapper.text()).toContain('Updated Breakfast Spot')
    })
  })

  describe('Session Types', () => {
    it('correctly identifies meal sessions', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const mealSessions = wrapper.findAll('[data-session-type="meal"]')
      expect(mealSessions.length).toBe(9) // 3 meals × 3 days
    })

    it('correctly identifies activity sessions', () => {
      const wrapper = mount(ItineraryTable, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      const activitySessions = wrapper.findAll('[data-session-type="activity"]')
      expect(activitySessions.length).toBe(9) // 3 activities × 3 days
    })
  })
})
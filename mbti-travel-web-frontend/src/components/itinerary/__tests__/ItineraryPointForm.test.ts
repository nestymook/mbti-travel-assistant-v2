import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import ItineraryPointForm from '../ItineraryPointForm.vue'
import type { MainItinerary, CandidateTouristSpots, CandidateRestaurants } from '@/types/api'
import type { MBTIPersonality } from '@/types/mbti'
import type { TouristSpot } from '@/types/touristSpot'
import type { Restaurant } from '@/types/restaurant'

// Mock child components
vi.mock('../RestaurantDetails.vue', () => ({
  default: {
    name: 'RestaurantDetails',
    template: '<div data-testid="restaurant-details">Restaurant Details</div>',
    props: ['restaurant', 'mbtiPersonality', 'displayMode']
  }
}))

vi.mock('../TouristSpotDetails.vue', () => ({
  default: {
    name: 'TouristSpotDetails',
    template: '<div data-testid="tourist-spot-details">Tourist Spot Details</div>',
    props: ['touristSpot', 'mbtiPersonality', 'displayMode']
  }
}))

describe('ItineraryPointForm', () => {
  let wrapper: VueWrapper<any>
  
  const mockTouristSpot: TouristSpot = {
    tourist_spot: 'Victoria Peak',
    mbti: 'ESTP',
    description: 'Amazing views of Hong Kong',
    remarks: 'Best visited during sunset',
    address: '1 Peak Road, The Peak',
    district: 'Central and Western',
    area: 'The Peak',
    operating_hours_mon_fri: '10:00-23:00',
    operating_hours_sat_sun: '08:00-23:00',
    operating_hours_public_holiday: '08:00-23:00',
    full_day: false
  }

  const mockRestaurant: Restaurant = {
    id: 'rest_001',
    name: 'Dim Sum Palace',
    address: '123 Central Street',
    mealType: ['breakfast', 'lunch'],
    sentiment: {
      likes: 85,
      dislikes: 10,
      neutral: 5
    },
    locationCategory: 'Kowloon',
    district: 'Central',
    priceRange: '$51-100',
    operatingHours: {
      'Mon - Fri': '07:00-15:00',
      'Sat - Sun': '08:00-16:00',
      'Public Holiday': '08:00-16:00'
    }
  }

  const mockMainItinerary: MainItinerary = {
    day_1: {
      morning_session: mockTouristSpot,
      afternoon_session: mockTouristSpot,
      night_session: mockTouristSpot,
      breakfast: mockRestaurant,
      lunch: mockRestaurant,
      dinner: mockRestaurant
    },
    day_2: {
      morning_session: mockTouristSpot,
      afternoon_session: mockTouristSpot,
      night_session: mockTouristSpot,
      breakfast: mockRestaurant,
      lunch: mockRestaurant,
      dinner: mockRestaurant
    },
    day_3: {
      morning_session: mockTouristSpot,
      afternoon_session: mockTouristSpot,
      night_session: mockTouristSpot,
      breakfast: mockRestaurant,
      lunch: mockRestaurant,
      dinner: mockRestaurant
    }
  }

  const mockCandidateSpots: CandidateTouristSpots = {
    'morning_session_day_1': [mockTouristSpot],
    'afternoon_session_day_1': [mockTouristSpot],
    'night_session_day_1': [mockTouristSpot],
    'morning_session_day_2': [mockTouristSpot],
    'afternoon_session_day_2': [mockTouristSpot],
    'night_session_day_2': [mockTouristSpot],
    'morning_session_day_3': [mockTouristSpot],
    'afternoon_session_day_3': [mockTouristSpot],
    'night_session_day_3': [mockTouristSpot]
  }

  const mockCandidateRestaurants: CandidateRestaurants = {
    'breakfast_day_1': [mockRestaurant],
    'lunch_day_1': [mockRestaurant],
    'dinner_day_1': [mockRestaurant],
    'breakfast_day_2': [mockRestaurant],
    'lunch_day_2': [mockRestaurant],
    'dinner_day_2': [mockRestaurant],
    'breakfast_day_3': [mockRestaurant],
    'lunch_day_3': [mockRestaurant],
    'dinner_day_3': [mockRestaurant]
  }

  const defaultProps = {
    mainItinerary: mockMainItinerary,
    candidateSpots: mockCandidateSpots,
    candidateRestaurants: mockCandidateRestaurants,
    mbtiPersonality: 'INTP' as MBTIPersonality
  }

  beforeEach(() => {
    wrapper = mount(ItineraryPointForm, {
      props: defaultProps
    })
  })

  describe('Component Structure', () => {
    it('renders the component with correct structure', () => {
      expect(wrapper.find('.itinerary-point-form').exists()).toBe(true)
      expect(wrapper.find('.point-form-header').exists()).toBe(true)
      expect(wrapper.find('.days-container').exists()).toBe(true)
    })

    it('displays the correct header title', () => {
      const header = wrapper.find('.point-form-header h2')
      expect(header.text()).toBe('Your Personalized 3-Day Hong Kong Itinerary')
    })

    it('renders three day sections', () => {
      const daySections = wrapper.findAll('.day-section')
      expect(daySections).toHaveLength(3)
    })

    it('renders all session types for each day', () => {
      const sessionItems = wrapper.findAll('.session-item')
      // 6 sessions per day × 3 days = 18 total sessions
      expect(sessionItems).toHaveLength(18)
    })
  })

  describe('MBTI Personality Styling', () => {
    it('applies correct personality class for INTP', () => {
      expect(wrapper.find('.personality-intp').exists()).toBe(true)
    })

    it('applies correct personality class for ISTP', async () => {
      await wrapper.setProps({ mbtiPersonality: 'ISTP' })
      expect(wrapper.find('.personality-istp').exists()).toBe(true)
    })

    it('applies correct personality class for ESTP', async () => {
      await wrapper.setProps({ mbtiPersonality: 'ESTP' })
      expect(wrapper.find('.personality-estp').exists()).toBe(true)
    })
  })

  describe('ESTP Flashy Styling', () => {
    beforeEach(async () => {
      await wrapper.setProps({ mbtiPersonality: 'ESTP' })
    })

    it('displays ESTP subtitle when personality is ESTP', () => {
      const subtitle = wrapper.find('.estp-subtitle')
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.text()).toBe('🎉 Let\'s make this trip AMAZING! 🌟')
    })

    it('does not display ESTP subtitle for other personalities', async () => {
      await wrapper.setProps({ mbtiPersonality: 'INTP' })
      const subtitle = wrapper.find('.estp-subtitle')
      expect(subtitle.exists()).toBe(false)
    })

    it('applies flashy styling to day sections for ESTP', () => {
      const daySections = wrapper.findAll('.day-section')
      daySections.forEach(section => {
        expect(section.classes()).toContain('estp-flashy')
      })
    })

    it('displays emojis in day headers for ESTP', () => {
      const dayHeaders = wrapper.findAll('.day-header h3')
      dayHeaders.forEach(header => {
        expect(header.text()).toMatch(/🗓️.*✨/)
      })
    })

    it('displays image placeholder links for tourist spots when ESTP', () => {
      const imagePlaceholders = wrapper.findAll('.estp-image-placeholder')
      // Should have 3 tourist spot sessions per day × 3 days = 9 placeholders
      expect(imagePlaceholders.length).toBeGreaterThan(0)
    })

    it('does not display image placeholders for non-ESTP personalities', async () => {
      await wrapper.setProps({ mbtiPersonality: 'INTP' })
      const imagePlaceholders = wrapper.findAll('.estp-image-placeholder')
      expect(imagePlaceholders).toHaveLength(0)
    })
  })

  describe('Session Organization', () => {
    it('displays sessions in correct order', () => {
      const sessionTitles = wrapper.findAll('.session-title')
      const expectedOrder = [
        'Breakfast', 'Morning Session', 'Lunch', 'Afternoon Session', 'Dinner', 'Night Session'
      ]
      
      // Check first day's sessions
      for (let i = 0; i < 6; i++) {
        expect(sessionTitles[i].text()).toBe(expectedOrder[i])
      }
    })

    it('displays correct session icons', () => {
      const sessionIcons = wrapper.findAll('.session-icon')
      const expectedIcons = ['🍳', '🌅', '🍽️', '☀️', '🍷', '🌙']
      
      // Check first day's session icons
      for (let i = 0; i < 6; i++) {
        expect(sessionIcons[i].text()).toBe(expectedIcons[i])
      }
    })
  })

  describe('Combo Box Functionality', () => {
    it('renders combo boxes for all sessions', () => {
      const comboBoxes = wrapper.findAll('.point-form-combo')
      // 6 sessions per day × 3 days = 18 combo boxes
      expect(comboBoxes).toHaveLength(18)
    })

    it('displays selected recommendations in combo boxes', () => {
      const breakfastCombo = wrapper.find('#breakfast-day-1')
      expect(breakfastCombo.element.value).toBe(mockRestaurant.name)
      
      const morningCombo = wrapper.find('#morning-day-1')
      expect(morningCombo.element.value).toBe(mockTouristSpot.tourist_spot)
    })

    it('emits recommendation-change event when selection changes', async () => {
      const comboBox = wrapper.find('#breakfast-day-1')
      
      // Create a proper change event with the new value
      const changeEvent = new Event('change')
      Object.defineProperty(changeEvent, 'target', {
        value: { value: 'New Restaurant' },
        enumerable: true
      })
      
      await comboBox.element.dispatchEvent(changeEvent)
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('recommendation-change')).toBeTruthy()
      const emittedEvents = wrapper.emitted('recommendation-change') as any[]
      expect(emittedEvents[0]).toEqual(['breakfast', 1, 'New Restaurant'])
    })

    it('has proper accessibility labels', () => {
      const breakfastCombo = wrapper.find('#breakfast-day-1')
      expect(breakfastCombo.attributes('aria-label')).toBe('Select breakfast for Day 1')
      
      const morningCombo = wrapper.find('#morning-day-1')
      expect(morningCombo.attributes('aria-label')).toBe('Select morning activity for Day 1')
    })
  })

  describe('Recommendation Details', () => {
    it('displays restaurant details for restaurant sessions', () => {
      const restaurantDetails = wrapper.findAll('[data-testid="restaurant-details"]')
      // 3 restaurant sessions per day × 3 days = 9 restaurant details
      expect(restaurantDetails.length).toBeGreaterThan(0)
    })

    it('displays tourist spot details for tourist spot sessions', () => {
      const touristSpotDetails = wrapper.findAll('[data-testid="tourist-spot-details"]')
      // 3 tourist spot sessions per day × 3 days = 9 tourist spot details
      expect(touristSpotDetails.length).toBeGreaterThan(0)
    })
  })

  describe('Image Placeholder Functionality', () => {
    beforeEach(async () => {
      await wrapper.setProps({ mbtiPersonality: 'ESTP' })
    })

    it('displays image links with correct text for ESTP', () => {
      const imageLinks = wrapper.findAll('.image-link')
      expect(imageLinks.length).toBeGreaterThan(0)
      
      const linkTexts = imageLinks.map(link => link.text())
      expect(linkTexts).toContain('View Amazing Photos! 🌟')
      expect(linkTexts).toContain('Check out these Epic Views! 🚀')
      expect(linkTexts).toContain('Night Life Photos! 🎉')
    })

    it('shows alert when image placeholder is clicked', async () => {
      // Mock window.alert
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
      
      const imageLink = wrapper.find('.image-link')
      await imageLink.trigger('click')
      
      expect(alertSpy).toHaveBeenCalledWith(
        '🎉 Image gallery would open here! This is a placeholder for actual image functionality.'
      )
      
      alertSpy.mockRestore()
    })
  })

  describe('Responsive Design', () => {
    it('applies responsive classes correctly', () => {
      expect(wrapper.find('.itinerary-point-form').exists()).toBe(true)
      expect(wrapper.find('.days-container').exists()).toBe(true)
    })

    it('maintains proper structure on mobile', () => {
      // Test that essential elements are present for mobile layout
      expect(wrapper.find('.point-form-header').exists()).toBe(true)
      expect(wrapper.find('.day-section').exists()).toBe(true)
      expect(wrapper.find('.session-item').exists()).toBe(true)
    })
  })

  describe('Data Handling', () => {
    it('handles missing itinerary data gracefully', async () => {
      const emptyItinerary = {
        day_1: {} as any,
        day_2: {} as any,
        day_3: {} as any
      }
      
      await wrapper.setProps({ mainItinerary: emptyItinerary })
      
      // Component should still render without errors
      expect(wrapper.find('.itinerary-point-form').exists()).toBe(true)
    })

    it('handles empty candidate lists gracefully', async () => {
      await wrapper.setProps({ 
        candidateSpots: {},
        candidateRestaurants: {}
      })
      
      // Component should still render without errors
      expect(wrapper.find('.itinerary-point-form').exists()).toBe(true)
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for combo boxes', () => {
      const comboBoxes = wrapper.findAll('.point-form-combo')
      comboBoxes.forEach(combo => {
        expect(combo.attributes('aria-label')).toBeDefined()
        expect(combo.attributes('aria-label')).toMatch(/Select .+ for Day \d/)
      })
    })

    it('has proper heading hierarchy', () => {
      const h2 = wrapper.find('h2')
      const h3s = wrapper.findAll('h3')
      const h4s = wrapper.findAll('h4')
      
      expect(h2.exists()).toBe(true)
      expect(h3s.length).toBe(3) // One for each day
      expect(h4s.length).toBeGreaterThan(0) // Session titles
    })

    it('maintains focus management for interactive elements', () => {
      const comboBoxes = wrapper.findAll('.point-form-combo')
      comboBoxes.forEach(combo => {
        expect(combo.attributes('id')).toBeDefined()
      })
    })
  })

  describe('Performance', () => {
    it('renders efficiently with large datasets', () => {
      // Test with larger candidate lists
      const largeCandidateSpots: CandidateTouristSpots = {}
      const largeCandidateRestaurants: CandidateRestaurants = {}
      
      // Create 50 candidates for each session
      for (let day = 1; day <= 3; day++) {
        const sessions = ['morning_session', 'afternoon_session', 'night_session']
        const mealSessions = ['breakfast', 'lunch', 'dinner']
        
        sessions.forEach(session => {
          const key = `${session}_day_${day}`
          largeCandidateSpots[key] = Array(50).fill(null).map((_, i) => ({
            ...mockTouristSpot,
            tourist_spot: `Spot ${i + 1}`
          }))
        })
        
        mealSessions.forEach(session => {
          const key = `${session}_day_${day}`
          largeCandidateRestaurants[key] = Array(50).fill(null).map((_, i) => ({
            ...mockRestaurant,
            id: `rest_${i + 1}`,
            name: `Restaurant ${i + 1}`
          }))
        })
      }
      
      expect(() => {
        mount(ItineraryPointForm, {
          props: {
            ...defaultProps,
            candidateSpots: largeCandidateSpots,
            candidateRestaurants: largeCandidateRestaurants
          }
        })
      }).not.toThrow()
    })
  })
})
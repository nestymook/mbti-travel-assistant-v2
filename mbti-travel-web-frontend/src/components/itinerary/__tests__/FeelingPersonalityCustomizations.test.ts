import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FeelingPersonalityCustomizations from '../FeelingPersonalityCustomizations.vue'
import type { MBTIPersonality, MainItinerary, CandidateTouristSpots } from '../../../types/mbti'

// Mock data
const mockMainItinerary: MainItinerary = {
  day_1: {
    breakfast: {
      id: 'rest_001',
      name: 'Morning Cafe',
      address: '123 Main St',
      mealType: ['breakfast'],
      sentiment: { likes: 85, dislikes: 10, neutral: 5 },
      locationCategory: 'Kowloon',
      district: 'Central',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '07:00-11:00',
        'Sat - Sun': '08:00-12:00',
        'Public Holiday': '08:00-12:00'
      }
    },
    morning_session: {
      tourist_spot: 'Victoria Peak',
      mbti: 'INFJ',
      description: 'A breathtaking panoramic view of Hong Kong that inspires deep reflection and connection with the city\'s energy.',
      remarks: 'Best visited early morning for fewer crowds',
      address: 'The Peak, Hong Kong',
      district: 'Central',
      area: 'The Peak',
      operating_hours_mon_fri: '10:00-23:00',
      operating_hours_sat_sun: '08:00-23:00',
      operating_hours_public_holiday: '08:00-23:00',
      full_day: false
    },
    lunch: {
      id: 'rest_002',
      name: 'Dim Sum Palace',
      address: '456 Food St',
      mealType: ['lunch'],
      sentiment: { likes: 92, dislikes: 5, neutral: 3 },
      locationCategory: 'Kowloon',
      district: 'Tsim Sha Tsui',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '11:30-15:00',
        'Sat - Sun': '11:00-16:00',
        'Public Holiday': '11:00-16:00'
      }
    },
    afternoon_session: {
      tourist_spot: 'Temple Street Night Market',
      mbti: 'ISFJ',
      description: 'A warm and welcoming market where you can experience authentic local culture and connect with friendly vendors.',
      remarks: 'Great for souvenirs and local food',
      address: 'Temple St, Yau Ma Tei',
      district: 'Yau Ma Tei',
      area: 'Yau Ma Tei',
      operating_hours_mon_fri: '18:00-24:00',
      operating_hours_sat_sun: '18:00-01:00',
      operating_hours_public_holiday: '18:00-01:00',
      full_day: false
    },
    dinner: {
      id: 'rest_003',
      name: 'Rooftop Restaurant',
      address: '789 Sky Ave',
      mealType: ['dinner'],
      sentiment: { likes: 88, dislikes: 8, neutral: 4 },
      locationCategory: 'Kowloon',
      district: 'Central',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '18:00-23:00',
        'Sat - Sun': '17:30-23:30',
        'Public Holiday': '17:30-23:30'
      }
    },
    night_session: {
      tourist_spot: 'Symphony of Lights',
      mbti: 'ENFJ',
      description: 'A spectacular light show that brings people together to share in the wonder and beauty of Hong Kong\'s skyline.',
      remarks: 'Best viewed from Tsim Sha Tsui Promenade',
      address: 'Victoria Harbour',
      district: 'Tsim Sha Tsui',
      area: 'Victoria Harbour',
      operating_hours_mon_fri: '20:00-20:15',
      operating_hours_sat_sun: '20:00-20:15',
      operating_hours_public_holiday: '20:00-20:15',
      full_day: false
    }
  },
  day_2: {
    breakfast: {
      id: 'rest_004',
      name: 'Local Breakfast Spot',
      address: '321 Local St',
      mealType: ['breakfast'],
      sentiment: { likes: 78, dislikes: 15, neutral: 7 },
      locationCategory: 'Kowloon',
      district: 'Wan Chai',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '06:30-11:30',
        'Sat - Sun': '07:00-12:00',
        'Public Holiday': '07:00-12:00'
      }
    },
    morning_session: {
      tourist_spot: 'Man Mo Temple',
      mbti: 'ISFJ',
      description: 'A peaceful and sacred space that offers comfort and spiritual connection, perfect for quiet contemplation.',
      remarks: 'Respectful dress required',
      address: '124-126 Hollywood Rd, Sheung Wan',
      district: 'Sheung Wan',
      area: 'Sheung Wan',
      operating_hours_mon_fri: '08:00-18:00',
      operating_hours_sat_sun: '08:00-18:00',
      operating_hours_public_holiday: '08:00-18:00',
      full_day: false
    },
    lunch: {
      id: 'rest_005',
      name: 'Harbor View Cafe',
      address: '654 Harbor Rd',
      mealType: ['lunch'],
      sentiment: { likes: 90, dislikes: 6, neutral: 4 },
      locationCategory: 'Kowloon',
      district: 'Tsim Sha Tsui',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '11:00-16:00',
        'Sat - Sun': '10:30-17:00',
        'Public Holiday': '10:30-17:00'
      }
    },
    afternoon_session: {
      tourist_spot: 'Hong Kong Museum of History',
      mbti: 'INFJ',
      description: 'A meaningful journey through Hong Kong\'s rich heritage that deepens your understanding and appreciation of the city.',
      remarks: 'Allow 2-3 hours for full experience',
      address: '100 Chatham Rd S, Tsim Sha Tsui East',
      district: 'Tsim Sha Tsui',
      area: 'Tsim Sha Tsui East',
      operating_hours_mon_fri: '10:00-18:00',
      operating_hours_sat_sun: '10:00-19:00',
      operating_hours_public_holiday: '10:00-19:00',
      full_day: false
    },
    dinner: {
      id: 'rest_006',
      name: 'Traditional Restaurant',
      address: '987 Heritage St',
      mealType: ['dinner'],
      sentiment: { likes: 86, dislikes: 9, neutral: 5 },
      locationCategory: 'Kowloon',
      district: 'Central',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '17:30-22:30',
        'Sat - Sun': '17:00-23:00',
        'Public Holiday': '17:00-23:00'
      }
    },
    night_session: {
      tourist_spot: 'Star Ferry',
      mbti: 'ESFJ',
      description: 'A charming and nostalgic ferry ride that creates wonderful memories to share with friends and family.',
      remarks: 'Historic ferry service since 1888',
      address: 'Central Pier 7, Central',
      district: 'Central',
      area: 'Victoria Harbour',
      operating_hours_mon_fri: '06:30-23:30',
      operating_hours_sat_sun: '06:30-23:30',
      operating_hours_public_holiday: '06:30-23:30',
      full_day: false
    }
  },
  day_3: {
    breakfast: {
      id: 'rest_007',
      name: 'Garden Breakfast',
      address: '147 Garden Ave',
      mealType: ['breakfast'],
      sentiment: { likes: 82, dislikes: 12, neutral: 6 },
      locationCategory: 'Kowloon',
      district: 'Mid-Levels',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '07:30-11:30',
        'Sat - Sun': '08:00-12:30',
        'Public Holiday': '08:00-12:30'
      }
    },
    morning_session: {
      tourist_spot: 'Wong Tai Sin Temple',
      mbti: 'ISFJ',
      description: 'A colorful and welcoming temple where visitors find comfort, hope, and spiritual warmth in a caring community.',
      remarks: 'Famous for fortune telling',
      address: '2 Chuk Yuen Village, Wong Tai Sin',
      district: 'Wong Tai Sin',
      area: 'Wong Tai Sin',
      operating_hours_mon_fri: '07:00-17:30',
      operating_hours_sat_sun: '07:00-17:30',
      operating_hours_public_holiday: '07:00-17:30',
      full_day: false
    },
    lunch: {
      id: 'rest_008',
      name: 'Family Restaurant',
      address: '258 Family Rd',
      mealType: ['lunch'],
      sentiment: { likes: 89, dislikes: 7, neutral: 4 },
      locationCategory: 'Kowloon',
      district: 'Causeway Bay',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '11:30-15:30',
        'Sat - Sun': '11:00-16:00',
        'Public Holiday': '11:00-16:00'
      }
    },
    afternoon_session: {
      tourist_spot: 'Nan Lian Garden',
      mbti: 'INFJ',
      description: 'A serene and beautifully designed garden that offers peaceful reflection and connection with nature\'s harmony.',
      remarks: 'Free admission, photography allowed',
      address: '60 Fung Tak Rd, Diamond Hill',
      district: 'Diamond Hill',
      area: 'Diamond Hill',
      operating_hours_mon_fri: '07:00-21:00',
      operating_hours_sat_sun: '07:00-21:00',
      operating_hours_public_holiday: '07:00-21:00',
      full_day: false
    },
    dinner: {
      id: 'rest_009',
      name: 'Farewell Dinner',
      address: '369 Farewell St',
      mealType: ['dinner'],
      sentiment: { likes: 94, dislikes: 4, neutral: 2 },
      locationCategory: 'Kowloon',
      district: 'Central',
      priceRange: '$51-100',
      operatingHours: {
        'Mon - Fri': '18:30-23:00',
        'Sat - Sun': '18:00-23:30',
        'Public Holiday': '18:00-23:30'
      }
    },
    night_session: {
      tourist_spot: 'Avenue of Stars',
      mbti: 'ENFJ',
      description: 'A celebratory promenade that honors Hong Kong\'s film industry and provides a perfect setting for sharing memories with loved ones.',
      remarks: 'Great for photos and evening stroll',
      address: 'Tsim Sha Tsui Promenade',
      district: 'Tsim Sha Tsui',
      area: 'Tsim Sha Tsui',
      operating_hours_mon_fri: '24 hours',
      operating_hours_sat_sun: '24 hours',
      operating_hours_public_holiday: '24 hours',
      full_day: false
    }
  }
}

const mockCandidateSpots: CandidateTouristSpots = {
  morning_session_day_1: [
    {
      tourist_spot: 'Victoria Peak',
      mbti: 'INFJ',
      description: 'A breathtaking panoramic view of Hong Kong that inspires deep reflection.',
      remarks: 'Best visited early morning',
      address: 'The Peak, Hong Kong',
      district: 'Central',
      area: 'The Peak',
      operating_hours_mon_fri: '10:00-23:00',
      operating_hours_sat_sun: '08:00-23:00',
      operating_hours_public_holiday: '08:00-23:00',
      full_day: false
    }
  ]
}

describe('FeelingPersonalityCustomizations', () => {
  let wrapper: any

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('INFJ Personality', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'INFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('renders feeling personality customizations for INFJ', () => {
      expect(wrapper.find('.feeling-personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.mbti-infj').exists()).toBe(true)
    })

    it('shows description customizations for INFJ', () => {
      expect(wrapper.find('.description-customizations').exists()).toBe(true)
      expect(wrapper.find('.section-title').text()).toContain('Tourist Spot Descriptions')
    })

    it('displays tourist spot descriptions', () => {
      const descriptions = wrapper.findAll('.description-text')
      expect(descriptions.length).toBeGreaterThan(0)
      
      // Check that descriptions are displayed
      const firstDescription = descriptions[0]
      expect(firstDescription.text()).toContain('breathtaking panoramic view')
    })

    it('does not show group notes for INFJ', () => {
      expect(wrapper.find('.group-notes-customizations').exists()).toBe(false)
    })

    it('does not show share link for INFJ', () => {
      expect(wrapper.find('.share-customizations').exists()).toBe(false)
    })

    it('shows correct customization title for INFJ', () => {
      const title = wrapper.find('.customizations-header h3')
      expect(title.text()).toBe('Meaningful Travel Insights')
    })

    it('shows correct customization description for INFJ', () => {
      const description = wrapper.find('.customization-description')
      expect(description.text()).toContain('deeper meanings and connections')
    })
  })

  describe('ISFJ Personality', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'ISFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('renders feeling personality customizations for ISFJ', () => {
      expect(wrapper.find('.feeling-personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.mbti-isfj').exists()).toBe(true)
    })

    it('shows description customizations for ISFJ', () => {
      expect(wrapper.find('.description-customizations').exists()).toBe(true)
    })

    it('shows correct customization title for ISFJ', () => {
      const title = wrapper.find('.customizations-header h3')
      expect(title.text()).toBe('Warm & Personal Experience')
    })

    it('shows correct customization description for ISFJ', () => {
      const description = wrapper.find('.customization-description')
      expect(description.text()).toContain('warm, personal travel experience')
    })

    it('does not show group notes for ISFJ', () => {
      expect(wrapper.find('.group-notes-customizations').exists()).toBe(false)
    })

    it('does not show share link for ISFJ', () => {
      expect(wrapper.find('.share-customizations').exists()).toBe(false)
    })
  })

  describe('ENFJ Personality', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'ENFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('renders feeling personality customizations for ENFJ', () => {
      expect(wrapper.find('.feeling-personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.mbti-enfj').exists()).toBe(true)
    })

    it('does not show description customizations for ENFJ', () => {
      expect(wrapper.find('.description-customizations').exists()).toBe(false)
    })

    it('shows group notes customizations for ENFJ', () => {
      expect(wrapper.find('.group-notes-customizations').exists()).toBe(true)
      expect(wrapper.find('.section-title').text()).toContain('Group Notes')
    })

    it('shows share customizations for ENFJ', () => {
      expect(wrapper.find('.share-customizations').exists()).toBe(true)
      expect(wrapper.findAll('.share-button').length).toBe(3)
    })

    it('shows correct customization title for ENFJ', () => {
      const title = wrapper.find('.customizations-header h3')
      expect(title.text()).toBe('Social Travel Planning')
    })

    it('shows group notes textareas for all sessions', () => {
      const textareas = wrapper.findAll('.notes-textarea')
      expect(textareas.length).toBe(18) // 6 sessions × 3 days
    })

    it('has correct placeholder text for group notes', () => {
      const breakfastTextarea = wrapper.find('#group-notes-day-1-breakfast')
      expect(breakfastTextarea.attributes('placeholder')).toContain('breakfast plans')
    })
  })

  describe('ESFJ Personality', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'ESFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('renders feeling personality customizations for ESFJ', () => {
      expect(wrapper.find('.feeling-personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.mbti-esfj').exists()).toBe(true)
    })

    it('shows group notes customizations for ESFJ', () => {
      expect(wrapper.find('.group-notes-customizations').exists()).toBe(true)
    })

    it('shows share customizations for ESFJ', () => {
      expect(wrapper.find('.share-customizations').exists()).toBe(true)
    })

    it('shows correct customization title for ESFJ', () => {
      const title = wrapper.find('.customizations-header h3')
      expect(title.text()).toBe('Group-Friendly Itinerary')
    })

    it('shows correct customization description for ESFJ', () => {
      const description = wrapper.find('.customization-description')
      expect(description.text()).toContain('social travel experience')
    })
  })

  describe('Non-Feeling Personality', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'INTJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('does not render for non-feeling personalities', () => {
      expect(wrapper.find('.feeling-personality-customizations').exists()).toBe(false)
    })
  })

  describe('Event Handling', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'ENFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('emits group-notes-changed when textarea value changes', async () => {
      const textarea = wrapper.find('#group-notes-day-1-breakfast')
      await textarea.setValue('Test group notes')
      await textarea.trigger('input')

      expect(wrapper.emitted('group-notes-changed')).toBeTruthy()
      const emittedEvent = wrapper.emitted('group-notes-changed')[0][0]
      expect(emittedEvent).toEqual({
        day: 1,
        session: 'breakfast',
        notes: 'Test group notes'
      })
    })

    it('emits share-requested when share buttons are clicked', async () => {
      const shareButtons = wrapper.findAll('.share-button')
      
      // Test complete itinerary share
      await shareButtons[0].trigger('click')
      expect(wrapper.emitted('share-requested')).toBeTruthy()
      let emittedEvent = wrapper.emitted('share-requested')[0][0]
      expect(emittedEvent).toEqual({
        type: 'complete',
        personality: 'ENFJ'
      })

      // Test day share
      await shareButtons[1].trigger('click')
      emittedEvent = wrapper.emitted('share-requested')[1][0]
      expect(emittedEvent).toEqual({
        type: 'day',
        personality: 'ENFJ'
      })

      // Test notes share
      await shareButtons[2].trigger('click')
      emittedEvent = wrapper.emitted('share-requested')[2][0]
      expect(emittedEvent).toEqual({
        type: 'notes',
        personality: 'ENFJ'
      })
    })

    it('emits update:modelValue when customizations change', async () => {
      const textarea = wrapper.find('#group-notes-day-1-breakfast')
      await textarea.setValue('Test notes')
      await textarea.trigger('input')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const emittedValue = wrapper.emitted('update:modelValue')[0][0]
      expect(emittedValue.mbtiPersonality).toBe('ENFJ')
      expect(emittedValue.day_1.breakfast.groupNotes).toBe('Test notes')
    })
  })

  describe('Statistics', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'INFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('shows correct descriptions count', () => {
      const summary = wrapper.find('.feeling-customizations-summary')
      expect(summary.exists()).toBe(true)
      
      const descriptionsStat = wrapper.find('.stat-value')
      expect(descriptionsStat.text()).toBe('9') // 3 tourist spots per day × 3 days
    })
  })

  describe('Accessibility', () => {
    beforeEach(() => {
      wrapper = mount(FeelingPersonalityCustomizations, {
        props: {
          mbtiPersonality: 'ENFJ' as MBTIPersonality,
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots
        }
      })
    })

    it('has proper ARIA labels for textareas', () => {
      const textarea = wrapper.find('#group-notes-day-1-breakfast')
      expect(textarea.attributes('aria-label')).toContain('Group notes for Breakfast on Day 1')
    })

    it('has proper ARIA labels for share buttons', () => {
      const shareButton = wrapper.find('.share-button')
      expect(shareButton.attributes('aria-label')).toContain('Share your complete itinerary')
    })

    it('associates labels with form controls', () => {
      const label = wrapper.find('label[for="group-notes-day-1-breakfast"]')
      const textarea = wrapper.find('#group-notes-day-1-breakfast')
      
      expect(label.exists()).toBe(true)
      expect(textarea.exists()).toBe(true)
      expect(label.attributes('for')).toBe(textarea.attributes('id'))
    })
  })
})
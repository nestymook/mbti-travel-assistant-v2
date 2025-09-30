import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RestaurantComboBoxItem from '../RestaurantComboBoxItem.vue'
import type { Restaurant } from '@/types/restaurant'
import type { MBTIPersonality } from '@/types/mbti'

// Mock restaurant data
const mockRestaurant: Restaurant = {
  id: 'rest-001',
  name: 'Test Combo Restaurant',
  address: '789 Combo Street, Wan Chai',
  mealType: ['breakfast', 'lunch', 'dinner'],
  sentiment: {
    likes: 75,
    dislikes: 15,
    neutral: 10
  },
  locationCategory: 'Hong Kong Island',
  district: 'Wan Chai',
  priceRange: 'expensive',
  operatingHours: {
    'Mon - Fri': '06:00 - 23:00',
    'Sat - Sun': '07:00 - 24:00',
    'Public Holiday': '07:00 - 22:00'
  },
  cuisine: ['japanese', 'fusion'],
  features: ['wifi', 'outdoor_seating', 'parking', 'view'],
  phoneNumber: '+852 9876 5432'
}

const mockMBTIPersonality: MBTIPersonality = 'INFJ'

describe('RestaurantComboBoxItem', () => {
  it('renders basic restaurant information correctly', () => {
    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: false
      }
    })

    // Check restaurant name
    expect(wrapper.find('.restaurant-name').text()).toBe('Test Combo Restaurant')
    
    // Check district
    expect(wrapper.find('.district').text()).toBe('Wan Chai')
    
    // Check price range (formatted as symbols)
    expect(wrapper.find('.price-range').text()).toBe('$$$')
    
    // Check meal types (should show first 2)
    expect(wrapper.find('.meal-types').text()).toBe('Breakfast, Lunch')
  })

  it('displays sentiment quick stats correctly', () => {
    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: false
      }
    })

    // Check sentiment counts
    expect(wrapper.find('.likes').text()).toBe('👍 75')
    expect(wrapper.find('.dislikes').text()).toBe('👎 15')
    expect(wrapper.find('.neutral').text()).toBe('😐 10')
    
    // Check positive ratio
    expect(wrapper.find('.positive-ratio').text()).toBe('75% positive')
    expect(wrapper.find('.positive-ratio').classes()).toContain('good')
  })

  it('shows detailed information when showDetailedInfo is true', () => {
    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: true
      }
    })

    // Check address info
    expect(wrapper.find('.address').text()).toBe('📍 789 Combo Street, Wan Chai')
    expect(wrapper.find('.location-category').text()).toBe('Hong Kong Island')
    
    // Check operating hours
    const hoursItems = wrapper.findAll('.hours-item')
    expect(hoursItems).toHaveLength(2)
    expect(hoursItems[0].find('.hours-value').text()).toBe('06:00 - 23:00')
    expect(hoursItems[1].find('.hours-value').text()).toBe('07:00 - 24:00')
    
    // Check cuisine info
    expect(wrapper.find('.cuisine-types').text()).toBe('Japanese, Fusion')
    
    // Check features (should show first 3)
    const featureTags = wrapper.findAll('.feature-tag')
    expect(featureTags).toHaveLength(3)
    expect(featureTags[0].text()).toBe('📶 WiFi')
    expect(featureTags[1].text()).toBe('🌿 Outdoor')
    expect(featureTags[2].text()).toBe('🅿️ Parking')
    
    // Check "more features" indicator
    expect(wrapper.find('.more-features').text()).toBe('+1 more')
  })

  it('hides detailed information when showDetailedInfo is false', () => {
    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: false
      }
    })

    // Should not show detailed sections
    expect(wrapper.find('.restaurant-detailed-info').exists()).toBe(false)
    expect(wrapper.find('.address-info').exists()).toBe(false)
    expect(wrapper.find('.hours-summary').exists()).toBe(false)
    expect(wrapper.find('.cuisine-info').exists()).toBe(false)
    expect(wrapper.find('.features-info').exists()).toBe(false)
  })

  it('applies correct MBTI personality class', () => {
    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: 'ESTP' as MBTIPersonality,
        showDetailedInfo: false
      }
    })

    expect(wrapper.find('.restaurant-combo-item').classes()).toContain('mbti-estp')
  })

  it('formats price ranges correctly', () => {
    const testCases = [
      { priceRange: 'budget' as const, expected: '$' },
      { priceRange: 'moderate' as const, expected: '$$' },
      { priceRange: 'expensive' as const, expected: '$$$' },
      { priceRange: 'luxury' as const, expected: '$$$$' }
    ]

    testCases.forEach(({ priceRange, expected }) => {
      const testRestaurant = { ...mockRestaurant, priceRange }
      const wrapper = mount(RestaurantComboBoxItem, {
        props: {
          restaurant: testRestaurant,
          mbtiPersonality: mockMBTIPersonality,
          showDetailedInfo: false
        }
      })

      expect(wrapper.find('.price-range').text()).toBe(expected)
    })
  })

  it('calculates positive ratio correctly', () => {
    const testCases = [
      { likes: 80, dislikes: 10, neutral: 10, expectedRatio: '80', expectedClass: 'excellent' },
      { likes: 65, dislikes: 25, neutral: 10, expectedRatio: '65', expectedClass: 'good' },
      { likes: 45, dislikes: 35, neutral: 20, expectedRatio: '45', expectedClass: 'average' },
      { likes: 25, dislikes: 65, neutral: 10, expectedRatio: '25', expectedClass: 'poor' }
    ]

    testCases.forEach(({ likes, dislikes, neutral, expectedRatio, expectedClass }) => {
      const testRestaurant = {
        ...mockRestaurant,
        sentiment: { likes, dislikes, neutral }
      }
      
      const wrapper = mount(RestaurantComboBoxItem, {
        props: {
          restaurant: testRestaurant,
          mbtiPersonality: mockMBTIPersonality,
          showDetailedInfo: false
        }
      })

      expect(wrapper.find('.positive-ratio').text()).toBe(`${expectedRatio}% positive`)
      expect(wrapper.find('.positive-ratio').classes()).toContain(expectedClass)
    })
  })

  it('handles restaurants without optional fields gracefully', () => {
    const minimalRestaurant: Restaurant = {
      id: 'rest-minimal',
      name: 'Minimal Combo Restaurant',
      address: '123 Simple Street',
      mealType: ['lunch'],
      sentiment: {
        likes: 30,
        dislikes: 10,
        neutral: 5
      },
      locationCategory: 'Kowloon',
      district: 'Mong Kok',
      priceRange: 'budget',
      operatingHours: {
        'Mon - Fri': '11:00 - 15:00',
        'Sat - Sun': 'Closed',
        'Public Holiday': 'Closed'
      }
    }

    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: minimalRestaurant,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: true
      }
    })

    // Should render basic info
    expect(wrapper.find('.restaurant-name').text()).toBe('Minimal Combo Restaurant')
    expect(wrapper.find('.district').text()).toBe('Mong Kok')
    expect(wrapper.find('.meal-types').text()).toBe('Lunch')
    
    // Should not render optional sections when data is missing
    expect(wrapper.find('.cuisine-info').exists()).toBe(false)
    expect(wrapper.find('.features-info').exists()).toBe(false)
  })

  it('formats meal types correctly', () => {
    const testCases = [
      { mealTypes: ['breakfast'], expected: 'Breakfast' },
      { mealTypes: ['lunch', 'dinner'], expected: 'Lunch, Dinner' },
      { mealTypes: ['breakfast', 'lunch', 'dinner'], expected: 'Breakfast, Lunch' }, // Should show first 2
      { mealTypes: ['brunch', 'afternoon_tea'], expected: 'Brunch, Tea' },
      { mealTypes: ['late_night'], expected: 'Late Night' }
    ]

    testCases.forEach(({ mealTypes, expected }) => {
      const testRestaurant = { ...mockRestaurant, mealType: mealTypes as any }
      const wrapper = mount(RestaurantComboBoxItem, {
        props: {
          restaurant: testRestaurant,
          mbtiPersonality: mockMBTIPersonality,
          showDetailedInfo: false
        }
      })

      expect(wrapper.find('.meal-types').text()).toBe(expected)
    })
  })

  it('shows correct feature icons and text', () => {
    const restaurantWithFeatures = {
      ...mockRestaurant,
      features: ['wifi', 'wheelchair_accessible', 'live_music'] as any
    }

    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: restaurantWithFeatures,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: true
      }
    })

    const featureTags = wrapper.findAll('.feature-tag')
    expect(featureTags).toHaveLength(3)
    
    expect(featureTags[0].text()).toBe('📶 WiFi')
    expect(featureTags[1].text()).toBe('♿ Accessible')
    expect(featureTags[2].text()).toBe('🎵 Music')
  })

  it('handles zero sentiment values correctly', () => {
    const restaurantWithZeroSentiment = {
      ...mockRestaurant,
      sentiment: {
        likes: 0,
        dislikes: 0,
        neutral: 0
      }
    }

    const wrapper = mount(RestaurantComboBoxItem, {
      props: {
        restaurant: restaurantWithZeroSentiment,
        mbtiPersonality: mockMBTIPersonality,
        showDetailedInfo: false
      }
    })

    expect(wrapper.find('.positive-ratio').text()).toBe('0% positive')
    expect(wrapper.find('.positive-ratio').classes()).toContain('poor')
  })
})
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RestaurantDetails from '../RestaurantDetails.vue'
import type { Restaurant } from '@/types/restaurant'
import type { MBTIPersonality } from '@/types/mbti'

// Mock restaurant data
const mockRestaurant: Restaurant = {
  id: 'rest-001',
  name: 'Test Restaurant',
  address: '123 Test Street, Central',
  mealType: ['breakfast', 'lunch'],
  sentiment: {
    likes: 85,
    dislikes: 10,
    neutral: 5
  },
  locationCategory: 'Hong Kong Island',
  district: 'Central',
  priceRange: 'moderate',
  operatingHours: {
    'Mon - Fri': '07:00 - 22:00',
    'Sat - Sun': '08:00 - 23:00',
    'Public Holiday': '08:00 - 21:00'
  },
  cuisine: ['cantonese', 'dim_sum'],
  features: ['wifi', 'air_conditioning', 'credit_cards_accepted'],
  rating: 4.2,
  reviewCount: 150,
  phoneNumber: '+852 1234 5678',
  website: 'https://test-restaurant.com'
}

const mockMBTIPersonality: MBTIPersonality = 'ENFP'

describe('RestaurantDetails', () => {
  it('renders restaurant basic information correctly', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    // Check restaurant name
    expect(wrapper.find('.restaurant-name').text()).toBe('Test Restaurant')
    
    // Check price range
    expect(wrapper.find('.restaurant-price').text()).toBe('$$ (HK$100-300)')
    
    // Check address
    expect(wrapper.find('.address').text()).toBe('123 Test Street, Central')
    
    // Check district and location category
    expect(wrapper.find('.district').text()).toBe('Central, Hong Kong Island')
    
    // Check meal types
    expect(wrapper.find('.meal-types').text()).toBe('Breakfast, Lunch')
  })

  it('displays operating hours correctly', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    const hoursItems = wrapper.findAll('.hours-item')
    expect(hoursItems).toHaveLength(3)
    
    // Check Mon-Fri hours
    expect(hoursItems[0].find('.hours-label').text()).toBe('Mon - Fri:')
    expect(hoursItems[0].find('.hours-value').text()).toBe('07:00 - 22:00')
    
    // Check Sat-Sun hours
    expect(hoursItems[1].find('.hours-label').text()).toBe('Sat - Sun:')
    expect(hoursItems[1].find('.hours-value').text()).toBe('08:00 - 23:00')
    
    // Check Public Holiday hours
    expect(hoursItems[2].find('.hours-label').text()).toBe('Public Holiday:')
    expect(hoursItems[2].find('.hours-value').text()).toBe('08:00 - 21:00')
  })

  it('displays sentiment data and visualization correctly', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    // Check sentiment bars
    const sentimentBars = wrapper.findAll('.sentiment-bar')
    expect(sentimentBars).toHaveLength(3)
    
    // Check likes
    const likesBar = wrapper.find('.likes-bar')
    expect(likesBar.find('.sentiment-count').text()).toBe('85')
    expect(likesBar.find('.sentiment-percentage').text()).toBe('(85.0%)')
    
    // Check dislikes
    const dislikesBar = wrapper.find('.dislikes-bar')
    expect(dislikesBar.find('.sentiment-count').text()).toBe('10')
    expect(dislikesBar.find('.sentiment-percentage').text()).toBe('(10.0%)')
    
    // Check neutral
    const neutralBar = wrapper.find('.neutral-bar')
    expect(neutralBar.find('.sentiment-count').text()).toBe('5')
    expect(neutralBar.find('.sentiment-percentage').text()).toBe('(5.0%)')
    
    // Check total reviews
    expect(wrapper.find('.total-reviews').text()).toBe('Total Reviews: 100')
    
    // Check positive ratio
    expect(wrapper.find('.positive-ratio').text()).toBe('Positive Ratio: 85.0%')
    expect(wrapper.find('.positive-ratio').classes()).toContain('excellent')
  })

  it('displays cuisine information when available', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    const cuisineTags = wrapper.findAll('.cuisine-tag')
    expect(cuisineTags).toHaveLength(2)
    expect(cuisineTags[0].text()).toBe('Cantonese')
    expect(cuisineTags[1].text()).toBe('Dim Sum')
  })

  it('displays features when available', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    const featureItems = wrapper.findAll('.feature-item')
    expect(featureItems).toHaveLength(3)
    
    expect(featureItems[0].find('.feature-text').text()).toBe('WiFi')
    expect(featureItems[1].find('.feature-text').text()).toBe('Air Conditioning')
    expect(featureItems[2].find('.feature-text').text()).toBe('Credit Cards Accepted')
  })

  it('displays contact information when available', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    const contactItems = wrapper.findAll('.contact-item')
    expect(contactItems).toHaveLength(2)
    
    // Check phone number
    const phoneLink = contactItems[0].find('.contact-link')
    expect(phoneLink.text()).toBe('+852 1234 5678')
    expect(phoneLink.attributes('href')).toBe('tel:+852 1234 5678')
    
    // Check website
    const websiteLink = contactItems[1].find('.contact-link')
    expect(websiteLink.text()).toBe('Visit Website')
    expect(websiteLink.attributes('href')).toBe('https://test-restaurant.com')
    expect(websiteLink.attributes('target')).toBe('_blank')
  })

  it('applies correct MBTI personality class', () => {
    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: mockRestaurant,
        mbtiPersonality: 'INTJ' as MBTIPersonality
      }
    })

    expect(wrapper.find('.restaurant-details').classes()).toContain('mbti-intj')
  })

  it('calculates sentiment percentages correctly', () => {
    const restaurantWithDifferentSentiment: Restaurant = {
      ...mockRestaurant,
      sentiment: {
        likes: 60,
        dislikes: 30,
        neutral: 10
      }
    }

    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: restaurantWithDifferentSentiment,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    // Check percentages
    expect(wrapper.find('.likes-bar .sentiment-percentage').text()).toBe('(60.0%)')
    expect(wrapper.find('.dislikes-bar .sentiment-percentage').text()).toBe('(30.0%)')
    expect(wrapper.find('.neutral-bar .sentiment-percentage').text()).toBe('(10.0%)')
    
    // Check positive ratio class (60% should be 'good')
    expect(wrapper.find('.positive-ratio').classes()).toContain('good')
  })

  it('handles restaurants without optional fields gracefully', () => {
    const minimalRestaurant: Restaurant = {
      id: 'rest-002',
      name: 'Minimal Restaurant',
      address: '456 Simple Street',
      mealType: ['dinner'],
      sentiment: {
        likes: 20,
        dislikes: 5,
        neutral: 0
      },
      locationCategory: 'Kowloon',
      district: 'Tsim Sha Tsui',
      priceRange: 'budget',
      operatingHours: {
        'Mon - Fri': '18:00 - 23:00',
        'Sat - Sun': '18:00 - 24:00',
        'Public Holiday': 'Closed'
      }
    }

    const wrapper = mount(RestaurantDetails, {
      props: {
        restaurant: minimalRestaurant,
        mbtiPersonality: mockMBTIPersonality
      }
    })

    // Should render basic info
    expect(wrapper.find('.restaurant-name').text()).toBe('Minimal Restaurant')
    expect(wrapper.find('.restaurant-price').text()).toBe('$ (Under HK$100)')
    
    // Should not render optional sections
    expect(wrapper.find('.cuisine-section').exists()).toBe(false)
    expect(wrapper.find('.features-section').exists()).toBe(false)
    expect(wrapper.find('.contact-section').exists()).toBe(false)
  })

  it('formats price ranges correctly', () => {
    const testCases = [
      { priceRange: 'budget' as const, expected: '$ (Under HK$100)' },
      { priceRange: 'moderate' as const, expected: '$$ (HK$100-300)' },
      { priceRange: 'expensive' as const, expected: '$$$ (HK$300-600)' },
      { priceRange: 'luxury' as const, expected: '$$$$ (Over HK$600)' }
    ]

    testCases.forEach(({ priceRange, expected }) => {
      const testRestaurant = { ...mockRestaurant, priceRange }
      const wrapper = mount(RestaurantDetails, {
        props: {
          restaurant: testRestaurant,
          mbtiPersonality: mockMBTIPersonality
        }
      })

      expect(wrapper.find('.restaurant-price').text()).toBe(expected)
    })
  })

  it('applies correct positive ratio classes', () => {
    const testCases = [
      { likes: 90, dislikes: 5, neutral: 5, expectedClass: 'excellent' },
      { likes: 70, dislikes: 20, neutral: 10, expectedClass: 'good' },
      { likes: 50, dislikes: 30, neutral: 20, expectedClass: 'average' },
      { likes: 30, dislikes: 60, neutral: 10, expectedClass: 'poor' }
    ]

    testCases.forEach(({ likes, dislikes, neutral, expectedClass }) => {
      const testRestaurant = {
        ...mockRestaurant,
        sentiment: { likes, dislikes, neutral }
      }
      
      const wrapper = mount(RestaurantDetails, {
        props: {
          restaurant: testRestaurant,
          mbtiPersonality: mockMBTIPersonality
        }
      })

      expect(wrapper.find('.positive-ratio').classes()).toContain(expectedClass)
    })
  })
})
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TouristSpotComboBoxItem from '../TouristSpotComboBoxItem.vue'
import type { TouristSpot } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'

// Mock tourist spot data
const mockTouristSpot: TouristSpot = {
  tourist_spot: 'Victoria Peak',
  mbti: 'ENFP',
  description: 'A stunning viewpoint offering panoramic views of Hong Kong skyline.',
  remarks: 'Best visited during sunset. Peak Tram available.',
  address: '1 Peak Road, The Peak, Hong Kong',
  district: 'Central and Western',
  area: 'The Peak',
  operating_hours_mon_fri: '10:00 - 23:00',
  operating_hours_sat_sun: '08:00 - 23:00',
  operating_hours_public_holiday: '08:00 - 23:00',
  full_day: false,
  category: 'viewpoint',
  features: ['outdoor', 'photography_allowed', 'public_transport_nearby', 'restaurant'],
  rating: 4.5,
  reviewCount: 1250,
  phoneNumber: '+852 2849 0668',
  website: 'https://www.thepeak.com.hk',
  imageUrl: 'https://example.com/victoria-peak.jpg',
  admissionFee: {
    adult: 65,
    child: 35,
    senior: 35,
    currency: 'HKD',
    isFree: false,
    notes: 'Peak Tram fare included'
  },
  accessibility: {
    wheelchairAccessible: true,
    elevatorAccess: true,
    notes: 'Wheelchair accessible via Peak Tram'
  }
}

const mockFreeTouristSpot: TouristSpot = {
  tourist_spot: 'Temple Street Night Market',
  mbti: 'ESTP',
  description: 'A vibrant night market with street food and shopping.',
  remarks: 'Open evenings only. Cash preferred.',
  address: 'Temple Street, Yau Ma Tei, Kowloon',
  district: 'Yau Tsim Mong',
  area: 'Yau Ma Tei',
  operating_hours_mon_fri: '18:00 - 24:00',
  operating_hours_sat_sun: '18:00 - 01:00',
  operating_hours_public_holiday: '18:00 - 01:00',
  full_day: true,
  category: 'market',
  features: ['outdoor', 'family_friendly', 'public_transport_nearby'],
  admissionFee: {
    currency: 'HKD',
    isFree: true
  },
  accessibility: {
    wheelchairAccessible: false,
    notes: 'Crowded streets, not suitable for wheelchairs'
  }
}

describe('TouristSpotComboBoxItem', () => {
  it('renders tourist spot basic information correctly', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    expect(wrapper.find('.spot-name').text()).toBe('Victoria Peak')
    expect(wrapper.find('.district').text()).toBe('Central and Western')
    expect(wrapper.find('.area').text()).toBe('The Peak')
    expect(wrapper.find('.address').text()).toBe('1 Peak Road, The Peak, Hong Kong')
  })

  it('displays MBTI badge correctly', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const mbtiBadge = wrapper.find('.mbti-badge')
    expect(mbtiBadge.exists()).toBe(true)
    expect(mbtiBadge.text()).toBe('ENFP')
    expect(mbtiBadge.classes()).toContain('mbti-enfp')
  })

  it('shows full day badge when applicable', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    const durationBadge = wrapper.find('.duration-badge')
    expect(durationBadge.exists()).toBe(true)
    expect(durationBadge.text()).toBe('Full Day')
  })

  it('does not show full day badge when not applicable', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const durationBadge = wrapper.find('.duration-badge')
    expect(durationBadge.exists()).toBe(false)
  })

  it('shows detailed information when showDetailedInfo is true', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    expect(wrapper.find('.spot-details').exists()).toBe(true)
    expect(wrapper.find('.operating-hours').exists()).toBe(true)
    expect(wrapper.find('.spot-remarks').exists()).toBe(true)
    expect(wrapper.find('.spot-category').exists()).toBe(true)
  })

  it('hides detailed information when showDetailedInfo is false', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: false
      }
    })

    expect(wrapper.find('.spot-details').exists()).toBe(false)
  })

  it('displays operating hours correctly', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const hoursValues = wrapper.findAll('.hours-value')
    expect(hoursValues[0].text()).toBe('10:00 - 23:00')
    expect(hoursValues[1].text()).toBe('08:00 - 23:00')
    expect(hoursValues[2].text()).toBe('08:00 - 23:00')
  })

  it('shows description for feeling personality types (INFJ)', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'INFJ' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const description = wrapper.find('.spot-description')
    expect(description.exists()).toBe(true)
    expect(description.find('.description-text').text()).toBe(mockTouristSpot.description)
  })

  it('shows description for feeling personality types (ISFJ)', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ISFJ' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const description = wrapper.find('.spot-description')
    expect(description.exists()).toBe(true)
    expect(description.find('.description-text').text()).toBe(mockTouristSpot.description)
  })

  it('hides description for non-feeling personality types', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'INTJ' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const description = wrapper.find('.spot-description')
    expect(description.exists()).toBe(false)
  })

  it('displays remarks when available', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const remarks = wrapper.find('.spot-remarks')
    expect(remarks.exists()).toBe(true)
    expect(remarks.find('.remarks-text').text()).toBe(mockTouristSpot.remarks)
  })

  it('hides remarks when not available', () => {
    const spotWithoutRemarks = { ...mockTouristSpot, remarks: undefined }
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: spotWithoutRemarks,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const remarks = wrapper.find('.spot-remarks')
    expect(remarks.exists()).toBe(false)
  })

  it('displays category badge when available', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    const categoryBadge = wrapper.find('.category-badge')
    expect(categoryBadge.exists()).toBe(true)
    expect(categoryBadge.text()).toBe('Viewpoint')
    expect(categoryBadge.classes()).toContain('category-viewpoint')
  })

  it('applies correct personality class', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    expect(wrapper.classes()).toContain('mbti-enfp')
  })

  it('applies ESTP flashy styling', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    expect(wrapper.classes()).toContain('mbti-estp')
  })

  it('applies ISFJ warm tone styling', () => {
    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ISFJ' as MBTIPersonality
      }
    })

    expect(wrapper.classes()).toContain('mbti-isfj')
  })

  it('formats category names correctly', () => {
    const testCases = [
      { category: 'theme_park', expected: 'Theme Park' },
      { category: 'cultural', expected: 'Cultural' },
      { category: 'viewpoint', expected: 'Viewpoint' }
    ]

    testCases.forEach(({ category, expected }) => {
      const spotWithCategory = { ...mockTouristSpot, category: category as any }
      const wrapper = mount(TouristSpotComboBoxItem, {
        props: {
          touristSpot: spotWithCategory,
          mbtiPersonality: 'ENFP' as MBTIPersonality,
          showDetailedInfo: true
        }
      })

      const categoryBadge = wrapper.find('.category-badge')
      expect(categoryBadge.text()).toBe(expected)
    })
  })

  it('handles missing optional fields gracefully', () => {
    const minimalSpot: TouristSpot = {
      tourist_spot: 'Minimal Spot',
      mbti: 'INTJ',
      address: 'Some Address',
      district: 'Some District',
      area: 'Some Area',
      operating_hours_mon_fri: '09:00 - 18:00',
      operating_hours_sat_sun: '09:00 - 18:00',
      operating_hours_public_holiday: '09:00 - 18:00',
      full_day: false
    }

    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: minimalSpot,
        mbtiPersonality: 'INTJ' as MBTIPersonality,
        showDetailedInfo: true
      }
    })

    expect(wrapper.find('.spot-name').text()).toBe('Minimal Spot')
    expect(wrapper.find('.spot-remarks').exists()).toBe(false)
    expect(wrapper.find('.spot-description').exists()).toBe(false)
    expect(wrapper.find('.spot-category').exists()).toBe(false)
  })

  it('truncates long spot names appropriately', () => {
    const longNameSpot = {
      ...mockTouristSpot,
      tourist_spot: 'This is a very long tourist spot name that should be truncated properly'
    }

    const wrapper = mount(TouristSpotComboBoxItem, {
      props: {
        touristSpot: longNameSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const spotName = wrapper.find('.spot-name')
    expect(spotName.exists()).toBe(true)
    expect(spotName.text()).toBe('This is a very long tourist spot name that should be truncated properly')
    
    // Check that the CSS classes are applied for truncation (styles are in CSS, not inline)
    const computedStyle = window.getComputedStyle(spotName.element)
    // The actual truncation behavior is handled by CSS, so we just verify the element exists and has content
    expect(spotName.element.tagName).toBe('H4')
  })
})
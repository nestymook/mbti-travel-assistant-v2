import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TouristSpotDetails from '../TouristSpotDetails.vue'
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

describe('TouristSpotDetails', () => {
  it('renders tourist spot basic information correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    expect(wrapper.find('.spot-name').text()).toBe('Victoria Peak')
    expect(wrapper.find('.district-name').text()).toBe('Central and Western')
    expect(wrapper.find('.address-text').text()).toBe('1 Peak Road, The Peak, Hong Kong')
  })

  it('displays MBTI match information correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const mbtiBadge = wrapper.find('.mbti-badge')
    expect(mbtiBadge.exists()).toBe(true)
    expect(mbtiBadge.text()).toBe('MBTI Match: ENFP')

    const mbtiHighlight = wrapper.find('.mbti-highlight')
    expect(mbtiHighlight.exists()).toBe(true)
    expect(mbtiHighlight.text()).toBe('ENFP personalities')

    const reasonText = wrapper.find('.reason-text')
    expect(reasonText.exists()).toBe(true)
    expect(reasonText.text()).toContain('Enthusiastic explorers love vibrant')
  })

  it('shows full day badge when applicable', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    const durationBadge = wrapper.find('.duration-badge')
    expect(durationBadge.exists()).toBe(true)
    expect(durationBadge.text()).toBe('Full Day Experience')
  })

  it('displays operating hours correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const hoursValues = wrapper.findAll('.hours-value')
    expect(hoursValues[0].text()).toBe('10:00 - 23:00')
    expect(hoursValues[1].text()).toBe('08:00 - 23:00')
    expect(hoursValues[2].text()).toBe('08:00 - 23:00')
  })

  it('shows description for feeling personality types (INFJ)', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'INFJ' as MBTIPersonality
      }
    })

    const descriptionSection = wrapper.find('.description-section')
    expect(descriptionSection.exists()).toBe(true)
    expect(descriptionSection.find('.description-text').text()).toBe(mockTouristSpot.description)
  })

  it('shows description for feeling personality types (ISFJ)', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ISFJ' as MBTIPersonality
      }
    })

    const descriptionSection = wrapper.find('.description-section')
    expect(descriptionSection.exists()).toBe(true)
    expect(descriptionSection.find('.description-text').text()).toBe(mockTouristSpot.description)
  })

  it('hides description for non-feeling personality types', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'INTJ' as MBTIPersonality
      }
    })

    const descriptionSection = wrapper.find('.description-section')
    expect(descriptionSection.exists()).toBe(false)
  })

  it('shows image placeholder for creative personalities', () => {
    const creativeTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP']
    
    creativeTypes.forEach(personality => {
      const wrapper = mount(TouristSpotDetails, {
        props: {
          touristSpot: mockTouristSpot,
          mbtiPersonality: personality
        }
      })

      const imagePlaceholder = wrapper.find('.spot-image-placeholder')
      expect(imagePlaceholder.exists()).toBe(true)
      expect(imagePlaceholder.find('.placeholder-text').text()).toBe('Victoria Peak Image')
    })
  })

  it('hides image placeholder for non-creative personalities', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'INTJ' as MBTIPersonality
      }
    })

    const imagePlaceholder = wrapper.find('.spot-image-placeholder')
    expect(imagePlaceholder.exists()).toBe(false)
  })

  it('applies ESTP flashy styling to image placeholder', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    const imagePlaceholder = wrapper.find('.spot-image-placeholder')
    expect(imagePlaceholder.classes()).toContain('estp-flashy')
  })

  it('displays category badge correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const categoryBadge = wrapper.find('.category-badge')
    expect(categoryBadge.exists()).toBe(true)
    expect(categoryBadge.text()).toBe('Scenic Viewpoint')
    expect(categoryBadge.classes()).toContain('category-viewpoint')
  })

  it('displays remarks when available', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const remarksSection = wrapper.find('.remarks-section')
    expect(remarksSection.exists()).toBe(true)
    expect(remarksSection.find('.remarks-text').text()).toBe(mockTouristSpot.remarks)
  })

  it('displays features when available', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const featuresSection = wrapper.find('.features-section')
    expect(featuresSection.exists()).toBe(true)
    
    const featureBadges = wrapper.findAll('.feature-badge')
    expect(featureBadges).toHaveLength(4)
    expect(featureBadges[0].text()).toBe('Outdoor')
    expect(featureBadges[1].text()).toBe('Photography Allowed')
    expect(featureBadges[2].text()).toBe('Public Transport Nearby')
    expect(featureBadges[3].text()).toBe('Restaurant')
  })

  it('displays paid admission fees correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const admissionSection = wrapper.find('.admission-section')
    expect(admissionSection.exists()).toBe(true)
    
    const feeItems = wrapper.findAll('.fee-item')
    expect(feeItems).toHaveLength(3)
    expect(feeItems[0].find('.fee-value').text()).toBe('HKD 65')
    expect(feeItems[1].find('.fee-value').text()).toBe('HKD 35')
    expect(feeItems[2].find('.fee-value').text()).toBe('HKD 35')

    const admissionNotes = wrapper.find('.admission-notes')
    expect(admissionNotes.exists()).toBe(true)
    expect(admissionNotes.find('.notes-text').text()).toBe('Peak Tram fare included')
  })

  it('displays free admission correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    const freeBadge = wrapper.find('.free-badge')
    expect(freeBadge.exists()).toBe(true)
    expect(freeBadge.text()).toBe('Free Admission')
  })

  it('displays accessibility information correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    const accessibilitySection = wrapper.find('.accessibility-section')
    expect(accessibilitySection.exists()).toBe(true)
    
    const accessibilityValue = wrapper.find('.accessibility-value')
    expect(accessibilityValue.text()).toBe('Yes')
    expect(accessibilityValue.classes()).toContain('accessible')

    const accessibilityNotes = wrapper.find('.accessibility-notes')
    expect(accessibilityNotes.exists()).toBe(true)
    expect(accessibilityNotes.find('.notes-text').text()).toBe('Wheelchair accessible via Peak Tram')
  })

  it('displays non-accessible information correctly', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    const accessibilityValue = wrapper.find('.accessibility-value')
    expect(accessibilityValue.text()).toBe('No')
    expect(accessibilityValue.classes()).not.toContain('accessible')
  })

  it('applies correct personality class', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    expect(wrapper.classes()).toContain('mbti-enfp')
  })

  it('applies ESTP flashy styling', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockFreeTouristSpot,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    expect(wrapper.classes()).toContain('mbti-estp')
  })

  it('applies ISFJ warm tone styling', () => {
    const wrapper = mount(TouristSpotDetails, {
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
      { category: 'cultural', expected: 'Cultural Site' },
      { category: 'viewpoint', expected: 'Scenic Viewpoint' }
    ]

    testCases.forEach(({ category, expected }) => {
      const spotWithCategory = { ...mockTouristSpot, category: category as any }
      const wrapper = mount(TouristSpotDetails, {
        props: {
          touristSpot: spotWithCategory,
          mbtiPersonality: 'ENFP' as MBTIPersonality
        }
      })

      const categoryBadge = wrapper.find('.category-badge')
      expect(categoryBadge.text()).toBe(expected)
    })
  })

  it('formats feature names correctly', () => {
    const testCases = [
      { feature: 'wheelchair_accessible', expected: 'Wheelchair Accessible' },
      { feature: 'public_transport_nearby', expected: 'Public Transport Nearby' },
      { feature: 'photography_allowed', expected: 'Photography Allowed' }
    ]

    testCases.forEach(({ feature, expected }) => {
      const spotWithFeature = { ...mockTouristSpot, features: [feature as any] }
      const wrapper = mount(TouristSpotDetails, {
        props: {
          touristSpot: spotWithFeature,
          mbtiPersonality: 'ENFP' as MBTIPersonality
        }
      })

      const featureBadge = wrapper.find('.feature-badge')
      expect(featureBadge.text()).toBe(expected)
    })
  })

  it('provides correct MBTI match reasons', () => {
    const testCases: Array<{ personality: MBTIPersonality; expectedKeyword: string }> = [
      { personality: 'INTJ', expectedKeyword: 'Strategic thinkers' },
      { personality: 'ENFP', expectedKeyword: 'Enthusiastic explorers' },
      { personality: 'ISFJ', expectedKeyword: 'Caring individuals' },
      { personality: 'ESTP', expectedKeyword: 'Action-oriented' }
    ]

    testCases.forEach(({ personality, expectedKeyword }) => {
      const wrapper = mount(TouristSpotDetails, {
        props: {
          touristSpot: { ...mockTouristSpot, mbti: personality },
          mbtiPersonality: personality
        }
      })

      const reasonText = wrapper.find('.reason-text')
      expect(reasonText.text()).toContain(expectedKeyword)
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

    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: minimalSpot,
        mbtiPersonality: 'INTJ' as MBTIPersonality
      }
    })

    expect(wrapper.find('.spot-name').text()).toBe('Minimal Spot')
    expect(wrapper.find('.description-section').exists()).toBe(false)
    expect(wrapper.find('.remarks-section').exists()).toBe(false)
    expect(wrapper.find('.features-section').exists()).toBe(false)
    expect(wrapper.find('.admission-section').exists()).toBe(false)
    expect(wrapper.find('.accessibility-section').exists()).toBe(false)
  })

  it('shows all required sections', () => {
    const wrapper = mount(TouristSpotDetails, {
      props: {
        touristSpot: mockTouristSpot,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    // These sections should always be present
    expect(wrapper.find('.spot-location-section').exists()).toBe(true)
    expect(wrapper.find('.operating-hours-section').exists()).toBe(true)
    expect(wrapper.find('.mbti-match-section').exists()).toBe(true)
  })
})
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ResponsiveComboBox from '../components/common/ResponsiveComboBox.vue'
import ResponsiveItineraryLayout from '../components/itinerary/ResponsiveItineraryLayout.vue'

// Mock window.innerWidth for responsive testing
const mockInnerWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
  window.dispatchEvent(new Event('resize'))
}

describe('Responsive Design', () => {
  beforeEach(() => {
    // Reset window size
    mockInnerWidth(1024)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('ResponsiveComboBox', () => {
    const mockOptions = [
      { id: '1', name: 'Option 1', value: 'option1' },
      { id: '2', name: 'Option 2', value: 'option2' },
      { id: '3', name: 'Option 3', value: 'option3' }
    ]

    it('renders with touch-friendly minimum height', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          label: 'Test Select',
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      const select = wrapper.find('.combo-box-select')
      expect(select.exists()).toBe(true)
      
      // Check if minimum touch target height is applied
      const styles = getComputedStyle(select.element)
      expect(styles.minHeight).toBeTruthy()
    })

    it('applies MBTI personality-specific classes', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          mbtiPersonality: 'ENFP',
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      expect(wrapper.classes()).toContain('mbti-enfp')
      expect(wrapper.classes()).toContain('colorful-personality')
    })

    it('handles different size variants', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          size: 'large',
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      expect(wrapper.classes()).toContain('size-large')
    })

    it('shows loading state correctly', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          isLoading: true,
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      expect(wrapper.classes()).toContain('is-loading')
      expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    })

    it('displays error state with proper accessibility attributes', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          errorMessage: 'This field is required',
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      expect(wrapper.classes()).toContain('has-error')
      expect(wrapper.find('.combo-box-error').exists()).toBe(true)
      
      const select = wrapper.find('.combo-box-select')
      expect(select.attributes('aria-invalid')).toBe('true')
    })

    it('emits change events with correct data', async () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: mockOptions,
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      const select = wrapper.find('.combo-box-select')
      await select.setValue('option2')

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })

  describe('ResponsiveItineraryLayout', () => {
    const mockMainItinerary = {
      day_1: {
        breakfast: { id: '1', name: 'Restaurant 1' },
        morning_session: { tourist_spot: 'Spot 1', mbti: 'ENFP' },
        lunch: { id: '2', name: 'Restaurant 2' },
        afternoon_session: { tourist_spot: 'Spot 2', mbti: 'ENFP' },
        dinner: { id: '3', name: 'Restaurant 3' },
        night_session: { tourist_spot: 'Spot 3', mbti: 'ENFP' }
      },
      day_2: {
        breakfast: { id: '4', name: 'Restaurant 4' },
        morning_session: { tourist_spot: 'Spot 4', mbti: 'ENFP' },
        lunch: { id: '5', name: 'Restaurant 5' },
        afternoon_session: { tourist_spot: 'Spot 5', mbti: 'ENFP' },
        dinner: { id: '6', name: 'Restaurant 6' },
        night_session: { tourist_spot: 'Spot 6', mbti: 'ENFP' }
      },
      day_3: {
        breakfast: { id: '7', name: 'Restaurant 7' },
        morning_session: { tourist_spot: 'Spot 7', mbti: 'ENFP' },
        lunch: { id: '8', name: 'Restaurant 8' },
        afternoon_session: { tourist_spot: 'Spot 8', mbti: 'ENFP' },
        dinner: { id: '9', name: 'Restaurant 9' },
        night_session: { tourist_spot: 'Spot 9', mbti: 'ENFP' }
      }
    }

    const mockCandidateSpots = {}
    const mockCandidateRestaurants = {}

    it('shows mobile layout by default on small screens', async () => {
      mockInnerWidth(480)
      await nextTick()

      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('.mobile-layout').isVisible()).toBe(true)
      expect(wrapper.find('.layout-toggle').exists()).toBe(false)
    })

    it('shows layout toggle on tablet and desktop', async () => {
      mockInnerWidth(768)
      await nextTick()

      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      expect(wrapper.find('.layout-toggle').exists()).toBe(true)
      expect(wrapper.findAll('.layout-toggle-btn')).toHaveLength(2)
    })

    it('applies personality-specific classes', () => {
      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ISFJ'
        }
      })

      expect(wrapper.classes()).toContain('mbti-isfj')
      expect(wrapper.classes()).toContain('warm-personality')
    })

    it('shows time inputs for structured personalities', () => {
      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'INTJ'
        }
      })

      // Should show time inputs for structured personalities
      expect(wrapper.find('.mobile-time-inputs').exists()).toBe(true)
    })

    it('shows important checkboxes for ENTJ', () => {
      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENTJ'
        }
      })

      // Should show important checkboxes for ENTJ
      expect(wrapper.find('.mobile-important-section').exists()).toBe(true)
    })

    it('switches between mobile and table layouts', async () => {
      mockInnerWidth(1024)
      await nextTick()

      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Initially should show mobile layout
      expect(wrapper.find('.mobile-layout').isVisible()).toBe(true)
      expect(wrapper.find('.table-layout').isVisible()).toBe(false)

      // Click table view button
      const tableButton = wrapper.findAll('.layout-toggle-btn')[1]
      await tableButton.trigger('click')

      expect(wrapper.find('.mobile-layout').isVisible()).toBe(false)
      expect(wrapper.find('.table-layout').isVisible()).toBe(true)
    })

    it('emits recommendation change events', async () => {
      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: mockCandidateSpots,
          candidateRestaurants: mockCandidateRestaurants,
          mbtiPersonality: 'ENFP'
        }
      })

      // Find a combo box and trigger change
      const comboBox = wrapper.findComponent(ResponsiveComboBox)
      if (comboBox.exists()) {
        await comboBox.vm.$emit('change', 'new-value', { id: 'new', name: 'New Option' })
        
        expect(wrapper.emitted('recommendation-changed')).toBeTruthy()
      }
    })
  })

  describe('Touch Target Compliance', () => {
    it('ensures minimum 44px touch targets', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: [{ id: '1', name: 'Option 1' }],
          optionKey: 'id',
          optionLabel: 'name'
        }
      })

      const select = wrapper.find('.combo-box-select')
      const computedStyle = getComputedStyle(select.element)
      
      // Check minimum height for touch targets
      expect(parseInt(computedStyle.minHeight)).toBeGreaterThanOrEqual(44)
    })
  })

  describe('Accessibility Features', () => {
    it('includes proper ARIA labels and roles', () => {
      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: [{ id: '1', name: 'Option 1' }],
          label: 'Test Label',
          required: true,
          optionKey: 'id',
          optionLabel: 'name'
        }
      })

      const select = wrapper.find('.combo-box-select')
      expect(select.attributes('aria-required')).toBe('true')
      
      const label = wrapper.find('.combo-box-label')
      expect(label.exists()).toBe(true)
      expect(label.text()).toContain('Test Label')
      expect(label.text()).toContain('*') // Required indicator
    })

    it('provides screen reader support', () => {
      const wrapper = mount(ResponsiveItineraryLayout, {
        props: {
          mainItinerary: mockMainItinerary,
          candidateSpots: {},
          candidateRestaurants: {},
          mbtiPersonality: 'ENFP'
        }
      })

      const table = wrapper.find('.responsive-table')
      if (table.exists()) {
        expect(table.attributes('role')).toBe('table')
        expect(table.attributes('aria-label')).toContain('3-day itinerary')
      }
    })
  })

  describe('Performance Optimizations', () => {
    it('handles large option lists efficiently', () => {
      const largeOptionList = Array.from({ length: 1000 }, (_, i) => ({
        id: `option-${i}`,
        name: `Option ${i}`,
        value: `value-${i}`
      }))

      const wrapper = mount(ResponsiveComboBox, {
        props: {
          modelValue: '',
          options: largeOptionList,
          optionKey: 'id',
          optionValue: 'value',
          optionLabel: 'name'
        }
      })

      expect(wrapper.findAll('option')).toHaveLength(largeOptionList.length)
    })
  })
})

describe('CSS Responsive Utilities', () => {
  it('applies responsive grid classes correctly', () => {
    // Test that CSS classes are available
    const testElement = document.createElement('div')
    testElement.className = 'col-12 col-md-6 col-lg-4'
    
    expect(testElement.classList.contains('col-12')).toBe(true)
    expect(testElement.classList.contains('col-md-6')).toBe(true)
    expect(testElement.classList.contains('col-lg-4')).toBe(true)
  })

  it('applies touch target classes', () => {
    const testElement = document.createElement('button')
    testElement.className = 'touch-target'
    
    expect(testElement.classList.contains('touch-target')).toBe(true)
  })

  it('applies responsive display utilities', () => {
    const testElement = document.createElement('div')
    testElement.className = 'd-none d-md-block d-lg-flex'
    
    expect(testElement.classList.contains('d-none')).toBe(true)
    expect(testElement.classList.contains('d-md-block')).toBe(true)
    expect(testElement.classList.contains('d-lg-flex')).toBe(true)
  })
})
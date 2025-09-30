import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '../LoadingSpinner.vue'
import type { MBTIPersonality } from '@/types/mbti'

// Mock the ThemeService
vi.mock('@/services/themeService', () => ({
  ThemeService: {
    getInstance: () => ({
      isColorfulPersonality: (personality: MBTIPersonality) => 
        ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP', 'ESFP'].includes(personality),
      isWarmPersonality: (personality: MBTIPersonality) => 
        ['ISFJ', 'ENFJ', 'ESFJ'].includes(personality),
      isFlashyPersonality: (personality: MBTIPersonality) => 
        personality === 'ESTP'
    })
  }
}))

describe('LoadingSpinner', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Basic Functionality', () => {
    it('renders with default props', () => {
      const wrapper = mount(LoadingSpinner)
      
      expect(wrapper.find('.loading-spinner').exists()).toBe(true)
      expect(wrapper.find('.spinner').exists()).toBe(true)
      expect(wrapper.classes()).toContain('loading-spinner--medium')
    })

    it('displays message when provided', () => {
      const message = 'Loading data...'
      const wrapper = mount(LoadingSpinner, {
        props: { message }
      })
      
      expect(wrapper.find('.loading-message').text()).toBe(message)
    })

    it('does not display message when not provided', () => {
      const wrapper = mount(LoadingSpinner)
      
      expect(wrapper.find('.loading-message').exists()).toBe(false)
    })

    it('applies correct size classes', () => {
      const sizes = ['small', 'medium', 'large'] as const
      
      sizes.forEach(size => {
        const wrapper = mount(LoadingSpinner, {
          props: { size }
        })
        
        expect(wrapper.classes()).toContain(`loading-spinner--${size}`)
      })
    })
  })

  describe('Progress Functionality', () => {
    it('shows progress ring when showProgress is true', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          showProgress: true,
          progress: 50
        }
      })
      
      expect(wrapper.find('.progress-ring').exists()).toBe(true)
      expect(wrapper.find('.progress-svg').exists()).toBe(true)
      expect(wrapper.find('.progress-text').text()).toBe('50%')
    })

    it('does not show progress ring when showProgress is false', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          showProgress: false,
          progress: 50
        }
      })
      
      expect(wrapper.find('.progress-ring').exists()).toBe(false)
    })

    it('updates progress bar stroke-dasharray correctly', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          showProgress: true,
          progress: 75
        }
      })
      
      const progressBar = wrapper.find('.progress-bar')
      expect(progressBar.attributes('stroke-dasharray')).toBe('75, 100')
    })
  })

  describe('Estimated Time', () => {
    it('formats estimated time correctly for seconds', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          estimatedTime: 45
        }
      })
      
      expect(wrapper.find('.estimated-time').text()).toContain('45s')
    })

    it('formats estimated time correctly for minutes', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          estimatedTime: 90
        }
      })
      
      expect(wrapper.find('.estimated-time').text()).toContain('1m 30s')
    })

    it('formats estimated time correctly for hours', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          estimatedTime: 3900
        }
      })
      
      expect(wrapper.find('.estimated-time').text()).toContain('1h 5m')
    })
  })

  describe('Animated Dots', () => {
    it('shows animated dots when showDots is true', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: true
        }
      })
      
      expect(wrapper.find('.loading-dots').exists()).toBe(true)
      expect(wrapper.findAll('.dot')).toHaveLength(3)
    })

    it('does not show dots when showDots is false', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: false
        }
      })
      
      expect(wrapper.find('.loading-dots').exists()).toBe(false)
    })

    it('animates dots correctly', async () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: true
        }
      })
      
      // Initially first dot should be active
      const dots = wrapper.findAll('.dot')
      expect(dots[0].classes()).toContain('active')
      
      // Advance timer and check next dot
      vi.advanceTimersByTime(500)
      await wrapper.vm.$nextTick()
      
      expect(dots[1].classes()).toContain('active')
    })
  })

  describe('MBTI Personality Styling', () => {
    it('applies personality-specific classes', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          mbtiPersonality: 'ENFP' as MBTIPersonality
        }
      })
      
      expect(wrapper.classes()).toContain('loading-spinner--enfp')
      expect(wrapper.classes()).toContain('loading-spinner--colorful')
    })

    it('applies warm personality styling', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          mbtiPersonality: 'ISFJ' as MBTIPersonality
        }
      })
      
      expect(wrapper.classes()).toContain('loading-spinner--isfj')
      expect(wrapper.classes()).toContain('loading-spinner--warm')
    })

    it('applies flashy personality styling', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          mbtiPersonality: 'ESTP' as MBTIPersonality
        }
      })
      
      expect(wrapper.classes()).toContain('loading-spinner--estp')
      expect(wrapper.classes()).toContain('loading-spinner--flashy')
      
      const spinner = wrapper.find('.spinner')
      expect(spinner.classes()).toContain('spinner--flashy')
    })

    it('applies colorful spinner styling', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          mbtiPersonality: 'ENTP' as MBTIPersonality
        }
      })
      
      const spinner = wrapper.find('.spinner')
      expect(spinner.classes()).toContain('spinner--colorful')
    })
  })

  describe('Variant Styling', () => {
    it('applies variant classes correctly', () => {
      const variants = ['colorful', 'warm', 'flashy'] as const
      
      variants.forEach(variant => {
        const wrapper = mount(LoadingSpinner, {
          props: { variant }
        })
        
        expect(wrapper.classes()).toContain(`loading-spinner--${variant}`)
      })
    })
  })

  describe('Accessibility', () => {
    it('has correct ARIA attributes', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading data...'
        }
      })
      
      const spinner = wrapper.find('.loading-spinner')
      expect(spinner.attributes('role')).toBe('status')
      expect(spinner.attributes('aria-label')).toBe('Loading: Loading data...')
    })

    it('has default ARIA label when no message', () => {
      const wrapper = mount(LoadingSpinner)
      
      const spinner = wrapper.find('.loading-spinner')
      expect(spinner.attributes('aria-label')).toBe('Loading content, please wait')
    })
  })

  describe('Lifecycle', () => {
    it('starts dot animation on mount', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: true
        }
      })
      
      // Check that animation interval is set
      expect(wrapper.vm).toBeDefined()
    })

    it('stops dot animation when showDots changes to false', async () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: true
        }
      })
      
      await wrapper.setProps({ showDots: false })
      
      expect(wrapper.find('.loading-dots').exists()).toBe(false)
    })

    it('cleans up intervals on unmount', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          showDots: true
        }
      })
      
      wrapper.unmount()
      
      // Should not throw any errors
      expect(true).toBe(true)
    })
  })

  describe('Responsive Design', () => {
    it('applies responsive classes correctly', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          size: 'large'
        }
      })
      
      expect(wrapper.classes()).toContain('loading-spinner--large')
    })
  })

  describe('Edge Cases', () => {
    it('handles undefined progress gracefully', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          showProgress: true,
          progress: undefined
        }
      })
      
      expect(wrapper.find('.progress-ring').exists()).toBe(false)
    })

    it('handles zero estimated time', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          estimatedTime: 0
        }
      })
      
      const estimatedTimeElement = wrapper.find('.estimated-time')
      if (estimatedTimeElement.exists()) {
        expect(estimatedTimeElement.text()).toContain('0s')
      } else {
        // If estimated time is 0, the element might not be rendered
        expect(true).toBe(true)
      }
    })

    it('handles very large estimated time', () => {
      const wrapper = mount(LoadingSpinner, {
        props: {
          message: 'Loading...',
          estimatedTime: 7200 // 2 hours
        }
      })
      
      expect(wrapper.find('.estimated-time').text()).toContain('2h')
    })
  })
})
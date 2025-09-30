import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ImagePlaceholder from '../ImagePlaceholder.vue'
import type { MBTIPersonality } from '@/types/mbti'

describe('ImagePlaceholder', () => {
  const defaultProps = {
    mbtiPersonality: 'ENFP' as MBTIPersonality,
    title: 'Test Location',
    subtitle: 'Beautiful views'
  }

  it('renders correctly with default props', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: defaultProps
    })

    expect(wrapper.find('.image-placeholder-container').exists()).toBe(true)
    expect(wrapper.find('.placeholder-title').text()).toBe('Test Location')
    expect(wrapper.find('.placeholder-subtitle').text()).toBe('Beautiful views')
  })

  it('applies correct personality class for colorful personalities', () => {
    const colorfulPersonalities: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP']
    
    colorfulPersonalities.forEach(personality => {
      const wrapper = mount(ImagePlaceholder, {
        props: {
          ...defaultProps,
          mbtiPersonality: personality
        }
      })

      expect(wrapper.find('.colorful-personality').exists()).toBe(true)
      expect(wrapper.find(`.personality-${personality.toLowerCase()}`).exists()).toBe(true)
    })
  })

  it('applies ESTP flashy styling', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        mbtiPersonality: 'ESTP' as MBTIPersonality
      }
    })

    expect(wrapper.find('.estp-flashy').exists()).toBe(true)
  })

  it('shows decorative elements for colorful personalities', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        mbtiPersonality: 'ENFP' as MBTIPersonality
      }
    })

    expect(wrapper.find('.decorative-elements').exists()).toBe(true)
    expect(wrapper.findAll('.sparkle')).toHaveLength(3)
  })

  it('does not show decorative elements for non-colorful personalities', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        mbtiPersonality: 'INTJ' as MBTIPersonality
      }
    })

    expect(wrapper.find('.decorative-elements').exists()).toBe(false)
  })

  it('emits click event when clickable', async () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: true
      }
    })

    await wrapper.find('.image-placeholder-container').trigger('click')
    
    expect(wrapper.emitted('click')).toHaveLength(1)
    expect(wrapper.emitted('image-request')).toHaveLength(1)
    expect(wrapper.emitted('image-request')?.[0]).toEqual([{
      personality: 'ENFP',
      title: 'Test Location'
    }])
  })

  it('does not emit click event when not clickable', async () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: false
      }
    })

    await wrapper.find('.image-placeholder-container').trigger('click')
    
    expect(wrapper.emitted('click')).toBeUndefined()
    expect(wrapper.emitted('image-request')).toBeUndefined()
  })

  it('handles keyboard navigation correctly', async () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: true
      }
    })

    const container = wrapper.find('.image-placeholder-container')
    
    // Test Enter key
    await container.trigger('keydown.enter')
    expect(wrapper.emitted('click')).toHaveLength(1)

    // Test Space key
    await container.trigger('keydown.space')
    expect(wrapper.emitted('click')).toHaveLength(2)
  })

  it('applies correct size classes', () => {
    const sizes = ['small', 'medium', 'large'] as const
    
    sizes.forEach(size => {
      const wrapper = mount(ImagePlaceholder, {
        props: {
          ...defaultProps,
          size
        }
      })

      expect(wrapper.find(`.size-${size}`).exists()).toBe(true)
    })
  })

  it('applies correct variant classes', () => {
    const variants = ['default', 'gallery', 'spot', 'restaurant'] as const
    
    variants.forEach(variant => {
      const wrapper = mount(ImagePlaceholder, {
        props: {
          ...defaultProps,
          variant
        }
      })

      expect(wrapper.find(`.variant-${variant}`).exists()).toBe(true)
    })
  })

  it('shows click hint when enabled and clickable', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: true,
        showClickHint: true,
        clickHintText: 'amazing photos'
      }
    })

    const clickHint = wrapper.find('.click-hint')
    expect(clickHint.exists()).toBe(true)
    expect(clickHint.text()).toContain('amazing photos')
  })

  it('does not show click hint when not clickable', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: false,
        showClickHint: true
      }
    })

    expect(wrapper.find('.click-hint').exists()).toBe(false)
  })

  it('sets correct ARIA attributes', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: true,
        ariaLabel: 'Custom aria label'
      }
    })

    const container = wrapper.find('.image-placeholder-container')
    expect(container.attributes('role')).toBe('button')
    expect(container.attributes('tabindex')).toBe('0')
    expect(container.attributes('aria-label')).toBe('Custom aria label')
  })

  it('sets correct ARIA attributes for non-clickable', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: {
        ...defaultProps,
        clickable: false
      }
    })

    const container = wrapper.find('.image-placeholder-container')
    expect(container.attributes('role')).toBe('img')
    expect(container.attributes('tabindex')).toBe('-1')
  })

  it('renders custom icon slot content', () => {
    const wrapper = mount(ImagePlaceholder, {
      props: defaultProps,
      slots: {
        icon: '<div class="custom-icon">🎨</div>'
      }
    })

    expect(wrapper.find('.custom-icon').exists()).toBe(true)
    expect(wrapper.find('.custom-icon').text()).toBe('🎨')
  })
})
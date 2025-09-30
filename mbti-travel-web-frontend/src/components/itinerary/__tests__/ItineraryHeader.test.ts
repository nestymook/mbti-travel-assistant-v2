import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ItineraryHeader from '../ItineraryHeader.vue'
import type { MBTIPersonality } from '../../../types'

describe('ItineraryHeader', () => {
  let router: any

  beforeEach(() => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
        { path: '/itinerary/:mbti', name: 'itinerary', component: { template: '<div>Itinerary</div>' } }
      ]
    })
  })

  it('should render the header with correct MBTI personality', async () => {
    const wrapper = mount(ItineraryHeader, {
      props: {
        mbtiPersonality: 'INTJ' as MBTIPersonality
      },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.find('.itinerary-header').exists()).toBe(true)
    expect(wrapper.find('.main-title').text()).toBe('Hong Kong MBTI Travel Planner')
    expect(wrapper.find('.subtitle').text()).toContain('3-Day Itinerary for')
    expect(wrapper.find('.personality-highlight').text()).toBe('INTJ')
  })

  it('should emit back event and navigate when back button is clicked', async () => {
    const wrapper = mount(ItineraryHeader, {
      props: {
        mbtiPersonality: 'ENFP' as MBTIPersonality
      },
      global: {
        plugins: [router]
      }
    })

    const backButton = wrapper.find('.back-button')
    expect(backButton.exists()).toBe(true)

    await backButton.trigger('click')

    // Check that back event was emitted
    expect(wrapper.emitted('back')).toBeTruthy()
    expect(wrapper.emitted('back')).toHaveLength(1)
  })

  it('should apply correct personality-specific CSS classes', async () => {
    const testCases: MBTIPersonality[] = ['INTJ', 'ENFP', 'ISFJ', 'ESTP']

    for (const personality of testCases) {
      const wrapper = mount(ItineraryHeader, {
        props: {
          mbtiPersonality: personality
        },
        global: {
          plugins: [router]
        }
      })

      const personalityHighlight = wrapper.find('.personality-highlight')
      expect(personalityHighlight.classes()).toContain(`personality-${personality.toLowerCase()}`)
      expect(personalityHighlight.text()).toBe(personality)
    }
  })

  it('should have proper accessibility attributes', async () => {
    const wrapper = mount(ItineraryHeader, {
      props: {
        mbtiPersonality: 'INFJ' as MBTIPersonality
      },
      global: {
        plugins: [router]
      }
    })

    const backButton = wrapper.find('.back-button')
    expect(backButton.attributes('aria-label')).toBe('Go back to input page')
  })

  it('should display different personalities correctly', async () => {
    const personalities: MBTIPersonality[] = [
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP',
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]

    for (const personality of personalities) {
      const wrapper = mount(ItineraryHeader, {
        props: {
          mbtiPersonality: personality
        },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('.personality-highlight').text()).toBe(personality)
      expect(wrapper.find('.subtitle').text()).toContain(`3-Day Itinerary for ${personality} Personality`)
    }
  })
})
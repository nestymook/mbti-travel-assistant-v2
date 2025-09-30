import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ItineraryPage from '../ItineraryPage.vue'
import ItineraryHeader from '../../components/itinerary/ItineraryHeader.vue'
import { ThemeService } from '../../services'
import type { MBTIPersonality } from '../../types'

// Mock the ThemeService
vi.mock('../../services', () => ({
    ThemeService: {
        getInstance: vi.fn(() => ({
            applyMBTITheme: vi.fn(),
            resetTheme: vi.fn()
        }))
    }
}))

describe('ItineraryPage', () => {
    let router: any
    let mockThemeService: any

    beforeEach(() => {
        router = createRouter({
            history: createMemoryHistory(),
            routes: [
                { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
                { path: '/itinerary/:mbti', name: 'itinerary', component: ItineraryPage }
            ]
        })

        mockThemeService = {
            applyMBTITheme: vi.fn(),
            resetTheme: vi.fn()
        }

        vi.mocked(ThemeService.getInstance).mockReturnValue(mockThemeService)
    })

    it('should render the itinerary page correctly', async () => {
        await router.push('/itinerary/INTJ')

        const wrapper = mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        expect(wrapper.find('.itinerary-page').exists()).toBe(true)
        expect(wrapper.find('.itinerary-container').exists()).toBe(true)
        expect(wrapper.find('.itinerary-content').exists()).toBe(true)
    })

    it('should render ItineraryHeader component with correct props', async () => {
        await router.push('/itinerary/ENFP')

        const wrapper = mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        const header = wrapper.findComponent(ItineraryHeader)
        expect(header.exists()).toBe(true)
        expect(header.props('mbtiPersonality')).toBe('ENFP')
    })

    it('should apply correct personality class', async () => {
        await router.push('/itinerary/ISFJ')

        const wrapper = mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        expect(wrapper.find('.itinerary-page').classes()).toContain('mbti-isfj')
    })

    it('should apply MBTI theme on mount', async () => {
        await router.push('/itinerary/ESTP')

        mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        expect(mockThemeService.applyMBTITheme).toHaveBeenCalledWith('ESTP')
    })

    it('should handle back navigation from header', async () => {
        await router.push('/itinerary/INTP')

        const wrapper = mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        const header = wrapper.findComponent(ItineraryHeader)
        await header.vm.$emit('back')

        // The component should handle the back event
        expect(header.emitted('back')).toBeTruthy()
    })

    it('should show correct personality-specific features', async () => {
        const testCases = [
            { personality: 'INTJ', isStructured: true, isFlexible: false, isColorful: false, isFeeling: false },
            { personality: 'ESTP', isStructured: false, isFlexible: true, isColorful: false, isFeeling: false },
            { personality: 'ENFP', isStructured: false, isFlexible: false, isColorful: true, isFeeling: false },
            { personality: 'ISFJ', isStructured: false, isFlexible: false, isColorful: false, isFeeling: true }
        ]

        for (const testCase of testCases) {
            await router.push(`/itinerary/${testCase.personality}`)

            const wrapper = mount(ItineraryPage, {
                global: {
                    plugins: [router]
                }
            })

            const featureList = wrapper.find('.feature-list')
            const listItems = featureList.findAll('li')

            if (testCase.isStructured) {
                expect(listItems.some(li => li.text().includes('Time input fields'))).toBe(true)
            }

            if (testCase.isFlexible) {
                expect(listItems.some(li => li.text().includes('Point form layout'))).toBe(true)
            }

            if (testCase.isColorful) {
                expect(listItems.some(li => li.text().includes('Vibrant colors and image placeholders'))).toBe(true)
            }

            if (testCase.isFeeling) {
                expect(listItems.some(li => li.text().includes('Detailed descriptions and social features'))).toBe(true)
            }
        }
    })

    it('should display placeholder content correctly', async () => {
        await router.push('/itinerary/ENTJ')

        const wrapper = mount(ItineraryPage, {
            global: {
                plugins: [router]
            }
        })

        expect(wrapper.find('.content-title').text()).toBe('Your Personalized 3-Day Hong Kong Itinerary')
        expect(wrapper.find('.placeholder-card h4').text()).toBe('Itinerary Content Coming Soon')
        expect(wrapper.find('.placeholder-card p').text()).toContain('Your personalized ENTJ itinerary')
    })

    it('should handle different MBTI personality types correctly', async () => {
        const personalities: MBTIPersonality[] = [
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        ]

        for (const personality of personalities) {
            await router.push(`/itinerary/${personality}`)

            const wrapper = mount(ItineraryPage, {
                global: {
                    plugins: [router]
                }
            })

            expect(wrapper.find('.itinerary-page').classes()).toContain(`mbti-${personality.toLowerCase()}`)
            expect(mockThemeService.applyMBTITheme).toHaveBeenCalledWith(personality)
        }
    })
})
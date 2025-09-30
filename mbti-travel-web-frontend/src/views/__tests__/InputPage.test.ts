import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import InputPage from '../InputPage.vue'
import { ValidationService, ApiService } from '../../services'

// Mock the services
vi.mock('../../services', () => ({
    ValidationService: {
        getInstance: vi.fn(() => ({
            validateMBTICode: vi.fn(() => ({ isValid: true }))
        }))
    },
    ApiService: {
        getInstance: vi.fn(() => ({
            generateItinerary: vi.fn(() => Promise.resolve({
                main_itinerary: {},
                candidate_tourist_spots: {},
                candidate_restaurants: {},
                metadata: {}
            }))
        }))
    }
}))

// Mock the auth composable
vi.mock('../../composables/useAuth', () => ({
    useAuthGuard: () => ({
        guardComponent: vi.fn(() => Promise.resolve())
    })
}))

describe('InputPage', () => {
    let router: any

    beforeEach(() => {
        router = createRouter({
            history: createMemoryHistory(),
            routes: [
                { path: '/', component: InputPage },
                { path: '/itinerary/:mbti', name: 'itinerary', component: { template: '<div>Itinerary</div>' } }
            ]
        })
    })

    it('should render the input page correctly', async () => {
        const wrapper = mount(InputPage, {
            global: {
                plugins: [router]
            }
        })

        expect(wrapper.find('.input-page').exists()).toBe(true)
        expect(wrapper.find('.input-form-container').exists()).toBe(true)
    })

    it('should handle form submission', async () => {
        const mockApiService = {
            generateItinerary: vi.fn(() => Promise.resolve({
                main_itinerary: {},
                candidate_tourist_spots: {},
                candidate_restaurants: {},
                metadata: {}
            }))
        }

        vi.mocked(ApiService.getInstance).mockReturnValue(mockApiService as any)

        const wrapper = mount(InputPage, {
            global: {
                plugins: [router]
            }
        })

        // Find the MBTIInputForm component and trigger submit
        const form = wrapper.findComponent({ name: 'MBTIInputForm' })
        expect(form.exists()).toBe(true)

        // Simulate form submission
        await form.vm.$emit('submit', 'INTJ')
        await wrapper.vm.$nextTick()

        expect(mockApiService.generateItinerary).toHaveBeenCalledWith({
            mbtiPersonality: 'INTJ',
            preferences: {
                includeRestaurants: true,
                includeTouristSpots: true,
                days: 3
            }
        })
    })

    it('should handle validation errors', async () => {
        const mockValidationService = {
            validateMBTICode: vi.fn(() => ({
                isValid: false,
                message: 'Invalid MBTI code'
            }))
        }

        vi.mocked(ValidationService.getInstance).mockReturnValue(mockValidationService as any)

        const wrapper = mount(InputPage, {
            global: {
                plugins: [router]
            }
        })

        const form = wrapper.findComponent({ name: 'MBTIInputForm' })
        await form.vm.$emit('submit', 'INVALID')
        await wrapper.vm.$nextTick()

        // Check that error message is passed to the form
        expect(form.props('errorMessage')).toBe('Invalid MBTI code')
    })

    it('should have proper component structure', async () => {
        const wrapper = mount(InputPage, {
            global: {
                plugins: [router]
            }
        })

        // Check that the component has the expected structure
        expect(wrapper.find('.input-page').exists()).toBe(true)
        expect(wrapper.find('.input-form-container').exists()).toBe(true)

        // Check that MBTIInputForm is rendered
        const form = wrapper.findComponent({ name: 'MBTIInputForm' })
        expect(form.exists()).toBe(true)

        // Check that form has the expected props
        expect(form.props()).toMatchObject({
            modelValue: '',
            isLoading: false,
            errorMessage: ''
        })
    })
})
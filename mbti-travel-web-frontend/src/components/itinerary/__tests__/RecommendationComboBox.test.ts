import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import RecommendationComboBox from '@/components/itinerary/RecommendationComboBox.vue'
import type { Restaurant } from '@/types/restaurant'
import type { TouristSpot } from '@/types/touristSpot'

// Mock the theme service
const mockThemeService = {
    isColorfulPersonality: vi.fn(),
    shouldShowImages: vi.fn(),
    getPersonalityColors: vi.fn()
}

vi.mock('@/services/themeService', () => ({
    ThemeService: {
        getInstance: () => mockThemeService
    }
}))

describe('RecommendationComboBox', () => {
    const mockRestaurant: Restaurant = {
        id: 'rest_001',
        name: 'Test Restaurant',
        address: '123 Test St',
        district: 'Central',
        mealType: ['lunch'],
        sentiment: { likes: 85, dislikes: 10, neutral: 5 },
        locationCategory: 'restaurant',
        priceRange: '$$',
        operatingHours: {
            'Mon - Fri': '11:30-15:00',
            'Sat - Sun': '11:30-15:30',
            'Public Holiday': '11:30-15:30'
        }
    }

    const mockTouristSpot: TouristSpot = {
        tourist_spot: 'Test Tourist Spot',
        mbti: 'ENFP',
        description: 'A wonderful place to visit',
        address: '456 Tourist Ave',
        district: 'Tsim Sha Tsui',
        area: 'Kowloon',
        operating_hours_mon_fri: '09:00-18:00',
        operating_hours_sat_sun: '09:00-19:00',
        operating_hours_public_holiday: '09:00-19:00',
        full_day: false
    }

    const mockRestaurantOptions: Restaurant[] = [
        mockRestaurant,
        {
            id: 'rest_002',
            name: 'Alternative Restaurant',
            address: '789 Alt St',
            district: 'Wan Chai',
            mealType: ['lunch'],
            sentiment: { likes: 75, dislikes: 15, neutral: 10 },
            locationCategory: 'cafe',
            priceRange: '$',
            operatingHours: {
                'Mon - Fri': '11:00-16:00',
                'Sat - Sun': '10:30-16:30',
                'Public Holiday': '10:30-16:30'
            }
        }
    ]

    const mockTouristSpotOptions: TouristSpot[] = [
        mockTouristSpot,
        {
            tourist_spot: 'Alternative Tourist Spot',
            mbti: 'ENFP',
            description: 'Another great place',
            address: '321 Alt Tourist St',
            district: 'Central',
            area: 'Hong Kong Island',
            operating_hours_mon_fri: '10:00-17:00',
            operating_hours_sat_sun: '10:00-18:00',
            operating_hours_public_holiday: '10:00-18:00',
            full_day: false
        }
    ]

    beforeEach(() => {
        vi.clearAllMocks()

        mockThemeService.isColorfulPersonality.mockReturnValue(true)
        mockThemeService.shouldShowImages.mockReturnValue(true)
        mockThemeService.getPersonalityColors.mockReturnValue({
            name: 'ENFP - The Campaigner',
            primary: '#ff5722',
            secondary: '#d84315',
            accent: '#4caf50',
            colorful: true
        })
    })

    describe('Restaurant ComboBox', () => {
        it('renders restaurant combo box correctly', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('select').exists()).toBe(true)
            expect(wrapper.find('.recommendation-details').exists()).toBe(true)
        })

        it('displays restaurant options in select', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            const options = wrapper.findAll('option')
            expect(options.length).toBe(2)
            expect(options[0].text()).toBe('Test Restaurant')
            expect(options[1].text()).toBe('Alternative Restaurant')
        })

        it('shows restaurant details when selected', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Test Restaurant')
            expect(wrapper.text()).toContain('123 Test St')
            expect(wrapper.text()).toContain('Central')
            expect(wrapper.text()).toContain('$$')
            expect(wrapper.text()).toContain('85 likes')
        })

        it('displays operating hours for restaurants', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Mon - Fri: 11:30-15:00')
            expect(wrapper.text()).toContain('Sat - Sun: 11:30-15:30')
            expect(wrapper.text()).toContain('Public Holiday: 11:30-15:30')
        })

        it('shows sentiment data for restaurants', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('85 likes')
            expect(wrapper.text()).toContain('10 dislikes')
            expect(wrapper.text()).toContain('5 neutral')
        })
    })

    describe('Tourist Spot ComboBox', () => {
        it('renders tourist spot combo box correctly', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('select').exists()).toBe(true)
            expect(wrapper.find('.recommendation-details').exists()).toBe(true)
        })

        it('displays tourist spot options in select', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            const options = wrapper.findAll('option')
            expect(options.length).toBe(2)
            expect(options[0].text()).toBe('Test Tourist Spot')
            expect(options[1].text()).toBe('Alternative Tourist Spot')
        })

        it('shows tourist spot details when selected', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Test Tourist Spot')
            expect(wrapper.text()).toContain('456 Tourist Ave')
            expect(wrapper.text()).toContain('Tsim Sha Tsui')
            expect(wrapper.text()).toContain('Kowloon')
            expect(wrapper.text()).toContain('MBTI Match: ENFP')
        })

        it('displays description for tourist spots', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('A wonderful place to visit')
        })

        it('shows operating hours for tourist spots', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Mon - Fri: 09:00-18:00')
            expect(wrapper.text()).toContain('Sat - Sun: 09:00-19:00')
            expect(wrapper.text()).toContain('Public Holiday: 09:00-19:00')
        })
    })

    describe('Selection Changes', () => {
        it('emits update:modelValue when restaurant selection changes', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            const select = wrapper.find('select')
            await select.setValue('rest_002')

            expect(wrapper.emitted('update:modelValue')).toHaveLength(1)
            expect(wrapper.emitted('update:modelValue')?.[0][0]).toEqual(mockRestaurantOptions[1])
        })

        it('emits update:modelValue when tourist spot selection changes', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            const select = wrapper.find('select')
            await select.setValue('Alternative Tourist Spot')

            expect(wrapper.emitted('update:modelValue')).toHaveLength(1)
            expect(wrapper.emitted('update:modelValue')?.[0][0]).toEqual(mockTouristSpotOptions[1])
        })

        it('updates displayed details when selection changes', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Test Restaurant')

            const select = wrapper.find('select')
            await select.setValue('rest_002')
            await nextTick()

            // Update the modelValue prop to simulate parent component update
            await wrapper.setProps({ modelValue: mockRestaurantOptions[1] })

            expect(wrapper.text()).toContain('Alternative Restaurant')
        })
    })

    describe('Personality-Specific Features', () => {
        it('shows image placeholders for colorful personalities', () => {
            mockThemeService.shouldShowImages.mockReturnValue(true)

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('.image-placeholder').exists()).toBe(true)
        })

        it('hides image placeholders for non-image personalities', () => {
            mockThemeService.shouldShowImages.mockReturnValue(false)

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'INTJ'
                }
            })

            expect(wrapper.find('.image-placeholder').exists()).toBe(false)
        })

        it('applies colorful styling for colorful personalities', () => {
            mockThemeService.isColorfulPersonality.mockReturnValue(true)

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('.combo-box--colorful').exists()).toBe(true)
        })

        it('applies standard styling for non-colorful personalities', () => {
            mockThemeService.isColorfulPersonality.mockReturnValue(false)

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'INTJ'
                }
            })

            expect(wrapper.find('.combo-box--colorful').exists()).toBe(false)
            expect(wrapper.find('.combo-box--standard').exists()).toBe(true)
        })
    })

    describe('Loading State', () => {
        it('shows loading state when options are being updated', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: [],
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP',
                    isLoading: true
                }
            })

            expect(wrapper.find('.combo-box--loading').exists()).toBe(true)
            expect(wrapper.text()).toContain('Loading options...')
        })

        it('disables select during loading', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP',
                    isLoading: true
                }
            })

            const select = wrapper.find('select')
            expect(select.attributes('disabled')).toBeDefined()
        })
    })

    describe('Accessibility', () => {
        it('has proper ARIA labels for restaurant combo box', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP',
                    sessionType: 'lunch',
                    day: 'day_1'
                }
            })

            const select = wrapper.find('select')
            expect(select.attributes('aria-label')).toBe('Select restaurant for lunch on Day 1')
        })

        it('has proper ARIA labels for tourist spot combo box', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockTouristSpot,
                    options: mockTouristSpotOptions,
                    type: 'tourist-spot',
                    mbtiPersonality: 'ENFP',
                    sessionType: 'morning_session',
                    day: 'day_2'
                }
            })

            const select = wrapper.find('select')
            expect(select.attributes('aria-label')).toBe('Select tourist spot for morning session on Day 2')
        })

        it('has proper ARIA describedby for details', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP',
                    sessionType: 'lunch',
                    day: 'day_1'
                }
            })

            const select = wrapper.find('select')
            const detailsId = select.attributes('aria-describedby')
            expect(detailsId).toBeDefined()
            expect(wrapper.find(`#${detailsId}`).exists()).toBe(true)
        })

        it('supports keyboard navigation', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            const select = wrapper.find('select')

            // Test arrow key navigation
            await select.trigger('keydown.down')
            expect(wrapper.emitted('keydown')).toBeDefined()

            // Test Enter key selection
            await select.trigger('keydown.enter')
            expect(wrapper.emitted('keydown')).toBeDefined()
        })
    })

    describe('Error Handling', () => {
        it('handles empty options array gracefully', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: [],
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('select').exists()).toBe(true)
            expect(wrapper.text()).toContain('No options available')
        })

        it('handles missing modelValue gracefully', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: null,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('select').exists()).toBe(true)
            expect(wrapper.text()).toContain('Select an option')
        })

        it('handles theme service errors gracefully', () => {
            mockThemeService.isColorfulPersonality.mockImplementation(() => {
                throw new Error('Theme service error')
            })

            expect(() => {
                mount(RecommendationComboBox, {
                    props: {
                        modelValue: mockRestaurant,
                        options: mockRestaurantOptions,
                        type: 'restaurant',
                        mbtiPersonality: 'ENFP'
                    }
                })
            }).not.toThrow()
        })

        it('handles malformed data gracefully', () => {
            const malformedRestaurant = {
                id: 'rest_001',
                name: 'Test Restaurant'
                // Missing required fields
            } as Restaurant

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: malformedRestaurant,
                    options: [malformedRestaurant],
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('select').exists()).toBe(true)
            expect(wrapper.text()).toContain('Test Restaurant')
        })
    })

    describe('Performance', () => {
        it('does not re-render when props do not change', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            const initialRenderCount = wrapper.findAll('option').length

            // Update with same props
            await wrapper.setProps({
                modelValue: mockRestaurant,
                options: mockRestaurantOptions,
                type: 'restaurant',
                mbtiPersonality: 'ENFP'
            })

            const newRenderCount = wrapper.findAll('option').length
            expect(newRenderCount).toBe(initialRenderCount)
        })

        it('efficiently handles large option lists', () => {
            const largeOptionList = Array.from({ length: 100 }, (_, i) => ({
                ...mockRestaurant,
                id: `rest_${i}`,
                name: `Restaurant ${i}`
            }))

            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: largeOptionList,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.findAll('option').length).toBe(100)
            expect(wrapper.find('select').exists()).toBe(true)
        })
    })

    describe('Data Updates', () => {
        it('updates display when modelValue changes', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.text()).toContain('Test Restaurant')

            await wrapper.setProps({ modelValue: mockRestaurantOptions[1] })
            await nextTick()

            expect(wrapper.text()).toContain('Alternative Restaurant')
        })

        it('updates options when options prop changes', async () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: [mockRestaurant],
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.findAll('option').length).toBe(1)

            await wrapper.setProps({ options: mockRestaurantOptions })
            await nextTick()

            expect(wrapper.findAll('option').length).toBe(2)
        })
    })

    describe('Responsive Design', () => {
        it('applies responsive classes', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            expect(wrapper.find('.combo-box--responsive').exists()).toBe(true)
        })

        it('has touch-friendly interface elements', () => {
            const wrapper = mount(RecommendationComboBox, {
                props: {
                    modelValue: mockRestaurant,
                    options: mockRestaurantOptions,
                    type: 'restaurant',
                    mbtiPersonality: 'ENFP'
                }
            })

            const select = wrapper.find('select')
            expect(select.classes()).toContain('touch-friendly')
        })
    })
})
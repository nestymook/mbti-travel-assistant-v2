import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import type { AxiosError } from 'axios'
import { ApiService } from '../apiService'
import { AuthService } from '../authService'
import type { ItineraryRequest, ItineraryResponse } from '../../types'
import type { PriceRange } from '../../types/restaurant'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

// Mock AuthService
vi.mock('../authService')
const MockedAuthService = vi.mocked(AuthService)

describe('ApiService', () => {
    let apiService: ApiService
    let mockAuthService: any
    let mockAxiosInstance: any

    beforeEach(() => {
        // Reset all mocks
        vi.clearAllMocks()

        // Mock AuthService instance
        mockAuthService = {
            getToken: vi.fn(),
            setToken: vi.fn(),
            isAuthenticated: vi.fn(),
            refreshToken: vi.fn(),
            redirectToLogin: vi.fn()
        }

        MockedAuthService.getInstance.mockReturnValue(mockAuthService)

        // Mock axios instance
        mockAxiosInstance = {
            interceptors: {
                request: { use: vi.fn() },
                response: { use: vi.fn() }
            },
            request: vi.fn(),
            get: vi.fn(),
            post: vi.fn()
        }

        mockedAxios.create.mockReturnValue(mockAxiosInstance)

        // Clear singleton instance to get fresh instance
        // @ts-expect-error - accessing private static property for testing
        ApiService.instance = undefined

        // Get fresh instance
        apiService = ApiService.getInstance()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('getInstance', () => {
        it('should return singleton instance', () => {
            const instance1 = ApiService.getInstance()
            const instance2 = ApiService.getInstance()
            expect(instance1).toBe(instance2)
        })
    })

    describe('generateItinerary', () => {
        const validRequest: ItineraryRequest = {
            mbtiPersonality: 'ENFP',
            userId: 'test-user',
            preferences: {
                budgetRange: 'medium'
            }
        }

        const mockResponse: ItineraryResponse = {
            main_itinerary: {
                day_1: {
                    morning_session: {
                        tourist_spot: 'Test Spot',
                        mbti: 'ENFP',
                        address: 'Test Address',
                        district: 'Test District',
                        area: 'Test Area',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    afternoon_session: {
                        tourist_spot: 'Test Spot 2',
                        mbti: 'ENFP',
                        address: 'Test Address 2',
                        district: 'Test District 2',
                        area: 'Test Area 2',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    night_session: {
                        tourist_spot: 'Test Spot 3',
                        mbti: 'ENFP',
                        address: 'Test Address 3',
                        district: 'Test District 3',
                        area: 'Test Area 3',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    breakfast: {
                        id: 'rest-1',
                        name: 'Test Restaurant',
                        address: 'Test Address',
                        mealType: ['breakfast'],
                        sentiment: { likes: 10, dislikes: 2, neutral: 3 },
                        locationCategory: 'Kowloon',
                        district: 'Test District',
                        priceRange: 'medium' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '7:00-11:00',
                            'Sat - Sun': '8:00-12:00',
                            'Public Holiday': '8:00-12:00'
                        }
                    },
                    lunch: {
                        id: 'rest-2',
                        name: 'Test Restaurant 2',
                        address: 'Test Address 2',
                        mealType: ['lunch'],
                        sentiment: { likes: 15, dislikes: 1, neutral: 2 },
                        locationCategory: 'Kowloon',
                        district: 'Test District 2',
                        priceRange: 'medium' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '11:30-15:00',
                            'Sat - Sun': '12:00-16:00',
                            'Public Holiday': '12:00-16:00'
                        }
                    },
                    dinner: {
                        id: 'rest-3',
                        name: 'Test Restaurant 3',
                        address: 'Test Address 3',
                        mealType: ['dinner'],
                        sentiment: { likes: 20, dislikes: 0, neutral: 1 },
                        locationCategory: 'Kowloon',
                        district: 'Test District 3',
                        priceRange: 'high' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '18:00-22:00',
                            'Sat - Sun': '17:30-23:00',
                            'Public Holiday': '17:30-22:30'
                        }
                    }
                },
                day_2: {
                    morning_session: {
                        tourist_spot: 'Test Spot Day 2',
                        mbti: 'ENFP',
                        address: 'Test Address Day 2',
                        district: 'Test District Day 2',
                        area: 'Test Area Day 2',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    afternoon_session: {
                        tourist_spot: 'Test Spot Day 2 Afternoon',
                        mbti: 'ENFP',
                        address: 'Test Address Day 2 Afternoon',
                        district: 'Test District Day 2 Afternoon',
                        area: 'Test Area Day 2 Afternoon',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    night_session: {
                        tourist_spot: 'Test Spot Day 2 Night',
                        mbti: 'ENFP',
                        address: 'Test Address Day 2 Night',
                        district: 'Test District Day 2 Night',
                        area: 'Test Area Day 2 Night',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    breakfast: {
                        id: 'rest-4',
                        name: 'Test Restaurant Day 2',
                        address: 'Test Address Day 2',
                        mealType: ['breakfast'],
                        sentiment: { likes: 8, dislikes: 3, neutral: 4 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 2',
                        priceRange: 'low' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '7:00-11:00',
                            'Sat - Sun': '8:00-12:00',
                            'Public Holiday': '8:00-12:00'
                        }
                    },
                    lunch: {
                        id: 'rest-5',
                        name: 'Test Restaurant Day 2 Lunch',
                        address: 'Test Address Day 2 Lunch',
                        mealType: ['lunch'],
                        sentiment: { likes: 12, dislikes: 2, neutral: 3 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 2 Lunch',
                        priceRange: 'medium' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '11:30-15:00',
                            'Sat - Sun': '12:00-16:00',
                            'Public Holiday': '12:00-16:00'
                        }
                    },
                    dinner: {
                        id: 'rest-6',
                        name: 'Test Restaurant Day 2 Dinner',
                        address: 'Test Address Day 2 Dinner',
                        mealType: ['dinner'],
                        sentiment: { likes: 18, dislikes: 1, neutral: 2 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 2 Dinner',
                        priceRange: 'high' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '18:00-22:00',
                            'Sat - Sun': '17:30-23:00',
                            'Public Holiday': '17:30-22:30'
                        }
                    }
                },
                day_3: {
                    morning_session: {
                        tourist_spot: 'Test Spot Day 3',
                        mbti: 'ENFP',
                        address: 'Test Address Day 3',
                        district: 'Test District Day 3',
                        area: 'Test Area Day 3',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    afternoon_session: {
                        tourist_spot: 'Test Spot Day 3 Afternoon',
                        mbti: 'ENFP',
                        address: 'Test Address Day 3 Afternoon',
                        district: 'Test District Day 3 Afternoon',
                        area: 'Test Area Day 3 Afternoon',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    night_session: {
                        tourist_spot: 'Test Spot Day 3 Night',
                        mbti: 'ENFP',
                        address: 'Test Address Day 3 Night',
                        district: 'Test District Day 3 Night',
                        area: 'Test Area Day 3 Night',
                        operating_hours_mon_fri: '9:00-18:00',
                        operating_hours_sat_sun: '10:00-17:00',
                        operating_hours_public_holiday: '10:00-16:00',
                        full_day: false
                    },
                    breakfast: {
                        id: 'rest-7',
                        name: 'Test Restaurant Day 3',
                        address: 'Test Address Day 3',
                        mealType: ['breakfast'],
                        sentiment: { likes: 9, dislikes: 2, neutral: 4 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 3',
                        priceRange: 'medium' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '7:00-11:00',
                            'Sat - Sun': '8:00-12:00',
                            'Public Holiday': '8:00-12:00'
                        }
                    },
                    lunch: {
                        id: 'rest-8',
                        name: 'Test Restaurant Day 3 Lunch',
                        address: 'Test Address Day 3 Lunch',
                        mealType: ['lunch'],
                        sentiment: { likes: 14, dislikes: 1, neutral: 2 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 3 Lunch',
                        priceRange: 'medium' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '11:30-15:00',
                            'Sat - Sun': '12:00-16:00',
                            'Public Holiday': '12:00-16:00'
                        }
                    },
                    dinner: {
                        id: 'rest-9',
                        name: 'Test Restaurant Day 3 Dinner',
                        address: 'Test Address Day 3 Dinner',
                        mealType: ['dinner'],
                        sentiment: { likes: 22, dislikes: 0, neutral: 1 },
                        locationCategory: 'Kowloon',
                        district: 'Test District Day 3 Dinner',
                        priceRange: 'high' as PriceRange,
                        operatingHours: {
                            'Mon - Fri': '18:00-22:00',
                            'Sat - Sun': '17:30-23:00',
                            'Public Holiday': '17:30-22:30'
                        }
                    }
                }
            },
            candidate_tourist_spots: {
                'day_1_morning': [],
                'day_1_afternoon': [],
                'day_1_night': []
            },
            candidate_restaurants: {
                'day_1_breakfast': [],
                'day_1_lunch': [],
                'day_1_dinner': []
            },
            metadata: {
                generatedAt: new Date().toISOString(),
                mbtiPersonality: 'ENFP',
                version: '1.0.0',
                processingTime: 1500
            }
        }

        it('should successfully generate itinerary', async () => {
            // Mock successful API response
            mockAxiosInstance.request.mockResolvedValue({
                data: mockResponse,
                status: 200
            })

            const result = await apiService.generateItinerary(validRequest)
            expect(result).toEqual(mockResponse)
        })

        it('should validate MBTI personality type', async () => {
            const invalidRequest = { ...validRequest, mbtiPersonality: 'INVALID' as never }

            await expect(apiService.generateItinerary(invalidRequest)).rejects.toThrow(
                'Invalid MBTI personality type: INVALID'
            )
        })

        it('should require MBTI personality', async () => {
            const invalidRequest = { ...validRequest, mbtiPersonality: '' as never }

            await expect(apiService.generateItinerary(invalidRequest)).rejects.toThrow(
                'MBTI personality is required'
            )
        })

        it('should validate response structure', async () => {
            const invalidResponse = { invalid: 'response' }

            mockAxiosInstance.request.mockResolvedValue({
                data: invalidResponse,
                status: 200
            })

            await expect(apiService.generateItinerary(validRequest)).rejects.toThrow(
                'Invalid response: missing main_itinerary'
            )
        })
    })

    describe('authentication integration', () => {
        it('should set auth token using AuthService', () => {
            const token = 'test-token'
            apiService.setAuthToken(token)

            expect(mockAuthService.setToken).toHaveBeenCalledWith({
                accessToken: token,
                tokenType: 'Bearer',
                expiresAt: expect.any(Number)
            })
        })

        it('should get auth token from AuthService', () => {
            mockAuthService.getToken.mockReturnValue('test-token')

            const token = apiService.getAuthToken()
            expect(token).toBe('test-token')
            expect(mockAuthService.getToken).toHaveBeenCalled()
        })

        it('should check authentication status', () => {
            mockAuthService.isAuthenticated.mockReturnValue(true)

            const isAuth = apiService.isAuthenticated()
            expect(isAuth).toBe(true)
            expect(mockAuthService.isAuthenticated).toHaveBeenCalled()
        })
    })

    describe('error handling', () => {
        it('should handle network errors', async () => {
            const networkError = new Error('Network Error') as AxiosError
            networkError.code = 'NETWORK_ERROR'

            mockAxiosInstance.request.mockRejectedValue(networkError)

            await expect(apiService.generateItinerary({
                mbtiPersonality: 'ENFP'
            })).rejects.toThrow('Failed to generate itinerary')
        })

        it('should handle API errors', async () => {
            const apiError = {
                response: {
                    status: 500,
                    data: { message: 'Internal Server Error' }
                },
                config: { headers: {} }
            } as AxiosError

            mockAxiosInstance.request.mockRejectedValue(apiError)

            await expect(apiService.generateItinerary({
                mbtiPersonality: 'ENFP'
            })).rejects.toThrow('Failed to generate itinerary')
        })
    })

    describe('connectivity test', () => {
        it('should test API connectivity successfully', async () => {
            mockAxiosInstance.get.mockResolvedValue({ status: 200 })

            const isConnected = await apiService.testConnection()
            expect(isConnected).toBe(true)
        })

        it('should handle connectivity test failure', async () => {
            mockAxiosInstance.get.mockRejectedValue(new Error('Connection failed'))

            const isConnected = await apiService.testConnection()
            expect(isConnected).toBe(false)
        })
    })
})
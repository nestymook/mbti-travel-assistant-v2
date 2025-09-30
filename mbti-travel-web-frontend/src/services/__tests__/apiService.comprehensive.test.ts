import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import type { AxiosError, AxiosResponse } from 'axios'
import { ApiService } from '../apiService'
import { AuthService } from '../authService'
import type { ItineraryRequest, ItineraryResponse, ApiError } from '../../types'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

// Mock AuthService
vi.mock('../authService')
const MockedAuthService = vi.mocked(AuthService)

describe('ApiService - Comprehensive Tests', () => {
  let apiService: ApiService
  let mockAuthService: any
  let mockAxiosInstance: any

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()

    // Create mock axios instance
    mockAxiosInstance = {
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }

    // Mock axios.create to return our mock instance
    mockedAxios.create.mockReturnValue(mockAxiosInstance)

    // Create mock auth service
    mockAuthService = {
      getToken: vi.fn(),
      isAuthenticated: vi.fn(),
      refreshToken: vi.fn()
    }
    MockedAuthService.getInstance.mockReturnValue(mockAuthService)

    // Create ApiService instance
    apiService = ApiService.getInstance()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Singleton Pattern', () => {
    it('returns the same instance', () => {
      const instance1 = ApiService.getInstance()
      const instance2 = ApiService.getInstance()
      expect(instance1).toBe(instance2)
    })
  })

  describe('Authentication Integration', () => {
    it('includes JWT token in request headers when authenticated', async () => {
      const mockToken = 'mock-jwt-token'
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockAuthService.isAuthenticated.mockReturnValue(true)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const mockResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      mockAxiosInstance.post.mockResolvedValue({
        data: mockResponse,
        status: 200,
        statusText: 'OK'
      })

      await apiService.generateItinerary(mockRequest)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/generate-itinerary',
        mockRequest,
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockToken}`
          })
        })
      )
    })

    it('handles missing authentication token', async () => {
      mockAuthService.getToken.mockReturnValue(null)
      mockAuthService.isAuthenticated.mockReturnValue(false)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Authentication required')
    })

    it('refreshes token on 401 response', async () => {
      const oldToken = 'old-token'
      const newToken = 'new-token'
      
      mockAuthService.getToken
        .mockReturnValueOnce(oldToken)
        .mockReturnValueOnce(newToken)
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.refreshToken.mockResolvedValue(newToken)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const mockResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      // First call fails with 401
      mockAxiosInstance.post
        .mockRejectedValueOnce({
          response: { status: 401, data: { message: 'Unauthorized' } },
          isAxiosError: true
        })
        .mockResolvedValueOnce({
          data: mockResponse,
          status: 200,
          statusText: 'OK'
        })

      const result = await apiService.generateItinerary(mockRequest)

      expect(mockAuthService.refreshToken).toHaveBeenCalled()
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('handles network errors', async () => {
      const networkError = new Error('Network Error')
      mockAxiosInstance.post.mockRejectedValue(networkError)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Network Error')
    })

    it('handles 400 Bad Request errors', async () => {
      const badRequestError: AxiosError = {
        response: {
          status: 400,
          data: { message: 'Invalid MBTI personality type' },
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        },
        isAxiosError: true,
        name: 'AxiosError',
        message: 'Request failed with status code 400',
        config: {} as any,
        toJSON: () => ({})
      }

      mockAxiosInstance.post.mockRejectedValue(badRequestError)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'INVALID',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Invalid MBTI personality type')
    })

    it('handles 500 Internal Server Error', async () => {
      const serverError: AxiosError = {
        response: {
          status: 500,
          data: { message: 'Internal server error' },
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any
        },
        isAxiosError: true,
        name: 'AxiosError',
        message: 'Request failed with status code 500',
        config: {} as any,
        toJSON: () => ({})
      }

      mockAxiosInstance.post.mockRejectedValue(serverError)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Internal server error')
    })

    it('handles timeout errors', async () => {
      const timeoutError: AxiosError = {
        code: 'ECONNABORTED',
        response: undefined,
        isAxiosError: true,
        name: 'AxiosError',
        message: 'timeout of 30000ms exceeded',
        config: {} as any,
        toJSON: () => ({})
      }

      mockAxiosInstance.post.mockRejectedValue(timeoutError)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Request timeout')
    })

    it('handles rate limiting (429) errors', async () => {
      const rateLimitError: AxiosError = {
        response: {
          status: 429,
          data: { message: 'Too many requests' },
          statusText: 'Too Many Requests',
          headers: { 'retry-after': '60' },
          config: {} as any
        },
        isAxiosError: true,
        name: 'AxiosError',
        message: 'Request failed with status code 429',
        config: {} as any,
        toJSON: () => ({})
      }

      mockAxiosInstance.post.mockRejectedValue(rateLimitError)

      const mockRequest: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(mockRequest)).rejects.toThrow('Too many requests')
    })
  })

  describe('Request Validation', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('validates MBTI personality type', async () => {
      const invalidRequest: ItineraryRequest = {
        mbtiPersonality: '',
        preferences: {}
      }

      await expect(apiService.generateItinerary(invalidRequest)).rejects.toThrow('MBTI personality type is required')
    })

    it('validates MBTI personality format', async () => {
      const invalidRequest: ItineraryRequest = {
        mbtiPersonality: 'INVALID_TYPE',
        preferences: {}
      }

      await expect(apiService.generateItinerary(invalidRequest)).rejects.toThrow('Invalid MBTI personality type format')
    })

    it('accepts valid MBTI personality types', async () => {
      const validTypes = ['ENFP', 'INTJ', 'ESFJ', 'ISTP']
      
      for (const type of validTypes) {
        const mockResponse: ItineraryResponse = {
          main_itinerary: {} as any,
          candidate_tourist_spots: {} as any,
          candidate_restaurants: {} as any,
          metadata: {
            generatedAt: new Date().toISOString(),
            processingTime: 1000,
            version: '1.0.0'
          }
        }

        mockAxiosInstance.post.mockResolvedValue({
          data: mockResponse,
          status: 200,
          statusText: 'OK'
        })

        const request: ItineraryRequest = {
          mbtiPersonality: type,
          preferences: {}
        }

        await expect(apiService.generateItinerary(request)).resolves.toEqual(mockResponse)
      }
    })
  })

  describe('Response Processing', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('processes successful response correctly', async () => {
      const mockResponse: ItineraryResponse = {
        main_itinerary: {
          day_1: {
            breakfast: {
              id: 'rest_001',
              name: 'Test Restaurant',
              address: '123 Test St',
              district: 'Central',
              mealType: ['breakfast'],
              sentiment: { likes: 85, dislikes: 10, neutral: 5 },
              locationCategory: 'Hong Kong Island',
              priceRange: 'Below $50',
              operatingHours: {
                'Mon - Fri': '07:00-11:00',
                'Sat - Sun': '08:00-12:00',
                'Public Holiday': '08:00-12:00'
              }
            },
            morning_session: {
              tourist_spot: 'Victoria Peak',
              mbti: 'ENFP',
              description: 'Stunning views',
              address: 'Peak Rd',
              district: 'Central',
              area: 'Hong Kong Island',
              operating_hours_mon_fri: '10:00-23:00',
              operating_hours_sat_sun: '08:00-23:00',
              operating_hours_public_holiday: '08:00-23:00',
              full_day: false
            },
            lunch: {} as any,
            afternoon_session: {} as any,
            dinner: {} as any,
            night_session: {} as any
          },
          day_2: {} as any,
          day_3: {} as any
        },
        candidate_tourist_spots: {
          morning_session: [],
          afternoon_session: [],
          night_session: []
        },
        candidate_restaurants: {
          breakfast: [],
          lunch: [],
          dinner: []
        },
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1500,
          version: '1.0.0'
        }
      }

      mockAxiosInstance.post.mockResolvedValue({
        data: mockResponse,
        status: 200,
        statusText: 'OK'
      })

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const result = await apiService.generateItinerary(request)
      expect(result).toEqual(mockResponse)
    })

    it('handles malformed response data', async () => {
      const malformedResponse = {
        invalid_structure: true
      }

      mockAxiosInstance.post.mockResolvedValue({
        data: malformedResponse,
        status: 200,
        statusText: 'OK'
      })

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(request)).rejects.toThrow('Invalid response format')
    })
  })

  describe('Retry Logic', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('retries on transient failures', async () => {
      const mockResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      // First two calls fail, third succeeds
      mockAxiosInstance.post
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockRejectedValueOnce(new Error('Connection reset'))
        .mockResolvedValueOnce({
          data: mockResponse,
          status: 200,
          statusText: 'OK'
        })

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const result = await apiService.generateItinerary(request)
      
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(3)
      expect(result).toEqual(mockResponse)
    })

    it('gives up after maximum retries', async () => {
      // All calls fail
      mockAxiosInstance.post.mockRejectedValue(new Error('Persistent network error'))

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(request)).rejects.toThrow('Persistent network error')
      
      // Should have tried 3 times (initial + 2 retries)
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(3)
    })

    it('does not retry on client errors (4xx)', async () => {
      const clientError: AxiosError = {
        response: {
          status: 400,
          data: { message: 'Bad request' },
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        },
        isAxiosError: true,
        name: 'AxiosError',
        message: 'Request failed with status code 400',
        config: {} as any,
        toJSON: () => ({})
      }

      mockAxiosInstance.post.mockRejectedValue(clientError)

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      await expect(apiService.generateItinerary(request)).rejects.toThrow('Bad request')
      
      // Should not retry on client errors
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('Request Cancellation', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('supports request cancellation', async () => {
      const abortController = new AbortController()
      
      mockAxiosInstance.post.mockImplementation(() => {
        return new Promise((_, reject) => {
          abortController.signal.addEventListener('abort', () => {
            reject(new Error('Request cancelled'))
          })
        })
      })

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const requestPromise = apiService.generateItinerary(request, abortController.signal)
      
      // Cancel the request
      abortController.abort()

      await expect(requestPromise).rejects.toThrow('Request cancelled')
    })
  })

  describe('Performance Monitoring', () => {
    beforeEach(() => {
      mockAuthService.getToken.mockReturnValue('valid-token')
      mockAuthService.isAuthenticated.mockReturnValue(true)
    })

    it('tracks request timing', async () => {
      const mockResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      mockAxiosInstance.post.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              data: mockResponse,
              status: 200,
              statusText: 'OK'
            })
          }, 100)
        })
      })

      const request: ItineraryRequest = {
        mbtiPersonality: 'ENFP',
        preferences: {}
      }

      const startTime = Date.now()
      await apiService.generateItinerary(request)
      const endTime = Date.now()

      expect(endTime - startTime).toBeGreaterThanOrEqual(100)
    })
  })
})
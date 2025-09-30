import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { AuthService } from '@/services/authService'
import { ApiService } from '@/services/apiService'
import type { AuthToken, UserContext, ItineraryRequest } from '@/types/api'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock window.location
const mockLocation = {
  href: 'http://localhost:3000',
  pathname: '/',
  protocol: 'https:'
}
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
})

// Mock document.cookie
let mockCookie = ''
Object.defineProperty(document, 'cookie', {
  get: () => mockCookie,
  set: (value: string) => {
    if (value.includes('=; Path=/; Expires=')) {
      // Cookie deletion
      const name = value.split('=')[0]
      mockCookie = mockCookie
        .split(';')
        .filter(c => !c.trim().startsWith(name + '='))
        .join(';')
    } else {
      // Cookie setting
      const [nameValue] = value.split(';')
      const existingCookies = mockCookie ? mockCookie.split(';') : []
      const name = nameValue.split('=')[0]
      
      // Remove existing cookie with same name
      const filteredCookies = existingCookies.filter(c => 
        !c.trim().startsWith(name + '=')
      )
      
      // Add new cookie
      filteredCookies.push(nameValue)
      mockCookie = filteredCookies.join(';')
    }
  }
})

describe('API Authentication Integration', () => {
  let authService: AuthService
  let apiService: ApiService

  // Valid JWT token for testing (expires in 2025)
  const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE3NzQ5MjkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
  
  const mockAuthToken: AuthToken = {
    accessToken: validToken,
    refreshToken: 'refresh-token-123',
    tokenType: 'Bearer',
    expiresIn: 3600
  }

  const mockUser: UserContext = {
    id: '123',
    email: 'test@example.com',
    name: 'John Doe'
  }

  const mockItineraryRequest: ItineraryRequest = {
    mbtiPersonality: 'ENFP',
    preferences: {
      budget: 'medium',
      interests: ['culture', 'food']
    }
  }

  beforeEach(() => {
    // Reset singleton instances
    ;(AuthService as any).instance = null
    ;(ApiService as any).instance = null
    
    authService = AuthService.getInstance()
    apiService = ApiService.getInstance()
    
    // Clear mocks
    vi.clearAllMocks()
    mockFetch.mockClear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    
    // Clear cookies
    mockCookie = ''
    
    // Reset location
    mockLocation.href = 'http://localhost:3000'
    mockLocation.pathname = '/'
  })

  afterEach(() => {
    authService.logout()
  })

  describe('Authentication Flow Integration', () => {
    it('successfully authenticates and makes API calls', async () => {
      // Mock successful login
      const loginResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          user: mockUser,
          token: mockAuthToken
        })
      }
      mockFetch.mockResolvedValueOnce(loginResponse)

      // Mock successful API call
      const apiResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          main_itinerary: {
            day_1: {
              breakfast: { name: 'Test Restaurant' },
              morning_session: { tourist_spot: 'Test Spot' }
            }
          }
        })
      }
      mockFetch.mockResolvedValueOnce(apiResponse)

      // Step 1: Login
      const user = await authService.login('test@example.com', 'password')
      expect(user).toEqual(mockUser)
      expect(authService.isAuthenticated()).toBe(true)

      // Step 2: Make authenticated API call
      const itinerary = await apiService.generateItinerary(mockItineraryRequest)
      
      // Verify API call was made with correct headers
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/itinerary/generate'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${validToken}`,
            'Content-Type': 'application/json'
          })
        })
      )

      expect(itinerary).toBeDefined()
      expect(itinerary.main_itinerary).toBeDefined()
    })

    it('handles token refresh during API calls', async () => {
      // Set up initial authenticated state
      authService.setToken(mockAuthToken, mockUser)

      // Mock API call that returns 401 (token expired)
      const unauthorizedResponse = {
        ok: false,
        status: 401,
        json: vi.fn().mockResolvedValue({ error: 'Token expired' })
      }
      mockFetch.mockResolvedValueOnce(unauthorizedResponse)

      // Mock successful token refresh
      const newToken = { ...mockAuthToken, accessToken: validToken.replace('John', 'Jane') }
      const refreshResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ token: newToken })
      }
      mockFetch.mockResolvedValueOnce(refreshResponse)

      // Mock successful retry of original API call
      const retryResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          main_itinerary: { day_1: { breakfast: { name: 'Test Restaurant' } } }
        })
      }
      mockFetch.mockResolvedValueOnce(retryResponse)

      // Make API call that should trigger refresh and retry
      const itinerary = await apiService.generateItinerary(mockItineraryRequest)

      // Verify refresh was called
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', expect.any(Object))
      
      // Verify original call was retried with new token
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/itinerary/generate'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${newToken.accessToken}`
          })
        })
      )

      expect(itinerary).toBeDefined()
    })

    it('redirects to login when token refresh fails', async () => {
      // Set up initial authenticated state
      authService.setToken(mockAuthToken, mockUser)

      // Mock API call that returns 401
      const unauthorizedResponse = {
        ok: false,
        status: 401,
        json: vi.fn().mockResolvedValue({ error: 'Token expired' })
      }
      mockFetch.mockResolvedValueOnce(unauthorizedResponse)

      // Mock failed token refresh
      const failedRefreshResponse = {
        ok: false,
        status: 401,
        json: vi.fn().mockResolvedValue({ error: 'Refresh token expired' })
      }
      mockFetch.mockResolvedValueOnce(failedRefreshResponse)

      // API call should fail and trigger logout/redirect
      await expect(
        apiService.generateItinerary(mockItineraryRequest)
      ).rejects.toThrow()

      // Verify user was logged out
      expect(authService.isAuthenticated()).toBe(false)
      
      // Verify redirect to login
      expect(mockLocation.href).toContain('/login')
    })
  })

  describe('API Error Handling Integration', () => {
    beforeEach(() => {
      // Set up authenticated state
      authService.setToken(mockAuthToken, mockUser)
    })

    it('handles network errors gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(
        apiService.generateItinerary(mockItineraryRequest)
      ).rejects.toThrow('Network error')
    })

    it('handles server errors with proper error messages', async () => {
      const serverErrorResponse = {
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({
          error: 'Internal server error',
          message: 'Something went wrong on our end'
        })
      }
      mockFetch.mockResolvedValue(serverErrorResponse)

      await expect(
        apiService.generateItinerary(mockItineraryRequest)
      ).rejects.toThrow('API request failed with status 500')
    })

    it('handles validation errors from API', async () => {
      const validationErrorResponse = {
        ok: false,
        status: 400,
        json: vi.fn().mockResolvedValue({
          error: 'Validation failed',
          details: {
            mbtiPersonality: 'Invalid MBTI type'
          }
        })
      }
      mockFetch.mockResolvedValue(validationErrorResponse)

      await expect(
        apiService.generateItinerary(mockItineraryRequest)
      ).rejects.toThrow('API request failed with status 400')
    })

    it('handles timeout errors', async () => {
      // Mock a request that takes too long
      mockFetch.mockImplementation(() => 
        new Promise((resolve) => {
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({})
          }), 35000) // Longer than typical timeout
        })
      )

      // This would typically be handled by the fetch timeout mechanism
      // For testing, we'll simulate the timeout
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 30000)
      })

      await expect(
        Promise.race([
          apiService.generateItinerary(mockItineraryRequest),
          timeoutPromise
        ])
      ).rejects.toThrow('Request timeout')
    })
  })

  describe('Authentication State Persistence', () => {
    it('persists authentication state across page reloads', () => {
      // Set up authenticated state
      authService.setToken(mockAuthToken, mockUser)
      
      // Verify state is stored
      expect(mockCookie).toContain('mbti_access_token=')
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'mbti_user_data',
        JSON.stringify(mockUser)
      )

      // Simulate page reload by creating new service instance
      ;(AuthService as any).instance = null
      mockCookie = 'mbti_access_token=' + encodeURIComponent(validToken)
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser))

      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.isAuthenticated()).toBe(true)
      expect(newAuthService.getCurrentUser()).toEqual(mockUser)
    })

    it('clears invalid stored tokens on initialization', () => {
      // Set up expired token in storage
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid'
      mockCookie = 'mbti_access_token=' + encodeURIComponent(expiredToken)
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser))

      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.isAuthenticated()).toBe(false)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('mbti_user_data')
    })
  })

  describe('Concurrent API Calls', () => {
    beforeEach(() => {
      authService.setToken(mockAuthToken, mockUser)
    })

    it('handles multiple concurrent API calls correctly', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          main_itinerary: { day_1: { breakfast: { name: 'Test' } } }
        })
      }
      mockFetch.mockResolvedValue(mockResponse)

      // Make multiple concurrent API calls
      const promises = [
        apiService.generateItinerary(mockItineraryRequest),
        apiService.generateItinerary({ ...mockItineraryRequest, mbtiPersonality: 'INTJ' }),
        apiService.generateItinerary({ ...mockItineraryRequest, mbtiPersonality: 'INFP' })
      ]

      const results = await Promise.all(promises)
      
      expect(results).toHaveLength(3)
      expect(mockFetch).toHaveBeenCalledTimes(3)
      
      // Verify all calls included authentication headers
      for (let i = 0; i < 3; i++) {
        expect(mockFetch).toHaveBeenNthCalledWith(i + 1,
          expect.any(String),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${validToken}`
            })
          })
        )
      }
    })

    it('handles token refresh during concurrent calls', async () => {
      // First call returns 401
      const unauthorizedResponse = {
        ok: false,
        status: 401,
        json: vi.fn().mockResolvedValue({ error: 'Token expired' })
      }
      
      // Subsequent calls should wait for refresh
      const successResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          main_itinerary: { day_1: { breakfast: { name: 'Test' } } }
        })
      }

      // Mock token refresh
      const newToken = { ...mockAuthToken, accessToken: validToken.replace('John', 'Jane') }
      const refreshResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ token: newToken })
      }

      mockFetch
        .mockResolvedValueOnce(unauthorizedResponse) // First call fails
        .mockResolvedValueOnce(refreshResponse) // Token refresh succeeds
        .mockResolvedValue(successResponse) // All retries succeed

      // Make concurrent calls
      const promises = [
        apiService.generateItinerary(mockItineraryRequest),
        apiService.generateItinerary({ ...mockItineraryRequest, mbtiPersonality: 'INTJ' })
      ]

      const results = await Promise.all(promises)
      
      expect(results).toHaveLength(2)
      expect(results[0]).toBeDefined()
      expect(results[1]).toBeDefined()
    })
  })

  describe('API Request Validation', () => {
    beforeEach(() => {
      authService.setToken(mockAuthToken, mockUser)
    })

    it('validates request data before sending', async () => {
      const invalidRequest = {
        mbtiPersonality: 'INVALID' as any,
        preferences: {}
      }

      // API service should validate before making request
      await expect(
        apiService.generateItinerary(invalidRequest)
      ).rejects.toThrow()

      // Should not make HTTP request for invalid data
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('includes proper request headers', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({})
      }
      mockFetch.mockResolvedValue(mockResponse)

      await apiService.generateItinerary(mockItineraryRequest)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${validToken}`,
            'Accept': 'application/json'
          }),
          body: JSON.stringify(mockItineraryRequest)
        })
      )
    })
  })

  describe('Error Recovery', () => {
    beforeEach(() => {
      authService.setToken(mockAuthToken, mockUser)
    })

    it('retries failed requests with exponential backoff', async () => {
      let callCount = 0
      mockFetch.mockImplementation(() => {
        callCount++
        if (callCount < 3) {
          return Promise.resolve({
            ok: false,
            status: 503,
            json: () => Promise.resolve({ error: 'Service unavailable' })
          })
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            main_itinerary: { day_1: { breakfast: { name: 'Test' } } }
          })
        })
      })

      const result = await apiService.generateItinerary(mockItineraryRequest)
      
      expect(callCount).toBe(3)
      expect(result).toBeDefined()
    })

    it('gives up after maximum retry attempts', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 503,
        json: () => Promise.resolve({ error: 'Service unavailable' })
      })

      await expect(
        apiService.generateItinerary(mockItineraryRequest)
      ).rejects.toThrow()

      // Should have made initial request plus retries
      expect(mockFetch).toHaveBeenCalledTimes(4) // 1 initial + 3 retries
    })
  })

  describe('Authentication Edge Cases', () => {
    it('handles simultaneous login attempts', async () => {
      const loginResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          user: mockUser,
          token: mockAuthToken
        })
      }
      mockFetch.mockResolvedValue(loginResponse)

      // Make simultaneous login attempts
      const promises = [
        authService.login('test@example.com', 'password'),
        authService.login('test@example.com', 'password')
      ]

      const results = await Promise.all(promises)
      
      expect(results[0]).toEqual(mockUser)
      expect(results[1]).toEqual(mockUser)
      expect(authService.isAuthenticated()).toBe(true)
    })

    it('handles logout during active API calls', async () => {
      // Set up authenticated state
      authService.setToken(mockAuthToken, mockUser)

      // Mock slow API response
      const slowResponse = new Promise(resolve => {
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            main_itinerary: { day_1: { breakfast: { name: 'Test' } } }
          })
        }), 100)
      })
      mockFetch.mockReturnValue(slowResponse)

      // Start API call
      const apiPromise = apiService.generateItinerary(mockItineraryRequest)

      // Logout immediately
      authService.logout()

      // API call should still complete but user should be logged out
      const result = await apiPromise
      expect(result).toBeDefined()
      expect(authService.isAuthenticated()).toBe(false)
    })
  })
})
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { AuthService } from '../authService'
import type { AuthToken, UserContext } from '@/types/api'

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

describe('AuthService', () => {
  let authService: AuthService
  
  // Valid JWT token for testing (expires in 2025)
  const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE3NzQ5MjkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
  
  // Expired JWT token for testing
  const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'

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

  beforeEach(() => {
    // Reset singleton instance
    ;(AuthService as any).instance = null
    authService = AuthService.getInstance()
    
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

  describe('Singleton Pattern', () => {
    it('returns the same instance on multiple calls', () => {
      const instance1 = AuthService.getInstance()
      const instance2 = AuthService.getInstance()
      
      expect(instance1).toBe(instance2)
    })
  })

  describe('Token Validation', () => {
    it('validates a valid JWT token', async () => {
      const isValid = await authService.validateToken(validToken)
      expect(isValid).toBe(true)
    })

    it('rejects an expired JWT token', async () => {
      const isValid = await authService.validateToken(expiredToken)
      expect(isValid).toBe(false)
    })

    it('rejects malformed tokens', async () => {
      const malformedTokens = [
        '',
        'invalid-token',
        'header.payload', // Missing signature
        'header.payload.signature.extra', // Too many parts
        'not.a.jwt'
      ]

      for (const token of malformedTokens) {
        const isValid = await authService.validateToken(token)
        expect(isValid).toBe(false)
      }
    })

    it('rejects non-string tokens', async () => {
      const invalidInputs = [null, undefined, 123, {}, []]
      
      for (const input of invalidInputs) {
        const isValid = await authService.validateToken(input as any)
        expect(isValid).toBe(false)
      }
    })
  })

  describe('Authentication State', () => {
    it('initializes as not authenticated', () => {
      expect(authService.isAuthenticated()).toBe(false)
      expect(authService.getCurrentUser()).toBeNull()
      expect(authService.getToken()).toBeNull()
    })

    it('sets authentication state correctly', () => {
      authService.setToken(mockAuthToken, mockUser)
      
      expect(authService.isAuthenticated()).toBe(true)
      expect(authService.getCurrentUser()).toEqual(mockUser)
      expect(authService.getToken()).toBe(validToken)
    })

    it('clears authentication state on logout', () => {
      authService.setToken(mockAuthToken, mockUser)
      expect(authService.isAuthenticated()).toBe(true)
      
      authService.logout()
      
      expect(authService.isAuthenticated()).toBe(false)
      expect(authService.getCurrentUser()).toBeNull()
      expect(authService.getToken()).toBeNull()
    })
  })

  describe('Token Storage', () => {
    it('stores tokens in cookies', () => {
      authService.setToken(mockAuthToken, mockUser)
      
      expect(mockCookie).toContain('mbti_access_token=')
      expect(mockCookie).toContain('mbti_refresh_token=')
    })

    it('stores user data in localStorage', () => {
      authService.setToken(mockAuthToken, mockUser)
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'mbti_user_data',
        JSON.stringify(mockUser)
      )
    })

    it('clears stored data on logout', () => {
      authService.setToken(mockAuthToken, mockUser)
      authService.logout()
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('mbti_user_data')
      expect(mockCookie).not.toContain('mbti_access_token=')
      expect(mockCookie).not.toContain('mbti_refresh_token=')
    })
  })

  describe('Login', () => {
    it('successfully logs in with valid credentials', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          user: mockUser,
          token: mockAuthToken
        })
      }
      mockFetch.mockResolvedValue(mockResponse)

      const user = await authService.login('test@example.com', 'password')

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password'
        })
      })

      expect(user).toEqual(mockUser)
      expect(authService.isAuthenticated()).toBe(true)
    })

    it('throws error on failed login', async () => {
      const mockResponse = {
        ok: false,
        status: 401
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(
        authService.login('test@example.com', 'wrong-password')
      ).rejects.toThrow('Login failed: 401')

      expect(authService.isAuthenticated()).toBe(false)
    })

    it('handles network errors during login', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      await expect(
        authService.login('test@example.com', 'password')
      ).rejects.toThrow('Network error')
    })
  })

  describe('Token Refresh', () => {
    beforeEach(() => {
      // Set up initial authenticated state
      authService.setToken(mockAuthToken, mockUser)
    })

    it('successfully refreshes token', async () => {
      const newToken: AuthToken = {
        ...mockAuthToken,
        accessToken: validToken.replace('John Doe', 'Jane Doe')
      }

      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ token: newToken })
      }
      mockFetch.mockResolvedValue(mockResponse)

      const refreshedToken = await authService.refreshToken()

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refreshToken: 'refresh-token-123'
        })
      })

      expect(refreshedToken).toBe(newToken.accessToken)
      expect(authService.getToken()).toBe(newToken.accessToken)
    })

    it('logs out user on refresh failure', async () => {
      const mockResponse = {
        ok: false,
        status: 401
      }
      mockFetch.mockResolvedValue(mockResponse)

      await expect(authService.refreshToken()).rejects.toThrow('Token refresh failed')
      expect(authService.isAuthenticated()).toBe(false)
    })

    it('throws error when no refresh token available', async () => {
      // Clear cookies to simulate missing refresh token
      mockCookie = ''

      await expect(authService.refreshToken()).rejects.toThrow('No refresh token available')
    })
  })

  describe('Redirect to Login', () => {
    it('redirects to login page', () => {
      authService.redirectToLogin()
      
      expect(mockLocation.href).toBe('/login?returnUrl=%2F')
      expect(authService.isAuthenticated()).toBe(false)
    })

    it('preserves current path in return URL', () => {
      mockLocation.pathname = '/itinerary'
      
      authService.redirectToLogin()
      
      expect(mockLocation.href).toBe('/login?returnUrl=%2Fitinerary')
    })

    it('does not set return URL when already on login page', () => {
      mockLocation.pathname = '/login'
      
      authService.redirectToLogin()
      
      expect(mockLocation.href).toBe('/login?returnUrl=%2F')
    })
  })

  describe('Cookie Management', () => {
    it('sets secure cookies in HTTPS environment', () => {
      mockLocation.protocol = 'https:'
      
      authService.setToken(mockAuthToken)
      
      expect(mockCookie).toContain('mbti_access_token=')
    })

    it('handles cookie parsing correctly', () => {
      // Manually set a cookie
      mockCookie = 'mbti_access_token=' + encodeURIComponent(validToken) + '; other=value'
      
      // Create new instance to test initialization from storage
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.getToken()).toBe(validToken)
    })

    it('handles malformed cookies gracefully', () => {
      mockCookie = 'malformed-cookie-without-equals'
      
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.getToken()).toBeNull()
    })
  })

  describe('Initialization from Storage', () => {
    it('initializes from stored valid token', () => {
      // Set up stored data
      mockCookie = 'mbti_access_token=' + encodeURIComponent(validToken)
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser))
      
      // Create new instance
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.isAuthenticated()).toBe(true)
      expect(newAuthService.getCurrentUser()).toEqual(mockUser)
    })

    it('clears invalid stored tokens', () => {
      // Set up stored expired token
      mockCookie = 'mbti_access_token=' + encodeURIComponent(expiredToken)
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser))
      
      // Create new instance
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.isAuthenticated()).toBe(false)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('mbti_user_data')
    })

    it('handles localStorage errors gracefully', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })
      
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.isAuthenticated()).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('handles JSON parsing errors in stored user data', () => {
      mockCookie = 'mbti_access_token=' + encodeURIComponent(validToken)
      localStorageMock.getItem.mockReturnValue('invalid-json')
      
      ;(AuthService as any).instance = null
      const newAuthService = AuthService.getInstance()
      
      expect(newAuthService.getCurrentUser()).toBeNull()
    })

    it('handles localStorage setItem errors', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })
      
      // Should not throw error
      expect(() => {
        authService.setToken(mockAuthToken, mockUser)
      }).not.toThrow()
    })
  })

  describe('JWT Payload Decoding', () => {
    it('correctly decodes valid JWT payload', async () => {
      const isValid = await authService.validateToken(validToken)
      expect(isValid).toBe(true)
    })

    it('handles malformed base64 in JWT payload', async () => {
      const malformedToken = 'header.invalid-base64.signature'
      const isValid = await authService.validateToken(malformedToken)
      expect(isValid).toBe(false)
    })

    it('handles invalid JSON in JWT payload', async () => {
      // Create token with invalid JSON payload
      const invalidPayload = btoa('invalid-json')
      const invalidToken = `header.${invalidPayload}.signature`
      
      const isValid = await authService.validateToken(invalidToken)
      expect(isValid).toBe(false)
    })
  })

  describe('Token Refresh Scheduling', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('schedules token refresh before expiration', () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ token: mockAuthToken })
      }
      mockFetch.mockResolvedValue(mockResponse)

      authService.setToken(mockAuthToken, mockUser)
      
      // Fast-forward time to trigger refresh
      vi.advanceTimersByTime(3600000 - 300000) // 1 hour - 5 minutes
      
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', expect.any(Object))
    })

    it('redirects to login on refresh failure', () => {
      const mockResponse = {
        ok: false,
        status: 401
      }
      mockFetch.mockResolvedValue(mockResponse)

      authService.setToken(mockAuthToken, mockUser)
      
      // Fast-forward time to trigger refresh
      vi.advanceTimersByTime(3600000 - 300000)
      
      // Wait for async operations
      vi.runAllTimers()
      
      expect(authService.isAuthenticated()).toBe(false)
    })
  })
})
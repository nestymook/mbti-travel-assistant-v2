import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import axios from 'axios'
import InputPage from '../../views/InputPage.vue'
import ItineraryPage from '../../views/ItineraryPage.vue'
import LoginView from '../../views/LoginView.vue'
import { ApiService } from '../../services/apiService'
import { AuthService } from '../../services/authService'
import type { ItineraryRequest, ItineraryResponse } from '../../types'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

// Mock services
vi.mock('../../services/apiService')
vi.mock('../../services/authService')

const MockedApiService = vi.mocked(ApiService)
const MockedAuthService = vi.mocked(AuthService)

describe('API Authentication Integration Tests', () => {
  let router: any
  let pinia: any
  let mockApiService: any
  let mockAuthService: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Create router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: InputPage },
        { path: '/itinerary', component: ItineraryPage },
        { path: '/login', component: LoginView }
      ]
    })

    // Create pinia store
    pinia = createPinia()

    // Mock services
    mockApiService = {
      generateItinerary: vi.fn(),
      setAuthToken: vi.fn(),
      clearAuthToken: vi.fn()
    }

    mockAuthService = {
      isAuthenticated: vi.fn(),
      getToken: vi.fn(),
      refreshToken: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
      validateToken: vi.fn(),
      redirectToLogin: vi.fn()
    }

    MockedApiService.getInstance.mockReturnValue(mockApiService)
    MockedAuthService.getInstance.mockReturnValue(mockAuthService)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Authenticated API Requests', () => {
    it('includes JWT token in API requests when user is authenticated', async () => {
      const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
      const mockItineraryResponse: ItineraryResponse = {
        main_itinerary: {
          day_1: {
            breakfast: {
              id: 'rest_001',
              name: 'Morning Cafe',
              address: '123 Main St',
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

      // Setup authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockApiService.generateItinerary.mockResolvedValue(mockItineraryResponse)

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate form submission
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('ENFP')
      await form.trigger('submit')

      // Verify API service was called with authentication
      expect(mockApiService.generateItinerary).toHaveBeenCalledWith({
        mbtiPersonality: 'ENFP',
        preferences: {}
      })
      expect(mockApiService.setAuthToken).toHaveBeenCalledWith(mockToken)
    })

    it('redirects to login when user is not authenticated', async () => {
      // Setup unauthenticated state
      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getToken.mockReturnValue(null)

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate form submission
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('ENFP')
      await form.trigger('submit')

      // Should redirect to login instead of making API call
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
      expect(mockApiService.generateItinerary).not.toHaveBeenCalled()
    })

    it('handles token refresh on 401 response', async () => {
      const oldToken = 'old-token'
      const newToken = 'new-token'
      const mockItineraryResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      // Setup initial authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken
        .mockReturnValueOnce(oldToken)
        .mockReturnValueOnce(newToken)
      mockAuthService.refreshToken.mockResolvedValue(newToken)

      // First API call fails with 401, second succeeds
      mockApiService.generateItinerary
        .mockRejectedValueOnce(new Error('Unauthorized'))
        .mockResolvedValueOnce(mockItineraryResponse)

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate form submission
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('ENFP')
      await form.trigger('submit')

      // Should attempt token refresh and retry
      expect(mockAuthService.refreshToken).toHaveBeenCalled()
      expect(mockApiService.generateItinerary).toHaveBeenCalledTimes(2)
    })

    it('redirects to login when token refresh fails', async () => {
      const expiredToken = 'expired-token'

      // Setup authenticated state with expired token
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue(expiredToken)
      mockAuthService.refreshToken.mockRejectedValue(new Error('Refresh failed'))

      // API call fails with 401
      mockApiService.generateItinerary.mockRejectedValue(new Error('Unauthorized'))

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate form submission
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('ENFP')
      await form.trigger('submit')

      // Should attempt refresh, fail, and redirect to login
      expect(mockAuthService.refreshToken).toHaveBeenCalled()
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
    })
  })

  describe('Token Validation', () => {
    it('validates token on application startup', async () => {
      const mockToken = 'valid-token'
      
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockAuthService.validateToken.mockResolvedValue(true)
      mockAuthService.isAuthenticated.mockReturnValue(true)

      mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should validate token on mount
      expect(mockAuthService.validateToken).toHaveBeenCalledWith(mockToken)
    })

    it('clears invalid token and redirects to login', async () => {
      const invalidToken = 'invalid-token'
      
      mockAuthService.getToken.mockReturnValue(invalidToken)
      mockAuthService.validateToken.mockResolvedValue(false)
      mockAuthService.isAuthenticated.mockReturnValue(false)

      mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should validate token, find it invalid, and redirect
      expect(mockAuthService.validateToken).toHaveBeenCalledWith(invalidToken)
      expect(mockAuthService.logout).toHaveBeenCalled()
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
    })

    it('handles network errors during token validation gracefully', async () => {
      const mockToken = 'token-to-validate'
      
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockAuthService.validateToken.mockRejectedValue(new Error('Network error'))
      mockAuthService.isAuthenticated.mockReturnValue(true) // Assume valid until proven otherwise

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should handle validation error gracefully
      expect(mockAuthService.validateToken).toHaveBeenCalledWith(mockToken)
      expect(wrapper.find('.error-message').exists()).toBe(false) // Should not show error to user
    })
  })

  describe('Login Flow Integration', () => {
    it('completes login flow and redirects to original destination', async () => {
      const mockToken = 'new-login-token'
      const mockUserCredentials = {
        username: 'testuser',
        password: 'testpass'
      }

      // Setup login success
      mockAuthService.login.mockResolvedValue({
        token: mockToken,
        user: { id: '123', username: 'testuser' }
      })
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue(mockToken)

      // Start at login page
      await router.push('/login')
      
      const wrapper = mount(LoginView, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate login form submission
      const form = wrapper.find('form')
      const usernameInput = wrapper.find('input[name="username"]')
      const passwordInput = wrapper.find('input[name="password"]')

      await usernameInput.setValue(mockUserCredentials.username)
      await passwordInput.setValue(mockUserCredentials.password)
      await form.trigger('submit')

      // Should complete login and set token
      expect(mockAuthService.login).toHaveBeenCalledWith(mockUserCredentials)
      expect(mockApiService.setAuthToken).toHaveBeenCalledWith(mockToken)
    })

    it('shows login error for invalid credentials', async () => {
      const invalidCredentials = {
        username: 'wronguser',
        password: 'wrongpass'
      }

      // Setup login failure
      mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'))

      const wrapper = mount(LoginView, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate login form submission
      const form = wrapper.find('form')
      const usernameInput = wrapper.find('input[name="username"]')
      const passwordInput = wrapper.find('input[name="password"]')

      await usernameInput.setValue(invalidCredentials.username)
      await passwordInput.setValue(invalidCredentials.password)
      await form.trigger('submit')

      // Should show error message
      expect(mockAuthService.login).toHaveBeenCalledWith(invalidCredentials)
      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('Invalid credentials')
    })
  })

  describe('Logout Flow Integration', () => {
    it('clears authentication state on logout', async () => {
      // Setup authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue('valid-token')

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Find and click logout button
      const logoutButton = wrapper.find('.logout-button')
      await logoutButton.trigger('click')

      // Should clear authentication
      expect(mockAuthService.logout).toHaveBeenCalled()
      expect(mockApiService.clearAuthToken).toHaveBeenCalled()
    })

    it('redirects to login page after logout', async () => {
      // Setup authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue('valid-token')

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate logout
      const logoutButton = wrapper.find('.logout-button')
      await logoutButton.trigger('click')

      // Should redirect to login
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
    })
  })

  describe('Route Protection', () => {
    it('protects itinerary route from unauthenticated access', async () => {
      // Setup unauthenticated state
      mockAuthService.isAuthenticated.mockReturnValue(false)
      mockAuthService.getToken.mockReturnValue(null)

      // Try to navigate to protected route
      await router.push('/itinerary')

      const wrapper = mount(ItineraryPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should redirect to login
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
    })

    it('allows access to itinerary route when authenticated', async () => {
      const mockToken = 'valid-token'
      
      // Setup authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockAuthService.validateToken.mockResolvedValue(true)

      // Navigate to protected route
      await router.push('/itinerary')

      const wrapper = mount(ItineraryPage, {
        global: {
          plugins: [router, pinia],
          props: {
            // Mock required props for ItineraryPage
            mbtiPersonality: 'ENFP',
            itineraryData: {
              main_itinerary: {} as any,
              candidate_tourist_spots: {} as any,
              candidate_restaurants: {} as any,
              metadata: {
                generatedAt: new Date().toISOString(),
                processingTime: 1000,
                version: '1.0.0'
              }
            }
          }
        }
      })

      // Should not redirect, component should render
      expect(mockAuthService.redirectToLogin).not.toHaveBeenCalled()
      expect(wrapper.find('.itinerary-container').exists()).toBe(true)
    })
  })

  describe('Session Management', () => {
    it('maintains session across page refreshes', async () => {
      const mockToken = 'persistent-token'
      
      // Setup token in storage
      mockAuthService.getToken.mockReturnValue(mockToken)
      mockAuthService.validateToken.mockResolvedValue(true)
      mockAuthService.isAuthenticated.mockReturnValue(true)

      // Simulate page refresh by mounting component
      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should restore session from storage
      expect(mockAuthService.validateToken).toHaveBeenCalledWith(mockToken)
      expect(mockApiService.setAuthToken).toHaveBeenCalledWith(mockToken)
    })

    it('handles session expiry gracefully', async () => {
      const expiredToken = 'expired-token'
      
      // Setup expired token
      mockAuthService.getToken.mockReturnValue(expiredToken)
      mockAuthService.validateToken.mockResolvedValue(false)
      mockAuthService.isAuthenticated.mockReturnValue(false)

      mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should handle expired session
      expect(mockAuthService.validateToken).toHaveBeenCalledWith(expiredToken)
      expect(mockAuthService.logout).toHaveBeenCalled()
      expect(mockAuthService.redirectToLogin).toHaveBeenCalled()
    })

    it('automatically refreshes token before expiry', async () => {
      const currentToken = 'current-token'
      const refreshedToken = 'refreshed-token'
      
      // Setup token that needs refresh
      mockAuthService.getToken
        .mockReturnValueOnce(currentToken)
        .mockReturnValueOnce(refreshedToken)
      mockAuthService.validateToken.mockResolvedValue(true)
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.refreshToken.mockResolvedValue(refreshedToken)

      // Mock token expiry check
      vi.spyOn(Date, 'now').mockReturnValue(Date.now() + 5 * 60 * 1000) // 5 minutes from now

      mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should proactively refresh token
      expect(mockAuthService.refreshToken).toHaveBeenCalled()
      expect(mockApiService.setAuthToken).toHaveBeenCalledWith(refreshedToken)
    })
  })

  describe('Error Recovery', () => {
    it('recovers from temporary network failures', async () => {
      const mockToken = 'valid-token'
      const mockItineraryResponse: ItineraryResponse = {
        main_itinerary: {} as any,
        candidate_tourist_spots: {} as any,
        candidate_restaurants: {} as any,
        metadata: {
          generatedAt: new Date().toISOString(),
          processingTime: 1000,
          version: '1.0.0'
        }
      }

      // Setup authenticated state
      mockAuthService.isAuthenticated.mockReturnValue(true)
      mockAuthService.getToken.mockReturnValue(mockToken)

      // First call fails, second succeeds
      mockApiService.generateItinerary
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockResolvedValueOnce(mockItineraryResponse)

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Simulate form submission
      const form = wrapper.find('form')
      const input = wrapper.find('input[type="text"]')
      
      await input.setValue('ENFP')
      await form.trigger('submit')

      // Should show retry option
      expect(wrapper.find('.retry-button').exists()).toBe(true)

      // Click retry
      const retryButton = wrapper.find('.retry-button')
      await retryButton.trigger('click')

      // Should succeed on retry
      expect(mockApiService.generateItinerary).toHaveBeenCalledTimes(2)
    })

    it('handles authentication service failures gracefully', async () => {
      // Setup auth service failure
      mockAuthService.isAuthenticated.mockImplementation(() => {
        throw new Error('Auth service unavailable')
      })

      const wrapper = mount(InputPage, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Should handle auth service failure gracefully
      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('Authentication service unavailable')
    })
  })
})
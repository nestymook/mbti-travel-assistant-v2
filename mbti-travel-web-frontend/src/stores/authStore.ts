import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { cognitoAuth } from '@/services/cognitoAuthService'
import type { UserContext, AuthToken } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<UserContext | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)

  // Computed
  const isAuthenticated = computed(() => {
    return user.value !== null
  })

  const hasError = computed(() => error.value !== null)

  const userDisplayName = computed(() => {
    if (!user.value) return null
    return user.value.name || user.value.email || 'User'
  })

  // Actions
  async function initialize(): Promise<void> {
    if (isInitialized.value) return

    try {
      isLoading.value = true
      error.value = null

      // Check if Cognito is configured
      if (!cognitoAuth.isConfigurationValid()) {
        console.warn('Cognito not configured. Using mock authentication.')
        return
      }

      // Check if user is already authenticated
      const currentUser = await cognitoAuth.getCurrentUser()
      if (currentUser) {
        user.value = currentUser
      }
    } catch (err) {
      console.error('Auth initialization failed:', err)
      error.value = 'Failed to initialize authentication'
    } finally {
      isLoading.value = false
      isInitialized.value = true
    }
  }

  async function login(email: string, password: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      // Use Cognito authentication if configured, otherwise use mock
      if (cognitoAuth.isConfigurationValid()) {
        const userData = await cognitoAuth.login(email, password)
        user.value = userData
      } else {
        // Mock authentication for demo
        console.warn('Using mock authentication - Cognito not configured')
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate delay
        
        if (!email || !password) {
          throw new Error('Email and password are required')
        }
        
        user.value = {
          id: 'mock-user-123',
          email: email,
          name: email.split('@')[0],
          roles: ['user'],
          preferences: {
            theme: 'light',
            language: 'en'
          }
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      if (cognitoAuth.isConfigurationValid()) {
        await cognitoAuth.logout()
      }
      user.value = null
      error.value = null
    } catch (err) {
      console.error('Logout failed:', err)
      // Force clear state even if logout fails
      user.value = null
      error.value = null
    }
  }

  async function refreshToken(): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      if (cognitoAuth.isConfigurationValid()) {
        // Cognito handles token refresh automatically
        const currentUser = await cognitoAuth.getCurrentUser()
        if (currentUser) {
          user.value = currentUser
        } else {
          throw new Error('Session expired')
        }
      }
    } catch (err) {
      console.error('Token refresh failed:', err)
      error.value = 'Session expired. Please log in again.'
      
      // Clear auth state and redirect to login
      await logout()
      redirectToLogin()
    } finally {
      isLoading.value = false
    }
  }

  function setAuthData(authToken: AuthToken, userData: UserContext): void {
    try {
      // For Cognito, tokens are managed automatically
      user.value = userData
      error.value = null
    } catch (err) {
      console.error('Failed to set auth data:', err)
      error.value = 'Failed to set authentication data'
    }
  }

  function clearError(): void {
    error.value = null
  }

  async function getAuthToken(): Promise<string | null> {
    if (cognitoAuth.isConfigurationValid()) {
      return await cognitoAuth.getAuthToken()
    }
    return null
  }

  async function validateCurrentToken(): Promise<boolean> {
    try {
      if (cognitoAuth.isConfigurationValid()) {
        const isValid = await cognitoAuth.validateSession()
        if (!isValid) {
          await logout()
          return false
        }
        return true
      }
      return user.value !== null // For mock auth
    } catch (err) {
      console.error('Token validation failed:', err)
      await logout()
      return false
    }
  }

  function redirectToLogin(): void {
    // Clear any existing auth data
    user.value = null
    error.value = null
    
    // Get current path to redirect back after login
    const currentPath = window.location.pathname
    const returnUrl = currentPath !== '/login' ? currentPath : '/'
    
    // Redirect to login with return URL
    const loginUrl = `/login?returnUrl=${encodeURIComponent(returnUrl)}`
    window.location.href = loginUrl
  }

  // Auto-initialize when store is created
  initialize()

  return {
    // State
    user,
    isLoading,
    error,
    isInitialized,
    
    // Computed
    isAuthenticated,
    hasError,
    userDisplayName,
    
    // Actions
    initialize,
    login,
    logout,
    refreshToken,
    setAuthData,
    clearError,
    getAuthToken,
    validateCurrentToken,
    redirectToLogin
  }
})
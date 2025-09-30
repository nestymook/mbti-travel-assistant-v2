import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { AuthService } from '@/services/authService'
import type { UserContext, AuthToken } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<UserContext | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)

  // Get AuthService instance
  const authService = AuthService.getInstance()

  // Computed
  const isAuthenticated = computed(() => {
    return authService.isAuthenticated() && user.value !== null
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

      // Check if user is already authenticated
      if (authService.isAuthenticated()) {
        const currentUser = authService.getCurrentUser()
        if (currentUser) {
          user.value = currentUser
        }
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

      const userData = await authService.login(email, password)
      user.value = userData
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  function logout(): void {
    try {
      authService.logout()
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

      await authService.refreshToken()
      
      // Update user data after token refresh
      const currentUser = authService.getCurrentUser()
      if (currentUser) {
        user.value = currentUser
      }
    } catch (err) {
      console.error('Token refresh failed:', err)
      error.value = 'Session expired. Please log in again.'
      
      // Clear auth state and redirect to login
      logout()
      authService.redirectToLogin()
    } finally {
      isLoading.value = false
    }
  }

  function setAuthData(authToken: AuthToken, userData: UserContext): void {
    try {
      authService.setToken(authToken, userData)
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

  function getAuthToken(): string | null {
    return authService.getToken()
  }

  async function validateCurrentToken(): Promise<boolean> {
    const token = authService.getToken()
    if (!token) return false

    try {
      const isValid = await authService.validateToken(token)
      if (!isValid) {
        // Token is invalid, clear auth state
        logout()
        return false
      }
      return true
    } catch (err) {
      console.error('Token validation failed:', err)
      logout()
      return false
    }
  }

  function redirectToLogin(): void {
    authService.redirectToLogin()
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
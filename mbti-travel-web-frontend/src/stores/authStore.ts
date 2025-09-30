import { ref, computed } from 'vue'
import { defineStore, getActivePinia } from 'pinia'
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

  // Utility functions
  function clearAllApplicationState(): void {
    try {
      // Clear all Pinia stores
      const pinia = getActivePinia()
      if (pinia) {
        // Reset all stores to their initial state
        pinia._s.forEach((store) => {
          if (store.$id !== 'auth') { // Don't reset auth store as we're managing it manually
            if (store.$reset) {
              store.$reset()
            }
          }
        })
      }

      // Clear browser storage
      try {
        localStorage.clear()
      } catch (e) {
        console.warn('Failed to clear localStorage:', e)
      }

      try {
        sessionStorage.clear()
      } catch (e) {
        console.warn('Failed to clear sessionStorage:', e)
      }

      // Clear any cached data in memory
      if (window.caches) {
        window.caches.keys().then(cacheNames => {
          cacheNames.forEach(cacheName => {
            window.caches.delete(cacheName)
          })
        }).catch(e => {
          console.warn('Failed to clear caches:', e)
        })
      }

      // Clear any IndexedDB data if used
      if (window.indexedDB) {
        try {
          // This is a more aggressive approach - in production you might want to be more selective
          const databases = ['amplify-datastore', 'aws-amplify-cache', 'keyval-store']
          databases.forEach(dbName => {
            const deleteReq = window.indexedDB.deleteDatabase(dbName)
            deleteReq.onerror = () => console.warn(`Failed to delete database: ${dbName}`)
          })
        } catch (e) {
          console.warn('Failed to clear IndexedDB:', e)
        }
      }

      console.log('Application state cleared successfully')
    } catch (error) {
      console.error('Error clearing application state:', error)
    }
  }

  // Actions
  async function initialize(): Promise<void> {
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
        console.log('User authenticated:', currentUser.email)
      } else {
        console.log('No authenticated user found')
        user.value = null
      }
    } catch (err) {
      console.error('Auth initialization failed:', err)
      error.value = 'Failed to initialize authentication'
      user.value = null
    } finally {
      isLoading.value = false
      isInitialized.value = true
    }
  }

  // Login is now handled entirely through Cognito Hosted UI
  // This method is kept for compatibility but redirects to Hosted UI
  async function login(email?: string, password?: string): Promise<void> {
    console.log('Redirecting to Cognito Hosted UI for authentication')
    redirectToHostedUI()
  }

  async function loginWithHostedUI(): Promise<void> {
    try {
      isLoading.value = true
      error.value = null

      if (cognitoAuth.isConfigurationValid()) {
        // Redirect to Cognito Hosted UI
        await cognitoAuth.signInWithHostedUI()
      } else {
        throw new Error('Cognito not configured')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Hosted UI login failed'
      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  function redirectToHostedUI(): void {
    try {
      if (cognitoAuth.isConfigurationValid()) {
        const hostedUIUrl = cognitoAuth.getHostedUILoginUrl()
        window.location.href = hostedUIUrl
      } else {
        // Fallback to login page if Cognito not configured
        window.location.href = '/login'
      }
    } catch (err) {
      console.error('Failed to redirect to hosted UI:', err)
      window.location.href = '/login'
    }
  }

  async function logout(): Promise<void> {
    try {
      // Clear all application state first
      clearAllApplicationState()
      
      // Clear auth store state
      user.value = null
      error.value = null
      isInitialized.value = false
      
      // Sign out from Cognito using Hosted UI logout
      if (cognitoAuth.isConfigurationValid()) {
        // Use Cognito Hosted UI logout which will redirect to the logout URL
        cognitoAuth.logoutWithHostedUI()
      } else {
        // If Cognito not configured, just redirect to login
        redirectToLogin()
      }
    } catch (err) {
      console.error('Logout failed:', err)
      
      // Force clear state even if logout fails
      clearAllApplicationState()
      user.value = null
      error.value = null
      isInitialized.value = false
      
      // Try Cognito logout as fallback
      if (cognitoAuth.isConfigurationValid()) {
        try {
          cognitoAuth.logoutWithHostedUI()
        } catch (fallbackError) {
          console.error('Fallback logout failed:', fallbackError)
          redirectToLogin()
        }
      } else {
        redirectToLogin()
      }
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
      
      // Clear all application state when session expires
      clearAllApplicationState()
      user.value = null
      error.value = null
      isInitialized.value = false
      
      // Redirect to login
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
          // Clear state when token is invalid
          clearAllApplicationState()
          user.value = null
          error.value = null
          isInitialized.value = false
          return false
        }
        return true
      }
      return user.value !== null // For mock auth
    } catch (err) {
      console.error('Token validation failed:', err)
      
      // Clear state on validation error
      clearAllApplicationState()
      user.value = null
      error.value = null
      isInitialized.value = false
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

  // Handle browser close/refresh to clear sensitive data
  function setupBrowserEventHandlers(): void {
    // Clear sensitive data when browser is closing/refreshing
    window.addEventListener('beforeunload', () => {
      try {
        // Only clear sensitive data, not all application state
        // as user might just be refreshing the page
        const sensitiveKeys = ['aws-amplify-cache', 'amplify-datastore']
        sensitiveKeys.forEach(key => {
          try {
            localStorage.removeItem(key)
            sessionStorage.removeItem(key)
          } catch (e) {
            // Ignore errors
          }
        })
      } catch (error) {
        // Ignore errors during cleanup
      }
    })

    // Handle visibility change (tab switching, minimizing)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        // Optionally clear sensitive data when tab becomes hidden
        // This is more aggressive and might not be desired for UX
        // Uncomment if needed for high security requirements
        // clearSensitiveData()
      }
    })
  }

  // Auto-initialize when store is created
  initialize()
  setupBrowserEventHandlers()

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
    redirectToLogin,
    redirectToHostedUI,
    clearAllApplicationState
  }
})
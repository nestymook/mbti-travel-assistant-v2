import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import type { UserContext } from '@/types/api'

/**
 * Composable for authentication functionality
 */
export function useAuth() {
  const router = useRouter()
  const authStore = useAuthStore()

  // Computed properties
  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const isLoading = computed(() => authStore.isLoading)
  const user = computed(() => authStore.user)
  const error = computed(() => authStore.error)
  const userDisplayName = computed(() => authStore.userDisplayName)

  // Methods
  async function login(email: string, password: string): Promise<void> {
    return await authStore.login(email, password)
  }

  function logout(): void {
    authStore.logout()
    router.push({ name: 'login' })
  }

  async function refreshToken(): Promise<void> {
    return await authStore.refreshToken()
  }

  function clearError(): void {
    authStore.clearError()
  }

  function getAuthToken(): string | null {
    return authStore.getAuthToken()
  }

  async function validateToken(): Promise<boolean> {
    return await authStore.validateCurrentToken()
  }

  function redirectToLogin(): void {
    authStore.redirectToLogin()
  }

  // Guard function for protecting routes/components
  async function requireAuth(): Promise<boolean> {
    if (!authStore.isInitialized) {
      await authStore.initialize()
    }

    if (!isAuthenticated.value) {
      const isValid = await validateToken()
      if (!isValid) {
        redirectToLogin()
        return false
      }
    }

    return true
  }

  // Auto-initialize on mount
  onMounted(async () => {
    if (!authStore.isInitialized) {
      await authStore.initialize()
    }
  })

  return {
    // State
    isAuthenticated,
    isLoading,
    user,
    error,
    userDisplayName,

    // Methods
    login,
    logout,
    refreshToken,
    clearError,
    getAuthToken,
    validateToken,
    redirectToLogin,
    requireAuth
  }
}

/**
 * Composable for authentication guards in components
 */
export function useAuthGuard() {
  const { requireAuth, redirectToLogin } = useAuth()

  // Component guard - call this in component setup
  async function guardComponent(): Promise<void> {
    const isAuthorized = await requireAuth()
    if (!isAuthorized) {
      redirectToLogin()
    }
  }

  return {
    guardComponent
  }
}
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'
import { preserveRouteState, getPreservedState, clearPreservedState } from '@/router'

export interface NavigationState {
  scrollPosition: number
  formData?: Record<string, any>
  timestamp: number
  [key: string]: any
}

export interface NavigationOptions {
  preserveState?: boolean
  replace?: boolean
  force?: boolean
}

/**
 * Composable for enhanced navigation with state preservation
 */
export function useNavigation() {
  const router = useRouter()
  const route = useRoute()
  
  // Navigation state
  const isNavigating = ref(false)
  const navigationError = ref<string | null>(null)
  
  // Computed properties
  const currentRouteName = computed(() => route.name?.toString() || '')
  const canGoBack = computed(() => window.history.length > 1)
  const canGoForward = computed(() => {
    // This is a simplified check - in a real app you might track this more precisely
    return false
  })
  
  /**
   * Navigate to a route with enhanced options
   */
  async function navigateTo(
    to: RouteLocationRaw, 
    options: NavigationOptions = {}
  ): Promise<void> {
    try {
      isNavigating.value = true
      navigationError.value = null
      
      // Preserve current state if requested
      if (options.preserveState && currentRouteName.value) {
        const currentState = getCurrentState()
        preserveRouteState(currentRouteName.value, currentState)
      }
      
      // Perform navigation
      if (options.replace) {
        await router.replace(to)
      } else {
        await router.push(to)
      }
    } catch (error) {
      console.error('Navigation failed:', error)
      navigationError.value = error instanceof Error ? error.message : 'Navigation failed'
      throw error
    } finally {
      isNavigating.value = false
    }
  }
  
  /**
   * Go back in browser history
   */
  function goBack(): void {
    if (canGoBack.value) {
      router.go(-1)
    } else {
      // Fallback to home if no history
      navigateTo({ name: 'home' }, { replace: true })
    }
  }
  
  /**
   * Go forward in browser history
   */
  function goForward(): void {
    if (canGoForward.value) {
      router.go(1)
    }
  }
  
  /**
   * Navigate to home page
   */
  function goHome(options: NavigationOptions = {}): Promise<void> {
    return navigateTo({ name: 'home' }, options)
  }
  
  /**
   * Navigate to login page with return URL
   */
  function goToLogin(returnUrl?: string): Promise<void> {
    const query = returnUrl ? { returnUrl: encodeURIComponent(returnUrl) } : {}
    return navigateTo({ name: 'login', query }, { replace: true })
  }
  
  /**
   * Navigate to itinerary page
   */
  function goToItinerary(mbti: string, options: NavigationOptions = {}): Promise<void> {
    return navigateTo({ 
      name: 'itinerary', 
      params: { mbti: mbti.toUpperCase() } 
    }, options)
  }
  
  /**
   * Refresh current route
   */
  async function refresh(): Promise<void> {
    const currentRoute = { ...route }
    await router.replace({ path: '/refresh' })
    await router.replace(currentRoute)
  }
  
  /**
   * Get current route state for preservation
   */
  function getCurrentState(): NavigationState {
    return {
      scrollPosition: window.scrollY,
      timestamp: Date.now(),
      // Add any additional state you want to preserve
      path: route.path,
      query: { ...route.query },
      params: { ...route.params }
    }
  }
  
  /**
   * Restore preserved state for current route
   */
  function restoreState(): NavigationState | null {
    if (currentRouteName.value) {
      const state = getPreservedState(currentRouteName.value)
      if (state) {
        // Restore scroll position
        if (state.scrollPosition !== undefined) {
          setTimeout(() => {
            window.scrollTo({
              top: state.scrollPosition,
              behavior: 'smooth'
            })
          }, 100)
        }
        return state
      }
    }
    return null
  }
  
  /**
   * Clear preserved state for current or all routes
   */
  function clearState(routeName?: string): void {
    clearPreservedState(routeName || currentRouteName.value)
  }
  
  /**
   * Check if a route exists
   */
  function routeExists(name: string): boolean {
    try {
      const resolved = router.resolve({ name })
      return resolved.name !== undefined
    } catch {
      return false
    }
  }
  
  /**
   * Generate URL for a route
   */
  function getRouteUrl(to: RouteLocationRaw): string {
    try {
      const resolved = router.resolve(to)
      return resolved.href
    } catch (error) {
      console.error('Failed to resolve route:', error)
      return '/'
    }
  }
  
  /**
   * Check if current route matches
   */
  function isCurrentRoute(name: string, params?: Record<string, any>): boolean {
    if (route.name !== name) return false
    
    if (params) {
      return Object.entries(params).every(([key, value]) => 
        route.params[key] === value
      )
    }
    
    return true
  }
  
  /**
   * Handle deep linking
   */
  function handleDeepLink(url: string): Promise<void> {
    try {
      // Validate the URL is safe (relative path only)
      if (!url.startsWith('/') || url.startsWith('//')) {
        throw new Error('Invalid deep link URL')
      }
      
      return navigateTo(url)
    } catch (error) {
      console.error('Deep link navigation failed:', error)
      return goHome({ replace: true })
    }
  }
  
  /**
   * Setup navigation event listeners
   */
  function setupNavigationListeners(): void {
    // Handle browser back/forward buttons
    const handlePopState = (event: PopStateEvent) => {
      // Custom handling for browser navigation
      console.log('Browser navigation detected:', event.state)
    }
    
    // Handle page visibility changes
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, preserve state
        if (currentRouteName.value) {
          const state = getCurrentState()
          preserveRouteState(currentRouteName.value, state)
        }
      }
    }
    
    window.addEventListener('popstate', handlePopState)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    // Cleanup on unmount
    onBeforeUnmount(() => {
      window.removeEventListener('popstate', handlePopState)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    })
  }
  
  /**
   * Preload a route component
   */
  async function preloadRoute(name: string): Promise<void> {
    try {
      const route = router.resolve({ name })
      if (route.matched.length > 0) {
        const component = route.matched[0].components?.default
        if (typeof component === 'function') {
          await component()
        }
      }
    } catch (error) {
      console.warn('Failed to preload route:', name, error)
    }
  }
  
  // Auto-setup listeners
  setupNavigationListeners()
  
  return {
    // State
    isNavigating: computed(() => isNavigating.value),
    navigationError: computed(() => navigationError.value),
    currentRouteName,
    canGoBack,
    canGoForward,
    
    // Navigation methods
    navigateTo,
    goBack,
    goForward,
    goHome,
    goToLogin,
    goToItinerary,
    refresh,
    
    // State management
    getCurrentState,
    restoreState,
    clearState,
    
    // Utilities
    routeExists,
    getRouteUrl,
    isCurrentRoute,
    handleDeepLink,
    preloadRoute,
    
    // Clear error
    clearNavigationError: () => { navigationError.value = null }
  }
}

/**
 * Composable for route-specific navigation guards
 */
export function useRouteGuard() {
  const router = useRouter()
  const route = useRoute()
  
  /**
   * Add a before leave guard to current route
   */
  function addBeforeLeaveGuard(
    guard: (to: any, from: any, next: any) => void
  ): () => void {
    const removeGuard = router.beforeEach((to, from, next) => {
      if (from.name === route.name) {
        guard(to, from, next)
      } else {
        next()
      }
    })
    
    return removeGuard
  }
  
  /**
   * Confirm navigation away from current route
   */
  function confirmNavigation(message: string = 'Are you sure you want to leave?'): () => void {
    return addBeforeLeaveGuard((to, from, next) => {
      if (window.confirm(message)) {
        next()
      } else {
        next(false)
      }
    })
  }
  
  return {
    addBeforeLeaveGuard,
    confirmNavigation
  }
}
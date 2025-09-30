import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, NavigationGuardNext, RouteRecordNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { CognitoAuthService } from '@/services/cognitoAuthService'

// Route-based code splitting with lazy loading
const InputPage = () => import('../views/InputPage.vue')
const ItineraryPage = () => import('../views/ItineraryPage.vue')
const LoginView = () => import('../views/LoginView.vue')
const AboutView = () => import('../views/AboutView.vue')

// Define route metadata interface
interface RouteMeta extends Record<PropertyKey, unknown> {
  requiresAuth?: boolean
  hideForAuthenticated?: boolean
  title?: string
  preserveState?: boolean
  allowDeepLink?: boolean
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  // Enable strict mode for better route matching
  strict: true,
  // Enable sensitive mode for case-sensitive routes
  sensitive: false,
  routes: [
    {
      path: '/',
      name: 'home',
      component: InputPage,
      meta: { 
        requiresAuth: true,
        title: 'MBTI Travel Planner - Home',
        preserveState: true,
        allowDeepLink: true
      }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { 
        requiresAuth: false, 
        hideForAuthenticated: true,
        title: 'Sign In - MBTI Travel Planner',
        preserveState: false,
        allowDeepLink: true
      }
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('../views/AuthCallbackView.vue'),
      meta: {
        requiresAuth: false,
        title: 'Authenticating...',
        preserveState: false,
        allowDeepLink: true
      }
    },
    {
      path: '/itinerary/:mbti',
      name: 'itinerary',
      component: ItineraryPage,
      props: (route) => ({
        mbti: route.params.mbti,
        // Pass query parameters as props for deep linking support
        ...route.query
      }),
      meta: { 
        requiresAuth: true,
        title: 'Your Itinerary - MBTI Travel Planner',
        preserveState: true,
        allowDeepLink: true
      },
      // Validate MBTI parameter
      beforeEnter: (to, from, next) => {
        const mbti = to.params.mbti as string
        const validMBTI = /^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$/i
        
        if (!mbti || !validMBTI.test(mbti)) {
          // Invalid MBTI, redirect to home with error
          next({ 
            name: 'home', 
            query: { error: 'invalid-mbti' }
          })
        } else {
          // Normalize MBTI to uppercase
          if (mbti !== mbti.toUpperCase()) {
            next({ 
              name: 'itinerary', 
              params: { mbti: mbti.toUpperCase() },
              query: to.query
            })
          } else {
            next()
          }
        }
      }
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { 
        requiresAuth: false,
        title: 'About - MBTI Travel Planner',
        preserveState: false,
        allowDeepLink: true
      }
    },
    {
      path: '/oauth-test.html',
      name: 'oauth-test',
      beforeEnter() {
        // Redirect to the actual static HTML file
        window.location.href = '/oauth-test.html'
      },
      meta: {
        requiresAuth: false,
        title: 'OAuth Test',
        preserveState: false,
        allowDeepLink: true
      }
    },
    {
      path: '/debug-auth.html',
      name: 'debug-auth',
      beforeEnter() {
        // Redirect to the actual static HTML file
        window.location.href = '/debug-auth.html'
      },
      meta: {
        requiresAuth: false,
        title: 'Auth Debug',
        preserveState: false,
        allowDeepLink: true
      }
    },
    // Catch-all route for 404 handling
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
      meta: {
        requiresAuth: false,
        title: 'Page Not Found - MBTI Travel Planner',
        preserveState: false,
        allowDeepLink: false
      }
    }
  ],
  // Scroll behavior for better UX
  scrollBehavior(to, from, savedPosition) {
    // If there's a saved position (back/forward navigation), use it
    if (savedPosition) {
      return savedPosition
    }
    
    // If navigating to a hash anchor, scroll to it
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth'
      }
    }
    
    // For new routes, scroll to top
    return { top: 0, behavior: 'smooth' }
  }
})

// State preservation utilities
const preservedState = new Map<string, any>()

function preserveRouteState(routeName: string, state: any): void {
  if (state && Object.keys(state).length > 0) {
    preservedState.set(routeName, { ...state, timestamp: Date.now() })
  }
}

function getPreservedState(routeName: string): any {
  const state = preservedState.get(routeName)
  if (state) {
    // Clean up old state (older than 1 hour)
    const oneHour = 60 * 60 * 1000
    if (Date.now() - state.timestamp > oneHour) {
      preservedState.delete(routeName)
      return null
    }
    return state
  }
  return null
}

function clearPreservedState(routeName?: string): void {
  if (routeName) {
    preservedState.delete(routeName)
  } else {
    preservedState.clear()
  }
}

// Enhanced authentication guard with state preservation
async function authGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const authStore = useAuthStore()
  
  try {
    // Skip authentication guard for static files and debug pages
    const staticPaths = ['/oauth-test.html', '/debug-auth.html', '/test-oauth.html']
    if (staticPaths.some(path => to.path.includes(path))) {
      console.log('Skipping auth guard for static file:', to.path)
      next()
      return
    }

    // Skip authentication guard for debug and test routes
    if (to.name === 'oauth-test' || to.name === 'debug-auth') {
      console.log('Skipping auth guard for debug route:', to.name)
      next()
      return
    }

    // Wait for auth store to initialize
    if (!authStore.isInitialized) {
      await authStore.initialize()
    }

    const toMeta = to.meta as RouteMeta
    const fromMeta = from.meta as RouteMeta
    const requiresAuth = toMeta.requiresAuth ?? false
    const hideForAuthenticated = toMeta.hideForAuthenticated ?? false
    const isAuthenticated = authStore.isAuthenticated

    // Preserve state from the current route if configured
    if (fromMeta.preserveState && from.name) {
      const currentState = getCurrentRouteState()
      if (currentState) {
        preserveRouteState(from.name.toString(), currentState)
      }
    }

    // If route requires authentication and user is not authenticated
    if (requiresAuth && !isAuthenticated) {
      // Check if this is an OAuth callback
      if (to.query.code) {
        console.log('OAuth callback detected, redirecting to auth callback handler')
        // This is an OAuth callback, redirect to auth callback handler
        next({ name: 'auth-callback', query: to.query, replace: true })
        return
      }
      
      // Validate current token before redirecting
      const isTokenValid = await authStore.validateCurrentToken()
      
      if (!isTokenValid) {
        // Store the intended destination for deep linking support
        const returnUrl = to.fullPath !== '/login' ? to.fullPath : '/'
        
        // Clear any preserved state for security
        clearPreservedState()
        
        // Redirect to internal login page
        next({
          name: 'login',
          query: { returnUrl: encodeURIComponent(returnUrl) },
          replace: true
        })
        return
      }
    }

    // If route should be hidden for authenticated users (like login page)
    if (hideForAuthenticated && isAuthenticated) {
      // Check if there's a return URL for deep linking
      const returnUrl = to.query.returnUrl as string
      if (returnUrl && isValidReturnUrl(returnUrl)) {
        try {
          const decodedUrl = decodeURIComponent(returnUrl)
          next({ path: decodedUrl, replace: true })
        } catch (error) {
          console.warn('Invalid return URL:', returnUrl)
          next({ name: 'home', replace: true })
        }
      } else {
        next({ name: 'home', replace: true })
      }
      return
    }

    // Validate deep linking permissions
    if (toMeta.allowDeepLink === false && !from.name) {
      // This route doesn't allow direct access, redirect to home
      next({ name: 'home', replace: true })
      return
    }

    // Allow navigation
    next()
  } catch (error) {
    console.error('Navigation guard error:', error)
    // On error, redirect to login or home based on auth requirement
    if (to.meta.requiresAuth) {
      next({ name: 'login', replace: true })
    } else {
      next({ name: 'home', replace: true })
    }
  }
}

// Utility functions
function getCurrentRouteState(): any {
  // This would be implemented to capture current component state
  // For now, return basic route information
  return {
    scrollPosition: window.scrollY,
    timestamp: Date.now()
  }
}

function isValidReturnUrl(url: string): boolean {
  try {
    const decodedUrl = decodeURIComponent(url)
    // Only allow relative URLs for security
    return decodedUrl.startsWith('/') && !decodedUrl.startsWith('//')
  } catch {
    return false
  }
}

// Global navigation guards
router.beforeEach(authGuard)

// After each navigation, update document title and handle state restoration
router.afterEach((to, from) => {
  const toMeta = to.meta as RouteMeta
  
  // Update document title for better SEO and UX
  if (toMeta.title) {
    document.title = toMeta.title
  }
  
  // Restore preserved state if available
  if (toMeta.preserveState && to.name) {
    const preservedRouteState = getPreservedState(to.name.toString())
    if (preservedRouteState) {
      // Restore scroll position after a short delay to ensure DOM is ready
      setTimeout(() => {
        if (preservedRouteState.scrollPosition) {
          window.scrollTo({
            top: preservedRouteState.scrollPosition,
            behavior: 'smooth'
          })
        }
      }, 100)
    }
  }
  
  // Analytics or tracking could be added here
  if (import.meta.env.PROD) {
    // Track page views in production
    console.log(`Navigation: ${from.path} -> ${to.path}`)
  }
})

// Enhanced error handling for navigation failures
router.onError((error, to, from) => {
  console.error('Router navigation error:', error)
  
  // Handle different types of navigation errors
  if (error.message.includes('auth') || error.message.includes('token')) {
    // Authentication error
    const authStore = useAuthStore()
    clearPreservedState() // Clear state for security
    authStore.redirectToLogin()
  } else if (error.message.includes('chunk')) {
    // Code splitting chunk load error - reload the page
    console.warn('Chunk load error, reloading page')
    window.location.reload()
  } else if (error.message.includes('network') || error.message.includes('fetch')) {
    // Network error during route loading
    console.warn('Network error during navigation, retrying...')
    // Could implement retry logic here
  } else {
    // Generic error - redirect to home
    console.warn('Unknown navigation error, redirecting to home')
    router.push({ name: 'home' }).catch(() => {
      // If even home navigation fails, reload
      window.location.href = '/'
    })
  }
})

// Handle browser back/forward navigation
router.beforeResolve((to, from, next) => {
  // This runs after all component guards and async route components are resolved
  // but before the navigation is confirmed
  
  // Handle any final validation or state preparation here
  next()
})

// Export router and utility functions for use in components
export default router

// Export utility functions for state management
export {
  preserveRouteState,
  getPreservedState,
  clearPreservedState
}

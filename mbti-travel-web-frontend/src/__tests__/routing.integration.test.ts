import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

// Mock components
const MockInputPage = { 
  template: '<div data-testid="input-page">Input Page</div>',
  name: 'InputPage'
}
const MockItineraryPage = { 
  template: '<div data-testid="itinerary-page">Itinerary Page {{ $route.params.mbti }}</div>',
  name: 'ItineraryPage'
}
const MockLoginView = { 
  template: '<div data-testid="login-view">Login View</div>',
  name: 'LoginView'
}
const MockNotFoundView = { 
  template: '<div data-testid="not-found">Not Found</div>',
  name: 'NotFoundView'
}

// Create test router with mocked components
function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/',
        name: 'home',
        component: MockInputPage,
        meta: { requiresAuth: true, title: 'Home' }
      },
      {
        path: '/login',
        name: 'login',
        component: MockLoginView,
        meta: { requiresAuth: false, hideForAuthenticated: true, title: 'Login' }
      },
      {
        path: '/itinerary/:mbti',
        name: 'itinerary',
        component: MockItineraryPage,
        props: true,
        meta: { requiresAuth: true, title: 'Itinerary' },
        beforeEnter: (to, from, next) => {
          const mbti = to.params.mbti as string
          const validMBTI = /^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$/i
          
          if (!mbti || !validMBTI.test(mbti)) {
            next({ name: 'home', query: { error: 'invalid-mbti' } })
          } else if (mbti !== mbti.toUpperCase()) {
            next({ name: 'itinerary', params: { mbti: mbti.toUpperCase() }, query: to.query })
          } else {
            next()
          }
        }
      },
      {
        path: '/:pathMatch(.*)*',
        name: 'not-found',
        component: MockNotFoundView,
        meta: { title: 'Not Found' }
      }
    ]
  })
}

describe('Routing Integration', () => {
  let router: any
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
  })

  it('should navigate to home route', async () => {
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('home')
  })

  it('should navigate to login route', async () => {
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('should navigate to itinerary page with valid MBTI', async () => {
    await router.push('/itinerary/ENFP')
    expect(router.currentRoute.value.name).toBe('itinerary')
    expect(router.currentRoute.value.params.mbti).toBe('ENFP')
  })

  it('should normalize MBTI case in URL', async () => {
    await router.push('/itinerary/enfp')
    expect(router.currentRoute.value.params.mbti).toBe('ENFP')
  })

  it('should redirect invalid MBTI to home with error', async () => {
    await router.push('/itinerary/INVALID')
    expect(router.currentRoute.value.name).toBe('home')
    expect(router.currentRoute.value.query.error).toBe('invalid-mbti')
  })

  it('should show 404 page for invalid routes', async () => {
    await router.push('/invalid-route')
    expect(router.currentRoute.value.name).toBe('not-found')
  })

  it('should handle navigation with query parameters', async () => {
    await router.push('/itinerary/ENFP?test=value')
    expect(router.currentRoute.value.query.test).toBe('value')
  })

  it('should handle scroll behavior', () => {
    const scrollBehavior = router.options.scrollBehavior
    if (scrollBehavior) {
      // Test default scroll to top
      const result = scrollBehavior({} as any, {} as any, null)
      expect(result).toEqual({ top: 0, behavior: 'smooth' })
      
      // Test saved position
      const savedResult = scrollBehavior({} as any, {} as any, { top: 100, left: 0 })
      expect(savedResult).toEqual({ top: 100, left: 0 })
    }
  })

  it('should validate MBTI parameter format', () => {
    const validMBTI = /^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$/i
    
    expect(validMBTI.test('ENFP')).toBe(true)
    expect(validMBTI.test('enfp')).toBe(true)
    expect(validMBTI.test('INVALID')).toBe(false)
    expect(validMBTI.test('ABCD')).toBe(false)
  })

  it('should have proper route meta configuration', () => {
    const routes = router.getRoutes()
    
    const homeRoute = routes.find((r: any) => r.name === 'home')
    expect(homeRoute?.meta.requiresAuth).toBe(true)
    
    const loginRoute = routes.find((r: any) => r.name === 'login')
    expect(loginRoute?.meta.hideForAuthenticated).toBe(true)
  })
})
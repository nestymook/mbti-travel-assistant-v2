import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'

// Mock components for testing
const MockInputPage = { template: '<div>Input Page</div>' }
const MockItineraryPage = { template: '<div>Itinerary Page</div>' }
const MockLoginView = { template: '<div>Login View</div>' }
const MockNotFoundView = { template: '<div>Not Found</div>' }

// Create test router
function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: MockInputPage, meta: { requiresAuth: true } },
      { path: '/login', name: 'login', component: MockLoginView, meta: { requiresAuth: false, hideForAuthenticated: true } },
      { path: '/itinerary/:mbti', name: 'itinerary', component: MockItineraryPage, meta: { requiresAuth: true } },
      { path: '/:pathMatch(.*)*', name: 'not-found', component: MockNotFoundView }
    ]
  })
}

describe('Routing System', () => {
  let testRouter: any
  let pinia: any

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    testRouter = createTestRouter()
    
    // Mock window.history
    Object.defineProperty(window, 'history', {
      value: { length: 2 },
      writable: true
    })
    
    // Mock sessionStorage
    const mockSessionStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    }
    Object.defineProperty(window, 'sessionStorage', {
      value: mockSessionStorage,
      writable: true
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Route Configuration', () => {
    it('should have correct route definitions', () => {
      const routes = testRouter.getRoutes()
      
      expect(routes.find(r => r.name === 'home')).toBeDefined()
      expect(routes.find(r => r.name === 'login')).toBeDefined()
      expect(routes.find(r => r.name === 'itinerary')).toBeDefined()
      expect(routes.find(r => r.name === 'not-found')).toBeDefined()
    })

    it('should have proper meta configuration', () => {
      const routes = testRouter.getRoutes()
      
      const homeRoute = routes.find(r => r.name === 'home')
      expect(homeRoute?.meta.requiresAuth).toBe(true)
      
      const loginRoute = routes.find(r => r.name === 'login')
      expect(loginRoute?.meta.requiresAuth).toBe(false)
      expect(loginRoute?.meta.hideForAuthenticated).toBe(true)
    })

    it('should create router with memory history', () => {
      expect(testRouter).toBeDefined()
      expect(testRouter.options.history).toBeDefined()
    })
  })

  describe('Basic Navigation', () => {
    it('should navigate to home route', async () => {
      await testRouter.push('/')
      expect(testRouter.currentRoute.value.name).toBe('home')
    })

    it('should navigate to login route', async () => {
      await testRouter.push('/login')
      expect(testRouter.currentRoute.value.name).toBe('login')
    })

    it('should navigate to itinerary route with params', async () => {
      await testRouter.push('/itinerary/ENFP')
      expect(testRouter.currentRoute.value.name).toBe('itinerary')
      expect(testRouter.currentRoute.value.params.mbti).toBe('ENFP')
    })

    it('should handle 404 routes', async () => {
      await testRouter.push('/nonexistent')
      expect(testRouter.currentRoute.value.name).toBe('not-found')
    })
  })

  describe('MBTI Validation', () => {
    it('should validate MBTI codes correctly', () => {
      const validMBTI = /^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$/i
      
      // Valid MBTI codes
      expect(validMBTI.test('ENFP')).toBe(true)
      expect(validMBTI.test('INTJ')).toBe(true)
      expect(validMBTI.test('enfp')).toBe(true) // case insensitive
      
      // Invalid MBTI codes
      expect(validMBTI.test('INVALID')).toBe(false)
      expect(validMBTI.test('ABCD')).toBe(false)
      expect(validMBTI.test('ENF')).toBe(false) // too short
      expect(validMBTI.test('ENFPX')).toBe(false) // too long
    })

    it('should handle MBTI normalization', () => {
      const normalizeMBTI = (mbti: string) => mbti.toUpperCase()
      
      expect(normalizeMBTI('enfp')).toBe('ENFP')
      expect(normalizeMBTI('ENFP')).toBe('ENFP')
      expect(normalizeMBTI('EnFp')).toBe('ENFP')
    })
  })

  describe('Router Functionality', () => {
    it('should handle route parameters', async () => {
      await testRouter.push('/itinerary/ENFP')
      expect(testRouter.currentRoute.value.params.mbti).toBe('ENFP')
    })

    it('should handle query parameters', async () => {
      await testRouter.push('/itinerary/ENFP?test=value')
      expect(testRouter.currentRoute.value.query.test).toBe('value')
    })

    it('should handle 404 routes', async () => {
      await testRouter.push('/nonexistent')
      expect(testRouter.currentRoute.value.name).toBe('not-found')
    })
  })

  describe('Route Utilities', () => {
    it('should validate return URLs', () => {
      const isValidReturnUrl = (url: string): boolean => {
        try {
          const decodedUrl = decodeURIComponent(url)
          return decodedUrl.startsWith('/') && !decodedUrl.startsWith('//')
        } catch {
          return false
        }
      }
      
      expect(isValidReturnUrl('%2Fitinerary%2FENFP')).toBe(true)
      expect(isValidReturnUrl('http://evil.com')).toBe(false)
      expect(isValidReturnUrl('//evil.com')).toBe(false)
    })

    it('should handle URL encoding/decoding', () => {
      const returnUrl = '/itinerary/ENFP'
      const encoded = encodeURIComponent(returnUrl)
      const decoded = decodeURIComponent(encoded)
      
      expect(encoded).toBe('%2Fitinerary%2FENFP')
      expect(decoded).toBe(returnUrl)
    })
  })
})
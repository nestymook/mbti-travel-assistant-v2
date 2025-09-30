import type { RouteRecordNormalized } from 'vue-router'
import router from '@/router'

interface PreloadOptions {
  priority?: 'high' | 'low'
  delay?: number
  onIdle?: boolean
}

interface PreloadedRoute {
  name: string
  component: any
  timestamp: number
}

class RoutePreloader {
  private preloadedRoutes = new Map<string, PreloadedRoute>()
  private preloadQueue = new Set<string>()
  private isPreloading = false
  
  /**
   * Preload a route component
   */
  async preloadRoute(routeName: string, options: PreloadOptions = {}): Promise<void> {
    // Skip if already preloaded or in queue
    if (this.preloadedRoutes.has(routeName) || this.preloadQueue.has(routeName)) {
      return
    }
    
    this.preloadQueue.add(routeName)
    
    try {
      // Add delay if specified
      if (options.delay) {
        await new Promise(resolve => setTimeout(resolve, options.delay))
      }
      
      // Use requestIdleCallback if onIdle is true and available
      if (options.onIdle && 'requestIdleCallback' in window) {
        await new Promise(resolve => {
          window.requestIdleCallback(() => resolve(undefined))
        })
      }
      
      const route = router.resolve({ name: routeName })
      if (route.matched.length === 0) {
        console.warn(`Route "${routeName}" not found for preloading`)
        return
      }
      
      const routeRecord = route.matched[0]
      const component = routeRecord.components?.default
      
      if (typeof component === 'function') {
        this.isPreloading = true
        const loadedComponent = await component()
        
        this.preloadedRoutes.set(routeName, {
          name: routeName,
          component: loadedComponent,
          timestamp: Date.now()
        })
        
        console.log(`Route "${routeName}" preloaded successfully`)
      }
    } catch (error) {
      console.error(`Failed to preload route "${routeName}":`, error)
    } finally {
      this.preloadQueue.delete(routeName)
      this.isPreloading = false
    }
  }
  
  /**
   * Preload multiple routes
   */
  async preloadRoutes(routeNames: string[], options: PreloadOptions = {}): Promise<void> {
    const promises = routeNames.map(name => this.preloadRoute(name, options))
    await Promise.allSettled(promises)
  }
  
  /**
   * Preload routes based on user behavior patterns
   */
  preloadLikelyRoutes(): void {
    // Common navigation patterns for MBTI Travel Planner
    const currentRoute = router.currentRoute.value
    
    if (currentRoute.name === 'home') {
      // From home, users likely go to itinerary or about
      this.preloadRoute('about', { priority: 'low', delay: 1000, onIdle: true })
    } else if (currentRoute.name === 'login') {
      // From login, users go to home
      this.preloadRoute('home', { priority: 'high', delay: 500 })
    } else if (currentRoute.name === 'itinerary') {
      // From itinerary, users might go back to home or to about
      this.preloadRoute('home', { priority: 'low', delay: 2000, onIdle: true })
    }
  }
  
  /**
   * Preload on hover (for navigation links)
   */
  preloadOnHover(routeName: string): void {
    this.preloadRoute(routeName, { priority: 'high', delay: 100 })
  }
  
  /**
   * Preload on intersection (when element comes into view)
   */
  preloadOnIntersection(routeName: string, element: Element): void {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              this.preloadRoute(routeName, { priority: 'low', onIdle: true })
              observer.unobserve(element)
            }
          })
        },
        { threshold: 0.1 }
      )
      
      observer.observe(element)
    }
  }
  
  /**
   * Clear old preloaded routes
   */
  clearOldPreloads(maxAge: number = 5 * 60 * 1000): void {
    const now = Date.now()
    
    for (const [routeName, preloaded] of this.preloadedRoutes.entries()) {
      if (now - preloaded.timestamp > maxAge) {
        this.preloadedRoutes.delete(routeName)
        console.log(`Cleared old preload for route "${routeName}"`)
      }
    }
  }
  
  /**
   * Get preload statistics
   */
  getStats(): {
    preloadedCount: number
    queueSize: number
    isPreloading: boolean
    preloadedRoutes: string[]
  } {
    return {
      preloadedCount: this.preloadedRoutes.size,
      queueSize: this.preloadQueue.size,
      isPreloading: this.isPreloading,
      preloadedRoutes: Array.from(this.preloadedRoutes.keys())
    }
  }
  
  /**
   * Clear all preloaded routes
   */
  clearAll(): void {
    this.preloadedRoutes.clear()
    this.preloadQueue.clear()
    console.log('All preloaded routes cleared')
  }
}

// Create singleton instance
const routePreloader = new RoutePreloader()

// Auto-cleanup old preloads every 5 minutes
setInterval(() => {
  routePreloader.clearOldPreloads()
}, 5 * 60 * 1000)

export default routePreloader

/**
 * Vue directive for preloading routes on hover
 */
export const vPreloadRoute = {
  mounted(el: HTMLElement, binding: { value: string }) {
    const routeName = binding.value
    
    const handleMouseEnter = () => {
      routePreloader.preloadOnHover(routeName)
    }
    
    el.addEventListener('mouseenter', handleMouseEnter, { once: true })
    
    // Store cleanup function
    ;(el as any)._preloadCleanup = () => {
      el.removeEventListener('mouseenter', handleMouseEnter)
    }
  },
  
  unmounted(el: HTMLElement) {
    if ((el as any)._preloadCleanup) {
      ;(el as any)._preloadCleanup()
    }
  }
}

/**
 * Vue directive for preloading routes on intersection
 */
export const vPreloadOnVisible = {
  mounted(el: HTMLElement, binding: { value: string }) {
    const routeName = binding.value
    routePreloader.preloadOnIntersection(routeName, el)
  }
}

/**
 * Composable for route preloading
 */
export function useRoutePreloader() {
  return {
    preloadRoute: (routeName: string, options?: PreloadOptions) => 
      routePreloader.preloadRoute(routeName, options),
    preloadRoutes: (routeNames: string[], options?: PreloadOptions) => 
      routePreloader.preloadRoutes(routeNames, options),
    preloadLikelyRoutes: () => routePreloader.preloadLikelyRoutes(),
    preloadOnHover: (routeName: string) => routePreloader.preloadOnHover(routeName),
    getStats: () => routePreloader.getStats(),
    clearAll: () => routePreloader.clearAll()
  }
}
/**
 * Performance optimization utilities
 * Provides debouncing, memoization, and virtual scrolling capabilities
 */

import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'

/**
 * Debounce function to limit the rate of function calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

/**
 * Throttle function to limit function calls to once per interval
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Memoization cache for expensive computations
 */
class MemoCache<K, V> {
  private cache = new Map<string, { value: V; timestamp: number }>()
  private maxSize: number
  private ttl: number

  constructor(maxSize = 100, ttl = 5 * 60 * 1000) { // 5 minutes default TTL
    this.maxSize = maxSize
    this.ttl = ttl
  }

  private getKey(key: K): string {
    return typeof key === 'string' ? key : JSON.stringify(key)
  }

  get(key: K): V | undefined {
    const keyStr = this.getKey(key)
    const cached = this.cache.get(keyStr)
    
    if (!cached) return undefined
    
    // Check if cache entry has expired
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(keyStr)
      return undefined
    }
    
    return cached.value
  }

  set(key: K, value: V): void {
    const keyStr = this.getKey(key)
    
    // Remove oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      this.cache.delete(oldestKey)
    }
    
    this.cache.set(keyStr, {
      value,
      timestamp: Date.now()
    })
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }
}

/**
 * Memoize expensive function calls
 */
export function memoize<T extends (...args: any[]) => any>(
  func: T,
  maxSize = 100,
  ttl = 5 * 60 * 1000
): T {
  const cache = new MemoCache<Parameters<T>, ReturnType<T>>(maxSize, ttl)
  
  return ((...args: Parameters<T>) => {
    const cached = cache.get(args)
    if (cached !== undefined) {
      return cached
    }
    
    const result = func(...args)
    cache.set(args, result)
    return result
  }) as T
}

/**
 * Composable for debounced reactive values
 */
export function useDebouncedRef<T>(value: T, delay: number): Ref<T> {
  const debouncedValue = ref(value) as Ref<T>
  
  const updateValue = debounce((newValue: T) => {
    debouncedValue.value = newValue
  }, delay)
  
  watch(() => value, updateValue, { immediate: true })
  
  return debouncedValue
}

/**
 * Composable for memoized computed properties
 */
export function useMemoizedComputed<T>(
  getter: () => T,
  dependencies: Ref[],
  maxSize = 50,
  ttl = 2 * 60 * 1000
): ComputedRef<T> {
  const cache = new MemoCache<string, T>(maxSize, ttl)
  
  return computed(() => {
    // Create cache key from dependency values
    const key = dependencies.map(dep => dep.value).join('|')
    
    const cached = cache.get(key)
    if (cached !== undefined) {
      return cached
    }
    
    const result = getter()
    cache.set(key, result)
    return result
  })
}

/**
 * Virtual scrolling implementation for large lists
 */
export interface VirtualScrollOptions {
  itemHeight: number
  containerHeight: number
  overscan?: number
  buffer?: number
}

export interface VirtualScrollItem {
  index: number
  top: number
  height: number
}

export function useVirtualScroll<T>(
  items: Ref<T[]>,
  options: VirtualScrollOptions
) {
  const scrollTop = ref(0)
  const { itemHeight, containerHeight, overscan = 5, buffer = 10 } = options
  
  const visibleRange = computed(() => {
    const start = Math.floor(scrollTop.value / itemHeight)
    const end = Math.min(
      start + Math.ceil(containerHeight / itemHeight),
      items.value.length
    )
    
    return {
      start: Math.max(0, start - overscan),
      end: Math.min(items.value.length, end + overscan)
    }
  })
  
  const visibleItems = computed(() => {
    const { start, end } = visibleRange.value
    return items.value.slice(start, end).map((item, index) => ({
      item,
      index: start + index,
      top: (start + index) * itemHeight,
      height: itemHeight
    }))
  })
  
  const totalHeight = computed(() => items.value.length * itemHeight)
  
  const offsetY = computed(() => visibleRange.value.start * itemHeight)
  
  const handleScroll = throttle((event: Event) => {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
  }, 16) // ~60fps
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    scrollTop
  }
}

/**
 * Intersection Observer for lazy loading
 */
export function useIntersectionObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
) {
  const observer = ref<IntersectionObserver | null>(null)
  const isSupported = 'IntersectionObserver' in window
  
  const observe = (element: Element) => {
    if (!isSupported || !element) return
    
    if (!observer.value) {
      observer.value = new IntersectionObserver(callback, {
        rootMargin: '50px',
        threshold: 0.1,
        ...options
      })
    }
    
    observer.value.observe(element)
  }
  
  const unobserve = (element: Element) => {
    if (observer.value && element) {
      observer.value.unobserve(element)
    }
  }
  
  const disconnect = () => {
    if (observer.value) {
      observer.value.disconnect()
      observer.value = null
    }
  }
  
  return {
    isSupported,
    observe,
    unobserve,
    disconnect
  }
}

/**
 * Lazy loading composable for images and components
 */
export function useLazyLoading() {
  const loadedItems = ref(new Set<string>())
  
  const { observe, unobserve, disconnect } = useIntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('data-lazy-id')
          if (id) {
            loadedItems.value.add(id)
            unobserve(entry.target)
          }
        }
      })
    }
  )
  
  const isLoaded = (id: string) => loadedItems.value.has(id)
  
  const markAsLoaded = (id: string) => {
    loadedItems.value.add(id)
  }
  
  return {
    observe,
    unobserve,
    disconnect,
    isLoaded,
    markAsLoaded
  }
}

/**
 * Performance monitoring utilities
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics = new Map<string, number[]>()
  
  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }
  
  startTiming(label: string): () => void {
    const start = performance.now()
    
    return () => {
      const duration = performance.now() - start
      this.recordMetric(label, duration)
    }
  }
  
  recordMetric(label: string, value: number): void {
    if (!this.metrics.has(label)) {
      this.metrics.set(label, [])
    }
    
    const values = this.metrics.get(label)!
    values.push(value)
    
    // Keep only last 100 measurements
    if (values.length > 100) {
      values.shift()
    }
  }
  
  getMetrics(label: string): { avg: number; min: number; max: number; count: number } | null {
    const values = this.metrics.get(label)
    if (!values || values.length === 0) return null
    
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length
    const min = Math.min(...values)
    const max = Math.max(...values)
    
    return { avg, min, max, count: values.length }
  }
  
  getAllMetrics(): Record<string, ReturnType<PerformanceMonitor['getMetrics']>> {
    const result: Record<string, ReturnType<PerformanceMonitor['getMetrics']>> = {}
    
    for (const [label] of this.metrics) {
      result[label] = this.getMetrics(label)
    }
    
    return result
  }
  
  clearMetrics(label?: string): void {
    if (label) {
      this.metrics.delete(label)
    } else {
      this.metrics.clear()
    }
  }
}

/**
 * Bundle size optimization utilities
 */
export const bundleOptimization = {
  /**
   * Dynamic import with error handling
   */
  async dynamicImport<T>(importFn: () => Promise<T>): Promise<T | null> {
    try {
      return await importFn()
    } catch (error) {
      console.error('Dynamic import failed:', error)
      return null
    }
  },
  
  /**
   * Preload critical resources
   */
  preloadResource(href: string, as: string): void {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = href
    link.as = as
    document.head.appendChild(link)
  },
  
  /**
   * Prefetch non-critical resources
   */
  prefetchResource(href: string): void {
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = href
    document.head.appendChild(link)
  }
}

/**
 * Memory management utilities
 */
export const memoryManagement = {
  /**
   * Cleanup function registry
   */
  cleanupFunctions: new Set<() => void>(),
  
  /**
   * Register cleanup function
   */
  registerCleanup(fn: () => void): void {
    this.cleanupFunctions.add(fn)
  },
  
  /**
   * Execute all cleanup functions
   */
  cleanup(): void {
    this.cleanupFunctions.forEach(fn => {
      try {
        fn()
      } catch (error) {
        console.error('Cleanup function failed:', error)
      }
    })
    this.cleanupFunctions.clear()
  },
  
  /**
   * Monitor memory usage (if available)
   */
  getMemoryInfo(): any {
    return (performance as any).memory || null
  }
}

// Export performance monitor instance
export const performanceMonitor = PerformanceMonitor.getInstance()
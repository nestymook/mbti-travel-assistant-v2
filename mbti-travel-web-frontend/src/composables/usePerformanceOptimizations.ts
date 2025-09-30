/**
 * Performance optimizations composable
 * Provides reactive performance monitoring and optimization utilities
 */

import { ref, computed, onMounted, onUnmounted, watch, type Ref } from 'vue'
import { 
  debounce, 
  throttle, 
  memoize, 
  useDebouncedRef, 
  useMemoizedComputed,
  performanceMonitor,
  memoryManagement,
  bundleOptimization
} from '@/utils/performance'

/**
 * Performance monitoring composable
 */
export function usePerformanceMonitoring(componentName: string) {
  const metrics = ref<Record<string, any>>({})
  const isMonitoring = ref(false)
  
  const startMonitoring = () => {
    isMonitoring.value = true
    performanceMonitor.clearMetrics(componentName)
  }
  
  const stopMonitoring = () => {
    isMonitoring.value = false
    metrics.value = performanceMonitor.getAllMetrics()
  }
  
  const recordMetric = (name: string, value: number) => {
    if (isMonitoring.value) {
      performanceMonitor.recordMetric(`${componentName}-${name}`, value)
    }
  }
  
  const timeOperation = (operationName: string) => {
    if (!isMonitoring.value) return () => {}
    return performanceMonitor.startTiming(`${componentName}-${operationName}`)
  }
  
  onMounted(() => {
    if (import.meta.env.DEV) {
      startMonitoring()
    }
  })
  
  onUnmounted(() => {
    stopMonitoring()
  })
  
  return {
    metrics: computed(() => metrics.value),
    isMonitoring: computed(() => isMonitoring.value),
    startMonitoring,
    stopMonitoring,
    recordMetric,
    timeOperation
  }
}

/**
 * Debounced input composable
 */
export function useDebouncedInput<T>(
  initialValue: T,
  delay: number = 300,
  options: {
    immediate?: boolean
    maxWait?: number
  } = {}
) {
  const inputValue = ref(initialValue) as Ref<T>
  const debouncedValue = ref(initialValue) as Ref<T>
  const isDebouncing = ref(false)
  
  let timeoutId: ReturnType<typeof setTimeout>
  let maxTimeoutId: ReturnType<typeof setTimeout>
  
  const updateDebouncedValue = (value: T) => {
    debouncedValue.value = value
    isDebouncing.value = false
  }
  
  const debouncedUpdate = debounce(updateDebouncedValue, delay)
  
  watch(inputValue, (newValue) => {
    isDebouncing.value = true
    
    // Clear existing timeouts
    clearTimeout(timeoutId)
    clearTimeout(maxTimeoutId)
    
    // Set up debounced update
    timeoutId = setTimeout(() => debouncedUpdate(newValue), delay)
    
    // Set up max wait timeout if specified
    if (options.maxWait) {
      maxTimeoutId = setTimeout(() => {
        clearTimeout(timeoutId)
        updateDebouncedValue(newValue)
      }, options.maxWait)
    }
  }, { immediate: options.immediate })
  
  onUnmounted(() => {
    clearTimeout(timeoutId)
    clearTimeout(maxTimeoutId)
  })
  
  return {
    inputValue,
    debouncedValue: computed(() => debouncedValue.value),
    isDebouncing: computed(() => isDebouncing.value),
    flush: () => {
      clearTimeout(timeoutId)
      clearTimeout(maxTimeoutId)
      updateDebouncedValue(inputValue.value)
    }
  }
}

/**
 * Throttled scroll composable
 */
export function useThrottledScroll(
  callback: (event: Event) => void,
  delay: number = 16 // ~60fps
) {
  const isScrolling = ref(false)
  const scrollPosition = ref({ x: 0, y: 0 })
  
  const throttledCallback = throttle((event: Event) => {
    const target = event.target as HTMLElement
    scrollPosition.value = {
      x: target.scrollLeft,
      y: target.scrollTop
    }
    callback(event)
  }, delay)
  
  const handleScroll = (event: Event) => {
    if (!isScrolling.value) {
      isScrolling.value = true
      requestAnimationFrame(() => {
        isScrolling.value = false
      })
    }
    throttledCallback(event)
  }
  
  return {
    handleScroll,
    isScrolling: computed(() => isScrolling.value),
    scrollPosition: computed(() => scrollPosition.value)
  }
}

/**
 * Memoized computation composable
 */
export function useMemoizedComputation<T, K>(
  computeFn: (key: K) => T,
  dependencies: Ref[],
  options: {
    maxSize?: number
    ttl?: number
  } = {}
) {
  const { maxSize = 50, ttl = 5 * 60 * 1000 } = options
  
  const memoizedFn = memoize(computeFn, maxSize, ttl)
  
  const compute = (key: K): T => {
    return memoizedFn(key)
  }
  
  // Clear cache when dependencies change
  watch(dependencies, () => {
    // Note: We can't directly clear the memoized function's cache
    // This would require extending the memoize utility
  }, { deep: true })
  
  return {
    compute
  }
}

/**
 * Lazy loading composable
 */
export function useLazyLoading<T>(
  loader: () => Promise<T>,
  options: {
    immediate?: boolean
    retries?: number
    retryDelay?: number
  } = {}
) {
  const { immediate = false, retries = 3, retryDelay = 1000 } = options
  
  const data = ref<T | null>(null)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  const retryCount = ref(0)
  
  const load = async (): Promise<T | null> => {
    if (isLoading.value) return data.value
    
    isLoading.value = true
    error.value = null
    
    try {
      const result = await loader()
      data.value = result
      retryCount.value = 0
      return result
    } catch (err) {
      error.value = err as Error
      
      // Retry logic
      if (retryCount.value < retries) {
        retryCount.value++
        await new Promise(resolve => setTimeout(resolve, retryDelay * retryCount.value))
        return load()
      }
      
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  const reload = () => {
    data.value = null
    error.value = null
    retryCount.value = 0
    return load()
  }
  
  if (immediate) {
    onMounted(load)
  }
  
  return {
    data: computed(() => data.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    retryCount: computed(() => retryCount.value),
    load,
    reload
  }
}

/**
 * Bundle optimization composable
 */
export function useBundleOptimization() {
  const loadedChunks = ref(new Set<string>())
  const loadingChunks = ref(new Set<string>())
  
  const preloadChunk = async (chunkName: string, importFn: () => Promise<any>) => {
    if (loadedChunks.value.has(chunkName) || loadingChunks.value.has(chunkName)) {
      return
    }
    
    loadingChunks.value.add(chunkName)
    
    try {
      await bundleOptimization.dynamicImport(importFn)
      loadedChunks.value.add(chunkName)
    } catch (error) {
      console.warn(`Failed to preload chunk ${chunkName}:`, error)
    } finally {
      loadingChunks.value.delete(chunkName)
    }
  }
  
  const preloadResource = (href: string, as: string) => {
    bundleOptimization.preloadResource(href, as)
  }
  
  const prefetchResource = (href: string) => {
    bundleOptimization.prefetchResource(href)
  }
  
  return {
    loadedChunks: computed(() => Array.from(loadedChunks.value)),
    loadingChunks: computed(() => Array.from(loadingChunks.value)),
    preloadChunk,
    preloadResource,
    prefetchResource
  }
}

/**
 * Memory management composable
 */
export function useMemoryManagement() {
  const cleanupFunctions = ref<(() => void)[]>([])
  
  const registerCleanup = (fn: () => void) => {
    cleanupFunctions.value.push(fn)
    memoryManagement.registerCleanup(fn)
  }
  
  const cleanup = () => {
    cleanupFunctions.value.forEach(fn => {
      try {
        fn()
      } catch (error) {
        console.error('Cleanup function failed:', error)
      }
    })
    cleanupFunctions.value = []
  }
  
  const getMemoryInfo = () => {
    return memoryManagement.getMemoryInfo()
  }
  
  onUnmounted(() => {
    cleanup()
  })
  
  return {
    registerCleanup,
    cleanup,
    getMemoryInfo,
    cleanupCount: computed(() => cleanupFunctions.value.length)
  }
}

/**
 * Performance optimization preset for MBTI components
 */
export function useMBTIPerformanceOptimizations(componentName: string) {
  const { recordMetric, timeOperation } = usePerformanceMonitoring(componentName)
  const { registerCleanup } = useMemoryManagement()
  const { preloadChunk } = useBundleOptimization()
  
  // Debounced theme application
  const { inputValue: themeInput, debouncedValue: debouncedTheme } = useDebouncedInput('', 200)
  
  // Memoized personality calculations
  const personalityCache = new Map<string, any>()
  
  const memoizedPersonalityCalculation = memoize((personality: string, data: any) => {
    const endTiming = timeOperation('personality-calculation')
    
    try {
      // Simulate expensive personality-based calculations
      const result = {
        category: getPersonalityCategory(personality),
        theme: getPersonalityTheme(personality),
        features: getPersonalityFeatures(personality, data)
      }
      
      recordMetric('personality-calculation-success', 1)
      return result
    } catch (error) {
      recordMetric('personality-calculation-error', 1)
      throw error
    } finally {
      endTiming()
    }
  }, 20, 10 * 60 * 1000) // Cache for 10 minutes
  
  // Preload personality-specific chunks
  const preloadPersonalityChunks = async (personality: string) => {
    const category = getPersonalityCategory(personality)
    const chunkName = `personality-${category}`
    
    await preloadChunk(chunkName, () => 
      import(`@/components/itinerary/layouts/${personality}Layout.vue`)
    )
  }
  
  // Helper functions
  function getPersonalityCategory(personality: string): string {
    const categories = {
      structured: ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'],
      flexible: ['INTP', 'ISTP', 'ESTP'],
      colorful: ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESFP'],
      feeling: ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ']
    }
    
    for (const [category, personalities] of Object.entries(categories)) {
      if (personalities.includes(personality)) {
        return category
      }
    }
    return 'default'
  }
  
  function getPersonalityTheme(personality: string): any {
    // This would integrate with the theme service
    return { personality, theme: 'default' }
  }
  
  function getPersonalityFeatures(personality: string, data: any): any {
    // This would calculate personality-specific features
    return { personality, features: [] }
  }
  
  // Cleanup registration
  registerCleanup(() => {
    personalityCache.clear()
  })
  
  return {
    // Theme optimization
    themeInput,
    debouncedTheme,
    
    // Personality calculations
    memoizedPersonalityCalculation,
    preloadPersonalityChunks,
    
    // Performance monitoring
    recordMetric,
    timeOperation
  }
}

/**
 * Component-specific performance optimizations
 */
export function useComponentPerformanceOptimizations(componentName: string) {
  const renderCount = ref(0)
  const lastRenderTime = ref(0)
  const averageRenderTime = ref(0)
  
  const { recordMetric, timeOperation } = usePerformanceMonitoring(componentName)
  
  // Track render performance
  const trackRender = () => {
    const endTiming = timeOperation('render')
    renderCount.value++
    
    return () => {
      const renderTime = performance.now() - lastRenderTime.value
      lastRenderTime.value = performance.now()
      
      // Calculate rolling average
      averageRenderTime.value = (averageRenderTime.value * (renderCount.value - 1) + renderTime) / renderCount.value
      
      recordMetric('render-time', renderTime)
      recordMetric('render-count', 1)
      
      endTiming()
    }
  }
  
  // Track component lifecycle
  onMounted(() => {
    recordMetric('mount', 1)
    lastRenderTime.value = performance.now()
  })
  
  onUnmounted(() => {
    recordMetric('unmount', 1)
  })
  
  return {
    renderCount: computed(() => renderCount.value),
    averageRenderTime: computed(() => averageRenderTime.value),
    trackRender
  }
}
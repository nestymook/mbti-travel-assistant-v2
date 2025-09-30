/**
 * Performance optimizations test suite
 * Tests debouncing, memoization, virtual scrolling, and lazy loading
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { 
  debounce, 
  throttle, 
  memoize, 
  useVirtualScroll,
  performanceMonitor,
  bundleOptimization
} from '@/utils/performance'
import { 
  usePerformanceMonitoring,
  useDebouncedInput,
  useThrottledScroll,
  useMemoizedComputation,
  useLazyLoading
} from '@/composables/usePerformanceOptimizations'

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByType: vi.fn(() => []),
    getEntriesByName: vi.fn(() => [])
  }
})

describe('Performance Optimizations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Debounce Utility', () => {
    it('should debounce function calls', async () => {
      const mockFn = vi.fn()
      const debouncedFn = debounce(mockFn, 100)

      // Call multiple times rapidly
      debouncedFn('call1')
      debouncedFn('call2')
      debouncedFn('call3')

      // Should not have been called yet
      expect(mockFn).not.toHaveBeenCalled()

      // Fast-forward time
      vi.advanceTimersByTime(100)

      // Should have been called once with the last argument
      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('call3')
    })

    it('should handle rapid successive calls correctly', async () => {
      const mockFn = vi.fn()
      const debouncedFn = debounce(mockFn, 50)

      debouncedFn('first')
      vi.advanceTimersByTime(25)
      debouncedFn('second')
      vi.advanceTimersByTime(25)
      debouncedFn('third')

      // Should not have been called yet
      expect(mockFn).not.toHaveBeenCalled()

      vi.advanceTimersByTime(50)

      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('third')
    })
  })

  describe('Throttle Utility', () => {
    it('should throttle function calls', async () => {
      const mockFn = vi.fn()
      const throttledFn = throttle(mockFn, 100)

      // First call should execute immediately
      throttledFn('call1')
      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('call1')

      // Subsequent calls within throttle period should be ignored
      throttledFn('call2')
      throttledFn('call3')
      expect(mockFn).toHaveBeenCalledTimes(1)

      // After throttle period, next call should execute
      vi.advanceTimersByTime(100)
      throttledFn('call4')
      expect(mockFn).toHaveBeenCalledTimes(2)
      expect(mockFn).toHaveBeenCalledWith('call4')
    })
  })

  describe('Memoization Utility', () => {
    it('should cache function results', () => {
      const expensiveFn = vi.fn((x: number) => x * 2)
      const memoizedFn = memoize(expensiveFn)

      // First call
      const result1 = memoizedFn(5)
      expect(result1).toBe(10)
      expect(expensiveFn).toHaveBeenCalledTimes(1)

      // Second call with same argument should use cache
      const result2 = memoizedFn(5)
      expect(result2).toBe(10)
      expect(expensiveFn).toHaveBeenCalledTimes(1)

      // Call with different argument should execute function
      const result3 = memoizedFn(10)
      expect(result3).toBe(20)
      expect(expensiveFn).toHaveBeenCalledTimes(2)
    })

    it('should respect cache size limits', () => {
      const expensiveFn = vi.fn((x: number) => x * 2)
      const memoizedFn = memoize(expensiveFn, 2) // Max 2 items

      // Fill cache
      memoizedFn(1)
      memoizedFn(2)
      expect(expensiveFn).toHaveBeenCalledTimes(2)

      // Add third item (should evict first)
      memoizedFn(3)
      expect(expensiveFn).toHaveBeenCalledTimes(3)

      // First item should no longer be cached
      memoizedFn(1)
      expect(expensiveFn).toHaveBeenCalledTimes(4)

      // Second and third items should still be cached
      memoizedFn(2)
      memoizedFn(3)
      expect(expensiveFn).toHaveBeenCalledTimes(4)
    })
  })

  describe('Performance Monitor', () => {
    it('should record metrics correctly', () => {
      const monitor = performanceMonitor

      monitor.recordMetric('test-metric', 100)
      monitor.recordMetric('test-metric', 200)
      monitor.recordMetric('test-metric', 150)

      const metrics = monitor.getMetrics('test-metric')
      expect(metrics).toBeDefined()
      expect(metrics?.count).toBe(3)
      expect(metrics?.avg).toBe(150)
      expect(metrics?.min).toBe(100)
      expect(metrics?.max).toBe(200)
    })

    it('should handle timing operations', () => {
      const monitor = performanceMonitor
      const endTiming = monitor.startTiming('test-operation')

      // Simulate some work
      vi.advanceTimersByTime(50)

      endTiming()

      const metrics = monitor.getMetrics('test-operation')
      expect(metrics).toBeDefined()
      expect(metrics?.count).toBe(1)
    })
  })

  describe('Bundle Optimization', () => {
    it('should handle dynamic imports gracefully', async () => {
      const mockImport = vi.fn().mockResolvedValue({ default: 'component' })
      
      const result = await bundleOptimization.dynamicImport(mockImport)
      expect(result).toBe('component')
      expect(mockImport).toHaveBeenCalledTimes(1)
    })

    it('should handle failed dynamic imports', async () => {
      const mockImport = vi.fn().mockRejectedValue(new Error('Import failed'))
      
      const result = await bundleOptimization.dynamicImport(mockImport)
      expect(result).toBeNull()
      expect(mockImport).toHaveBeenCalledTimes(1)
    })

    it('should create preload links', () => {
      const originalCreateElement = document.createElement
      const mockLink = {
        rel: '',
        href: '',
        as: '',
        setAttribute: vi.fn(),
        getAttribute: vi.fn()
      }
      
      document.createElement = vi.fn().mockReturnValue(mockLink)
      document.head.appendChild = vi.fn()

      bundleOptimization.preloadResource('/test.css', 'style')

      expect(document.createElement).toHaveBeenCalledWith('link')
      expect(mockLink.rel).toBe('preload')
      expect(mockLink.href).toBe('/test.css')
      expect(mockLink.as).toBe('style')
      expect(document.head.appendChild).toHaveBeenCalledWith(mockLink)

      // Restore original
      document.createElement = originalCreateElement
    })
  })

  describe('Performance Composables', () => {
    describe('usePerformanceMonitoring', () => {
      it('should initialize performance monitoring', () => {
        const { isMonitoring, startMonitoring, stopMonitoring } = usePerformanceMonitoring('test-component')

        expect(isMonitoring.value).toBe(false)

        startMonitoring()
        expect(isMonitoring.value).toBe(true)

        stopMonitoring()
        expect(isMonitoring.value).toBe(false)
      })
    })

    describe('useDebouncedInput', () => {
      it('should debounce input values', async () => {
        const { inputValue, debouncedValue, isDebouncing } = useDebouncedInput('', 100)

        expect(debouncedValue.value).toBe('')
        expect(isDebouncing.value).toBe(false)

        inputValue.value = 'test'
        expect(isDebouncing.value).toBe(true)
        expect(debouncedValue.value).toBe('')

        vi.advanceTimersByTime(100)
        await nextTick()

        expect(debouncedValue.value).toBe('test')
        expect(isDebouncing.value).toBe(false)
      })

      it('should handle rapid input changes', async () => {
        const { inputValue, debouncedValue } = useDebouncedInput('', 50)

        inputValue.value = 'a'
        vi.advanceTimersByTime(25)
        inputValue.value = 'ab'
        vi.advanceTimersByTime(25)
        inputValue.value = 'abc'

        expect(debouncedValue.value).toBe('')

        vi.advanceTimersByTime(50)
        await nextTick()

        expect(debouncedValue.value).toBe('abc')
      })
    })

    describe('useThrottledScroll', () => {
      it('should throttle scroll events', () => {
        const mockCallback = vi.fn()
        const { handleScroll, isScrolling } = useThrottledScroll(mockCallback, 16)

        const mockEvent = {
          target: {
            scrollLeft: 0,
            scrollTop: 100
          }
        } as Event

        // First call should execute immediately
        handleScroll(mockEvent)
        expect(mockCallback).toHaveBeenCalledTimes(1)
        expect(isScrolling.value).toBe(true)

        // Subsequent calls within throttle period should be ignored
        handleScroll(mockEvent)
        handleScroll(mockEvent)
        expect(mockCallback).toHaveBeenCalledTimes(1)

        // After throttle period
        vi.advanceTimersByTime(16)
        handleScroll(mockEvent)
        expect(mockCallback).toHaveBeenCalledTimes(2)
      })
    })

    describe('useLazyLoading', () => {
      it('should handle successful lazy loading', async () => {
        const mockLoader = vi.fn().mockResolvedValue('loaded-data')
        const { data, isLoading, error, load } = useLazyLoading(mockLoader)

        expect(data.value).toBeNull()
        expect(isLoading.value).toBe(false)
        expect(error.value).toBeNull()

        const loadPromise = load()
        expect(isLoading.value).toBe(true)

        const result = await loadPromise
        expect(result).toBe('loaded-data')
        expect(data.value).toBe('loaded-data')
        expect(isLoading.value).toBe(false)
        expect(error.value).toBeNull()
      })

      it('should handle loading errors with retries', async () => {
        const mockLoader = vi.fn()
          .mockRejectedValueOnce(new Error('First failure'))
          .mockRejectedValueOnce(new Error('Second failure'))
          .mockResolvedValue('success-after-retries')

        const { data, isLoading, error, load } = useLazyLoading(mockLoader, {
          retries: 2,
          retryDelay: 100
        })

        const loadPromise = load()
        expect(isLoading.value).toBe(true)

        // Fast-forward through retry delays
        vi.advanceTimersByTime(300)

        const result = await loadPromise
        expect(result).toBe('success-after-retries')
        expect(data.value).toBe('success-after-retries')
        expect(isLoading.value).toBe(false)
        expect(error.value).toBeNull()
        expect(mockLoader).toHaveBeenCalledTimes(3)
      })

      it('should fail after max retries', async () => {
        const mockLoader = vi.fn().mockRejectedValue(new Error('Persistent failure'))
        const { data, isLoading, error, load } = useLazyLoading(mockLoader, {
          retries: 2,
          retryDelay: 100
        })

        try {
          await load()
        } catch (err) {
          expect(err).toBeInstanceOf(Error)
        }

        expect(data.value).toBeNull()
        expect(isLoading.value).toBe(false)
        expect(error.value).toBeInstanceOf(Error)
        expect(mockLoader).toHaveBeenCalledTimes(3) // Initial + 2 retries
      })
    })
  })

  describe('Virtual Scrolling', () => {
    it('should calculate visible items correctly', () => {
      const items = Array.from({ length: 100 }, (_, i) => ({ id: i, name: `Item ${i}` }))
      const itemsRef = { value: items }
      
      const { visibleItems, totalHeight } = useVirtualScroll(itemsRef, {
        itemHeight: 50,
        containerHeight: 300,
        overscan: 2
      })

      expect(totalHeight.value).toBe(5000) // 100 items * 50px
      expect(visibleItems.value.length).toBeGreaterThan(0)
      expect(visibleItems.value.length).toBeLessThan(items.length)
    })

    it('should handle empty item lists', () => {
      const itemsRef = { value: [] }
      
      const { visibleItems, totalHeight } = useVirtualScroll(itemsRef, {
        itemHeight: 50,
        containerHeight: 300
      })

      expect(totalHeight.value).toBe(0)
      expect(visibleItems.value).toEqual([])
    })
  })

  describe('Integration Tests', () => {
    it('should work together in a realistic scenario', async () => {
      // Simulate MBTI input with debouncing and validation
      const { inputValue, debouncedValue } = useDebouncedInput('', 100)
      const validationFn = memoize((value: string) => {
        return value.length === 4 && /^[A-Z]{4}$/.test(value)
      })

      // Simulate user typing
      inputValue.value = 'E'
      inputValue.value = 'EN'
      inputValue.value = 'ENF'
      inputValue.value = 'ENFP'

      // Should not validate until debounced
      expect(validationFn(inputValue.value)).toBe(true)
      expect(debouncedValue.value).toBe('')

      vi.advanceTimersByTime(100)
      await nextTick()

      expect(debouncedValue.value).toBe('ENFP')
      expect(validationFn(debouncedValue.value)).toBe(true)

      // Second validation with same value should use cache
      expect(validationFn(debouncedValue.value)).toBe(true)
    })

    it('should handle performance monitoring in components', () => {
      const { recordMetric, timeOperation } = usePerformanceMonitoring('TestComponent')
      
      const endTiming = timeOperation('test-operation')
      
      // Simulate some work
      vi.advanceTimersByTime(50)
      
      endTiming()
      recordMetric('custom-metric', 100)

      const metrics = performanceMonitor.getAllMetrics()
      expect(Object.keys(metrics)).toContain('TestComponent-test-operation')
      expect(Object.keys(metrics)).toContain('TestComponent-custom-metric')
    })
  })

  describe('Memory Management', () => {
    it('should track cleanup functions', () => {
      const cleanup1 = vi.fn()
      const cleanup2 = vi.fn()

      const cleanupFunctions = new Set<() => void>()
      cleanupFunctions.add(cleanup1)
      cleanupFunctions.add(cleanup2)

      cleanupFunctions.forEach(fn => fn())

      expect(cleanup1).toHaveBeenCalledTimes(1)
      expect(cleanup2).toHaveBeenCalledTimes(1)
    })

    it('should handle cleanup errors gracefully', () => {
      const goodCleanup = vi.fn()
      const badCleanup = vi.fn().mockImplementation(() => {
        throw new Error('Cleanup failed')
      })

      const cleanupFunctions = [goodCleanup, badCleanup]
      
      cleanupFunctions.forEach(fn => {
        try {
          fn()
        } catch (error) {
          // Should handle errors gracefully
          expect(error).toBeInstanceOf(Error)
        }
      })

      expect(goodCleanup).toHaveBeenCalledTimes(1)
      expect(badCleanup).toHaveBeenCalledTimes(1)
    })
  })
})

describe('Performance Benchmarks', () => {
  it('should measure debounce performance', async () => {
    const start = performance.now()
    const mockFn = vi.fn()
    const debouncedFn = debounce(mockFn, 10)

    // Make 1000 rapid calls
    for (let i = 0; i < 1000; i++) {
      debouncedFn(i)
    }

    vi.advanceTimersByTime(10)
    const end = performance.now()

    expect(mockFn).toHaveBeenCalledTimes(1)
    expect(mockFn).toHaveBeenCalledWith(999)
    
    // Should be very fast since only one actual function call
    const duration = end - start
    expect(duration).toBeLessThan(100) // Should complete in less than 100ms
  })

  it('should measure memoization performance', () => {
    const expensiveFn = vi.fn((n: number) => {
      // Simulate expensive computation
      let result = 0
      for (let i = 0; i < n; i++) {
        result += i
      }
      return result
    })

    const memoizedFn = memoize(expensiveFn)

    const start = performance.now()
    
    // First call - should be slow
    memoizedFn(1000)
    const firstCallTime = performance.now() - start

    const secondStart = performance.now()
    
    // Second call - should be fast (cached)
    memoizedFn(1000)
    const secondCallTime = performance.now() - secondStart

    expect(expensiveFn).toHaveBeenCalledTimes(1)
    expect(secondCallTime).toBeLessThan(firstCallTime)
  })
})
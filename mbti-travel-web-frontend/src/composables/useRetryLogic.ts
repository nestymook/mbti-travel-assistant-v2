// Retry logic composable for handling transient API failures
import { ref, readonly } from 'vue'
import { useNetworkStatus } from './useNetworkStatus'
import { useErrorHandler } from './useErrorHandler'
import type { ApiError, NetworkError } from '@/types/error'

export interface RetryConfig {
  maxAttempts: number
  baseDelay: number
  maxDelay: number
  backoffMultiplier: number
  jitter: boolean
  retryCondition?: (error: unknown) => boolean
  onRetry?: (attempt: number, error: unknown) => void
  onMaxRetriesExceeded?: (error: unknown) => void
}

export interface RetryState {
  isRetrying: boolean
  currentAttempt: number
  maxAttempts: number
  nextRetryIn: number
  lastError?: unknown
}

const defaultRetryConfig: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  jitter: true
}

export function useRetryLogic(config: Partial<RetryConfig> = {}) {
  const { isOnline, retryWhenOnline } = useNetworkStatus()
  const { handleError, isRetryable } = useErrorHandler()

  const retryConfig = { ...defaultRetryConfig, ...config }
  const retryState = ref<RetryState>({
    isRetrying: false,
    currentAttempt: 0,
    maxAttempts: retryConfig.maxAttempts,
    nextRetryIn: 0,
    lastError: undefined
  })

  /**
   * Execute operation with retry logic
   */
  async function executeWithRetry<T>(
    operation: () => Promise<T>,
    customConfig?: Partial<RetryConfig>
  ): Promise<T> {
    const config = { ...retryConfig, ...customConfig }
    let lastError: unknown

    retryState.value.isRetrying = true
    retryState.value.maxAttempts = config.maxAttempts
    retryState.value.currentAttempt = 0

    try {
      for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
        retryState.value.currentAttempt = attempt

        try {
          // If offline, wait for network to come back
          if (!isOnline.value) {
            const result = await retryWhenOnline(operation, 1, 30000)
            return result
          }

          // Execute the operation
          const result = await operation()
          
          // Success - reset retry state
          resetRetryState()
          return result

        } catch (error) {
          lastError = error
          retryState.value.lastError = error

          // Check if we should retry this error
          if (!shouldRetry(error, config)) {
            throw error
          }

          // Don't wait after the last attempt
          if (attempt === config.maxAttempts) {
            break
          }

          // Calculate delay for next retry
          const delay = calculateRetryDelay(attempt, config)
          retryState.value.nextRetryIn = delay

          // Call retry callback if provided
          config.onRetry?.(attempt, error)

          // Wait before next retry
          await sleep(delay)
        }
      }

      // All retries exhausted
      config.onMaxRetriesExceeded?.(lastError)
      throw lastError

    } finally {
      resetRetryState()
    }
  }

  /**
   * Execute operation with exponential backoff
   */
  async function executeWithExponentialBackoff<T>(
    operation: () => Promise<T>,
    maxAttempts: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    return executeWithRetry(operation, {
      maxAttempts,
      baseDelay,
      backoffMultiplier: 2,
      jitter: true
    })
  }

  /**
   * Execute operation with linear backoff
   */
  async function executeWithLinearBackoff<T>(
    operation: () => Promise<T>,
    maxAttempts: number = 3,
    delay: number = 1000
  ): Promise<T> {
    return executeWithRetry(operation, {
      maxAttempts,
      baseDelay: delay,
      backoffMultiplier: 1,
      jitter: false
    })
  }

  /**
   * Execute operation with fixed delay
   */
  async function executeWithFixedDelay<T>(
    operation: () => Promise<T>,
    maxAttempts: number = 3,
    delay: number = 1000
  ): Promise<T> {
    return executeWithRetry(operation, {
      maxAttempts,
      baseDelay: delay,
      backoffMultiplier: 1,
      jitter: false
    })
  }

  /**
   * Retry specific to API calls
   */
  async function retryApiCall<T>(
    apiCall: () => Promise<T>,
    maxAttempts: number = 3
  ): Promise<T> {
    return executeWithRetry(apiCall, {
      maxAttempts,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2,
      jitter: true,
      retryCondition: (error) => {
        // Retry on network errors
        if (isNetworkError(error)) {
          return true
        }

        // Retry on specific HTTP status codes
        if (isApiError(error)) {
          const retryableStatuses = [408, 429, 500, 502, 503, 504]
          return retryableStatuses.includes(error.status)
        }

        return false
      },
      onRetry: (attempt, error) => {
        console.warn(`API call retry attempt ${attempt}:`, error)
      }
    })
  }

  /**
   * Retry with circuit breaker pattern
   */
  function createCircuitBreaker<T>(
    operation: () => Promise<T>,
    failureThreshold: number = 5,
    resetTimeout: number = 60000
  ) {
    let failureCount = 0
    let lastFailureTime = 0
    let state: 'closed' | 'open' | 'half-open' = 'closed'

    return async (): Promise<T> => {
      const now = Date.now()

      // Check if circuit should reset
      if (state === 'open' && now - lastFailureTime >= resetTimeout) {
        state = 'half-open'
        failureCount = 0
      }

      // Reject immediately if circuit is open
      if (state === 'open') {
        throw new Error('Circuit breaker is open - operation not allowed')
      }

      try {
        const result = await operation()
        
        // Success - reset circuit breaker
        if (state === 'half-open') {
          state = 'closed'
        }
        failureCount = 0
        
        return result
      } catch (error) {
        failureCount++
        lastFailureTime = now

        // Open circuit if failure threshold exceeded
        if (failureCount >= failureThreshold) {
          state = 'open'
        }

        throw error
      }
    }
  }

  /**
   * Batch retry operations
   */
  async function retryBatch<T>(
    operations: (() => Promise<T>)[],
    config?: Partial<RetryConfig>
  ): Promise<T[]> {
    const results = await Promise.allSettled(
      operations.map(op => executeWithRetry(op, config))
    )

    const failures: unknown[] = []
    const successes: T[] = []

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        successes.push(result.value)
      } else {
        failures.push(result.reason)
        console.error(`Batch operation ${index} failed:`, result.reason)
      }
    })

    if (failures.length > 0 && successes.length === 0) {
      throw new Error(`All batch operations failed: ${failures.length} failures`)
    }

    return successes
  }

  /**
   * Determine if error should be retried
   */
  function shouldRetry(error: unknown, config: RetryConfig): boolean {
    // Use custom retry condition if provided
    if (config.retryCondition) {
      return config.retryCondition(error)
    }

    // Use default retry logic
    if (isNetworkError(error)) {
      return !error.offline // Don't retry if offline
    }

    if (isApiError(error)) {
      return error.retryable
    }

    // Use error handler's retry logic
    return isRetryable(error as any)
  }

  /**
   * Calculate retry delay with backoff and jitter
   */
  function calculateRetryDelay(attempt: number, config: RetryConfig): number {
    let delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1)
    
    // Apply maximum delay limit
    delay = Math.min(delay, config.maxDelay)
    
    // Add jitter to prevent thundering herd
    if (config.jitter) {
      delay = delay * (0.5 + Math.random() * 0.5)
    }
    
    return Math.floor(delay)
  }

  /**
   * Sleep for specified milliseconds
   */
  function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Reset retry state
   */
  function resetRetryState(): void {
    retryState.value = {
      isRetrying: false,
      currentAttempt: 0,
      maxAttempts: retryConfig.maxAttempts,
      nextRetryIn: 0,
      lastError: undefined
    }
  }

  /**
   * Cancel current retry operation
   */
  function cancelRetry(): void {
    resetRetryState()
  }

  /**
   * Get retry statistics
   */
  function getRetryStats() {
    return {
      isRetrying: retryState.value.isRetrying,
      currentAttempt: retryState.value.currentAttempt,
      maxAttempts: retryState.value.maxAttempts,
      nextRetryIn: retryState.value.nextRetryIn,
      hasError: !!retryState.value.lastError,
      progress: retryState.value.maxAttempts > 0 
        ? retryState.value.currentAttempt / retryState.value.maxAttempts 
        : 0
    }
  }

  // Type guards
  function isNetworkError(error: unknown): error is NetworkError {
    return typeof error === 'object' && error !== null && 
           'type' in error && (error as any).type === 'network_error'
  }

  function isApiError(error: unknown): error is ApiError {
    return typeof error === 'object' && error !== null && 
           'type' in error && (error as any).type === 'api_error'
  }

  return {
    // State
    retryState: readonly(retryState),
    retryConfig,

    // Core retry methods
    executeWithRetry,
    executeWithExponentialBackoff,
    executeWithLinearBackoff,
    executeWithFixedDelay,

    // Specialized retry methods
    retryApiCall,
    createCircuitBreaker,
    retryBatch,

    // Utility methods
    shouldRetry,
    calculateRetryDelay,
    resetRetryState,
    cancelRetry,
    getRetryStats,
    sleep
  }
}
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useNetworkStatus } from '@/composables/useNetworkStatus'
import { useRetryLogic } from '@/composables/useRetryLogic'
import type { ApiError, NetworkError, ValidationError } from '@/types/error'

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
})

describe('Error Handling Integration', () => {
  let errorHandler: ReturnType<typeof useErrorHandler>
  let networkStatus: ReturnType<typeof useNetworkStatus>
  let retryLogic: ReturnType<typeof useRetryLogic>

  beforeEach(() => {
    errorHandler = useErrorHandler()
    networkStatus = useNetworkStatus()
    retryLogic = useRetryLogic()
    
    // Clear any existing notifications
    errorHandler.clearAllNotifications()
    errorHandler.clearError()
  })

  describe('Error categorization and handling', () => {
    it('handles network errors correctly', () => {
      const networkError = new TypeError('fetch failed')
      const result = errorHandler.handleError(networkError)

      expect(result.type).toBe('network_error')
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
      expect(errorHandler.globalErrorState.hasError).toBe(true)
    })

    it('handles API errors correctly', () => {
      const apiError = {
        status: 500,
        message: 'Internal Server Error',
        response: { status: 500 }
      }
      
      const result = errorHandler.handleError(apiError) as ApiError
      
      expect(result.type).toBe('api_error')
      expect(result.status).toBe(500)
      expect(result.retryable).toBe(true)
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
    })

    it('handles validation errors correctly', () => {
      const validationError = new Error('validation failed')
      const result = errorHandler.handleError(validationError) as ValidationError

      expect(result.type).toBe('validation_error')
      expect(result.message).toContain('validation failed')
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
    })
  })

  describe('Error recovery and retry logic', () => {
    it('provides retry actions for retryable errors', () => {
      const retryableError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }

      errorHandler.handleError(retryableError)
      const notification = errorHandler.activeNotifications.value[0]

      expect(notification.actions).toBeDefined()
      expect(notification.actions!.some(action => action.label === 'Retry')).toBe(true)
    })

    it('executes retry logic for transient failures', async () => {
      let attempts = 0
      const flakyOperation = vi.fn().mockImplementation(() => {
        attempts++
        if (attempts < 3) {
          throw new Error('Temporary failure')
        }
        return 'success'
      })

      const result = await retryLogic.executeWithRetry(flakyOperation, {
        maxAttempts: 3,
        baseDelay: 10 // Short delay for testing
      })

      expect(result).toBe('success')
      expect(flakyOperation).toHaveBeenCalledTimes(3)
    })

    it('fails after max retry attempts', async () => {
      const alwaysFailingOperation = vi.fn().mockRejectedValue(new Error('Always fails'))

      await expect(
        retryLogic.executeWithRetry(alwaysFailingOperation, {
          maxAttempts: 2,
          baseDelay: 10
        })
      ).rejects.toThrow('Always fails')

      expect(alwaysFailingOperation).toHaveBeenCalledTimes(2)
    })
  })

  describe('Network status integration', () => {
    it('detects online status', () => {
      navigator.onLine = true
      networkStatus.updateNetworkStatus()
      
      expect(networkStatus.isOnline.value).toBe(true)
    })

    it('detects offline status', () => {
      navigator.onLine = false
      networkStatus.updateNetworkStatus()
      
      expect(networkStatus.isOnline.value).toBe(false)
    })

    it('handles offline errors appropriately', () => {
      navigator.onLine = false
      
      const offlineError: NetworkError = {
        type: 'network_error',
        message: 'Network request failed',
        offline: true,
        timestamp: new Date().toISOString()
      }

      const result = errorHandler.handleError(offlineError)
      expect(result.type).toBe('network_error')
      expect(result.offline).toBe(true)
      
      const notification = errorHandler.activeNotifications.value[0]
      expect(notification.message).toContain('internet connection')
    })
  })

  describe('User-friendly error messages', () => {
    it('provides appropriate messages for different error types', () => {
      const testCases = [
        {
          error: { type: 'network_error', offline: true } as NetworkError,
          expectedMessage: 'No internet connection'
        },
        {
          error: { type: 'api_error', status: 500 } as ApiError,
          expectedMessage: 'Server error occurred'
        },
        {
          error: { type: 'api_error', status: 404 } as ApiError,
          expectedMessage: 'requested resource was not found'
        },
        {
          error: { type: 'auth_error', action: 'redirect_to_login' } as any,
          expectedMessage: 'Authentication required'
        }
      ]

      testCases.forEach(({ error, expectedMessage }) => {
        const message = errorHandler.getUserFriendlyMessage(error as any)
        expect(message).toContain(expectedMessage)
      })
    })
  })

  describe('Error state management', () => {
    it('tracks error state correctly', () => {
      expect(errorHandler.globalErrorState.hasError).toBe(false)
      
      const error = new Error('Test error')
      errorHandler.handleError(error)
      
      expect(errorHandler.globalErrorState.hasError).toBe(true)
      expect(errorHandler.globalErrorState.error).toBeDefined()
      expect(errorHandler.globalErrorState.lastErrorTime).toBeDefined()
    })

    it('clears error state', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)
      
      expect(errorHandler.globalErrorState.hasError).toBe(true)
      
      errorHandler.clearError()
      
      expect(errorHandler.globalErrorState.hasError).toBe(false)
      expect(errorHandler.globalErrorState.error).toBeUndefined()
    })

    it('manages notifications correctly', () => {
      const error1 = new Error('Error 1')
      const error2 = new Error('Error 2')
      
      errorHandler.handleError(error1)
      errorHandler.handleError(error2)
      
      expect(errorHandler.activeNotifications.value).toHaveLength(2)
      
      const firstNotificationId = errorHandler.activeNotifications.value[0].id
      errorHandler.dismissNotification(firstNotificationId)
      
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
      
      errorHandler.clearAllNotifications()
      expect(errorHandler.activeNotifications.value).toHaveLength(0)
    })
  })

  describe('Error context and logging', () => {
    it('includes context information in error handling', () => {
      const consoleSpy = vi.spyOn(console, 'group').mockImplementation(() => {})
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {})

      const error = new Error('Test error')
      const context = {
        userId: 'user123',
        additionalData: { action: 'test-action' }
      }
      
      errorHandler.handleError(error, context)
      
      expect(consoleSpy).toHaveBeenCalled()
      expect(consoleErrorSpy).toHaveBeenCalled()
      expect(consoleLogSpy).toHaveBeenCalled()
      expect(consoleGroupEndSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
      consoleErrorSpy.mockRestore()
      consoleLogSpy.mockRestore()
      consoleGroupEndSpy.mockRestore()
    })
  })

  describe('Circuit breaker pattern', () => {
    it('opens circuit after failure threshold', async () => {
      let attempts = 0
      const failingOperation = vi.fn().mockImplementation(() => {
        attempts++
        throw new Error(`Failure ${attempts}`)
      })

      const circuitBreaker = retryLogic.createCircuitBreaker(failingOperation, 3, 1000)

      // First 3 attempts should fail and open the circuit
      for (let i = 0; i < 3; i++) {
        await expect(circuitBreaker()).rejects.toThrow()
      }

      // 4th attempt should be rejected immediately due to open circuit
      await expect(circuitBreaker()).rejects.toThrow('Circuit breaker is open')
      
      // Should not have called the operation for the 4th time
      expect(failingOperation).toHaveBeenCalledTimes(3)
    })
  })

  describe('Batch operations', () => {
    it('handles batch retry operations', async () => {
      const operation1 = vi.fn().mockResolvedValue('result1')
      const operation2 = vi.fn().mockRejectedValue(new Error('fails'))
      const operation3 = vi.fn().mockResolvedValue('result3')

      const results = await retryLogic.retryBatch([operation1, operation2, operation3], {
        maxAttempts: 1,
        baseDelay: 10
      })

      expect(results).toEqual(['result1', 'result3'])
      expect(operation1).toHaveBeenCalledTimes(1)
      expect(operation2).toHaveBeenCalledTimes(1)
      expect(operation3).toHaveBeenCalledTimes(1)
    })
  })
})
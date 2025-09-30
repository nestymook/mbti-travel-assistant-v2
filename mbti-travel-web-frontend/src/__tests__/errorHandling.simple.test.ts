import { describe, it, expect, vi } from 'vitest'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { ApiError, NetworkError, ValidationError } from '@/types/error'

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
})

describe('Error Handling System', () => {
  describe('Error Handler Core Functionality', () => {
    it('categorizes and handles different error types correctly', () => {
      const errorHandler = useErrorHandler()
      
      // Test network error
      const networkError = new TypeError('fetch failed')
      const networkResult = errorHandler.categorizeError(networkError)
      expect(networkResult.type).toBe('network_error')
      
      // Test API error
      const apiError = { status: 500, response: { status: 500 } }
      const apiResult = errorHandler.categorizeError(apiError) as ApiError
      expect(apiResult.type).toBe('api_error')
      expect(apiResult.status).toBe(500)
      expect(apiResult.retryable).toBe(true)
      
      // Test validation error
      const validationError = new Error('validation failed')
      const validationResult = errorHandler.categorizeError(validationError) as ValidationError
      expect(validationResult.type).toBe('validation_error')
      expect(validationResult.message).toContain('validation failed')
    })

    it('provides user-friendly error messages', () => {
      const errorHandler = useErrorHandler()
      
      const testCases = [
        {
          error: { type: 'network_error', offline: true, message: 'Network failed', timestamp: new Date().toISOString() } as NetworkError,
          expectedMessage: 'No internet connection'
        },
        {
          error: { type: 'api_error', status: 500, message: 'Server Error', retryable: true, timestamp: new Date().toISOString() } as ApiError,
          expectedMessage: 'Server error occurred'
        },
        {
          error: { type: 'api_error', status: 404, message: 'Not Found', retryable: false, timestamp: new Date().toISOString() } as ApiError,
          expectedMessage: 'requested resource was not found'
        }
      ]

      testCases.forEach(({ error, expectedMessage }) => {
        const message = errorHandler.getUserFriendlyMessage(error)
        expect(message).toContain(expectedMessage)
      })
    })

    it('determines retryability correctly', () => {
      const errorHandler = useErrorHandler()
      
      // Retryable errors
      const retryableNetworkError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }
      expect(errorHandler.isRetryable(retryableNetworkError)).toBe(true)
      
      const retryableApiError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }
      expect(errorHandler.isRetryable(retryableApiError)).toBe(true)
      
      // Non-retryable errors
      const nonRetryableNetworkError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: true,
        timestamp: new Date().toISOString()
      }
      expect(errorHandler.isRetryable(nonRetryableNetworkError)).toBe(false)
      
      const nonRetryableApiError: ApiError = {
        type: 'api_error',
        status: 400,
        message: 'Bad Request',
        retryable: false,
        timestamp: new Date().toISOString()
      }
      expect(errorHandler.isRetryable(nonRetryableApiError)).toBe(false)
    })

    it('manages error state correctly', () => {
      const errorHandler = useErrorHandler()
      
      // Initial state
      expect(errorHandler.globalErrorState.hasError).toBe(false)
      
      // Handle error
      const error = new Error('Test error')
      errorHandler.handleError(error)
      
      expect(errorHandler.globalErrorState.hasError).toBe(true)
      expect(errorHandler.globalErrorState.error).toBeDefined()
      expect(errorHandler.globalErrorState.lastErrorTime).toBeDefined()
      
      // Clear error
      errorHandler.clearError()
      
      expect(errorHandler.globalErrorState.hasError).toBe(false)
      expect(errorHandler.globalErrorState.error).toBeUndefined()
    })

    it('manages notifications correctly', () => {
      const errorHandler = useErrorHandler()
      
      // Clear any existing notifications
      errorHandler.clearAllNotifications()
      
      // Handle multiple errors
      const error1 = new Error('Error 1')
      const error2 = new Error('Error 2')
      
      errorHandler.handleError(error1)
      errorHandler.handleError(error2)
      
      expect(errorHandler.activeNotifications.value).toHaveLength(2)
      
      // Dismiss one notification
      const firstNotificationId = errorHandler.activeNotifications.value[0].id
      errorHandler.dismissNotification(firstNotificationId)
      
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
      
      // Clear all notifications
      errorHandler.clearAllNotifications()
      expect(errorHandler.activeNotifications.value).toHaveLength(0)
    })

    it('generates appropriate recovery actions', () => {
      const errorHandler = useErrorHandler()
      errorHandler.clearAllNotifications()
      
      // Network error should have retry action
      const networkError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }
      
      errorHandler.handleError(networkError)
      const networkNotification = errorHandler.activeNotifications.value[0]
      
      expect(networkNotification.actions).toBeDefined()
      expect(networkNotification.actions!.some(action => action.label === 'Retry')).toBe(true)
      
      // Clear for next test
      errorHandler.clearAllNotifications()
      
      // API error should have retry action if retryable
      const apiError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }
      
      errorHandler.handleError(apiError)
      const apiNotification = errorHandler.activeNotifications.value[0]
      
      expect(apiNotification.actions).toBeDefined()
      expect(apiNotification.actions!.some(action => action.label === 'Retry')).toBe(true)
    })
  })

  describe('Error Message Formatting', () => {
    it('formats error titles correctly', () => {
      const errorHandler = useErrorHandler()
      
      const testCases = [
        { type: 'network_error', expectedTitle: 'Network Error' },
        { type: 'api_error', expectedTitle: 'Server Error' },
        { type: 'auth_error', expectedTitle: 'Authentication Required' },
        { type: 'validation_error', expectedTitle: 'Invalid Input' },
        { type: 'business_error', expectedTitle: 'Business Rule Error' },
        { type: 'application_error', expectedTitle: 'Application Error' }
      ]

      testCases.forEach(({ type, expectedTitle }) => {
        const error = { type, message: 'Test message', timestamp: new Date().toISOString() } as any
        const title = errorHandler.getErrorTitle(error)
        expect(title).toBe(expectedTitle)
      })
    })

    it('determines severity levels correctly', () => {
      const errorHandler = useErrorHandler()
      
      const testCases = [
        { type: 'validation_error', expectedSeverity: 'warning' },
        { type: 'business_error', expectedSeverity: 'warning' },
        { type: 'network_error', offline: false, expectedSeverity: 'warning' },
        { type: 'network_error', offline: true, expectedSeverity: 'error' },
        { type: 'api_error', expectedSeverity: 'error' },
        { type: 'auth_error', expectedSeverity: 'error' }
      ]

      testCases.forEach(({ type, offline, expectedSeverity }) => {
        const error = { 
          type, 
          message: 'Test message', 
          timestamp: new Date().toISOString(),
          ...(offline !== undefined && { offline })
        } as any
        const severity = errorHandler.getSeverityFromError(error)
        expect(severity).toBe(expectedSeverity)
      })
    })
  })

  describe('Error Context and Logging', () => {
    it('logs errors in development mode', () => {
      const consoleSpy = vi.spyOn(console, 'group').mockImplementation(() => {})
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {})

      const errorHandler = useErrorHandler()
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
})
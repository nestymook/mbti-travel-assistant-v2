import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useErrorHandler } from '../useErrorHandler'
import type { AppError, NetworkError, ApiError, AuthError, ValidationError } from '@/types/error'

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
})

describe('useErrorHandler', () => {
  let errorHandler: ReturnType<typeof useErrorHandler>

  beforeEach(() => {
    errorHandler = useErrorHandler()
    // Clear any existing notifications
    errorHandler.clearAllNotifications()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('categorizeError', () => {
    it('returns AppError as-is', () => {
      const appError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }

      const result = errorHandler.categorizeError(appError)
      expect(result).toBe(appError)
    })

    it('categorizes network errors', () => {
      const networkError = new TypeError('fetch failed')
      const result = errorHandler.categorizeError(networkError)

      expect(result.type).toBe('network_error')
      expect(result.message).toContain('fetch failed')
    })

    it('categorizes HTTP errors', () => {
      const httpError = {
        status: 500,
        message: 'Internal Server Error',
        response: { status: 500 }
      }

      const result = errorHandler.categorizeError(httpError) as ApiError
      expect(result.type).toBe('api_error')
      expect(result.status).toBe(500)
      expect(result.retryable).toBe(true)
    })

    it('categorizes validation errors', () => {
      const validationError = new Error('validation failed')
      const result = errorHandler.categorizeError(validationError) as ValidationError

      expect(result.type).toBe('validation_error')
      expect(result.message).toContain('validation failed')
    })

    it('categorizes auth errors', () => {
      const authError = new Error('unauthorized access')
      const result = errorHandler.categorizeError(authError) as AuthError

      expect(result.type).toBe('auth_error')
      expect(result.message).toContain('unauthorized access')
    })

    it('categorizes generic errors', () => {
      const genericError = new Error('Something went wrong')
      const result = errorHandler.categorizeError(genericError)

      expect(result.type).toBe('application_error')
      expect(result.message).toBe('Something went wrong')
    })

    it('handles unknown error types', () => {
      const unknownError = 'string error'
      const result = errorHandler.categorizeError(unknownError)

      expect(result.type).toBe('application_error')
      expect(result.message).toBe('An unknown error occurred')
    })
  })

  describe('handleError', () => {
    it('processes error and creates notification', () => {
      const error = new Error('Test error')
      const result = errorHandler.handleError(error)

      expect(result.type).toBe('application_error')
      expect(errorHandler.activeNotifications.value).toHaveLength(1)
    })

    it('updates global error state', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)

      expect(errorHandler.globalErrorState.hasError).toBe(true)
      expect(errorHandler.globalErrorState.error).toBeDefined()
    })

    it('includes context in error processing', () => {
      const error = new Error('Test error')
      const context = { userId: 'user123' }
      
      const consoleSpy = vi.spyOn(console, 'group').mockImplementation(() => {})
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {})

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

  describe('getUserFriendlyMessage', () => {
    it('returns user message if available', () => {
      const error: AppError = {
        type: 'application_error',
        message: 'Technical error',
        userMessage: 'User-friendly message',
        severity: 'medium',
        recoverable: true,
        timestamp: new Date().toISOString()
      }

      const message = errorHandler.getUserFriendlyMessage(error)
      expect(message).toBe('User-friendly message')
    })

    it('returns appropriate message for network errors', () => {
      const offlineError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: true,
        timestamp: new Date().toISOString()
      }

      const onlineError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }

      expect(errorHandler.getUserFriendlyMessage(offlineError))
        .toContain('No internet connection')
      expect(errorHandler.getUserFriendlyMessage(onlineError))
        .toContain('Network error occurred')
    })

    it('returns appropriate message for API errors', () => {
      const serverError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Internal Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }

      const notFoundError: ApiError = {
        type: 'api_error',
        status: 404,
        message: 'Not Found',
        retryable: false,
        timestamp: new Date().toISOString()
      }

      expect(errorHandler.getUserFriendlyMessage(serverError))
        .toContain('Server error occurred')
      expect(errorHandler.getUserFriendlyMessage(notFoundError))
        .toContain('requested resource was not found')
    })

    it('returns appropriate message for auth errors', () => {
      const authError: AuthError = {
        type: 'auth_error',
        message: 'Unauthorized',
        action: 'redirect_to_login',
        timestamp: new Date().toISOString()
      }

      expect(errorHandler.getUserFriendlyMessage(authError))
        .toContain('Authentication required')
    })
  })

  describe('isRetryable', () => {
    it('identifies retryable network errors', () => {
      const retryableError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }

      const nonRetryableError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: true,
        timestamp: new Date().toISOString()
      }

      expect(errorHandler.isRetryable(retryableError)).toBe(true)
      expect(errorHandler.isRetryable(nonRetryableError)).toBe(false)
    })

    it('identifies retryable API errors', () => {
      const retryableError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }

      const nonRetryableError: ApiError = {
        type: 'api_error',
        status: 400,
        message: 'Bad Request',
        retryable: false,
        timestamp: new Date().toISOString()
      }

      expect(errorHandler.isRetryable(retryableError)).toBe(true)
      expect(errorHandler.isRetryable(nonRetryableError)).toBe(false)
    })
  })

  describe('notification management', () => {
    it('creates notifications for errors', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)

      expect(errorHandler.activeNotifications.value).toHaveLength(1)
      const notification = errorHandler.activeNotifications.value[0]
      expect(notification.message).toContain('unexpected error occurred')
    })

    it('dismisses notifications', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)

      const notificationId = errorHandler.activeNotifications.value[0].id
      errorHandler.dismissNotification(notificationId)

      expect(errorHandler.activeNotifications.value).toHaveLength(0)
    })

    it('clears all notifications', () => {
      errorHandler.handleError(new Error('Error 1'))
      errorHandler.handleError(new Error('Error 2'))

      expect(errorHandler.activeNotifications.value).toHaveLength(2)

      errorHandler.clearAllNotifications()
      expect(errorHandler.activeNotifications.value).toHaveLength(0)
    })
  })

  describe('error state management', () => {
    it('updates global error state on error', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)

      expect(errorHandler.globalErrorState.hasError).toBe(true)
      expect(errorHandler.globalErrorState.error).toBeDefined()
      expect(errorHandler.globalErrorState.lastErrorTime).toBeDefined()
    })

    it('clears error state', () => {
      const error = new Error('Test error')
      errorHandler.handleError(error)

      errorHandler.clearError()

      expect(errorHandler.globalErrorState.hasError).toBe(false)
      expect(errorHandler.globalErrorState.error).toBeUndefined()
      expect(errorHandler.globalErrorState.recoveryAttempts).toBe(0)
    })
  })

  describe('recovery actions', () => {
    it('generates recovery actions for network errors', () => {
      const networkError: NetworkError = {
        type: 'network_error',
        message: 'Network failed',
        offline: false,
        timestamp: new Date().toISOString()
      }

      errorHandler.handleError(networkError)
      const notification = errorHandler.activeNotifications.value[0]
      
      expect(notification.actions).toBeDefined()
      expect(notification.actions!.length).toBeGreaterThan(0)
      expect(notification.actions![0].label).toBe('Retry')
    })

    it('generates recovery actions for API errors', () => {
      const apiError: ApiError = {
        type: 'api_error',
        status: 500,
        message: 'Server Error',
        retryable: true,
        timestamp: new Date().toISOString()
      }

      errorHandler.handleError(apiError)
      const notification = errorHandler.activeNotifications.value[0]
      
      expect(notification.actions).toBeDefined()
      expect(notification.actions!.some(action => action.label === 'Retry')).toBe(true)
    })

    it('generates recovery actions for auth errors', () => {
      const authError: AuthError = {
        type: 'auth_error',
        message: 'Unauthorized',
        action: 'redirect_to_login',
        timestamp: new Date().toISOString()
      }

      errorHandler.handleError(authError)
      const notification = errorHandler.activeNotifications.value[0]
      
      expect(notification.actions).toBeDefined()
      expect(notification.actions!.some(action => action.label === 'Login')).toBe(true)
    })
  })
})
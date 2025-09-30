// Global error handler composable with categorized error types
import { ref, reactive, readonly } from 'vue'
import type { 
  AppError, 
  ErrorNotification, 
  ErrorNotificationAction,
  ErrorRecoveryStrategy,
  ErrorContext,
  ErrorState,
  NetworkError,
  ApiError,
  AuthError,
  ValidationError,
  ApplicationError,
  BusinessError
} from '@/types/error'

// Global error state
const globalErrorState = reactive<ErrorState>({
  hasError: false,
  error: undefined,
  isRecovering: false,
  recoveryAttempts: 0,
  lastErrorTime: undefined
})

// Active error notifications
const activeNotifications = ref<ErrorNotification[]>([])

// Error handling configuration
const errorConfig = reactive({
  showTechnicalDetails: import.meta.env.DEV,
  enableRetry: true,
  maxRetryAttempts: 3,
  retryDelay: 1000,
  logErrors: true,
  reportErrors: !import.meta.env.DEV,
  autoCloseDelay: 5000
})

export function useErrorHandler() {
  /**
   * Handle any error and convert to appropriate error type
   */
  function handleError(error: unknown, context?: Partial<ErrorContext>): AppError {
    const appError = categorizeError(error)
    const errorContext = createErrorContext(context)
    
    // Log error if enabled
    if (errorConfig.logErrors) {
      logError(appError, errorContext)
    }
    
    // Update global error state
    updateGlobalErrorState(appError)
    
    // Show user notification
    showErrorNotification(appError)
    
    // Report error if enabled
    if (errorConfig.reportErrors) {
      reportError(appError, errorContext)
    }
    
    return appError
  }

  /**
   * Categorize unknown error into specific error type
   */
  function categorizeError(error: unknown): AppError {
    // Already an AppError
    if (isAppError(error)) {
      return error
    }

    // Network/fetch errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return createNetworkError(error.message, !navigator.onLine)
    }

    // HTTP errors (from axios or fetch)
    if (isHttpError(error)) {
      return createApiError(error)
    }

    // Validation errors
    if (isValidationError(error)) {
      return createValidationError(error)
    }

    // Authentication errors
    if (isAuthError(error)) {
      return createAuthError(error)
    }

    // Generic JavaScript errors
    if (error instanceof Error) {
      return createApplicationError(error)
    }

    // Unknown error type
    return createApplicationError(new Error('An unknown error occurred'))
  }

  /**
   * Show error notification to user
   */
  function showErrorNotification(error: AppError): void {
    const notification = createErrorNotification(error)
    activeNotifications.value.push(notification)

    // Auto-close notification after delay
    if (notification.autoClose) {
      setTimeout(() => {
        dismissNotification(notification.id)
      }, notification.duration || errorConfig.autoCloseDelay)
    }
  }

  /**
   * Create error notification from error
   */
  function createErrorNotification(error: AppError): ErrorNotification {
    const id = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    const baseNotification: ErrorNotification = {
      id,
      type: 'toast',
      severity: getSeverityFromError(error),
      title: getErrorTitle(error),
      message: getUserFriendlyMessage(error),
      autoClose: error.type !== 'auth_error',
      actions: []
    }

    // Add recovery actions based on error type
    const actions = getRecoveryActions(error)
    if (actions.length > 0) {
      baseNotification.actions = actions
      baseNotification.autoClose = false // Don't auto-close if there are actions
    }

    return baseNotification
  }

  /**
   * Get recovery actions for error
   */
  function getRecoveryActions(error: AppError): ErrorNotificationAction[] {
    const actions: ErrorNotificationAction[] = []

    switch (error.type) {
      case 'network_error':
        if (error.offline) {
          actions.push({
            label: 'Check Connection',
            action: () => window.location.reload(),
            style: 'primary'
          })
        } else {
          actions.push({
            label: 'Try Again',
            action: () => retryLastOperation(),
            style: 'primary'
          })
        }
        break

      case 'api_error':
        if (error.retryable) {
          actions.push({
            label: 'Try Again',
            action: () => retryLastOperation(),
            style: 'primary'
          })
        } else {
          actions.push({
            label: 'Refresh Page',
            action: () => window.location.reload(),
            style: 'primary'
          })
        }
        break

      case 'auth_error':
        if (error.action === 'redirect_to_login') {
          actions.push({
            label: 'Login',
            action: () => redirectToLogin(),
            style: 'primary'
          })
        } else if (error.action === 'refresh_token') {
          actions.push({
            label: 'Try Again',
            action: () => refreshTokenAndRetry(),
            style: 'primary'
          })
        }
        break

      case 'validation_error':
        if (error.suggestedValue) {
          actions.push({
            label: `Use "${error.suggestedValue}"`,
            action: () => applySuggestedValue(error.field, error.suggestedValue!),
            style: 'primary'
          })
        }
        break

      case 'application_error':
        if (error.recoverable) {
          actions.push({
            label: 'Try Again',
            action: () => retryLastOperation(),
            style: 'primary'
          })
        } else {
          actions.push({
            label: 'Refresh Page',
            action: () => window.location.reload(),
            style: 'primary'
          })
        }
        break
    }

    return actions
  }

  /**
   * Dismiss notification
   */
  function dismissNotification(id: string): void {
    const index = activeNotifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      activeNotifications.value.splice(index, 1)
    }
  }

  /**
   * Clear all notifications
   */
  function clearAllNotifications(): void {
    activeNotifications.value = []
  }

  /**
   * Retry last operation
   */
  async function retryLastOperation(): Promise<void> {
    if (globalErrorState.isRecovering) {
      return
    }

    globalErrorState.isRecovering = true
    globalErrorState.recoveryAttempts++

    try {
      // This would need to be implemented based on the specific operation
      // For now, we'll just clear the error state
      clearError()
    } catch (error) {
      handleError(error, { additionalData: { retryAttempt: globalErrorState.recoveryAttempts } })
    } finally {
      globalErrorState.isRecovering = false
    }
  }

  /**
   * Clear current error state
   */
  function clearError(): void {
    globalErrorState.hasError = false
    globalErrorState.error = undefined
    globalErrorState.isRecovering = false
    globalErrorState.recoveryAttempts = 0
  }

  /**
   * Check if error is retryable
   */
  function isRetryable(error: AppError): boolean {
    switch (error.type) {
      case 'network_error':
        return !error.offline
      case 'api_error':
        return error.retryable
      case 'application_error':
        return error.recoverable
      default:
        return false
    }
  }

  /**
   * Get user-friendly error message
   */
  function getUserFriendlyMessage(error: AppError): string {
    if (error.userMessage) {
      return error.userMessage
    }

    switch (error.type) {
      case 'network_error':
        return error.offline 
          ? 'No internet connection. Please check your network and try again.'
          : 'Network error occurred. Please try again.'
      
      case 'api_error':
        if (error.status >= 500) {
          return 'Server error occurred. Please try again later.'
        } else if (error.status === 404) {
          return 'The requested resource was not found.'
        } else if (error.status === 429) {
          return 'Too many requests. Please wait a moment and try again.'
        }
        return error.message || 'An error occurred while processing your request.'
      
      case 'auth_error':
        return 'Authentication required. Please log in to continue.'
      
      case 'validation_error':
        return error.message || 'Please check your input and try again.'
      
      case 'business_error':
        return error.message || 'Business rule validation failed.'
      
      case 'application_error':
        return error.severity === 'critical' 
          ? 'A critical error occurred. Please refresh the page.'
          : 'An unexpected error occurred. Please try again.'
      
      default:
        return 'An unexpected error occurred. Please try again.'
    }
  }

  /**
   * Get error title
   */
  function getErrorTitle(error: AppError): string {
    switch (error.type) {
      case 'network_error':
        return error.offline ? 'Connection Lost' : 'Network Error'
      case 'api_error':
        return 'Server Error'
      case 'auth_error':
        return 'Authentication Required'
      case 'validation_error':
        return 'Invalid Input'
      case 'business_error':
        return 'Business Rule Error'
      case 'application_error':
        return error.severity === 'critical' ? 'Critical Error' : 'Application Error'
      default:
        return 'Error'
    }
  }

  /**
   * Get severity from error type
   */
  function getSeverityFromError(error: AppError): 'info' | 'warning' | 'error' | 'success' {
    switch (error.type) {
      case 'validation_error':
        return 'warning'
      case 'business_error':
        return 'warning'
      case 'network_error':
        return error.offline ? 'error' : 'warning'
      case 'application_error':
        return error.severity === 'critical' ? 'error' : 'warning'
      default:
        return 'error'
    }
  }

  // Helper functions for error type checking
  function isAppError(error: unknown): error is AppError {
    return typeof error === 'object' && error !== null && 'type' in error
  }

  function isHttpError(error: unknown): boolean {
    return typeof error === 'object' && error !== null && 
           ('status' in error || 'response' in error)
  }

  function isValidationError(error: unknown): boolean {
    return error instanceof Error && 
           (error.message.includes('validation') || error.message.includes('invalid'))
  }

  function isAuthError(error: unknown): boolean {
    return error instanceof Error && 
           (error.message.includes('auth') || error.message.includes('unauthorized'))
  }

  // Error creation helpers
  function createNetworkError(message: string, offline: boolean): NetworkError {
    return {
      type: 'network_error',
      message,
      offline,
      timestamp: new Date().toISOString()
    }
  }

  function createApiError(error: any): ApiError {
    const status = error.status || error.response?.status || 500
    const message = error.message || error.response?.data?.message || 'API error occurred'
    
    return {
      type: 'api_error',
      status,
      message,
      retryable: status >= 500 || status === 408 || status === 429,
      timestamp: new Date().toISOString()
    }
  }

  function createAuthError(error: any): AuthError {
    return {
      type: 'auth_error',
      message: error.message || 'Authentication failed',
      action: 'redirect_to_login',
      timestamp: new Date().toISOString()
    }
  }

  function createValidationError(error: any): ValidationError {
    return {
      type: 'validation_error',
      field: error.field || 'unknown',
      message: error.message || 'Validation failed',
      timestamp: new Date().toISOString()
    }
  }

  function createApplicationError(error: Error): ApplicationError {
    return {
      type: 'application_error',
      message: error.message,
      severity: 'medium',
      recoverable: true,
      timestamp: new Date().toISOString()
    }
  }

  // Context and logging helpers
  function createErrorContext(context?: Partial<ErrorContext>): ErrorContext {
    return {
      userId: context?.userId,
      sessionId: context?.sessionId,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      stackTrace: new Error().stack,
      breadcrumbs: context?.breadcrumbs || [],
      additionalData: context?.additionalData || {}
    }
  }

  function updateGlobalErrorState(error: AppError): void {
    globalErrorState.hasError = true
    globalErrorState.error = error
    globalErrorState.lastErrorTime = new Date().toISOString()
  }

  function logError(error: AppError, context: ErrorContext): void {
    if (import.meta.env.DEV) {
      console.group(`🚨 ${error.type.toUpperCase()} Error`)
      console.error('Error:', error)
      console.log('Context:', context)
      console.groupEnd()
    }
  }

  function reportError(error: AppError, context: ErrorContext): void {
    // In a real application, this would send the error to a logging service
    // like Sentry, LogRocket, or AWS CloudWatch
    console.log('Error reported:', { error, context })
  }

  // Recovery action implementations
  function redirectToLogin(): void {
    window.location.href = '/login'
  }

  async function refreshTokenAndRetry(): Promise<void> {
    // This would integrate with the auth service
    console.log('Refreshing token and retrying...')
  }

  function applySuggestedValue(field: string, value: string): void {
    // This would need to be implemented based on the specific form
    console.log(`Applying suggested value "${value}" to field "${field}"`)
  }

  return {
    // State
    globalErrorState: readonly(globalErrorState),
    activeNotifications: readonly(activeNotifications),
    errorConfig,

    // Methods
    handleError,
    categorizeError,
    showErrorNotification,
    dismissNotification,
    clearAllNotifications,
    retryLastOperation,
    clearError,
    isRetryable,
    getUserFriendlyMessage,
    getErrorTitle,
    getSeverityFromError
  }
}
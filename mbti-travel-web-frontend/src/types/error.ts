// Comprehensive error handling types for different error categories

// Base error interface
export interface BaseError {
  message: string
  timestamp: string
  requestId?: string
  userMessage?: string
  technicalDetails?: unknown
}

// Authentication errors
export interface AuthError extends BaseError {
  type: 'auth_error'
  action: 'redirect_to_login' | 'refresh_token' | 'contact_support'
  authCode?: string
  tokenExpired?: boolean
}

// Validation errors
export interface ValidationError extends BaseError {
  type: 'validation_error'
  field: string
  value?: unknown
  suggestedValue?: string
  validationRule?: string
  constraints?: Record<string, unknown>
}

// API errors
export interface ApiError extends BaseError {
  type: 'api_error'
  status: number
  statusText?: string
  retryable: boolean
  retryAfter?: number
  endpoint?: string
  method?: string
  responseBody?: unknown
}

// Network errors
export interface NetworkError extends BaseError {
  type: 'network_error'
  offline: boolean
  connectionType?: string
  timeout?: boolean
  dns?: boolean
}

// Application errors
export interface ApplicationError extends BaseError {
  type: 'application_error'
  component?: string
  action?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  recoverable: boolean
}

// Business logic errors
export interface BusinessError extends BaseError {
  type: 'business_error'
  businessRule: string
  context?: Record<string, unknown>
  suggestedAction?: string
}

// Union type for all error types
export type AppError = 
  | AuthError 
  | ValidationError 
  | ApiError 
  | NetworkError 
  | ApplicationError 
  | BusinessError

// Error handling configuration
export interface ErrorHandlingConfig {
  showTechnicalDetails: boolean
  enableRetry: boolean
  maxRetryAttempts: number
  retryDelay: number
  logErrors: boolean
  reportErrors: boolean
}

// Error context for debugging
export interface ErrorContext {
  userId?: string
  sessionId?: string
  userAgent?: string
  url?: string
  timestamp: string
  stackTrace?: string
  breadcrumbs?: ErrorBreadcrumb[]
  additionalData?: Record<string, unknown>
}

export interface ErrorBreadcrumb {
  timestamp: string
  category: string
  message: string
  level: 'debug' | 'info' | 'warning' | 'error'
  data?: Record<string, unknown>
}

// Error recovery strategies
export interface ErrorRecoveryStrategy {
  type: 'retry' | 'fallback' | 'redirect' | 'ignore' | 'manual'
  config?: {
    maxAttempts?: number
    delay?: number
    fallbackValue?: unknown
    redirectUrl?: string
    userAction?: string
  }
}

// Error reporting
export interface ErrorReport {
  error: AppError
  context: ErrorContext
  recoveryStrategy?: ErrorRecoveryStrategy
  resolved: boolean
  reportedAt: string
}

// Error state management
export interface ErrorState {
  hasError: boolean
  error?: AppError
  isRecovering: boolean
  recoveryAttempts: number
  lastErrorTime?: string
}

// Error boundary props
export interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: {
    componentStack: string
  }
}

// Form validation errors
export interface FormValidationError {
  field: string
  message: string
  type: 'required' | 'format' | 'length' | 'custom'
  value?: unknown
}

export interface FormValidationState {
  isValid: boolean
  errors: FormValidationError[]
  touched: Record<string, boolean>
  isDirty: boolean
}

// HTTP error responses
export interface HttpErrorResponse {
  status: number
  statusText: string
  data?: {
    error?: {
      code: string
      message: string
      details?: unknown
    }
  }
  headers?: Record<string, string>
}

// Error logging levels
export type ErrorLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal'

// Error categories for filtering and handling
export type ErrorCategory = 
  | 'authentication'
  | 'authorization'
  | 'validation'
  | 'network'
  | 'server'
  | 'client'
  | 'business'
  | 'system'
  | 'unknown'

// Error handling utilities
export interface ErrorUtils {
  isRetryable: (error: AppError) => boolean
  getErrorMessage: (error: AppError) => string
  getRecoveryStrategy: (error: AppError) => ErrorRecoveryStrategy
  shouldReport: (error: AppError) => boolean
  categorizeError: (error: unknown) => ErrorCategory
}

// Error notification types
export interface ErrorNotification {
  id: string
  type: 'toast' | 'modal' | 'banner' | 'inline'
  severity: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  actions?: ErrorNotificationAction[]
  autoClose?: boolean
  duration?: number
}

export interface ErrorNotificationAction {
  label: string
  action: () => void | Promise<void>
  style?: 'primary' | 'secondary' | 'danger'
}
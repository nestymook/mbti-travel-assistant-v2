// Main types export file
export * from './api'
export * from './mbti'
export * from './restaurant'
export * from './touristSpot'
export * from './theme'

// Re-export specific types to avoid conflicts
export type {
  BaseError as ErrorBaseError,
  AuthError as ErrorAuthError,
  ValidationError as ErrorValidationError,
  ApiError as ErrorApiError,
  NetworkError as ErrorNetworkError,
  ApplicationError,
  BusinessError,
  AppError,
  ErrorHandlingConfig,
  ErrorContext,
  ErrorBreadcrumb,
  ErrorRecoveryStrategy,
  ErrorReport,
  ErrorState,
  ErrorBoundaryState,
  FormValidationError,
  FormValidationState as ErrorFormValidationState,
  HttpErrorResponse,
  ErrorLevel,
  ErrorCategory,
  ErrorUtils,
  ErrorNotification,
  ErrorNotificationAction
} from './error'

export type {
  ValidationRule,
  ValidationResult as ValidationValidationResult,
  FieldValidationResult,
  MBTIValidationConfig,
  MBTIValidationResult,
  FormField,
  FormValidationSchema,
  FormValidationState as ValidationFormValidationState,
  InputValidationConfig,
  ValidationType,
  ValidationError as ValidationValidationError,
  AsyncValidationResult,
  AsyncValidator,
  ValidationContext,
  ValidatorFunction,
  ValidationPresets,
  RealTimeValidationConfig,
  ValidationStateManager,
  UseValidationConfig,
  ValidationMessages,
  DEFAULT_VALIDATION_MESSAGES
} from './validation'

// Re-export constants without conflicts
export {
  PERSONALITY_CATEGORIES as MBTI_PERSONALITY_CATEGORIES,
  VALID_MBTI_TYPES as MBTI_VALID_TYPES,
  PERSONALITY_CUSTOMIZATIONS,
  PERSONALITY_THEMES,
  API_CONFIG,
  VALIDATION_CONFIG,
  UI_CONFIG,
  ERROR_MESSAGES,
  SESSION_TYPES,
  DAY_NUMBERS,
  getPersonalityCategory,
  getPersonalityCustomization,
  getPersonalityTheme,
  isValidMBTI
} from './constants'

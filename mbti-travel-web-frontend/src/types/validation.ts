import type { MBTIPersonality } from './mbti'

// Validation types for MBTI input and form validation
export interface ValidationRule<T = unknown> {
  name: string
  message: string
  validator: (value: T) => boolean | Promise<boolean>
  params?: Record<string, unknown>
}

export interface ValidationResult {
  isValid: boolean
  message?: string
  suggestedValue?: string
  errorCode?: string
  field?: string
}

export interface FieldValidationResult extends ValidationResult {
  field: string
  value: unknown
  rules: string[]
}

// MBTI-specific validation
export interface MBTIValidationConfig {
  required: boolean
  minLength: number
  maxLength: number
  allowedCharacters: RegExp
  validTypes: MBTIPersonality[]
  caseSensitive: boolean
  autoFormat: boolean
}

export interface MBTIValidationResult extends ValidationResult {
  formattedValue?: string
  detectedType?: MBTIPersonality
  suggestions?: MBTIPersonality[]
  confidence?: number
}

// Form validation
export interface FormField<T = unknown> {
  name: string
  value: T
  rules: ValidationRule<T>[]
  required: boolean
  touched: boolean
  dirty: boolean
  error?: string
}

export interface FormValidationSchema {
  [fieldName: string]: ValidationRule[]
}

export interface FormValidationState {
  isValid: boolean
  isValidating: boolean
  errors: Record<string, string>
  touched: Record<string, boolean>
  dirty: Record<string, boolean>
  fields: Record<string, FormField>
}

// Input validation utilities
export interface InputValidationConfig {
  debounceMs: number
  validateOnChange: boolean
  validateOnBlur: boolean
  showErrorsImmediately: boolean
  clearErrorsOnFocus: boolean
}

// Validation error types
export type ValidationType = 
  | 'required'
  | 'minLength'
  | 'maxLength'
  | 'pattern'
  | 'email'
  | 'url'
  | 'number'
  | 'integer'
  | 'positive'
  | 'negative'
  | 'range'
  | 'custom'
  | 'mbti'

export interface ValidationError {
  type: ValidationType
  field: string
  message: string
  value?: unknown
  params?: Record<string, unknown>
}

// Async validation
export interface AsyncValidationResult {
  isValid: boolean
  message?: string
  isLoading: boolean
  error?: Error
}

export interface AsyncValidator<T = unknown> {
  name: string
  validator: (value: T) => Promise<ValidationResult>
  debounceMs?: number
  dependencies?: string[]
}

// Validation context
export interface ValidationContext {
  formData: Record<string, unknown>
  fieldName: string
  fieldValue: unknown
  allFields: Record<string, FormField>
  isSubmitting: boolean
}

// Custom validation functions
export type ValidatorFunction<T = unknown> = (
  value: T,
  context?: ValidationContext
) => boolean | string | Promise<boolean | string>

// Validation presets
export interface ValidationPresets {
  mbtiPersonality: ValidationRule<string>[]
  email: ValidationRule<string>[]
  password: ValidationRule<string>[]
  phoneNumber: ValidationRule<string>[]
  url: ValidationRule<string>[]
  required: ValidationRule<unknown>[]
}

// Real-time validation
export interface RealTimeValidationConfig {
  enabled: boolean
  debounceMs: number
  validateOnMount: boolean
  validateOnChange: boolean
  validateOnBlur: boolean
  showSuccessState: boolean
}

// Validation state management
export interface ValidationStateManager {
  addField: (name: string, field: FormField) => void
  removeField: (name: string) => void
  updateField: (name: string, updates: Partial<FormField>) => void
  validateField: (name: string) => Promise<ValidationResult>
  validateAll: () => Promise<boolean>
  reset: () => void
  setTouched: (name: string, touched: boolean) => void
  setDirty: (name: string, dirty: boolean) => void
}

// Validation hooks configuration
export interface UseValidationConfig {
  schema: FormValidationSchema
  initialValues?: Record<string, unknown>
  validateOnMount?: boolean
  validateOnChange?: boolean
  validateOnBlur?: boolean
  debounceMs?: number
}

// Validation messages
export interface ValidationMessages {
  [key: string]: {
    [validationType in ValidationType]?: string
  }
}

// Default validation messages
export const DEFAULT_VALIDATION_MESSAGES: ValidationMessages = {
  mbtiPersonality: {
    required: 'MBTI personality type is required',
    pattern: 'Please enter a valid 4-letter MBTI code (e.g., ENFP)',
    mbti: 'Please enter a valid MBTI personality type'
  },
  email: {
    required: 'Email address is required',
    email: 'Please enter a valid email address'
  },
  password: {
    required: 'Password is required',
    minLength: 'Password must be at least {min} characters long'
  }
}
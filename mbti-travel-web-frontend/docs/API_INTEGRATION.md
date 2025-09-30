# API Integration Guide

This document provides comprehensive guidance for integrating with the MBTI Travel Assistant MCP backend service, including authentication, error handling, and best practices.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Service](#api-service)
- [Error Handling](#error-handling)
- [Request/Response Examples](#requestresponse-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The MBTI Travel Web Frontend integrates with the MBTI Travel Assistant MCP (Model Context Protocol) backend service to generate personalized travel itineraries. The integration includes:

- **JWT Authentication**: Secure authentication using AWS Cognito
- **RESTful API**: HTTP-based communication with the MCP endpoint
- **Error Handling**: Comprehensive error management and user feedback
- **Request Optimization**: Debouncing, caching, and retry logic

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue Frontend  │    │   API Gateway   │    │  MCP Backend    │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │ Auth      │  │───▶│  │ Cognito   │  │───▶│  │ MBTI      │  │
│  │ Service   │  │    │  │ Validator │  │    │  │ Assistant │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │ API       │  │───▶│  │ Rate      │  │───▶│  │ Knowledge │  │
│  │ Service   │  │    │  │ Limiting  │  │    │  │ Base      │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Authentication

### AWS Cognito Integration

The application uses AWS Cognito for user authentication and JWT token management.

#### Configuration

```typescript
// config/auth.ts
export interface CognitoConfig {
  userPoolId: string
  clientId: string
  domain: string
  region: string
}

export const cognitoConfig: CognitoConfig = {
  userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  clientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
  domain: import.meta.env.VITE_COGNITO_DOMAIN,
  region: import.meta.env.VITE_AWS_REGION || 'us-east-1'
}
```

#### AuthService Implementation

```typescript
// services/authService.ts
import { CognitoAuth } from '@aws-amplify/auth'
import type { CognitoConfig } from '@/config/auth'

export class AuthService {
  private cognitoAuth: CognitoAuth
  private tokenRefreshTimer?: NodeJS.Timeout

  constructor(config: CognitoConfig) {
    this.cognitoAuth = new CognitoAuth({
      userPoolId: config.userPoolId,
      userPoolWebClientId: config.clientId,
      authenticationFlowType: 'USER_SRP_AUTH'
    })
  }

  /**
   * Get current user's JWT token
   * @returns Promise<string> JWT token
   * @throws {AuthError} When authentication fails
   */
  async getCurrentToken(): Promise<string> {
    try {
      const session = await this.cognitoAuth.currentSession()
      const token = session.getIdToken().getJwtToken()
      
      // Schedule token refresh
      this.scheduleTokenRefresh(session.getIdToken().getExpiration())
      
      return token
    } catch (error) {
      throw new AuthError('Failed to get current token', error)
    }
  }

  /**
   * Refresh JWT token
   * @returns Promise<string> New JWT token
   * @throws {AuthError} When token refresh fails
   */
  async refreshToken(): Promise<string> {
    try {
      const session = await this.cognitoAuth.currentSession()
      const refreshToken = session.getRefreshToken()
      
      const newSession = await this.cognitoAuth.refreshSession(refreshToken)
      const newToken = newSession.getIdToken().getJwtToken()
      
      this.scheduleTokenRefresh(newSession.getIdToken().getExpiration())
      
      return newToken
    } catch (error) {
      throw new AuthError('Failed to refresh token', error)
    }
  }

  /**
   * Check if user is authenticated
   * @returns Promise<boolean> Authentication status
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getCurrentToken()
      return true
    } catch {
      return false
    }
  }

  /**
   * Sign out user
   */
  async signOut(): Promise<void> {
    try {
      await this.cognitoAuth.signOut()
      if (this.tokenRefreshTimer) {
        clearTimeout(this.tokenRefreshTimer)
      }
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  /**
   * Redirect to Cognito login page
   */
  redirectToLogin(): void {
    const loginUrl = `${cognitoConfig.domain}/login?client_id=${cognitoConfig.clientId}&response_type=code&scope=email+openid+profile&redirect_uri=${encodeURIComponent(window.location.origin)}`
    window.location.href = loginUrl
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(expirationTime: number): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer)
    }

    // Refresh token 5 minutes before expiration
    const refreshTime = (expirationTime * 1000) - Date.now() - (5 * 60 * 1000)
    
    if (refreshTime > 0) {
      this.tokenRefreshTimer = setTimeout(async () => {
        try {
          await this.refreshToken()
        } catch (error) {
          console.error('Automatic token refresh failed:', error)
          this.redirectToLogin()
        }
      }, refreshTime)
    }
  }
}

// Error classes
export class AuthError extends Error {
  constructor(message: string, public originalError?: any) {
    super(message)
    this.name = 'AuthError'
  }
}

// Singleton instance
export const authService = new AuthService(cognitoConfig)
```

#### Authentication Store

```typescript
// stores/authStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const currentToken = ref<string | null>(null)
  const user = ref<any>(null)
  const isLoading = ref(false)

  const isLoggedIn = computed(() => isAuthenticated.value && !!currentToken.value)

  /**
   * Initialize authentication state
   */
  const initialize = async () => {
    isLoading.value = true
    try {
      const authenticated = await authService.isAuthenticated()
      if (authenticated) {
        currentToken.value = await authService.getCurrentToken()
        isAuthenticated.value = true
      }
    } catch (error) {
      console.error('Auth initialization failed:', error)
      isAuthenticated.value = false
      currentToken.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get current JWT token
   */
  const getToken = async (): Promise<string> => {
    if (!currentToken.value) {
      currentToken.value = await authService.getCurrentToken()
    }
    return currentToken.value
  }

  /**
   * Sign out user
   */
  const signOut = async () => {
    await authService.signOut()
    isAuthenticated.value = false
    currentToken.value = null
    user.value = null
  }

  /**
   * Redirect to login
   */
  const redirectToLogin = () => {
    authService.redirectToLogin()
  }

  return {
    isAuthenticated: readonly(isAuthenticated),
    currentToken: readonly(currentToken),
    user: readonly(user),
    isLoading: readonly(isLoading),
    isLoggedIn,
    initialize,
    getToken,
    signOut,
    redirectToLogin
  }
})
```

## API Service

### Core API Service

```typescript
// services/apiService.ts
import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import type { 
  ItineraryRequest, 
  ItineraryResponse, 
  ApiError, 
  NetworkError 
} from '@/types/api'

export class ApiService {
  private client: AxiosInstance
  private baseURL: string
  private timeout: number

  constructor(baseURL: string, timeout: number = 100000) {
    this.baseURL = baseURL
    this.timeout = timeout
    
    this.client = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  /**
   * Generate personalized itinerary
   * @param request Itinerary request parameters
   * @returns Promise<ItineraryResponse> Generated itinerary
   * @throws {ApiError} When API request fails
   * @throws {NetworkError} When network is unavailable
   */
  async generateItinerary(request: ItineraryRequest): Promise<ItineraryResponse> {
    try {
      const response = await this.client.post<ItineraryResponse>(
        '/generate-itinerary',
        request,
        {
          timeout: this.timeout // Extended timeout for itinerary generation
        }
      )

      return response.data
    } catch (error) {
      throw this.handleError(error as AxiosError)
    }
  }

  /**
   * Test API connectivity
   * @returns Promise<boolean> Connection status
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.client.get('/health')
      return true
    } catch {
      return false
    }
  }

  /**
   * Set authentication token
   * @param token JWT token
   */
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  /**
   * Clear authentication token
   */
  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization']
  }

  /**
   * Setup request/response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const authStore = useAuthStore()
        
        try {
          const token = await authStore.getToken()
          config.headers.Authorization = `Bearer ${token}`
        } catch (error) {
          console.error('Failed to get auth token:', error)
          authStore.redirectToLogin()
          throw error
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const authStore = useAuthStore()

        if (error.response?.status === 401) {
          // Token expired or invalid
          try {
            const newToken = await authService.refreshToken()
            authStore.currentToken = newToken
            
            // Retry original request
            if (error.config) {
              error.config.headers.Authorization = `Bearer ${newToken}`
              return this.client.request(error.config)
            }
          } catch (refreshError) {
            authStore.redirectToLogin()
            throw new AuthError('Authentication failed', refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  /**
   * Handle API errors
   * @param error Axios error
   * @returns ApiError or NetworkError
   */
  private handleError(error: AxiosError): ApiError | NetworkError {
    if (!error.response) {
      // Network error
      return new NetworkError(
        'Network connection failed. Please check your internet connection.',
        !navigator.onLine
      )
    }

    const status = error.response.status
    const data = error.response.data as any

    // API error
    return new ApiError(
      data?.message || `API request failed with status ${status}`,
      status,
      this.isRetryableError(status),
      data?.retryAfter
    )
  }

  /**
   * Check if error is retryable
   * @param status HTTP status code
   * @returns boolean
   */
  private isRetryableError(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status)
  }
}

// Error classes
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public retryable: boolean = false,
    public retryAfter?: number
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string, public offline: boolean = false) {
    super(message)
    this.name = 'NetworkError'
  }
}

// Singleton instance
export const apiService = new ApiService(
  import.meta.env.VITE_API_BASE_URL,
  parseInt(import.meta.env.VITE_API_TIMEOUT) || 100000
)
```

### Request/Response Types

```typescript
// types/api.ts
export interface ItineraryRequest {
  /** MBTI personality type */
  mbti_personality: string
  /** Optional preferences */
  preferences?: {
    budget?: 'low' | 'medium' | 'high'
    interests?: string[]
    dietary_restrictions?: string[]
    mobility_requirements?: string[]
  }
  /** Request metadata */
  metadata?: {
    user_id?: string
    session_id?: string
    timestamp?: string
  }
}

export interface ItineraryResponse {
  /** Main 3-day itinerary */
  main_itinerary: MainItinerary
  /** Alternative tourist spot candidates */
  candidate_tourist_spots: CandidateTouristSpots
  /** Alternative restaurant candidates */
  candidate_restaurants: CandidateRestaurants
  /** Response metadata */
  metadata: ItineraryResponseMetadata
  /** Error information if any */
  error?: ItineraryErrorInfo
}

export interface MainItinerary {
  day_1: DayItinerary
  day_2: DayItinerary
  day_3: DayItinerary
}

export interface DayItinerary {
  morning_session: TouristSpot
  afternoon_session: TouristSpot
  night_session: TouristSpot
  breakfast: Restaurant
  lunch: Restaurant
  dinner: Restaurant
}

export interface TouristSpot {
  tourist_spot: string
  mbti: string
  description?: string
  remarks?: string
  address: string
  district: string
  area: string
  operating_hours_mon_fri: string
  operating_hours_sat_sun: string
  operating_hours_public_holiday: string
  full_day: boolean
}

export interface Restaurant {
  id: string
  name: string
  address: string
  mealType: string[]
  sentiment: {
    likes: number
    dislikes: number
    neutral: number
  }
  locationCategory: string
  district: string
  priceRange: string
  operatingHours: {
    'Mon - Fri': string
    'Sat - Sun': string
    'Public Holiday': string
  }
}

export interface CandidateTouristSpots {
  morning_session: TouristSpot[]
  afternoon_session: TouristSpot[]
  night_session: TouristSpot[]
}

export interface CandidateRestaurants {
  breakfast: Restaurant[]
  lunch: Restaurant[]
  dinner: Restaurant[]
}

export interface ItineraryResponseMetadata {
  request_id: string
  processing_time_ms: number
  model_used: string
  personality_analysis: {
    primary_traits: string[]
    customization_applied: string[]
  }
}

export interface ItineraryErrorInfo {
  code: string
  message: string
  details?: Record<string, any>
}
```

## Error Handling

### Error Handler Service

```typescript
// services/errorHandler.ts
import { ApiError, NetworkError, AuthError } from '@/services/apiService'

export class ErrorHandler {
  /**
   * Handle global application errors
   */
  static handleGlobalError(error: Error, instance?: any, info?: string): void {
    console.error('Global error:', error, info)
    
    if (error instanceof ApiError) {
      this.handleApiError(error)
    } else if (error instanceof NetworkError) {
      this.handleNetworkError(error)
    } else if (error instanceof AuthError) {
      this.handleAuthError(error)
    } else {
      this.handleUnknownError(error)
    }
  }

  /**
   * Handle API errors
   */
  static handleApiError(error: ApiError): void {
    const message = this.getApiErrorMessage(error)
    
    // Show user-friendly error message
    this.showErrorNotification(message, {
      type: 'api',
      retryable: error.retryable,
      retryAfter: error.retryAfter
    })
  }

  /**
   * Handle network errors
   */
  static handleNetworkError(error: NetworkError): void {
    const message = error.offline 
      ? 'You appear to be offline. Please check your internet connection.'
      : 'Network connection failed. Please try again.'
    
    this.showErrorNotification(message, {
      type: 'network',
      retryable: true
    })
  }

  /**
   * Handle authentication errors
   */
  static handleAuthError(error: AuthError): void {
    const message = 'Authentication failed. Please sign in again.'
    
    this.showErrorNotification(message, {
      type: 'auth',
      retryable: false
    })
    
    // Redirect to login after delay
    setTimeout(() => {
      authService.redirectToLogin()
    }, 2000)
  }

  /**
   * Handle unknown errors
   */
  static handleUnknownError(error: Error): void {
    const message = 'An unexpected error occurred. Please try again.'
    
    this.showErrorNotification(message, {
      type: 'unknown',
      retryable: true
    })
  }

  /**
   * Get user-friendly API error message
   */
  private static getApiErrorMessage(error: ApiError): string {
    switch (error.status) {
      case 400:
        return 'Invalid request. Please check your input and try again.'
      case 401:
        return 'Authentication required. Please sign in.'
      case 403:
        return 'Access denied. You do not have permission to perform this action.'
      case 404:
        return 'The requested resource was not found.'
      case 408:
        return 'Request timeout. The server took too long to respond.'
      case 429:
        return 'Too many requests. Please wait a moment and try again.'
      case 500:
        return 'Server error. Please try again later.'
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.'
      case 503:
        return 'Service unavailable. Please try again later.'
      case 504:
        return 'Gateway timeout. The server took too long to respond.'
      default:
        return error.message || 'An API error occurred.'
    }
  }

  /**
   * Show error notification to user
   */
  private static showErrorNotification(message: string, options: {
    type: string
    retryable: boolean
    retryAfter?: number
  }): void {
    // Implementation depends on your notification system
    // This could use a toast library, modal, or custom component
    console.error(`[${options.type.toUpperCase()}] ${message}`)
    
    // Example: Emit event for error component to handle
    window.dispatchEvent(new CustomEvent('app-error', {
      detail: { message, ...options }
    }))
  }
}
```

### Error Composable

```typescript
// composables/useErrorHandler.ts
import { ref } from 'vue'
import { ErrorHandler } from '@/services/errorHandler'

export function useErrorHandler() {
  const error = ref<Error | null>(null)
  const isRetryable = ref(false)
  const retryAfter = ref<number | undefined>()

  const handleError = (err: Error, context?: string) => {
    error.value = err
    
    if (err instanceof ApiError) {
      isRetryable.value = err.retryable
      retryAfter.value = err.retryAfter
    } else if (err instanceof NetworkError) {
      isRetryable.value = true
    } else {
      isRetryable.value = false
    }

    ErrorHandler.handleGlobalError(err, null, context)
  }

  const clearError = () => {
    error.value = null
    isRetryable.value = false
    retryAfter.value = undefined
  }

  const retry = async (retryFn: () => Promise<void>) => {
    if (!isRetryable.value) return

    try {
      clearError()
      await retryFn()
    } catch (err) {
      handleError(err as Error, 'retry')
    }
  }

  return {
    error: readonly(error),
    isRetryable: readonly(isRetryable),
    retryAfter: readonly(retryAfter),
    handleError,
    clearError,
    retry
  }
}
```

## Request/Response Examples

### Generate Itinerary Request

```typescript
// Example: Generate itinerary for ENFP personality
const request: ItineraryRequest = {
  mbti_personality: 'ENFP',
  preferences: {
    budget: 'medium',
    interests: ['culture', 'food', 'nightlife'],
    dietary_restrictions: ['vegetarian'],
    mobility_requirements: []
  },
  metadata: {
    user_id: 'user-123',
    session_id: 'session-456',
    timestamp: new Date().toISOString()
  }
}

try {
  const response = await apiService.generateItinerary(request)
  console.log('Generated itinerary:', response.main_itinerary)
  console.log('Processing time:', response.metadata.processing_time_ms, 'ms')
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message, 'Status:', error.status)
  } else if (error instanceof NetworkError) {
    console.error('Network Error:', error.message, 'Offline:', error.offline)
  }
}
```

### Example Response

```json
{
  "main_itinerary": {
    "day_1": {
      "morning_session": {
        "tourist_spot": "Hong Kong Museum of Art",
        "mbti": "ENFP",
        "description": "A vibrant cultural hub perfect for creative exploration",
        "address": "10 Salisbury Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "area": "Kowloon",
        "operating_hours_mon_fri": "10:00-18:00",
        "operating_hours_sat_sun": "10:00-19:00",
        "operating_hours_public_holiday": "10:00-19:00",
        "full_day": false
      },
      "breakfast": {
        "id": "rest_001",
        "name": "Café Corridor",
        "address": "123 Nathan Road, Tsim Sha Tsui",
        "mealType": ["breakfast", "brunch"],
        "sentiment": {
          "likes": 85,
          "dislikes": 10,
          "neutral": 5
        },
        "locationCategory": "Café",
        "district": "Tsim Sha Tsui",
        "priceRange": "$$",
        "operatingHours": {
          "Mon - Fri": "07:00-15:00",
          "Sat - Sun": "08:00-16:00",
          "Public Holiday": "08:00-16:00"
        }
      }
    }
  },
  "candidate_tourist_spots": {
    "morning_session": [
      {
        "tourist_spot": "Hong Kong Space Museum",
        "mbti": "ENFP",
        "description": "Interactive exhibits for curious minds"
      }
    ]
  },
  "candidate_restaurants": {
    "breakfast": [
      {
        "id": "rest_002",
        "name": "Morning Glory Café",
        "address": "456 Canton Road, Tsim Sha Tsui"
      }
    ]
  },
  "metadata": {
    "request_id": "req_789",
    "processing_time_ms": 15420,
    "model_used": "claude-3-sonnet",
    "personality_analysis": {
      "primary_traits": ["creative", "social", "flexible"],
      "customization_applied": ["colorful_theme", "image_placeholders"]
    }
  }
}
```

## Best Practices

### Request Optimization

1. **Debounce User Input**
```typescript
// composables/useDebouncedApi.ts
import { ref, watch } from 'vue'
import { debounce } from 'lodash-es'

export function useDebouncedApi<T>(
  apiCall: () => Promise<T>,
  delay: number = 300
) {
  const isLoading = ref(false)
  const data = ref<T | null>(null)
  const error = ref<Error | null>(null)

  const debouncedCall = debounce(async () => {
    isLoading.value = true
    error.value = null
    
    try {
      data.value = await apiCall()
    } catch (err) {
      error.value = err as Error
    } finally {
      isLoading.value = false
    }
  }, delay)

  return {
    data: readonly(data),
    isLoading: readonly(isLoading),
    error: readonly(error),
    execute: debouncedCall
  }
}
```

2. **Request Caching**
```typescript
// services/cacheService.ts
export class CacheService {
  private cache = new Map<string, { data: any, timestamp: number }>()
  private ttl: number

  constructor(ttlMinutes: number = 10) {
    this.ttl = ttlMinutes * 60 * 1000
  }

  get<T>(key: string): T | null {
    const cached = this.cache.get(key)
    if (!cached) return null

    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key)
      return null
    }

    return cached.data
  }

  set<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    })
  }

  clear(): void {
    this.cache.clear()
  }
}
```

3. **Retry Logic**
```typescript
// utils/retry.ts
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      
      if (attempt === maxRetries) break
      
      // Exponential backoff
      const delay = baseDelay * Math.pow(2, attempt)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError!
}
```

### Security Best Practices

1. **Token Security**
```typescript
// utils/tokenSecurity.ts
export class TokenSecurity {
  /**
   * Validate JWT token structure
   */
  static validateTokenStructure(token: string): boolean {
    const parts = token.split('.')
    return parts.length === 3
  }

  /**
   * Check if token is expired
   */
  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp * 1000 < Date.now()
    } catch {
      return true
    }
  }

  /**
   * Get token expiration time
   */
  static getTokenExpiration(token: string): number | null {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp * 1000
    } catch {
      return null
    }
  }
}
```

2. **Request Sanitization**
```typescript
// utils/sanitization.ts
export class RequestSanitizer {
  /**
   * Sanitize MBTI input
   */
  static sanitizeMBTI(input: string): string {
    return input
      .toUpperCase()
      .replace(/[^A-Z]/g, '')
      .slice(0, 4)
  }

  /**
   * Sanitize user preferences
   */
  static sanitizePreferences(preferences: any): any {
    const allowedBudgets = ['low', 'medium', 'high']
    const allowedInterests = [
      'culture', 'food', 'nightlife', 'nature', 
      'shopping', 'history', 'art', 'sports'
    ]

    return {
      budget: allowedBudgets.includes(preferences.budget) 
        ? preferences.budget 
        : 'medium',
      interests: Array.isArray(preferences.interests)
        ? preferences.interests.filter(i => allowedInterests.includes(i))
        : [],
      dietary_restrictions: Array.isArray(preferences.dietary_restrictions)
        ? preferences.dietary_restrictions.slice(0, 5)
        : [],
      mobility_requirements: Array.isArray(preferences.mobility_requirements)
        ? preferences.mobility_requirements.slice(0, 3)
        : []
    }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Problem**: 401 Unauthorized errors
**Solution**:
```typescript
// Debug authentication
const debugAuth = async () => {
  try {
    const token = await authService.getCurrentToken()
    console.log('Token valid:', !TokenSecurity.isTokenExpired(token))
    console.log('Token expires:', new Date(TokenSecurity.getTokenExpiration(token)!))
  } catch (error) {
    console.error('Auth debug failed:', error)
  }
}
```

#### 2. Network Timeouts

**Problem**: Request timeouts during itinerary generation
**Solution**:
```typescript
// Increase timeout for specific requests
const generateWithExtendedTimeout = async (request: ItineraryRequest) => {
  const extendedClient = axios.create({
    baseURL: apiService.baseURL,
    timeout: 180000 // 3 minutes
  })

  return await extendedClient.post('/generate-itinerary', request)
}
```

#### 3. CORS Issues

**Problem**: Cross-origin request blocked
**Solution**: Ensure backend includes proper CORS headers:
```typescript
// Expected CORS headers from backend
const expectedHeaders = {
  'Access-Control-Allow-Origin': window.location.origin,
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Allow-Credentials': 'true'
}
```

#### 4. Rate Limiting

**Problem**: 429 Too Many Requests
**Solution**:
```typescript
// Handle rate limiting with exponential backoff
const handleRateLimit = async (error: ApiError) => {
  if (error.status === 429) {
    const retryAfter = error.retryAfter || 60 // seconds
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000))
    // Retry request
  }
}
```

### Debug Tools

```typescript
// Debug API requests
const debugApiRequest = (config: AxiosRequestConfig) => {
  console.group('API Request Debug')
  console.log('URL:', config.url)
  console.log('Method:', config.method)
  console.log('Headers:', config.headers)
  console.log('Data:', config.data)
  console.groupEnd()
}

// Debug API responses
const debugApiResponse = (response: any) => {
  console.group('API Response Debug')
  console.log('Status:', response.status)
  console.log('Headers:', response.headers)
  console.log('Data:', response.data)
  console.log('Processing time:', response.data?.metadata?.processing_time_ms, 'ms')
  console.groupEnd()
}
```

---

This comprehensive API integration guide provides all the necessary information for successfully integrating with the MBTI Travel Assistant MCP backend service, including robust authentication, error handling, and best practices for production use.
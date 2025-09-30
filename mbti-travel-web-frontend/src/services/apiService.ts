// API service for MBTI travel assistant integration
import axios, { type AxiosInstance, type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import type { 
  ItineraryRequest, 
  ItineraryResponse, 
  NetworkError, 
  AuthError,
  ApiAppError,
  ApiConfig
} from '@/types'
import { AuthService } from './authService'

export class ApiService {
  private static instance: ApiService
  private client: AxiosInstance
  private authService: AuthService
  private retryAttempts: number = 3
  private retryDelay: number = 1000

  private constructor() {
    this.authService = AuthService.getInstance()
    
    const config: ApiConfig = {
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
      timeout: 120000, // 2 minutes for itinerary generation
      retryAttempts: 3,
      retryDelay: 1000
    }

    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })

    this.retryAttempts = config.retryAttempts
    this.retryDelay = config.retryDelay
    this.setupInterceptors()
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService()
    }
    return ApiService.instance
  }

  private setupInterceptors(): void {
    // Request interceptor for adding auth token and request logging
    this.client.interceptors.request.use(
      (config) => {
        // Add JWT token to request headers
        const token = this.authService.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()

        // Log request in development
        if (import.meta.env.DEV) {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
            headers: config.headers,
            data: config.data
          })
        }

        return config
      },
      (error) => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling and response logging
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response in development
        if (import.meta.env.DEV) {
          console.log(`[API Response] ${response.status} ${response.config.url}`, {
            data: response.data,
            headers: response.headers
          })
        }

        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        // Handle authentication errors
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            // Attempt to refresh token
            await this.authService.refreshToken()
            
            // Retry original request with new token
            const token = this.authService.getToken()
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.authService.redirectToLogin()
            return Promise.reject(this.createAuthError('Token refresh failed', 'redirect_to_login'))
          }
        }

        // Handle other errors
        const apiError = this.handleApiError(error)
        
        // Log error in development
        if (import.meta.env.DEV) {
          console.error('[API Response Error]', {
            error: apiError,
            originalError: error,
            config: error.config
          })
        }

        return Promise.reject(apiError)
      }
    )
  }

  /**
   * Generate itinerary based on MBTI personality type
   */
  async generateItinerary(request: ItineraryRequest): Promise<ItineraryResponse> {
    try {
      // Validate request
      this.validateItineraryRequest(request)

      // Make API call with retry logic
      const response = await this.makeRequestWithRetry<ItineraryResponse>({
        method: 'POST',
        url: '/api/itinerary/generate',
        data: request,
        timeout: 120000, // 2 minutes for itinerary generation
      })

      // Validate response structure
      this.validateItineraryResponse(response.data)

      return response.data
    } catch (error) {
      console.error('Itinerary generation failed:', error)
      
      // Re-throw validation errors directly
      if (error instanceof Error && (
        error.message.includes('MBTI personality is required') ||
        error.message.includes('Invalid MBTI personality type') ||
        error.message.includes('Invalid response')
      )) {
        throw error
      }
      
      throw new Error('Failed to generate itinerary. Please try again.')
    }
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string): void {
    // Use AuthService to manage token
    this.authService.setToken({
      accessToken: token,
      tokenType: 'Bearer',
      expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 hours default
    })
  }

  /**
   * Get current authentication token
   */
  getAuthToken(): string | null {
    return this.authService.getToken()
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.authService.isAuthenticated()
  }

  /**
   * Test API connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/health')
      return response.status === 200
    } catch (error) {
      console.error('API connection test failed:', error)
      return false
    }
  }

  /**
   * Make HTTP request with retry logic
   */
  private async makeRequestWithRetry<T>(config: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    let lastError: AxiosError | null = null

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        return await this.client.request<T>(config)
      } catch (error) {
        lastError = error as AxiosError
        
        // Don't retry on authentication errors or client errors (4xx)
        if (this.isNonRetryableError(lastError)) {
          throw lastError
        }

        // Don't retry on last attempt
        if (attempt === this.retryAttempts) {
          throw lastError
        }

        // Wait before retrying with exponential backoff
        const delay = this.retryDelay * Math.pow(2, attempt - 1)
        await this.sleep(delay)

        console.warn(`[API Retry] Attempt ${attempt + 1}/${this.retryAttempts} after ${delay}ms delay`)
      }
    }

    throw lastError
  }

  /**
   * Check if error should not be retried
   */
  private isNonRetryableError(error: AxiosError): boolean {
    if (!error.response) {
      return false // Network errors are retryable
    }

    const status = error.response.status
    
    // Don't retry client errors (4xx) except 408 (timeout) and 429 (rate limit)
    if (status >= 400 && status < 500 && status !== 408 && status !== 429) {
      return true
    }

    return false
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Validate itinerary request
   */
  private validateItineraryRequest(request: ItineraryRequest): void {
    if (!request.mbtiPersonality) {
      throw new Error('MBTI personality is required')
    }

    const validMBTITypes = [
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP',
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]

    if (!validMBTITypes.includes(request.mbtiPersonality)) {
      throw new Error(`Invalid MBTI personality type: ${request.mbtiPersonality}`)
    }
  }

  /**
   * Validate itinerary response structure
   */
  private validateItineraryResponse(response: ItineraryResponse): void {
    if (!response.main_itinerary) {
      throw new Error('Invalid response: missing main_itinerary')
    }

    if (!response.candidate_tourist_spots) {
      throw new Error('Invalid response: missing candidate_tourist_spots')
    }

    if (!response.candidate_restaurants) {
      throw new Error('Invalid response: missing candidate_restaurants')
    }

    if (!response.metadata) {
      throw new Error('Invalid response: missing metadata')
    }
  }

  /**
   * Handle API errors and convert to standardized error types
   */
  private handleApiError(error: AxiosError): ApiAppError {
    const requestId = error.config?.headers?.['X-Request-ID'] as string

    // Network errors (no response)
    if (!error.response) {
      return this.createNetworkError(error.message, !navigator.onLine, requestId)
    }

    const status = error.response.status
    const data = error.response.data as any

    // Authentication errors
    if (status === 401) {
      return this.createAuthError(
        data?.message || 'Authentication failed',
        'redirect_to_login',
        requestId
      )
    }

    if (status === 403) {
      return this.createAuthError(
        data?.message || 'Access forbidden',
        'contact_support',
        requestId
      )
    }

    // Validation errors
    if (status === 400) {
      return {
        type: 'validation_error',
        field: data?.field || 'unknown',
        message: data?.message || 'Invalid request data',
        suggestedValue: data?.suggestedValue,
        timestamp: new Date().toISOString(),
        requestId
      }
    }

    // API errors
    const isRetryable = this.isRetryableStatus(status)
    const retryAfter = this.getRetryAfter(error.response.headers)

    return {
      type: 'api_error',
      status,
      message: data?.message || error.message || `HTTP ${status} error`,
      retryable: isRetryable,
      retryAfter,
      timestamp: new Date().toISOString(),
      requestId
    }
  }

  /**
   * Create authentication error
   */
  private createAuthError(
    message: string, 
    action: AuthError['action'], 
    requestId?: string
  ): AuthError {
    return {
      type: 'auth_error',
      message,
      action,
      timestamp: new Date().toISOString(),
      requestId
    }
  }

  /**
   * Create network error
   */
  private createNetworkError(
    message: string, 
    offline: boolean, 
    requestId?: string
  ): NetworkError {
    return {
      type: 'network_error',
      message: offline ? 'No internet connection' : message,
      offline,
      timestamp: new Date().toISOString(),
      requestId
    }
  }

  /**
   * Check if HTTP status is retryable
   */
  private isRetryableStatus(status: number): boolean {
    // Retry on server errors (5xx) and specific client errors
    return status >= 500 || status === 408 || status === 429
  }

  /**
   * Extract retry-after header value
   */
  private getRetryAfter(headers: any): number | undefined {
    const retryAfter = headers?.['retry-after']
    if (retryAfter) {
      const seconds = parseInt(retryAfter, 10)
      return isNaN(seconds) ? undefined : seconds
    }
    return undefined
  }

  /**
   * Generate unique request ID for tracking
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}

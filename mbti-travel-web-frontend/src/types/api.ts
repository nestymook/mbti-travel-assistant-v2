// Import types from other files
import type { TouristSpot } from './touristSpot'
import type { Restaurant } from './restaurant'
import type { MBTIPersonality } from './mbti'

// API-related types
export interface ApiResponse<T = unknown> {
  data: T
  status: number
  message?: string
  timestamp?: string
}

// Error handling types for different error categories
export interface BaseError {
  message: string
  timestamp?: string
  requestId?: string
}

export interface AuthError extends BaseError {
  type: 'auth_error'
  action: 'redirect_to_login' | 'refresh_token' | 'contact_support'
}

export interface ValidationError extends BaseError {
  type: 'validation_error'
  field: string
  suggestedValue?: string
}

export interface ApiError extends BaseError {
  type: 'api_error'
  status: number
  retryable: boolean
  retryAfter?: number
}

export interface NetworkError extends BaseError {
  type: 'network_error'
  offline: boolean
}

// Union type for all error types
export type ApiAppError = AuthError | ValidationError | ApiError | NetworkError

// API request/response interfaces
export interface ItineraryRequest {
  mbtiPersonality: MBTIPersonality
  userId?: string
  preferences?: UserPreferences
}

export interface UserPreferences {
  dietaryRestrictions?: string[]
  budgetRange?: 'low' | 'medium' | 'high'
  mobilityRequirements?: string[]
  includeRestaurants?: boolean
  includeTouristSpots?: boolean
  days?: number
}

export interface ItineraryResponse {
  main_itinerary: MainItinerary
  candidate_tourist_spots: CandidateTouristSpots
  candidate_restaurants: CandidateRestaurants
  metadata: ItineraryResponseMetadata
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

export interface CandidateTouristSpots {
  [sessionKey: string]: TouristSpot[]
}

export interface CandidateRestaurants {
  [sessionKey: string]: Restaurant[]
}

export interface ItineraryResponseMetadata {
  generatedAt: string
  mbtiPersonality: MBTIPersonality
  version: string
  processingTime?: number
  totalCandidates?: {
    touristSpots: number
    restaurants: number
  }
}

export interface ItineraryErrorInfo {
  code: string
  message: string
  details?: unknown
  recoverable?: boolean
}

// Authentication related types
export interface UserContext {
  id: string
  email?: string
  name?: string
  preferences?: UserPreferences
  lastLogin?: string
}

export interface AuthToken {
  accessToken: string
  refreshToken?: string
  expiresAt: number
  tokenType: 'Bearer'
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: UserContext
  token: AuthToken
}

// HTTP client configuration
export interface ApiConfig {
  baseURL: string
  timeout: number
  retryAttempts: number
  retryDelay: number
}

// Loading states
export interface LoadingState {
  isLoading: boolean
  message?: string
  progress?: number
}

// Pagination for future use
export interface PaginationParams {
  page: number
  limit: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

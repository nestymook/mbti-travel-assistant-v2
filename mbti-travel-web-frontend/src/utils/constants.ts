// Application constants
import type { PersonalityCategories } from '@/types'

export const MBTI_TEST_URL = 'https://www.16personalities.com'

export const API_ENDPOINTS = {
  GENERATE_ITINERARY: '/generate-itinerary',
  HEALTH_CHECK: '/health',
} as const

export const PERSONALITY_CATEGORIES: PersonalityCategories = {
  structured: ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'],
  flexible: ['INTP', 'ISTP', 'ESTP'],
  colorful: ['ENTP', 'INFP', 'ENFP', 'ISFP'],
  feeling: ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'],
}

export const LOADING_MESSAGES = {
  GENERATING_ITINERARY: 'Generating Itinerary in progress...',
  LOADING_DATA: 'Loading data...',
  PROCESSING: 'Processing...',
} as const

export const ERROR_MESSAGES = {
  INVALID_MBTI: 'Please input correct MBTI Personality!',
  NETWORK_ERROR: 'Network connection error. Please try again.',
  API_ERROR: 'Service temporarily unavailable. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
} as const

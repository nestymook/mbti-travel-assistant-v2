// MBTI personality types and related interfaces
export type MBTIPersonality =
  | 'INTJ'
  | 'INTP'
  | 'ENTJ'
  | 'ENTP'
  | 'INFJ'
  | 'INFP'
  | 'ENFJ'
  | 'ENFP'
  | 'ISTJ'
  | 'ISFJ'
  | 'ESTJ'
  | 'ESFJ'
  | 'ISTP'
  | 'ISFP'
  | 'ESTP'
  | 'ESFP'

// MBTI dimensions for categorization
export type MBTIDimension = {
  energySource: 'E' | 'I' // Extraversion vs Introversion
  informationProcessing: 'S' | 'N' // Sensing vs Intuition
  decisionMaking: 'T' | 'F' // Thinking vs Feeling
  lifestyle: 'J' | 'P' // Judging vs Perceiving
}

// Personality categorization for UI customizations
export interface PersonalityCategories {
  structured: MBTIPersonality[] // INTJ, ENTJ, ISTJ, ESTJ
  flexible: MBTIPersonality[] // INTP, ISTP, ESTP
  colorful: MBTIPersonality[] // ENTP, INFP, ENFP, ISFP
  feeling: MBTIPersonality[] // INFJ, ISFJ, ENFJ, ESFJ
}

// Default personality categorization
export const PERSONALITY_CATEGORIES: PersonalityCategories = {
  structured: ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'],
  flexible: ['INTP', 'ISTP', 'ESTP'],
  colorful: ['ENTP', 'INFP', 'ENFP', 'ISFP'],
  feeling: ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ']
}

// All valid MBTI personality types
export const VALID_MBTI_TYPES: MBTIPersonality[] = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

// Theme and styling types
export interface PersonalityTheme {
  primary: string
  secondary: string
  accent: string
  background: string
  text: string
  warm?: boolean
  colorful?: boolean
  name: string
  description?: string
}

// Comprehensive customization configuration
export interface CustomizationConfig {
  showTimeInputs: boolean
  showImportantCheckboxes: boolean
  showPointForm: boolean
  showDescriptions: boolean
  showGroupNotes: boolean
  showShareLink: boolean
  showImages: boolean
  useFlashyStyle: boolean
  useWarmTones: boolean
}

// Import statements for API types
export type { MainItinerary, CandidateTouristSpots, CandidateRestaurants } from './api'

// Validation types
export interface ValidationResult {
  isValid: boolean
  message?: string
  suggestedValue?: string
  errorCode?: string
}

export interface MBTIValidationRules {
  minLength: number
  maxLength: number
  allowedCharacters: RegExp
  validTypes: MBTIPersonality[]
}

// Default validation rules
export const MBTI_VALIDATION_RULES: MBTIValidationRules = {
  minLength: 4,
  maxLength: 4,
  allowedCharacters: /^[A-Z]{4}$/,
  validTypes: VALID_MBTI_TYPES
}

// Personality-specific configuration mapping
export type PersonalityConfigMap = {
  [key in MBTIPersonality]: CustomizationConfig
}

// Theme configuration mapping
export type PersonalityThemeMap = {
  [key in MBTIPersonality]: PersonalityTheme
}

// Session customization types
export interface SessionCustomization {
  targetStartTime?: string
  targetEndTime?: string
  isImportant?: boolean
  groupNotes?: string
  personalNotes?: string
}

export interface DayCustomization {
  [sessionKey: string]: SessionCustomization
}

export interface ItineraryCustomization {
  day_1: DayCustomization
  day_2: DayCustomization
  day_3: DayCustomization
  mbtiPersonality: MBTIPersonality
  lastModified: string
}

// Personality insights and descriptions
export interface PersonalityInsight {
  personality: MBTIPersonality
  title: string
  description: string
  strengths: string[]
  preferences: string[]
  travelStyle: string
  recommendedActivities: string[]
}

// Input formatting and processing
export interface MBTIInputState {
  value: string
  isValid: boolean
  errorMessage?: string
  suggestions?: string[]
  isFormatted: boolean
}

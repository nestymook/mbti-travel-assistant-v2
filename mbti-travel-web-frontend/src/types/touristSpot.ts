import type { MBTIPersonality } from './mbti'

// Tourist spot-related types
export interface TouristSpot {
  tourist_spot: string
  mbti: MBTIPersonality
  description?: string
  remarks?: string
  address: string
  district: string
  area: string
  operating_hours_mon_fri: string
  operating_hours_sat_sun: string
  operating_hours_public_holiday: string
  full_day: boolean
  category?: TouristSpotCategory
  features?: TouristSpotFeature[]
  rating?: number
  reviewCount?: number
  phoneNumber?: string
  website?: string
  imageUrl?: string
  admissionFee?: AdmissionFee
  accessibility?: AccessibilityInfo
}

// Tourist spot categories
export type TouristSpotCategory = 
  | 'cultural'
  | 'historical'
  | 'nature'
  | 'entertainment'
  | 'shopping'
  | 'religious'
  | 'architectural'
  | 'museum'
  | 'park'
  | 'viewpoint'
  | 'beach'
  | 'temple'
  | 'market'
  | 'theme_park'
  | 'gallery'
  | 'landmark'

// Tourist spot features
export type TouristSpotFeature = 
  | 'indoor'
  | 'outdoor'
  | 'air_conditioned'
  | 'wheelchair_accessible'
  | 'parking_available'
  | 'public_transport_nearby'
  | 'guided_tours'
  | 'audio_guide'
  | 'gift_shop'
  | 'restaurant'
  | 'restrooms'
  | 'photography_allowed'
  | 'family_friendly'
  | 'pet_friendly'
  | 'free_wifi'

// Admission fee information
export interface AdmissionFee {
  adult?: number
  child?: number
  senior?: number
  student?: number
  family?: number
  currency: 'HKD'
  isFree: boolean
  notes?: string
}

// Accessibility information
export interface AccessibilityInfo {
  wheelchairAccessible: boolean
  elevatorAccess?: boolean
  brailleSignage?: boolean
  audioAssistance?: boolean
  visualAssistance?: boolean
  notes?: string
}

// Operating hours structure
export interface TouristSpotOperatingHours {
  monday_friday: string
  saturday_sunday: string
  public_holiday: string
  specialHours?: {
    [date: string]: string // Special hours for specific dates
  }
  closedDays?: string[]
  seasonalHours?: {
    season: string
    hours: string
    startDate: string
    endDate: string
  }[]
}

// MBTI personality matching
export interface MBTIMatch {
  personality: MBTIPersonality
  matchScore: number
  reasons: string[]
  recommendedTimeOfDay?: 'morning' | 'afternoon' | 'evening'
  recommendedDuration?: number // in hours
}

// Tourist spot search and filtering
export interface TouristSpotFilter {
  categories?: TouristSpotCategory[]
  districts?: string[]
  features?: TouristSpotFeature[]
  mbtiPersonalities?: MBTIPersonality[]
  minRating?: number
  maxAdmissionFee?: number
  isAccessible?: boolean
  openNow?: boolean
  fullDayOnly?: boolean
}

export interface TouristSpotSearchParams {
  query?: string
  filters?: TouristSpotFilter
  sortBy?: 'rating' | 'distance' | 'popularity' | 'mbti_match'
  sortOrder?: 'asc' | 'desc'
  limit?: number
}

// Tourist spot validation
export interface TouristSpotValidation {
  hasValidOperatingHours: boolean
  hasValidAddress: boolean
  hasValidMBTIMatch: boolean
  hasValidCategory: boolean
  isComplete: boolean
  missingFields?: string[]
}

// Formatted tourist spot for display
export interface FormattedTouristSpot extends TouristSpot {
  formattedOperatingHours: string
  formattedAdmissionFee?: string
  formattedFeatures: string[]
  mbtiMatchPercentage?: number
  isOpenNow?: boolean
  distanceFromUser?: number
  estimatedVisitDuration?: string
}

// Tourist spot recommendation context
export interface TouristSpotRecommendationContext {
  sessionType: 'morning_session' | 'afternoon_session' | 'night_session'
  dayNumber: 1 | 2 | 3
  previousSelections: TouristSpot[]
  mbtiPersonality: MBTIPersonality
  userPreferences?: {
    preferredCategories?: TouristSpotCategory[]
    avoidCategories?: TouristSpotCategory[]
    maxAdmissionFee?: number
    requiresAccessibility?: boolean
    preferredDuration?: 'short' | 'medium' | 'long' | 'full_day'
    avoidDuplicates?: boolean
  }
  weatherConsiderations?: {
    isRainy?: boolean
    isHot?: boolean
    preferIndoor?: boolean
  }
}

// Tourist spot session planning
export interface TouristSpotSession {
  spot: TouristSpot
  startTime?: string
  endTime?: string
  duration?: number
  notes?: string
  isImportant?: boolean
  transportationTo?: string
  estimatedCost?: number
}

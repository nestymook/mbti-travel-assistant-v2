// Restaurant-related types
export interface Restaurant {
  id: string
  name: string
  address: string
  mealType: MealType[]
  sentiment: RestaurantSentiment
  locationCategory: LocationCategory
  district: string
  priceRange: PriceRange
  operatingHours: OperatingHours
  features?: RestaurantFeature[]
  rating?: number
  reviewCount?: number
  phoneNumber?: string
  website?: string
  imageUrl?: string
}

export interface RestaurantSentiment {
  likes: number
  dislikes: number
  neutral: number
  totalReviews?: number
  averageRating?: number
}

export interface OperatingHours {
  'Mon - Fri': string
  'Sat - Sun': string
  'Public Holiday': string
}

// Meal type - stores keywords for restaurants
export type MealType = string

// Location category types
export type LocationCategory =
  | 'Hong Kong Island'
  | 'New Territories'
  | 'Kowloon'
  | 'Islands'

// Price range enumeration
export type PriceRange =
  | 'Below $50'      // Budget-friendly, street food, casual dining
  | '$51-100'        // Affordable dining, local restaurants  
  | '$101-200'       // Mid-range dining, popular restaurants
  | '$201-400'       // Upper mid-range, quality dining
  | '$401-800'       // Premium dining, upscale restaurants
  | 'Above $801'     // Fine dining, luxury establishments
  | 'Not specified'  // Price information unavailable



// Restaurant features
export type RestaurantFeature =
  | 'outdoor_seating'
  | 'air_conditioning'
  | 'wifi'
  | 'wheelchair_accessible'
  | 'parking'
  | 'private_rooms'
  | 'live_music'
  | 'view'
  | 'takeaway'
  | 'delivery'
  | 'reservations_required'
  | 'credit_cards_accepted'
  | 'english_menu'

// Restaurant search and filtering
export interface RestaurantFilter {
  mealTypes?: MealType[]
  priceRanges?: PriceRange[]
  districts?: string[]
  features?: RestaurantFeature[]
  minRating?: number
  openNow?: boolean
}

export interface RestaurantSearchParams {
  query?: string
  filters?: RestaurantFilter
  sortBy?: 'rating' | 'price' | 'distance' | 'popularity'
  sortOrder?: 'asc' | 'desc'
  limit?: number
}

// Restaurant validation
export interface RestaurantValidation {
  hasValidOperatingHours: boolean
  hasValidAddress: boolean
  hasValidPriceRange: boolean
  hasValidMealTypes: boolean
  isComplete: boolean
  missingFields?: string[]
}

// Restaurant display formatting
export interface FormattedRestaurant extends Restaurant {
  formattedPriceRange: string
  formattedOperatingHours: string
  formattedMealTypes: string
  sentimentPercentage: {
    likes: number
    dislikes: number
    neutral: number
  }
  isOpenNow?: boolean
  distanceFromUser?: number
}

// Restaurant recommendation context
export interface RestaurantRecommendationContext {
  sessionType: 'breakfast' | 'lunch' | 'dinner'
  dayNumber: 1 | 2 | 3
  previousSelections: Restaurant[]
  userPreferences?: {
    dietaryRestrictions?: string[]
    budgetRange?: PriceRange
    avoidDuplicates?: boolean
  }
}

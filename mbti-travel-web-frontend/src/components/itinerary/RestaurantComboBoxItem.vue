<template>
  <div class="restaurant-combo-item" :class="personalityClass">
    <div class="restaurant-basic-info">
      <div class="restaurant-name">{{ restaurant.name }}</div>
      <div class="restaurant-meta">
        <span class="district">{{ restaurant.district }}</span>
        <span class="price-range">{{ formatPriceRange(restaurant.priceRange) }}</span>
        <span class="meal-types">{{ formatMealTypes(restaurant.mealType) }}</span>
      </div>
    </div>
    
    <div class="restaurant-quick-stats">
      <div class="sentiment-quick">
        <span class="likes">👍 {{ restaurant.sentiment.likes }}</span>
        <span class="dislikes">👎 {{ restaurant.sentiment.dislikes }}</span>
        <span class="neutral">😐 {{ restaurant.sentiment.neutral }}</span>
      </div>
      <div class="positive-ratio" :class="getPositiveRatioClass()">
        {{ positiveRatio.toFixed(0) }}% positive
      </div>
    </div>

    <div v-if="showDetailedInfo" class="restaurant-detailed-info">
      <div class="address-info">
        <span class="address">📍 {{ restaurant.address }}</span>
        <span class="location-category">{{ restaurant.locationCategory }}</span>
      </div>
      
      <div class="hours-summary">
        <div class="hours-item">
          <span class="hours-label">Mon-Fri:</span>
          <span class="hours-value">{{ restaurant.operatingHours['Mon - Fri'] }}</span>
        </div>
        <div class="hours-item">
          <span class="hours-label">Weekends:</span>
          <span class="hours-value">{{ restaurant.operatingHours['Sat - Sun'] }}</span>
        </div>
      </div>

      <div v-if="restaurant.cuisine && restaurant.cuisine.length > 0" class="cuisine-info">
        <span class="cuisine-label">Cuisine:</span>
        <span class="cuisine-types">{{ formatCuisineTypes(restaurant.cuisine) }}</span>
      </div>

      <div v-if="restaurant.features && restaurant.features.length > 0" class="features-info">
        <span class="features-label">Features:</span>
        <div class="feature-tags">
          <span 
            v-for="feature in restaurant.features.slice(0, 3)" 
            :key="feature" 
            class="feature-tag"
          >
            {{ getFeatureIcon(feature) }} {{ formatFeature(feature) }}
          </span>
          <span v-if="restaurant.features.length > 3" class="more-features">
            +{{ restaurant.features.length - 3 }} more
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Restaurant, PriceRange, MealType, CuisineType, RestaurantFeature } from '@/types/restaurant'
import type { MBTIPersonality } from '@/types/mbti'

// Props
interface Props {
  restaurant: Restaurant
  mbtiPersonality: MBTIPersonality
  showDetailedInfo?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDetailedInfo: false
})

// Computed properties
const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

const totalReviews = computed(() => {
  return props.restaurant.sentiment.likes + 
         props.restaurant.sentiment.dislikes + 
         props.restaurant.sentiment.neutral
})

const positiveRatio = computed(() => {
  const total = totalReviews.value
  if (total === 0) return 0
  return (props.restaurant.sentiment.likes / total) * 100
})

// Helper functions
const formatPriceRange = (priceRange: PriceRange): string => {
  const priceMap: Record<PriceRange, string> = {
    budget: '$',
    moderate: '$$',
    expensive: '$$$',
    luxury: '$$$$'
  }
  return priceMap[priceRange] || priceRange
}

const formatMealTypes = (mealTypes: MealType[]): string => {
  const mealTypeMap: Record<MealType, string> = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    dinner: 'Dinner',
    brunch: 'Brunch',
    afternoon_tea: 'Tea',
    late_night: 'Late Night'
  }
  
  return mealTypes.map(type => mealTypeMap[type] || type).slice(0, 2).join(', ')
}

const formatCuisineTypes = (cuisines: CuisineType[]): string => {
  const cuisineMap: Record<CuisineType, string> = {
    cantonese: 'Cantonese',
    dim_sum: 'Dim Sum',
    international: 'International',
    japanese: 'Japanese',
    korean: 'Korean',
    thai: 'Thai',
    italian: 'Italian',
    french: 'French',
    american: 'American',
    indian: 'Indian',
    fusion: 'Fusion',
    vegetarian: 'Vegetarian',
    seafood: 'Seafood',
    barbecue: 'BBQ',
    dessert: 'Dessert',
    cafe: 'Café'
  }
  
  return cuisines.map(cuisine => cuisineMap[cuisine] || cuisine).slice(0, 2).join(', ')
}

const formatFeature = (feature: RestaurantFeature): string => {
  const featureMap: Record<RestaurantFeature, string> = {
    outdoor_seating: 'Outdoor',
    air_conditioning: 'A/C',
    wifi: 'WiFi',
    wheelchair_accessible: 'Accessible',
    parking: 'Parking',
    private_rooms: 'Private',
    live_music: 'Music',
    view: 'View',
    takeaway: 'Takeaway',
    delivery: 'Delivery',
    reservations_required: 'Reservations',
    credit_cards_accepted: 'Cards',
    english_menu: 'English'
  }
  
  return featureMap[feature] || feature
}

const getFeatureIcon = (feature: RestaurantFeature): string => {
  const iconMap: Record<RestaurantFeature, string> = {
    outdoor_seating: '🌿',
    air_conditioning: '❄️',
    wifi: '📶',
    wheelchair_accessible: '♿',
    parking: '🅿️',
    private_rooms: '🚪',
    live_music: '🎵',
    view: '🌅',
    takeaway: '🥡',
    delivery: '🚚',
    reservations_required: '📅',
    credit_cards_accepted: '💳',
    english_menu: '🇬🇧'
  }
  
  return iconMap[feature] || '✨'
}

const getPositiveRatioClass = (): string => {
  const ratio = positiveRatio.value
  if (ratio >= 80) return 'excellent'
  if (ratio >= 60) return 'good'
  if (ratio >= 40) return 'average'
  return 'poor'
}
</script>

<style scoped>
.restaurant-combo-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--mbti-surface, #ffffff);
  border-radius: 6px;
  border: 1px solid var(--mbti-border, #e5e7eb);
  transition: all 0.2s ease;
}

.restaurant-combo-item:hover {
  border-color: var(--mbti-primary, #3b82f6);
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.restaurant-basic-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.restaurant-name {
  font-weight: 600;
  font-size: 1rem;
  color: var(--mbti-primary, #1f2937);
  line-height: 1.2;
}

.restaurant-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.district {
  color: var(--mbti-secondary, #6b7280);
  font-weight: 500;
}

.price-range {
  color: var(--mbti-accent, #059669);
  font-weight: 600;
  background: var(--mbti-accent-light, #ecfdf5);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.meal-types {
  color: var(--mbti-text, #374151);
  font-style: italic;
}

.restaurant-quick-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: var(--mbti-background, #f9fafb);
  border-radius: 4px;
}

.sentiment-quick {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
}

.likes,
.dislikes,
.neutral {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 500;
}

.positive-ratio {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.positive-ratio.excellent {
  background: #dcfce7;
  color: #166534;
}

.positive-ratio.good {
  background: #fef3c7;
  color: #92400e;
}

.positive-ratio.average {
  background: #fed7aa;
  color: #9a3412;
}

.positive-ratio.poor {
  background: #fecaca;
  color: #991b1b;
}

.restaurant-detailed-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--mbti-border, #e5e7eb);
}

.address-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.address {
  color: var(--mbti-text, #374151);
  font-weight: 500;
}

.location-category {
  color: var(--mbti-secondary, #6b7280);
  font-size: 0.8rem;
}

.hours-summary {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hours-label {
  color: var(--mbti-secondary, #6b7280);
  font-weight: 500;
}

.hours-value {
  color: var(--mbti-text, #374151);
  font-weight: 600;
}

.cuisine-info,
.features-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.cuisine-label,
.features-label {
  color: var(--mbti-secondary, #6b7280);
  font-weight: 600;
}

.cuisine-types {
  color: var(--mbti-accent, #059669);
  font-weight: 500;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.feature-tag {
  background: var(--mbti-accent-light, #ecfdf5);
  color: var(--mbti-accent, #059669);
  padding: 0.125rem 0.375rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.more-features {
  color: var(--mbti-secondary, #6b7280);
  font-style: italic;
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
}

/* MBTI Personality-specific styling */
.mbti-intj,
.mbti-entj,
.mbti-istj,
.mbti-estj {
  --mbti-primary: #1f2937;
  --mbti-secondary: #6b7280;
  --mbti-accent: #374151;
  --mbti-background: #f9fafb;
  --mbti-surface: #ffffff;
  --mbti-border: #d1d5db;
  --mbti-text: #111827;
  --mbti-shadow: rgba(31, 41, 55, 0.1);
  --mbti-accent-light: #f3f4f6;
}

.mbti-intp,
.mbti-istp,
.mbti-estp {
  --mbti-primary: #059669;
  --mbti-secondary: #6b7280;
  --mbti-accent: #10b981;
  --mbti-background: #ecfdf5;
  --mbti-surface: #ffffff;
  --mbti-border: #a7f3d0;
  --mbti-text: #064e3b;
  --mbti-shadow: rgba(5, 150, 105, 0.1);
  --mbti-accent-light: #d1fae5;
}

.mbti-entp,
.mbti-infp,
.mbti-enfp,
.mbti-isfp {
  --mbti-primary: #7c3aed;
  --mbti-secondary: #a78bfa;
  --mbti-accent: #8b5cf6;
  --mbti-background: #f3e8ff;
  --mbti-surface: #ffffff;
  --mbti-border: #c4b5fd;
  --mbti-text: #581c87;
  --mbti-shadow: rgba(124, 58, 237, 0.1);
  --mbti-accent-light: #e9d5ff;
}

.mbti-infj,
.mbti-enfj,
.mbti-esfj {
  --mbti-primary: #dc2626;
  --mbti-secondary: #f87171;
  --mbti-accent: #ef4444;
  --mbti-background: #fef2f2;
  --mbti-surface: #ffffff;
  --mbti-border: #fca5a5;
  --mbti-text: #7f1d1d;
  --mbti-shadow: rgba(220, 38, 38, 0.1);
  --mbti-accent-light: #fee2e2;
}

.mbti-isfj {
  --mbti-primary: #d97706;
  --mbti-secondary: #f59e0b;
  --mbti-accent: #f59e0b;
  --mbti-background: #fef3c7;
  --mbti-surface: #ffffff;
  --mbti-border: #fcd34d;
  --mbti-text: #78350f;
  --mbti-shadow: rgba(217, 119, 6, 0.1);
  --mbti-accent-light: #fef3c7;
}

.mbti-estp .restaurant-combo-item {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  font-weight: bold;
}

.mbti-estp .restaurant-name,
.mbti-estp .district,
.mbti-estp .meal-types,
.mbti-estp .address,
.mbti-estp .hours-label,
.mbti-estp .hours-value,
.mbti-estp .cuisine-label,
.mbti-estp .features-label {
  color: white;
}

.mbti-estp .price-range {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.mbti-estp .restaurant-quick-stats {
  background: rgba(255, 255, 255, 0.1);
}

.mbti-estp .feature-tag {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* Responsive design */
@media (max-width: 768px) {
  .restaurant-combo-item {
    padding: 0.5rem;
  }
  
  .restaurant-meta {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .restaurant-quick-stats {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
    text-align: center;
  }
  
  .sentiment-quick {
    justify-content: center;
  }
  
  .hours-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.125rem;
  }
  
  .feature-tags {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .restaurant-name {
    font-size: 0.9rem;
  }
  
  .restaurant-meta {
    font-size: 0.8rem;
  }
  
  .sentiment-quick {
    font-size: 0.75rem;
    gap: 0.5rem;
  }
  
  .positive-ratio {
    font-size: 0.75rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .restaurant-combo-item {
    transition: none;
  }
}

@media (prefers-contrast: high) {
  .restaurant-combo-item {
    border-width: 2px;
  }
  
  .feature-tag {
    border: 1px solid currentColor;
  }
}
</style>
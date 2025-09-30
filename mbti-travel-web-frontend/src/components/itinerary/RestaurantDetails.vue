<template>
  <div class="restaurant-details" :class="personalityClass">
    <div class="restaurant-header">
      <h3 class="restaurant-name">{{ restaurant.name }}</h3>
      <div class="restaurant-price">{{ formatPriceRange(restaurant.priceRange) }}</div>
    </div>

    <div class="restaurant-info">
      <div class="info-section">
        <div class="info-item">
          <span class="info-icon">📍</span>
          <div class="info-content">
            <div class="address">{{ restaurant.address }}</div>
            <div class="district">{{ restaurant.district }}, {{ restaurant.locationCategory }}</div>
          </div>
        </div>

        <div class="info-item">
          <span class="info-icon">🍽️</span>
          <div class="info-content">
            <div class="meal-types">{{ formatMealTypes(restaurant.mealType) }}</div>
          </div>
        </div>
      </div>

      <div class="operating-hours-section">
        <h4 class="section-title">Operating Hours</h4>
        <div class="hours-grid">
          <div class="hours-item">
            <span class="hours-label">Mon - Fri:</span>
            <span class="hours-value">{{ restaurant.operatingHours['Mon - Fri'] }}</span>
          </div>
          <div class="hours-item">
            <span class="hours-label">Sat - Sun:</span>
            <span class="hours-value">{{ restaurant.operatingHours['Sat - Sun'] }}</span>
          </div>
          <div class="hours-item">
            <span class="hours-label">Public Holiday:</span>
            <span class="hours-value">{{ restaurant.operatingHours['Public Holiday'] }}</span>
          </div>
        </div>
      </div>

      <div class="sentiment-section">
        <h4 class="section-title">Customer Feedback</h4>
        <div class="sentiment-visualization">
          <div class="sentiment-bars">
            <div class="sentiment-bar likes-bar">
              <div class="bar-fill" :style="{ width: sentimentPercentages.likes + '%' }"></div>
              <div class="bar-label">
                <span class="sentiment-icon">👍</span>
                <span class="sentiment-count">{{ restaurant.sentiment.likes }}</span>
                <span class="sentiment-percentage">({{ sentimentPercentages.likes.toFixed(1) }}%)</span>
              </div>
            </div>
            
            <div class="sentiment-bar dislikes-bar">
              <div class="bar-fill" :style="{ width: sentimentPercentages.dislikes + '%' }"></div>
              <div class="bar-label">
                <span class="sentiment-icon">👎</span>
                <span class="sentiment-count">{{ restaurant.sentiment.dislikes }}</span>
                <span class="sentiment-percentage">({{ sentimentPercentages.dislikes.toFixed(1) }}%)</span>
              </div>
            </div>
            
            <div class="sentiment-bar neutral-bar">
              <div class="bar-fill" :style="{ width: sentimentPercentages.neutral + '%' }"></div>
              <div class="bar-label">
                <span class="sentiment-icon">😐</span>
                <span class="sentiment-count">{{ restaurant.sentiment.neutral }}</span>
                <span class="sentiment-percentage">({{ sentimentPercentages.neutral.toFixed(1) }}%)</span>
              </div>
            </div>
          </div>
          
          <div class="sentiment-summary">
            <div class="total-reviews">
              Total Reviews: {{ totalReviews }}
            </div>
            <div class="positive-ratio" :class="getPositiveRatioClass()">
              Positive Ratio: {{ positiveRatio.toFixed(1) }}%
            </div>
          </div>
        </div>
      </div>

      <div v-if="restaurant.cuisine && restaurant.cuisine.length > 0" class="cuisine-section">
        <h4 class="section-title">Cuisine</h4>
        <div class="cuisine-tags">
          <span 
            v-for="cuisine in restaurant.cuisine" 
            :key="cuisine" 
            class="cuisine-tag"
          >
            {{ formatCuisineType(cuisine) }}
          </span>
        </div>
      </div>

      <div v-if="restaurant.features && restaurant.features.length > 0" class="features-section">
        <h4 class="section-title">Features</h4>
        <div class="features-grid">
          <div 
            v-for="feature in restaurant.features" 
            :key="feature" 
            class="feature-item"
          >
            <span class="feature-icon">{{ getFeatureIcon(feature) }}</span>
            <span class="feature-text">{{ formatFeature(feature) }}</span>
          </div>
        </div>
      </div>

      <div v-if="restaurant.phoneNumber || restaurant.website" class="contact-section">
        <h4 class="section-title">Contact</h4>
        <div class="contact-info">
          <div v-if="restaurant.phoneNumber" class="contact-item">
            <span class="contact-icon">📞</span>
            <a :href="`tel:${restaurant.phoneNumber}`" class="contact-link">
              {{ restaurant.phoneNumber }}
            </a>
          </div>
          <div v-if="restaurant.website" class="contact-item">
            <span class="contact-icon">🌐</span>
            <a :href="restaurant.website" target="_blank" rel="noopener noreferrer" class="contact-link">
              Visit Website
            </a>
          </div>
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
  showDetailedView?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDetailedView: true
})

// Computed properties
const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

const totalReviews = computed(() => {
  return props.restaurant.sentiment.likes + 
         props.restaurant.sentiment.dislikes + 
         props.restaurant.sentiment.neutral
})

const sentimentPercentages = computed(() => {
  const total = totalReviews.value
  if (total === 0) {
    return { likes: 0, dislikes: 0, neutral: 0 }
  }
  
  return {
    likes: (props.restaurant.sentiment.likes / total) * 100,
    dislikes: (props.restaurant.sentiment.dislikes / total) * 100,
    neutral: (props.restaurant.sentiment.neutral / total) * 100
  }
})

const positiveRatio = computed(() => {
  const total = totalReviews.value
  if (total === 0) return 0
  return (props.restaurant.sentiment.likes / total) * 100
})

// Helper functions
const formatPriceRange = (priceRange: PriceRange): string => {
  const priceMap: Record<PriceRange, string> = {
    budget: '$ (Under HK$100)',
    moderate: '$$ (HK$100-300)',
    expensive: '$$$ (HK$300-600)',
    luxury: '$$$$ (Over HK$600)'
  }
  return priceMap[priceRange] || priceRange
}

const formatMealTypes = (mealTypes: MealType[]): string => {
  const mealTypeMap: Record<MealType, string> = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    dinner: 'Dinner',
    brunch: 'Brunch',
    afternoon_tea: 'Afternoon Tea',
    late_night: 'Late Night'
  }
  
  return mealTypes.map(type => mealTypeMap[type] || type).join(', ')
}

const formatCuisineType = (cuisine: CuisineType): string => {
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
    barbecue: 'Barbecue',
    dessert: 'Dessert',
    cafe: 'Café'
  }
  
  return cuisineMap[cuisine] || cuisine
}

const formatFeature = (feature: RestaurantFeature): string => {
  const featureMap: Record<RestaurantFeature, string> = {
    outdoor_seating: 'Outdoor Seating',
    air_conditioning: 'Air Conditioning',
    wifi: 'WiFi',
    wheelchair_accessible: 'Wheelchair Accessible',
    parking: 'Parking Available',
    private_rooms: 'Private Rooms',
    live_music: 'Live Music',
    view: 'Scenic View',
    takeaway: 'Takeaway',
    delivery: 'Delivery',
    reservations_required: 'Reservations Required',
    credit_cards_accepted: 'Credit Cards Accepted',
    english_menu: 'English Menu'
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
.restaurant-details {
  background: var(--mbti-surface, #ffffff);
  border: 2px solid var(--mbti-border, #e5e7eb);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
}

.restaurant-details:hover {
  box-shadow: 0 8px 12px var(--mbti-shadow, rgba(0, 0, 0, 0.15));
  transform: translateY(-2px);
}

.restaurant-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--mbti-border, #e5e7eb);
}

.restaurant-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--mbti-primary, #1f2937);
  margin: 0;
  flex: 1;
  line-height: 1.3;
}

.restaurant-price {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--mbti-accent, #059669);
  background: var(--mbti-accent-light, #ecfdf5);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  white-space: nowrap;
  margin-left: 1rem;
}

.restaurant-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.info-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.info-content {
  flex: 1;
}

.address {
  font-weight: 500;
  color: var(--mbti-text, #374151);
  margin-bottom: 0.25rem;
}

.district {
  font-size: 0.9rem;
  color: var(--mbti-secondary, #6b7280);
}

.meal-types {
  font-weight: 500;
  color: var(--mbti-accent, #059669);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--mbti-primary, #1f2937);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 1.1rem;
  background: var(--mbti-accent, #059669);
  border-radius: 2px;
}

.operating-hours-section {
  background: var(--mbti-background, #f9fafb);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.hours-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--mbti-border, #e5e7eb);
}

.hours-item:last-child {
  border-bottom: none;
}

.hours-label {
  font-weight: 500;
  color: var(--mbti-text, #374151);
}

.hours-value {
  font-weight: 600;
  color: var(--mbti-primary, #1f2937);
  text-align: right;
}

.sentiment-section {
  background: var(--mbti-background, #f9fafb);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.sentiment-visualization {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sentiment-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sentiment-bar {
  position: relative;
  background: #f3f4f6;
  border-radius: 6px;
  overflow: hidden;
  min-height: 2.5rem;
}

.bar-fill {
  height: 100%;
  transition: width 0.8s ease;
  border-radius: 6px;
}

.likes-bar .bar-fill {
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
}

.dislikes-bar .bar-fill {
  background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
}

.neutral-bar .bar-fill {
  background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
}

.bar-label {
  position: absolute;
  top: 50%;
  left: 1rem;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #374151;
  z-index: 1;
}

.sentiment-icon {
  font-size: 1.1rem;
}

.sentiment-count {
  font-weight: 600;
}

.sentiment-percentage {
  font-size: 0.9rem;
  color: #6b7280;
}

.sentiment-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.total-reviews {
  font-weight: 500;
  color: var(--mbti-text, #374151);
}

.positive-ratio {
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
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

.cuisine-section,
.features-section {
  background: var(--mbti-background, #f9fafb);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.cuisine-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.cuisine-tag {
  background: var(--mbti-accent, #059669);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.feature-icon {
  font-size: 1.1rem;
}

.feature-text {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--mbti-text, #374151);
}

.contact-section {
  background: var(--mbti-background, #f9fafb);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #e5e7eb);
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.contact-icon {
  font-size: 1.1rem;
}

.contact-link {
  color: var(--mbti-accent, #059669);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.contact-link:hover {
  color: var(--mbti-primary, #1f2937);
  text-decoration: underline;
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

.mbti-estp .restaurant-details {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  font-weight: bold;
}

.mbti-estp .restaurant-name,
.mbti-estp .section-title,
.mbti-estp .hours-label,
.mbti-estp .hours-value {
  color: white;
}

.mbti-estp .restaurant-price {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* Responsive design */
@media (max-width: 768px) {
  .restaurant-details {
    padding: 1rem;
  }
  
  .restaurant-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .restaurant-price {
    margin-left: 0;
    text-align: center;
  }
  
  .restaurant-name {
    font-size: 1.25rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .sentiment-summary {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
  
  .hours-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .hours-value {
    text-align: left;
  }
}

@media (max-width: 480px) {
  .restaurant-details {
    padding: 0.75rem;
  }
  
  .restaurant-name {
    font-size: 1.1rem;
  }
  
  .section-title {
    font-size: 1rem;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .bar-label {
    position: static;
    transform: none;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 4px;
    margin: 0.25rem;
  }
  
  .sentiment-bar {
    min-height: 3rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .restaurant-details,
  .bar-fill {
    transition: none;
  }
  
  .restaurant-details:hover {
    transform: none;
  }
}

@media (prefers-contrast: high) {
  .restaurant-details {
    border-width: 3px;
  }
  
  .section-title::before {
    width: 6px;
  }
  
  .sentiment-bar {
    border: 2px solid #000;
  }
}

/* Print styles */
@media print {
  .restaurant-details {
    box-shadow: none;
    border: 2px solid #000;
    break-inside: avoid;
  }
  
  .sentiment-bars {
    display: none;
  }
  
  .sentiment-summary {
    border: 1px solid #000;
  }
}
</style>
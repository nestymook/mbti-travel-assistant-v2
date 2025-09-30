<template>
  <div class="tourist-spot-combo-box-item" :class="personalityClass">
    <div class="spot-header">
      <h4 class="spot-name">{{ touristSpot.tourist_spot }}</h4>
      <div class="spot-badges">
        <span class="mbti-badge" :class="`mbti-${touristSpot.mbti.toLowerCase()}`">
          {{ touristSpot.mbti }}
        </span>
        <span v-if="touristSpot.full_day" class="duration-badge">
          Full Day
        </span>
      </div>
    </div>

    <div class="spot-location">
      <div class="location-info">
        <span class="district">{{ touristSpot.district }}</span>
        <span class="area">{{ touristSpot.area }}</span>
      </div>
      <div v-if="touristSpot.address" class="address">
        {{ touristSpot.address }}
      </div>
    </div>

    <div v-if="showDetailedInfo" class="spot-details">
      <div class="operating-hours">
        <div class="hours-section">
          <span class="hours-label">Mon-Fri:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_mon_fri }}</span>
        </div>
        <div class="hours-section">
          <span class="hours-label">Sat-Sun:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_sat_sun }}</span>
        </div>
        <div class="hours-section">
          <span class="hours-label">Holidays:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_public_holiday }}</span>
        </div>
      </div>

      <div v-if="touristSpot.remarks" class="spot-remarks">
        <span class="remarks-label">Info:</span>
        <span class="remarks-text">{{ touristSpot.remarks }}</span>
      </div>

      <!-- Show description for feeling personality types -->
      <div 
        v-if="shouldShowDescription && touristSpot.description" 
        class="spot-description"
      >
        <span class="description-label">Description:</span>
        <p class="description-text">{{ touristSpot.description }}</p>
      </div>

      <div v-if="touristSpot.category" class="spot-category">
        <span class="category-badge" :class="`category-${touristSpot.category}`">
          {{ formatCategory(touristSpot.category) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TouristSpot, TouristSpotCategory } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'

// Props interface
interface Props {
  touristSpot: TouristSpot
  mbtiPersonality: MBTIPersonality
  showDetailedInfo?: boolean
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  showDetailedInfo: false
})

// Computed properties
const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

// Check if description should be shown for feeling personality types (INFJ, ISFJ)
const shouldShowDescription = computed(() => {
  const feelingDescriptionTypes: MBTIPersonality[] = ['INFJ', 'ISFJ']
  return feelingDescriptionTypes.includes(props.mbtiPersonality)
})

// Helper functions
const formatCategory = (category: TouristSpotCategory): string => {
  const categoryMap: Record<TouristSpotCategory, string> = {
    'cultural': 'Cultural',
    'historical': 'Historical',
    'nature': 'Nature',
    'entertainment': 'Entertainment',
    'shopping': 'Shopping',
    'religious': 'Religious',
    'architectural': 'Architectural',
    'museum': 'Museum',
    'park': 'Park',
    'viewpoint': 'Viewpoint',
    'beach': 'Beach',
    'temple': 'Temple',
    'market': 'Market',
    'theme_park': 'Theme Park',
    'gallery': 'Gallery',
    'landmark': 'Landmark'
  }
  return categoryMap[category] || category
}
</script>

<style scoped>
.tourist-spot-combo-box-item {
  width: 100%;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: white;
  transition: all 0.2s ease;
}

.spot-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  gap: 0.75rem;
}

.spot-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color, #111827);
  margin: 0;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.spot-badges {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.mbti-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  background-color: var(--primary-color, #3b82f6);
}

.duration-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #059669;
  background-color: #ecfdf5;
  border: 1px solid #a7f3d0;
}

.spot-location {
  margin-bottom: 0.5rem;
}

.location-info {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.district {
  font-weight: 500;
  color: var(--primary-color, #3b82f6);
  font-size: 0.875rem;
}

.area {
  color: #6b7280;
  font-size: 0.875rem;
}

.address {
  font-size: 0.75rem;
  color: #9ca3af;
  line-height: 1.4;
}

.spot-details {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.operating-hours {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.hours-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

.hours-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 4rem;
}

.hours-value {
  color: #374151;
  text-align: right;
  flex: 1;
}

.spot-remarks {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
}

.remarks-label {
  font-weight: 500;
  color: #6b7280;
  flex-shrink: 0;
}

.remarks-text {
  color: #374151;
  line-height: 1.4;
}

.spot-description {
  margin-bottom: 0.5rem;
}

.description-label {
  display: block;
  font-weight: 500;
  color: #6b7280;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.description-text {
  font-size: 0.75rem;
  color: #374151;
  line-height: 1.4;
  margin: 0;
}

.spot-category {
  display: flex;
  justify-content: flex-end;
}

.category-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  background-color: #f3f4f6;
  color: #6b7280;
}

/* Category-specific colors */
.category-cultural { background-color: #fef3c7; color: #92400e; }
.category-historical { background-color: #fde68a; color: #78350f; }
.category-nature { background-color: #d1fae5; color: #065f46; }
.category-entertainment { background-color: #ddd6fe; color: #5b21b6; }
.category-shopping { background-color: #fce7f3; color: #be185d; }
.category-religious { background-color: #e0e7ff; color: #3730a3; }
.category-architectural { background-color: #f3f4f6; color: #374151; }
.category-museum { background-color: #fef2f2; color: #991b1b; }
.category-park { background-color: #ecfdf5; color: #047857; }
.category-viewpoint { background-color: #e0f2fe; color: #0c4a6e; }
.category-beach { background-color: #cffafe; color: #155e75; }
.category-temple { background-color: #fdf4ff; color: #86198f; }
.category-market { background-color: #fff7ed; color: #9a3412; }
.category-theme_park { background-color: #fef7ff; color: #a21caf; }
.category-gallery { background-color: #f0f9ff; color: #0369a1; }
.category-landmark { background-color: #fffbeb; color: #92400e; }

/* MBTI Personality-specific styling */
.mbti-intj,
.mbti-entj,
.mbti-istj,
.mbti-estj {
  --primary-color: #1f2937;
  --text-color: #111827;
}

.mbti-intp,
.mbti-istp,
.mbti-estp {
  --primary-color: #059669;
  --text-color: #111827;
}

.mbti-entp,
.mbti-infp,
.mbti-enfp,
.mbti-isfp {
  --primary-color: #7c3aed;
  --text-color: #111827;
}

.mbti-infj,
.mbti-isfj,
.mbti-enfj,
.mbti-esfj {
  --primary-color: #dc2626;
  --text-color: #111827;
}

.mbti-isfj {
  --primary-color: #d97706;
  --text-color: #111827;
}

/* ESTP flashy styling */
.mbti-estp {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  font-weight: bold;
}

.mbti-estp .spot-name,
.mbti-estp .district,
.mbti-estp .hours-label,
.mbti-estp .hours-value,
.mbti-estp .remarks-label,
.mbti-estp .remarks-text,
.mbti-estp .description-label,
.mbti-estp .description-text {
  color: white;
}

.mbti-estp .area,
.mbti-estp .address {
  color: rgba(255, 255, 255, 0.8);
}

.mbti-estp .mbti-badge {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.mbti-estp .duration-badge {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
}

.mbti-estp .spot-details {
  border-top-color: rgba(255, 255, 255, 0.2);
}

/* Colorful personalities styling */
.mbti-entp,
.mbti-infp,
.mbti-enfp,
.mbti-isfp {
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
  color: white;
}

.mbti-entp .spot-name,
.mbti-infp .spot-name,
.mbti-enfp .spot-name,
.mbti-isfp .spot-name,
.mbti-entp .district,
.mbti-infp .district,
.mbti-enfp .district,
.mbti-isfp .district {
  color: white;
}

.mbti-entp .area,
.mbti-infp .area,
.mbti-enfp .area,
.mbti-isfp .area,
.mbti-entp .address,
.mbti-infp .address,
.mbti-enfp .address,
.mbti-isfp .address {
  color: rgba(255, 255, 255, 0.8);
}

/* Warm tones for ISFJ */
.mbti-isfj {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.mbti-isfj .spot-name,
.mbti-isfj .district,
.mbti-isfj .hours-label,
.mbti-isfj .hours-value,
.mbti-isfj .remarks-label,
.mbti-isfj .remarks-text,
.mbti-isfj .description-label,
.mbti-isfj .description-text {
  color: white;
}

.mbti-isfj .area,
.mbti-isfj .address {
  color: rgba(255, 255, 255, 0.8);
}

/* Responsive design */
@media (max-width: 768px) {
  .spot-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .spot-badges {
    align-self: flex-end;
  }
  
  .location-info {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .operating-hours {
    gap: 0.375rem;
  }
  
  .hours-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.125rem;
  }
  
  .hours-label {
    min-width: auto;
  }
  
  .hours-value {
    text-align: left;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .tourist-spot-combo-box-item {
    border: 2px solid currentColor;
  }
  
  .mbti-badge,
  .duration-badge,
  .category-badge {
    border: 1px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .tourist-spot-combo-box-item {
    transition: none;
  }
}
</style>
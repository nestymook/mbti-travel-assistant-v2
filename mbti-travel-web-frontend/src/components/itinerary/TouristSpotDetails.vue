<template>
  <div class="tourist-spot-details" :class="personalityClass">
    <div class="spot-header">
      <div class="spot-title-section">
        <h3 class="spot-name">{{ touristSpot.tourist_spot }}</h3>
        <div class="spot-badges">
          <span class="mbti-badge" :class="`mbti-${touristSpot.mbti.toLowerCase()}`">
            MBTI Match: {{ touristSpot.mbti }}
          </span>
          <span v-if="touristSpot.full_day" class="duration-badge">
            Full Day Experience
          </span>
          <span v-if="touristSpot.category" class="category-badge" :class="`category-${touristSpot.category}`">
            {{ formatCategory(touristSpot.category) }}
          </span>
        </div>
      </div>
      
      <!-- Enhanced image placeholder for creative personalities -->
      <div v-if="shouldShowImages" class="spot-image-section">
        <ImagePlaceholder
          :mbti-personality="mbtiPersonality"
          :title="touristSpot.tourist_spot"
          :subtitle="getImageSubtitle()"
          :clickable="true"
          :click-hint-text="'stunning photos'"
          size="medium"
          variant="spot"
          :aria-label="`View images of ${touristSpot.tourist_spot}`"
          @click="handleImageClick"
          @image-request="handleImageRequest"
        />
        
        <!-- Additional image gallery for colorful personalities -->
        <div v-if="isColorfulPersonality" class="image-gallery-preview">
          <div class="gallery-title">
            <span class="gallery-icon">🖼️</span>
            Photo Gallery Preview
          </div>
          <div class="gallery-grid">
            <ImagePlaceholder
              v-for="(imageType, index) in getImageTypes()"
              :key="`${imageType}-${index}`"
              :mbti-personality="mbtiPersonality"
              :title="imageType"
              :clickable="true"
              size="small"
              variant="gallery"
              :aria-label="`View ${imageType} photos of ${touristSpot.tourist_spot}`"
              @click="handleGalleryImageClick(imageType)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="spot-location-section">
      <div class="location-header">
        <h4 class="section-title">Location Information</h4>
      </div>
      <div class="location-details">
        <div class="location-item">
          <span class="location-label">District:</span>
          <span class="location-value district-name">{{ touristSpot.district }}</span>
        </div>
        <div class="location-item">
          <span class="location-label">Area:</span>
          <span class="location-value">{{ touristSpot.area }}</span>
        </div>
        <div v-if="touristSpot.address" class="location-item address-item">
          <span class="location-label">Address:</span>
          <span class="location-value address-text">{{ touristSpot.address }}</span>
        </div>
      </div>
    </div>

    <div class="operating-hours-section">
      <div class="hours-header">
        <h4 class="section-title">Operating Hours</h4>
      </div>
      <div class="hours-grid">
        <div class="hours-item">
          <span class="hours-label">Monday - Friday:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_mon_fri }}</span>
        </div>
        <div class="hours-item">
          <span class="hours-label">Saturday - Sunday:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_sat_sun }}</span>
        </div>
        <div class="hours-item">
          <span class="hours-label">Public Holidays:</span>
          <span class="hours-value">{{ touristSpot.operating_hours_public_holiday }}</span>
        </div>
      </div>
    </div>

    <!-- MBTI Personality Matching Information -->
    <div class="mbti-match-section">
      <div class="match-header">
        <h4 class="section-title">MBTI Personality Match</h4>
      </div>
      <div class="match-details">
        <div class="match-item">
          <span class="match-label">Best suited for:</span>
          <span class="match-value mbti-highlight">{{ touristSpot.mbti }} personalities</span>
        </div>
        <div v-if="getMBTIMatchReason()" class="match-reason">
          <span class="reason-label">Why it matches:</span>
          <p class="reason-text">{{ getMBTIMatchReason() }}</p>
        </div>
      </div>
    </div>

    <!-- Description for feeling personality types (INFJ, ISFJ) -->
    <div 
      v-if="shouldShowDescription && touristSpot.description" 
      class="description-section"
    >
      <div class="description-header">
        <h4 class="section-title">Description</h4>
      </div>
      <div class="description-content">
        <p class="description-text">{{ touristSpot.description }}</p>
      </div>
    </div>

    <!-- Additional Information -->
    <div v-if="touristSpot.remarks" class="remarks-section">
      <div class="remarks-header">
        <h4 class="section-title">Additional Information</h4>
      </div>
      <div class="remarks-content">
        <p class="remarks-text">{{ touristSpot.remarks }}</p>
      </div>
    </div>

    <!-- Features and amenities -->
    <div v-if="touristSpot.features && touristSpot.features.length > 0" class="features-section">
      <div class="features-header">
        <h4 class="section-title">Features & Amenities</h4>
      </div>
      <div class="features-grid">
        <span 
          v-for="feature in touristSpot.features" 
          :key="feature"
          class="feature-badge"
        >
          {{ formatFeature(feature) }}
        </span>
      </div>
    </div>

    <!-- Admission fee information -->
    <div v-if="touristSpot.admissionFee" class="admission-section">
      <div class="admission-header">
        <h4 class="section-title">Admission</h4>
      </div>
      <div class="admission-content">
        <div v-if="touristSpot.admissionFee.isFree" class="admission-free">
          <span class="free-badge">Free Admission</span>
        </div>
        <div v-else class="admission-fees">
          <div v-if="touristSpot.admissionFee.adult" class="fee-item">
            <span class="fee-label">Adult:</span>
            <span class="fee-value">{{ touristSpot.admissionFee.currency }} {{ touristSpot.admissionFee.adult }}</span>
          </div>
          <div v-if="touristSpot.admissionFee.child" class="fee-item">
            <span class="fee-label">Child:</span>
            <span class="fee-value">{{ touristSpot.admissionFee.currency }} {{ touristSpot.admissionFee.child }}</span>
          </div>
          <div v-if="touristSpot.admissionFee.senior" class="fee-item">
            <span class="fee-label">Senior:</span>
            <span class="fee-value">{{ touristSpot.admissionFee.currency }} {{ touristSpot.admissionFee.senior }}</span>
          </div>
        </div>
        <div v-if="touristSpot.admissionFee.notes" class="admission-notes">
          <p class="notes-text">{{ touristSpot.admissionFee.notes }}</p>
        </div>
      </div>
    </div>

    <!-- Accessibility information -->
    <div v-if="touristSpot.accessibility" class="accessibility-section">
      <div class="accessibility-header">
        <h4 class="section-title">Accessibility</h4>
      </div>
      <div class="accessibility-content">
        <div class="accessibility-item">
          <span class="accessibility-label">Wheelchair Accessible:</span>
          <span class="accessibility-value" :class="{ 'accessible': touristSpot.accessibility.wheelchairAccessible }">
            {{ touristSpot.accessibility.wheelchairAccessible ? 'Yes' : 'No' }}
          </span>
        </div>
        <div v-if="touristSpot.accessibility.notes" class="accessibility-notes">
          <p class="notes-text">{{ touristSpot.accessibility.notes }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TouristSpot, TouristSpotCategory, TouristSpotFeature } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'
import ImagePlaceholder from '@/components/common/ImagePlaceholder.vue'

// Props interface
interface Props {
  touristSpot: TouristSpot
  mbtiPersonality: MBTIPersonality
}

// Props
const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'image-click', data: { spot: string; imageType?: string }): void
  (e: 'gallery-request', data: { spot: string; personality: MBTIPersonality }): void
}

const emit = defineEmits<Emits>()

// Computed properties
const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

// Check if description should be shown for feeling personality types (INFJ, ISFJ)
const shouldShowDescription = computed(() => {
  const feelingDescriptionTypes: MBTIPersonality[] = ['INFJ', 'ISFJ']
  return feelingDescriptionTypes.includes(props.mbtiPersonality)
})

// Check if images should be shown for creative personalities
const shouldShowImages = computed(() => {
  const creativeTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP']
  return creativeTypes.includes(props.mbtiPersonality)
})

// Check if personality is colorful type
const isColorfulPersonality = computed(() => {
  const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP']
  return colorfulTypes.includes(props.mbtiPersonality)
})

// Helper functions
const formatCategory = (category: TouristSpotCategory): string => {
  const categoryMap: Record<TouristSpotCategory, string> = {
    'cultural': 'Cultural Site',
    'historical': 'Historical Site',
    'nature': 'Nature & Outdoors',
    'entertainment': 'Entertainment',
    'shopping': 'Shopping',
    'religious': 'Religious Site',
    'architectural': 'Architecture',
    'museum': 'Museum',
    'park': 'Park & Recreation',
    'viewpoint': 'Scenic Viewpoint',
    'beach': 'Beach & Waterfront',
    'temple': 'Temple & Shrine',
    'market': 'Market & Local Life',
    'theme_park': 'Theme Park',
    'gallery': 'Art Gallery',
    'landmark': 'Landmark'
  }
  return categoryMap[category] || category
}

const formatFeature = (feature: TouristSpotFeature): string => {
  const featureMap: Record<TouristSpotFeature, string> = {
    'indoor': 'Indoor',
    'outdoor': 'Outdoor',
    'air_conditioned': 'Air Conditioned',
    'wheelchair_accessible': 'Wheelchair Accessible',
    'parking_available': 'Parking Available',
    'public_transport_nearby': 'Public Transport Nearby',
    'guided_tours': 'Guided Tours',
    'audio_guide': 'Audio Guide',
    'gift_shop': 'Gift Shop',
    'restaurant': 'Restaurant',
    'restrooms': 'Restrooms',
    'photography_allowed': 'Photography Allowed',
    'family_friendly': 'Family Friendly',
    'pet_friendly': 'Pet Friendly',
    'free_wifi': 'Free WiFi'
  }
  return featureMap[feature] || feature
}

const getMBTIMatchReason = (): string => {
  const reasons: Record<MBTIPersonality, string> = {
    'INTJ': 'Strategic thinkers appreciate well-planned, intellectually stimulating experiences with clear structure.',
    'INTP': 'Curious minds enjoy exploring unique concepts and discovering hidden gems at their own pace.',
    'ENTJ': 'Natural leaders prefer efficient, goal-oriented experiences with clear objectives and outcomes.',
    'ENTP': 'Innovative explorers love diverse, stimulating environments that spark creativity and new ideas.',
    'INFJ': 'Insightful individuals seek meaningful, authentic experiences that connect with deeper values.',
    'INFP': 'Creative souls are drawn to beautiful, inspiring places that resonate with personal values.',
    'ENFJ': 'People-focused individuals enjoy culturally rich experiences that can be shared with others.',
    'ENFP': 'Enthusiastic explorers love vibrant, dynamic environments full of possibilities and connections.',
    'ISTJ': 'Practical individuals prefer well-established, reliable attractions with clear historical significance.',
    'ISFJ': 'Caring individuals enjoy peaceful, harmonious environments with cultural and historical depth.',
    'ESTJ': 'Organized leaders appreciate efficient, well-managed attractions with clear structure and purpose.',
    'ESFJ': 'Social individuals enjoy popular, well-regarded attractions that offer great experiences to share.',
    'ISTP': 'Independent explorers prefer hands-on, practical experiences they can navigate at their own pace.',
    'ISFP': 'Gentle souls are drawn to beautiful, serene environments that offer personal reflection and beauty.',
    'ESTP': 'Action-oriented individuals love exciting, dynamic experiences with immediate engagement and fun.',
    'ESFP': 'Social butterflies enjoy lively, entertaining environments where they can connect with others.'
  }
  return reasons[props.touristSpot.mbti] || 'This location matches your personality preferences.'
}

// Get image subtitle based on personality
const getImageSubtitle = (): string => {
  const subtitles: Record<MBTIPersonality, string> = {
    'ENTP': 'Innovative perspectives await!',
    'INFP': 'Artistic beauty captured',
    'ENFP': 'Vibrant moments to explore',
    'ISFP': 'Serene beauty gallery',
    'ESTP': 'Action-packed adventures!'
  }
  return subtitles[props.mbtiPersonality] || 'Beautiful moments captured'
}

// Get image types for gallery preview
const getImageTypes = (): string[] => {
  const baseTypes = ['Exterior View', 'Interior', 'Details']
  
  if (props.touristSpot.category === 'nature' || props.touristSpot.category === 'park') {
    return [...baseTypes, 'Landscape', 'Wildlife']
  } else if (props.touristSpot.category === 'cultural' || props.touristSpot.category === 'historical') {
    return [...baseTypes, 'Architecture', 'Artifacts']
  } else if (props.touristSpot.category === 'entertainment' || props.touristSpot.category === 'theme_park') {
    return [...baseTypes, 'Activities', 'Atmosphere']
  }
  
  return baseTypes
}

// Handle image click events
const handleImageClick = (): void => {
  emit('image-click', { spot: props.touristSpot.tourist_spot })
}

const handleImageRequest = (data: { personality: MBTIPersonality; title: string }): void => {
  emit('gallery-request', { 
    spot: props.touristSpot.tourist_spot, 
    personality: data.personality 
  })
}

const handleGalleryImageClick = (imageType: string): void => {
  emit('image-click', { 
    spot: props.touristSpot.tourist_spot, 
    imageType 
  })
}
</script>

<style scoped>
.tourist-spot-details {
  width: 100%;
  padding: 1.5rem;
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.spot-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.spot-title-section {
  flex: 1;
  min-width: 0;
}

.spot-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color, #111827);
  margin: 0 0 0.75rem 0;
  line-height: 1.3;
}

.spot-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.mbti-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
  background-color: var(--primary-color, #3b82f6);
}

.duration-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #059669;
  background-color: #ecfdf5;
  border: 1px solid #a7f3d0;
}

.category-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  background-color: #f3f4f6;
  color: #6b7280;
}

.spot-image-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 200px;
}

.image-gallery-preview {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.gallery-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--mbti-primary, #3b82f6);
}

.gallery-icon {
  font-size: 1rem;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 0.5rem;
  max-width: 200px;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-color, #111827);
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--primary-color, #3b82f6);
}

.spot-location-section,
.operating-hours-section,
.mbti-match-section,
.description-section,
.remarks-section,
.features-section,
.admission-section,
.accessibility-section {
  margin-bottom: 1.5rem;
}

.location-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.location-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.location-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 4rem;
  flex-shrink: 0;
}

.location-value {
  color: var(--text-color, #374151);
  flex: 1;
}

.district-name {
  font-weight: 600;
  color: var(--primary-color, #3b82f6);
}

.address-item {
  align-items: flex-start;
}

.address-text {
  line-height: 1.5;
}

.hours-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f9fafb;
  border-radius: 0.375rem;
}

.hours-label {
  font-weight: 500;
  color: #6b7280;
}

.hours-value {
  color: var(--text-color, #374151);
  font-weight: 500;
}

.match-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.match-label {
  font-weight: 500;
  color: #6b7280;
}

.match-value {
  color: var(--text-color, #374151);
}

.mbti-highlight {
  font-weight: 600;
  color: var(--primary-color, #3b82f6);
  padding: 0.25rem 0.5rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 0.25rem;
}

.match-reason {
  padding: 0.75rem;
  background-color: #f0f9ff;
  border-radius: 0.5rem;
  border-left: 4px solid var(--primary-color, #3b82f6);
}

.reason-label {
  display: block;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.reason-text {
  color: var(--text-color, #374151);
  line-height: 1.6;
  margin: 0;
}

.description-content,
.remarks-content {
  padding: 0.75rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border-left: 4px solid var(--primary-color, #3b82f6);
}

.description-text,
.remarks-text {
  color: var(--text-color, #374151);
  line-height: 1.6;
  margin: 0;
}

.features-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.feature-badge {
  padding: 0.375rem 0.75rem;
  background-color: #f3f4f6;
  color: #6b7280;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.admission-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.admission-free {
  display: flex;
  align-items: center;
}

.free-badge {
  padding: 0.5rem 1rem;
  background-color: #ecfdf5;
  color: #059669;
  border-radius: 0.375rem;
  font-weight: 600;
  border: 1px solid #a7f3d0;
}

.admission-fees {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fee-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f9fafb;
  border-radius: 0.375rem;
}

.fee-label {
  font-weight: 500;
  color: #6b7280;
}

.fee-value {
  color: var(--text-color, #374151);
  font-weight: 600;
}

.admission-notes,
.accessibility-notes {
  padding: 0.5rem;
  background-color: #fffbeb;
  border-radius: 0.375rem;
  border-left: 3px solid #f59e0b;
}

.notes-text {
  color: #92400e;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

.accessibility-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.accessibility-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.accessibility-label {
  font-weight: 500;
  color: #6b7280;
}

.accessibility-value {
  color: var(--text-color, #374151);
  font-weight: 500;
}

.accessibility-value.accessible {
  color: #059669;
  font-weight: 600;
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
  border-color: #f59e0b;
}

.mbti-estp .spot-name,
.mbti-estp .section-title,
.mbti-estp .location-value,
.mbti-estp .hours-value,
.mbti-estp .match-value,
.mbti-estp .description-text,
.mbti-estp .remarks-text {
  color: white;
}

.mbti-estp .location-label,
.mbti-estp .hours-label,
.mbti-estp .match-label {
  color: rgba(255, 255, 255, 0.8);
}

.mbti-estp .section-title {
  border-bottom-color: rgba(255, 255, 255, 0.5);
}

.mbti-estp .hours-item,
.mbti-estp .description-content,
.mbti-estp .remarks-content {
  background-color: rgba(255, 255, 255, 0.1);
  border-left-color: rgba(255, 255, 255, 0.5);
}

/* Colorful personalities styling */
.mbti-entp,
.mbti-infp,
.mbti-enfp,
.mbti-isfp {
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
  color: white;
  border-color: #7c3aed;
}

.mbti-entp .spot-name,
.mbti-infp .spot-name,
.mbti-enfp .spot-name,
.mbti-isfp .spot-name,
.mbti-entp .section-title,
.mbti-infp .section-title,
.mbti-enfp .section-title,
.mbti-isfp .section-title {
  color: white;
}

/* Warm tones for ISFJ */
.mbti-isfj {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border-color: #d97706;
}

.mbti-isfj .spot-name,
.mbti-isfj .section-title,
.mbti-isfj .location-value,
.mbti-isfj .hours-value,
.mbti-isfj .match-value,
.mbti-isfj .description-text,
.mbti-isfj .remarks-text {
  color: white;
}

.mbti-isfj .location-label,
.mbti-isfj .hours-label,
.mbti-isfj .match-label {
  color: rgba(255, 255, 255, 0.8);
}

/* Responsive design */
@media (max-width: 768px) {
  .tourist-spot-details {
    padding: 1rem;
  }
  
  .spot-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .spot-image-section {
    min-width: auto;
    width: 100%;
  }
  
  .gallery-grid {
    max-width: none;
    grid-template-columns: repeat(3, 1fr);
  }
  
  .spot-badges {
    justify-content: flex-start;
  }
  
  .location-item,
  .match-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .location-label,
  .match-label {
    min-width: auto;
  }
  
  .hours-item,
  .fee-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .features-grid {
    gap: 0.375rem;
  }
  
  .feature-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .tourist-spot-details {
    border-width: 2px;
  }
  
  .mbti-badge,
  .duration-badge,
  .category-badge,
  .feature-badge {
    border: 1px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .estp-flashy {
    animation: none;
  }
}
</style>
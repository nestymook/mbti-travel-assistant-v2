<template>
  <div class="itinerary-point-form" :class="personalityClass">
    <div class="point-form-header">
      <h2>Your Personalized 3-Day Hong Kong Itinerary</h2>
      <p v-if="isESTP" class="estp-subtitle">🎉 Let's make this trip AMAZING! 🌟</p>
    </div>

    <div class="days-container">
      <div 
        v-for="day in [1, 2, 3]" 
        :key="`day-${day}`" 
        class="day-section"
        :class="getDayClass(day)"
      >
        <div class="day-header">
          <h3>
            <span v-if="isESTP">🗓️</span>
            Day {{ day }}
            <span v-if="isESTP">✨</span>
          </h3>
        </div>

        <div class="day-content">
          <div class="sessions-list">
            <!-- Breakfast -->
            <div class="session-item restaurant-session">
              <div class="session-header">
                <span class="session-icon">🍳</span>
                <h4 class="session-title">Breakfast</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`breakfast-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'breakfast')"
                    class="point-form-combo"
                    @change="onRecommendationChange('breakfast', day, $event)"
                    :aria-label="`Select breakfast for Day ${day}`"
                  >
                    <option 
                      v-for="restaurant in getCandidateRestaurants('breakfast', day)" 
                      :key="restaurant.id"
                      :value="restaurant.name"
                    >
                      {{ restaurant.name }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <RestaurantDetails 
                    v-if="getSelectedRestaurant(day, 'breakfast')"
                    :restaurant="getSelectedRestaurant(day, 'breakfast')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                </div>
              </div>
            </div>

            <!-- Morning Session -->
            <div class="session-item tourist-spot-session">
              <div class="session-header">
                <span class="session-icon">🌅</span>
                <h4 class="session-title">Morning Session</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`morning-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'morning_session')"
                    class="point-form-combo"
                    @change="onRecommendationChange('morning_session', day, $event)"
                    :aria-label="`Select morning activity for Day ${day}`"
                  >
                    <option 
                      v-for="spot in getCandidateTouristSpots('morning_session', day)" 
                      :key="spot.tourist_spot"
                      :value="spot.tourist_spot"
                    >
                      {{ spot.tourist_spot }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <TouristSpotDetails 
                    v-if="getSelectedTouristSpot(day, 'morning_session')"
                    :tourist-spot="getSelectedTouristSpot(day, 'morning_session')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                  <!-- Image placeholder for creative personalities -->
                  <div v-if="shouldShowImages" class="creative-image-placeholder">
                    <ImagePlaceholder
                      :mbti-personality="mbtiPersonality"
                      :title="`${getSelectedTouristSpot(day, 'morning_session')?.tourist_spot} Photos`"
                      :subtitle="getImageSubtitle()"
                      :clickable="true"
                      size="small"
                      variant="spot"
                      @click="handleImageClick('morning_session', day)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Lunch -->
            <div class="session-item restaurant-session">
              <div class="session-header">
                <span class="session-icon">🍽️</span>
                <h4 class="session-title">Lunch</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`lunch-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'lunch')"
                    class="point-form-combo"
                    @change="onRecommendationChange('lunch', day, $event)"
                    :aria-label="`Select lunch for Day ${day}`"
                  >
                    <option 
                      v-for="restaurant in getCandidateRestaurants('lunch', day)" 
                      :key="restaurant.id"
                      :value="restaurant.name"
                    >
                      {{ restaurant.name }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <RestaurantDetails 
                    v-if="getSelectedRestaurant(day, 'lunch')"
                    :restaurant="getSelectedRestaurant(day, 'lunch')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                </div>
              </div>
            </div>

            <!-- Afternoon Session -->
            <div class="session-item tourist-spot-session">
              <div class="session-header">
                <span class="session-icon">☀️</span>
                <h4 class="session-title">Afternoon Session</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`afternoon-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'afternoon_session')"
                    class="point-form-combo"
                    @change="onRecommendationChange('afternoon_session', day, $event)"
                    :aria-label="`Select afternoon activity for Day ${day}`"
                  >
                    <option 
                      v-for="spot in getCandidateTouristSpots('afternoon_session', day)" 
                      :key="spot.tourist_spot"
                      :value="spot.tourist_spot"
                    >
                      {{ spot.tourist_spot }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <TouristSpotDetails 
                    v-if="getSelectedTouristSpot(day, 'afternoon_session')"
                    :tourist-spot="getSelectedTouristSpot(day, 'afternoon_session')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                  <!-- Image placeholder for creative personalities -->
                  <div v-if="shouldShowImages" class="creative-image-placeholder">
                    <ImagePlaceholder
                      :mbti-personality="mbtiPersonality"
                      :title="`${getSelectedTouristSpot(day, 'afternoon_session')?.tourist_spot} Photos`"
                      :subtitle="getImageSubtitle()"
                      :clickable="true"
                      size="small"
                      variant="spot"
                      @click="handleImageClick('afternoon_session', day)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Dinner -->
            <div class="session-item restaurant-session">
              <div class="session-header">
                <span class="session-icon">🍷</span>
                <h4 class="session-title">Dinner</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`dinner-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'dinner')"
                    class="point-form-combo"
                    @change="onRecommendationChange('dinner', day, $event)"
                    :aria-label="`Select dinner for Day ${day}`"
                  >
                    <option 
                      v-for="restaurant in getCandidateRestaurants('dinner', day)" 
                      :key="restaurant.id"
                      :value="restaurant.name"
                    >
                      {{ restaurant.name }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <RestaurantDetails 
                    v-if="getSelectedRestaurant(day, 'dinner')"
                    :restaurant="getSelectedRestaurant(day, 'dinner')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                </div>
              </div>
            </div>

            <!-- Night Session -->
            <div class="session-item tourist-spot-session">
              <div class="session-header">
                <span class="session-icon">🌙</span>
                <h4 class="session-title">Night Session</h4>
              </div>
              <div class="session-content">
                <div class="recommendation-selector">
                  <select 
                    :id="`night-day-${day}`"
                    :value="getSelectedRecommendationName(day, 'night_session')"
                    class="point-form-combo"
                    @change="onRecommendationChange('night_session', day, $event)"
                    :aria-label="`Select night activity for Day ${day}`"
                  >
                    <option 
                      v-for="spot in getCandidateTouristSpots('night_session', day)" 
                      :key="spot.tourist_spot"
                      :value="spot.tourist_spot"
                    >
                      {{ spot.tourist_spot }}
                    </option>
                  </select>
                </div>
                <div class="recommendation-details">
                  <TouristSpotDetails 
                    v-if="getSelectedTouristSpot(day, 'night_session')"
                    :tourist-spot="getSelectedTouristSpot(day, 'night_session')"
                    :mbti-personality="mbtiPersonality"
                    display-mode="point-form"
                  />
                  <!-- Image placeholder for creative personalities -->
                  <div v-if="shouldShowImages" class="creative-image-placeholder">
                    <ImagePlaceholder
                      :mbti-personality="mbtiPersonality"
                      :title="`${getSelectedTouristSpot(day, 'night_session')?.tourist_spot} Photos`"
                      :subtitle="getImageSubtitle()"
                      :clickable="true"
                      size="small"
                      variant="spot"
                      @click="handleImageClick('night_session', day)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { 
  MainItinerary, 
  CandidateTouristSpots, 
  CandidateRestaurants 
} from '@/types/api'
import type { MBTIPersonality } from '@/types/mbti'
import type { TouristSpot } from '@/types/touristSpot'
import type { Restaurant } from '@/types/restaurant'
import RestaurantDetails from './RestaurantDetails.vue'
import TouristSpotDetails from './TouristSpotDetails.vue'
import ImagePlaceholder from '@/components/common/ImagePlaceholder.vue'

// Props
interface Props {
  mainItinerary: MainItinerary
  candidateSpots: CandidateTouristSpots
  candidateRestaurants: CandidateRestaurants
  mbtiPersonality: MBTIPersonality
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'recommendation-change', session: string, day: number, newValue: string): void
}

const emit = defineEmits<Emits>()

// Computed properties
const personalityClass = computed(() => {
  return `personality-${props.mbtiPersonality.toLowerCase()}`
})

const isESTP = computed(() => {
  return props.mbtiPersonality === 'ESTP'
})

// Check if images should be shown for creative personalities
const shouldShowImages = computed(() => {
  const creativeTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP']
  return creativeTypes.includes(props.mbtiPersonality)
})

// Methods
const getDayClass = (day: number): string => {
  const baseClass = `day-${day}`
  if (isESTP.value) {
    return `${baseClass} estp-flashy`
  }
  return baseClass
}

const getSelectedRecommendationName = (day: number, session: string): string => {
  const dayKey = `day_${day}` as keyof MainItinerary
  const dayItinerary = props.mainItinerary[dayKey]
  
  if (!dayItinerary) return ''
  
  const recommendation = dayItinerary[session as keyof typeof dayItinerary]
  
  if (!recommendation) return ''
  
  // Handle both restaurant and tourist spot types
  if ('name' in recommendation) {
    return recommendation.name
  } else if ('tourist_spot' in recommendation) {
    return recommendation.tourist_spot
  }
  
  return ''
}

const getSelectedRestaurant = (day: number, session: string): Restaurant | null => {
  const dayKey = `day_${day}` as keyof MainItinerary
  const dayItinerary = props.mainItinerary[dayKey]
  
  if (!dayItinerary) return null
  
  const recommendation = dayItinerary[session as keyof typeof dayItinerary]
  
  if (recommendation && 'name' in recommendation) {
    return recommendation as Restaurant
  }
  
  return null
}

const getSelectedTouristSpot = (day: number, session: string): TouristSpot | null => {
  const dayKey = `day_${day}` as keyof MainItinerary
  const dayItinerary = props.mainItinerary[dayKey]
  
  if (!dayItinerary) return null
  
  const recommendation = dayItinerary[session as keyof typeof dayItinerary]
  
  if (recommendation && 'tourist_spot' in recommendation) {
    return recommendation as TouristSpot
  }
  
  return null
}

const getCandidateRestaurants = (session: string, day: number): Restaurant[] => {
  const sessionKey = `${session}_day_${day}`
  return props.candidateRestaurants[sessionKey] || []
}

const getCandidateTouristSpots = (session: string, day: number): TouristSpot[] => {
  const sessionKey = `${session}_day_${day}`
  return props.candidateSpots[sessionKey] || []
}

const onRecommendationChange = (session: string, day: number, event: Event): void => {
  const target = event.target as HTMLSelectElement
  const newValue = target.value
  emit('recommendation-change', session, day, newValue)
}

// Get image subtitle based on personality
const getImageSubtitle = (): string => {
  const subtitles: Record<MBTIPersonality, string> = {
    'ENTP': 'Creative perspectives!',
    'INFP': 'Artistic moments',
    'ENFP': 'Vibrant experiences',
    'ISFP': 'Beautiful scenes',
    'ESTP': 'Action shots!'
  }
  return subtitles[props.mbtiPersonality] || 'Amazing views'
}

const handleImageClick = (session: string, day: number): void => {
  const spot = getSelectedTouristSpot(day, session)
  if (spot) {
    // Emit event or show modal - placeholder for actual functionality
    console.log(`🎉 Image gallery for ${spot.tourist_spot} would open here!`)
    // In a real implementation, this would open an image gallery modal
  }
}
</script>

<style scoped>
.itinerary-point-form {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.point-form-header {
  text-align: center;
  margin-bottom: 2rem;
}

.point-form-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color, #2c3e50);
  margin-bottom: 0.5rem;
}

.estp-subtitle {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--accent-color, #e74c3c);
  margin: 0;
  animation: bounce 2s infinite;
}

.days-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.day-section {
  background: var(--background-color, #ffffff);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 2px solid var(--secondary-color, #ecf0f1);
}

.day-section.estp-flashy {
  background: linear-gradient(135deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3);
  background-size: 400% 400%;
  animation: gradientShift 3s ease infinite;
  border: 3px solid #ff6b6b;
  box-shadow: 0 8px 16px rgba(255, 107, 107, 0.3);
}

.day-header {
  margin-bottom: 1.5rem;
  text-align: center;
}

.day-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary-color, #2c3e50);
  margin: 0;
}

.estp-flashy .day-header h3 {
  color: #ffffff;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  font-size: 1.8rem;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.session-item {
  background: var(--session-bg, #f8f9fa);
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid var(--accent-color, #3498db);
}

.estp-flashy .session-item {
  background: rgba(255, 255, 255, 0.9);
  border-left: 4px solid #ff6b6b;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.session-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.session-icon {
  font-size: 1.2rem;
}

.session-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary-color, #2c3e50);
  margin: 0;
}

.estp-flashy .session-title {
  color: #e74c3c;
  font-weight: 700;
}

.session-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendation-selector {
  margin-bottom: 0.5rem;
}

.point-form-combo {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--secondary-color, #bdc3c7);
  border-radius: 6px;
  font-size: 1rem;
  background: white;
  color: var(--text-color, #2c3e50);
  cursor: pointer;
  transition: all 0.3s ease;
}

.point-form-combo:hover {
  border-color: var(--accent-color, #3498db);
}

.point-form-combo:focus {
  outline: none;
  border-color: var(--accent-color, #3498db);
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
}

.estp-flashy .point-form-combo {
  border: 2px solid #ff6b6b;
  font-weight: 600;
}

.estp-flashy .point-form-combo:hover,
.estp-flashy .point-form-combo:focus {
  border-color: #e74c3c;
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.2);
}

.recommendation-details {
  background: white;
  border-radius: 6px;
  padding: 1rem;
  border: 1px solid var(--secondary-color, #ecf0f1);
}

.estp-flashy .recommendation-details {
  border: 2px solid #feca57;
  background: linear-gradient(45deg, #ffffff, #fff9e6);
}

.creative-image-placeholder {
  margin-top: 0.75rem;
}

/* Import colorful personality themes */
@import '../../styles/themes/colorful-personalities.css';

/* Import warm personality themes */
@import '../../styles/themes/warm-personalities.css';

/* Personality-specific styling */
.personality-intp {
  --primary-color: #6c5ce7;
  --secondary-color: #a29bfe;
  --accent-color: #fd79a8;
  --background-color: #f8f9fa;
  --text-color: #2d3436;
}

.personality-istp {
  --primary-color: #00b894;
  --secondary-color: #55efc4;
  --accent-color: #fdcb6e;
  --background-color: #f8f9fa;
  --text-color: #2d3436;
}

.personality-estp {
  --primary-color: #e17055;
  --secondary-color: #fab1a0;
  --accent-color: #fd79a8;
  --background-color: #fff5f5;
  --text-color: #2d3436;
}

/* Animations for ESTP */
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .itinerary-point-form {
    padding: 1rem;
  }
  
  .point-form-header h2 {
    font-size: 1.5rem;
  }
  
  .day-section {
    padding: 1rem;
  }
  
  .sessions-list {
    gap: 1rem;
  }
  
  .session-item {
    padding: 0.75rem;
  }
}

@media (max-width: 480px) {
  .point-form-header h2 {
    font-size: 1.3rem;
  }
  
  .estp-subtitle {
    font-size: 1rem;
  }
  
  .day-header h3 {
    font-size: 1.3rem;
  }
  
  .session-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>
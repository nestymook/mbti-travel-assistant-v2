<template>
  <div class="itinerary-table-container">
    <div class="table-header">
      <h2>Your Personalized 3-Day Hong Kong Itinerary</h2>
    </div>
    
    <div class="table-wrapper" :class="personalityClass">
      <table class="itinerary-table" role="table" :aria-label="`3-day itinerary for ${mbtiPersonality} personality`">
        <thead>
          <tr>
            <th scope="col" class="session-header">Session</th>
            <th scope="col" class="day-header">Day 1</th>
            <th scope="col" class="day-header">Day 2</th>
            <th scope="col" class="day-header">Day 3</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in sessions" :key="session.key" class="session-row">
            <th scope="row" class="session-label">
              {{ session.label }}
            </th>
            <td 
              v-for="day in [1, 2, 3]" 
              :key="`day-${day}`" 
              class="recommendation-cell"
              :class="getCellClass(session.type, day)"
            >
              <div class="cell-content">
                <!-- Combo box for recommendations -->
                <select 
                  :id="`${session.key}-day-${day}`"
                  :value="getOptionLabel(getSelectedRecommendation(day, session.key), session.type)"
                  class="combo-box"
                  :class="getComboBoxClass(session.type)"
                  @change="onRecommendationChange(session.key, day, $event)"
                  :aria-label="`Select ${session.label} for Day ${day}`"
                >
                  <option 
                    v-for="option in getCandidateOptions(session.key, day)" 
                    :key="getOptionKey(option, session.type)"
                    :value="getOptionLabel(option, session.type)"
                  >
                    {{ getOptionLabel(option, session.type) }}
                  </option>
                </select>
                
                <!-- Recommendation details -->
                <div 
                  v-if="getSelectedRecommendation(day, session.key)" 
                  class="recommendation-details"
                  :class="getDetailsClass(session.type)"
                >
                  <div v-if="session.type === 'tourist_spot'" class="tourist-spot-details">
                    <template v-if="getSelectedRecommendation(day, session.key) as TouristSpot">
                      <div class="address">
                        📍 {{ (getSelectedRecommendation(day, session.key) as TouristSpot).address }}
                      </div>
                      <div class="district">
                        🏙️ {{ (getSelectedRecommendation(day, session.key) as TouristSpot).district }}
                      </div>
                      <div class="mbti-match">
                        🎯 Best for: {{ (getSelectedRecommendation(day, session.key) as TouristSpot).mbti }}
                      </div>
                      <div class="hours">
                        🕒 Mon-Fri: {{ (getSelectedRecommendation(day, session.key) as TouristSpot).operating_hours_mon_fri }}
                      </div>
                      <div class="hours">
                        🕒 Weekends: {{ (getSelectedRecommendation(day, session.key) as TouristSpot).operating_hours_sat_sun }}
                      </div>
                      <div v-if="(getSelectedRecommendation(day, session.key) as TouristSpot).remarks" class="remarks">
                        ℹ️ {{ (getSelectedRecommendation(day, session.key) as TouristSpot).remarks }}
                      </div>
                    </template>
                  </div>
                  
                  <div v-else-if="session.type === 'restaurant'" class="restaurant-details-container">
                    <RestaurantDetails
                      v-if="getSelectedRecommendation(day, session.key) as Restaurant"
                      :restaurant="getSelectedRecommendation(day, session.key) as Restaurant"
                      :mbti-personality="mbtiPersonality"
                      :show-detailed-view="false"
                    />
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Personality-specific customizations -->
    <PersonalityCustomizations
      :mbti-personality="mbtiPersonality"
      v-model="itineraryCustomizations"
      @time-changed="onTimeChanged"
      @importance-changed="onImportanceChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, onMounted } from 'vue'
import type { 
  MainItinerary, 
  CandidateTouristSpots, 
  CandidateRestaurants 
} from '../../types/api'
import type { MBTIPersonality, ItineraryCustomization } from '../../types/mbti'
import type { TouristSpot } from '../../types/touristSpot'
import type { Restaurant, PriceRange } from '../../types/restaurant'
import { ThemeService } from '../../services/themeService'
import { useMBTIPerformanceOptimizations, useComponentPerformanceOptimizations } from '../../composables/usePerformanceOptimizations'
import RestaurantDetails from './RestaurantDetails.vue'
import PersonalityCustomizations from './PersonalityCustomizations.vue'

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
  (e: 'recommendation-changed', data: {
    session: string
    day: number
    recommendation: TouristSpot | Restaurant
    type: 'tourist_spot' | 'restaurant'
  }): void
  (e: 'customizations-changed', customizations: ItineraryCustomization): void
}

const emit = defineEmits<Emits>()

// Performance optimizations
const { 
  memoizedPersonalityCalculation, 
  preloadPersonalityChunks,
  recordMetric,
  timeOperation 
} = useMBTIPerformanceOptimizations('ItineraryTable')

const { trackRender } = useComponentPerformanceOptimizations('ItineraryTable')

// Session configuration
const sessions = [
  { key: 'breakfast', label: 'Breakfast', type: 'restaurant' as const },
  { key: 'morning_session', label: 'Morning Session', type: 'tourist_spot' as const },
  { key: 'lunch', label: 'Lunch', type: 'restaurant' as const },
  { key: 'afternoon_session', label: 'Afternoon Session', type: 'tourist_spot' as const },
  { key: 'dinner', label: 'Dinner', type: 'restaurant' as const },
  { key: 'night_session', label: 'Night Session', type: 'tourist_spot' as const }
]

// Reactive state for selected recommendations
const selectedRecommendations = reactive({
  day_1: {} as Record<string, TouristSpot | Restaurant>,
  day_2: {} as Record<string, TouristSpot | Restaurant>,
  day_3: {} as Record<string, TouristSpot | Restaurant>
})

// Reactive state for itinerary customizations
const itineraryCustomizations = reactive<ItineraryCustomization>({
  day_1: {},
  day_2: {},
  day_3: {},
  mbtiPersonality: props.mbtiPersonality,
  lastModified: new Date().toISOString()
})

// Helper function to safely get selected recommendation
const getSelectedRecommendation = (day: number, sessionKey: string): TouristSpot | Restaurant | undefined => {
  const dayKey = `day_${day}` as keyof typeof selectedRecommendations
  return selectedRecommendations[dayKey]?.[sessionKey]
}

// Theme service instance
const themeService = ThemeService.getInstance()

// Memoized computed properties for performance
const personalityClass = computed(() => {
  const endTiming = timeOperation('personality-class-calculation')
  
  try {
    const result = memoizedPersonalityCalculation(props.mbtiPersonality, {
      type: 'class-calculation'
    })
    
    const baseClass = `mbti-${props.mbtiPersonality.toLowerCase()}`
    const additionalClasses = []
    
    if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
      additionalClasses.push('colorful-personality')
    }
    
    if (themeService.isWarmPersonality(props.mbtiPersonality)) {
      additionalClasses.push('warm-personality')
    }
    
    if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
      additionalClasses.push('flashy-personality')
    }
    
    return [baseClass, ...additionalClasses].join(' ')
  } finally {
    endTiming()
  }
})

// Initialize selected recommendations from main itinerary
const initializeRecommendations = () => {
  // Day 1
  selectedRecommendations.day_1.breakfast = props.mainItinerary.day_1.breakfast
  selectedRecommendations.day_1.morning_session = props.mainItinerary.day_1.morning_session
  selectedRecommendations.day_1.lunch = props.mainItinerary.day_1.lunch
  selectedRecommendations.day_1.afternoon_session = props.mainItinerary.day_1.afternoon_session
  selectedRecommendations.day_1.dinner = props.mainItinerary.day_1.dinner
  selectedRecommendations.day_1.night_session = props.mainItinerary.day_1.night_session
  
  // Day 2
  selectedRecommendations.day_2.breakfast = props.mainItinerary.day_2.breakfast
  selectedRecommendations.day_2.morning_session = props.mainItinerary.day_2.morning_session
  selectedRecommendations.day_2.lunch = props.mainItinerary.day_2.lunch
  selectedRecommendations.day_2.afternoon_session = props.mainItinerary.day_2.afternoon_session
  selectedRecommendations.day_2.dinner = props.mainItinerary.day_2.dinner
  selectedRecommendations.day_2.night_session = props.mainItinerary.day_2.night_session
  
  // Day 3
  selectedRecommendations.day_3.breakfast = props.mainItinerary.day_3.breakfast
  selectedRecommendations.day_3.morning_session = props.mainItinerary.day_3.morning_session
  selectedRecommendations.day_3.lunch = props.mainItinerary.day_3.lunch
  selectedRecommendations.day_3.afternoon_session = props.mainItinerary.day_3.afternoon_session
  selectedRecommendations.day_3.dinner = props.mainItinerary.day_3.dinner
  selectedRecommendations.day_3.night_session = props.mainItinerary.day_3.night_session
}

// Get candidate options for a specific session and day
const getCandidateOptions = (sessionKey: string, day: number) => {
  const dayKey = `day_${day}`
  const sessionCandidateKey = `${dayKey}_${sessionKey}`
  
  // Get candidates from the appropriate source
  if (sessions.find(s => s.key === sessionKey)?.type === 'tourist_spot') {
    return props.candidateSpots[sessionCandidateKey] || []
  } else {
    return props.candidateRestaurants[sessionCandidateKey] || []
  }
}

// Get option key for v-for
const getOptionKey = (option: TouristSpot | Restaurant, type: 'tourist_spot' | 'restaurant') => {
  if (!option) return ''
  
  if (type === 'tourist_spot') {
    return (option as TouristSpot).tourist_spot || ''
  } else {
    return (option as Restaurant).id || ''
  }
}

// Get option label for display
const getOptionLabel = (option: TouristSpot | Restaurant | undefined, type: 'tourist_spot' | 'restaurant') => {
  if (!option) return ''
  
  if (type === 'tourist_spot') {
    return (option as TouristSpot).tourist_spot || ''
  } else {
    return (option as Restaurant).name || ''
  }
}

// Handle recommendation change
const onRecommendationChange = (sessionKey: string, day: number, event: Event) => {
  const target = event.target as HTMLSelectElement
  const selectedValue = target.value
  const sessionType = sessions.find(s => s.key === sessionKey)?.type
  
  if (!sessionType) return
  
  // Find the selected recommendation object
  const candidates = getCandidateOptions(sessionKey, day)
  const selectedRecommendation = candidates.find(candidate => {
    return getOptionLabel(candidate, sessionType) === selectedValue
  })
  
  if (selectedRecommendation) {
    // Update the reactive state
    const dayKey = `day_${day}` as keyof typeof selectedRecommendations
    selectedRecommendations[dayKey][sessionKey] = selectedRecommendation
    
    // Emit the change event
    emit('recommendation-changed', {
      session: sessionKey,
      day,
      recommendation: selectedRecommendation,
      type: sessionType
    })
  }
}

// Get CSS class for table cell
const getCellClass = (sessionType: 'tourist_spot' | 'restaurant', day: number) => {
  return [
    `${sessionType}-cell`,
    `day-${day}-cell`,
    'recommendation-cell'
  ].join(' ')
}

// Get CSS class for combo box
const getComboBoxClass = (sessionType: 'tourist_spot' | 'restaurant') => {
  return [
    'combo-box',
    `${sessionType}-combo`,
    'personality-styled'
  ].join(' ')
}

// Get CSS class for details section
const getDetailsClass = (sessionType: 'tourist_spot' | 'restaurant') => {
  return [
    'recommendation-details',
    `${sessionType}-details`
  ].join(' ')
}

// Format price range for display
const formatPriceRange = (priceRange: PriceRange): string => {
  const priceMap: Record<PriceRange, string> = {
    budget: '$ (Under HK$100)',
    moderate: '$$ (HK$100-300)',
    expensive: '$$$ (HK$300-600)',
    luxury: '$$$$ (Over HK$600)'
  }
  return priceMap[priceRange] || priceRange
}

// Handle customization events
const onTimeChanged = (data: { day: number; session: string; type: 'start' | 'end'; time: string }) => {
  // Emit customizations changed event
  emit('customizations-changed', itineraryCustomizations)
}

const onImportanceChanged = (data: { day: number; session: string; isImportant: boolean }) => {
  // Emit customizations changed event
  emit('customizations-changed', itineraryCustomizations)
}

// Watch for prop changes and reinitialize
watch(() => props.mainItinerary, () => {
  initializeRecommendations()
}, { deep: true })

// Apply theme on mount and when personality changes
onMounted(async () => {
  const endTiming = timeOperation('component-mount')
  
  try {
    // Track render performance
    const endRenderTiming = trackRender()
    
    // Apply theme
    themeService.applyMBTITheme(props.mbtiPersonality)
    
    // Initialize recommendations
    initializeRecommendations()
    
    // Preload personality-specific components
    await preloadPersonalityChunks(props.mbtiPersonality)
    
    recordMetric('component-mount-success', 1)
    endRenderTiming()
  } catch (error) {
    recordMetric('component-mount-error', 1)
    console.error('ItineraryTable mount failed:', error)
  } finally {
    endTiming()
  }
})

watch(() => props.mbtiPersonality, (newPersonality) => {
  themeService.applyMBTITheme(newPersonality)
  // Update customizations personality
  itineraryCustomizations.mbtiPersonality = newPersonality
  itineraryCustomizations.lastModified = new Date().toISOString()
})
</script>

<style scoped>
@import '../../styles/components/itinerary-table.css';
@import '../../styles/themes/colorful-personalities.css';

/* Additional component-specific styles */
.itinerary-table-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.table-header {
  text-align: center;
  margin-bottom: 2rem;
}

.table-header h2 {
  color: var(--mbti-primary);
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow);
  background: var(--mbti-surface);
}

.itinerary-table {
  width: 100%;
  min-width: 800px;
  border-collapse: collapse;
  font-family: inherit;
}

.itinerary-table th {
  background: var(--mbti-primary);
  color: var(--mbti-surface);
  padding: 1rem;
  text-align: center;
  font-weight: 600;
  font-size: 1.1rem;
  border: none;
}

.session-header {
  background: var(--mbti-secondary) !important;
  min-width: 150px;
}

.day-header {
  min-width: 250px;
}

.session-row:nth-child(even) {
  background: rgba(0, 0, 0, 0.02);
}

.session-label {
  background: var(--mbti-background);
  color: var(--mbti-primary);
  font-weight: 600;
  padding: 1rem;
  text-align: left;
  border-right: 2px solid var(--mbti-border);
  font-size: 0.95rem;
}

.recommendation-cell {
  padding: 1rem;
  vertical-align: top;
  border-bottom: 1px solid var(--mbti-border);
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.combo-box {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--mbti-border);
  border-radius: 6px;
  background: var(--mbti-surface);
  color: var(--mbti-text);
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.3s ease;
}

.combo-box:hover {
  border-color: var(--mbti-primary);
}

.combo-box:focus {
  outline: none;
  border-color: var(--mbti-primary);
  box-shadow: 0 0 0 3px var(--mbti-focus);
}

.recommendation-details {
  font-size: 0.85rem;
  line-height: 1.4;
  color: var(--mbti-text);
}

.recommendation-details > div {
  margin-bottom: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.recommendation-details > div:last-child {
  margin-bottom: 0;
}

.address {
  color: var(--mbti-secondary);
  font-weight: 500;
}

.district,
.district-price {
  color: var(--mbti-text);
}

.mbti-match {
  color: var(--mbti-accent);
  font-weight: 600;
}

.hours {
  color: var(--mbti-primary);
  font-size: 0.8rem;
}

.remarks {
  color: var(--mbti-secondary);
  font-style: italic;
  font-size: 0.8rem;
}

.meal-type {
  color: var(--mbti-accent);
  font-weight: 500;
}

.sentiment {
  color: var(--mbti-text);
  font-size: 0.8rem;
}

.restaurant-details-container {
  width: 100%;
}

.restaurant-details-container :deep(.restaurant-details) {
  padding: 1rem;
  margin: 0;
  box-shadow: none;
  border: 1px solid var(--mbti-border);
  border-radius: 6px;
}

.restaurant-details-container :deep(.restaurant-header) {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
}

.restaurant-details-container :deep(.restaurant-name) {
  font-size: 1.1rem;
}

.restaurant-details-container :deep(.section-title) {
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
}

.restaurant-details-container :deep(.operating-hours-section),
.restaurant-details-container :deep(.sentiment-section),
.restaurant-details-container :deep(.cuisine-section),
.restaurant-details-container :deep(.features-section),
.restaurant-details-container :deep(.contact-section) {
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.restaurant-details-container :deep(.sentiment-bar) {
  min-height: 2rem;
}

.restaurant-details-container :deep(.bar-label) {
  font-size: 0.8rem;
}

.restaurant-details-container :deep(.features-grid) {
  grid-template-columns: 1fr;
  gap: 0.5rem;
}

/* Personality-specific enhancements */
.colorful-personality .combo-box {
  background: linear-gradient(135deg, var(--mbti-surface) 0%, rgba(255, 255, 255, 0.8) 100%);
}

.colorful-personality .recommendation-details {
  background: linear-gradient(135deg, transparent 0%, var(--mbti-hover) 100%);
  padding: 0.5rem;
  border-radius: 4px;
}

.warm-personality .table-wrapper {
  box-shadow: 0 4px 6px var(--mbti-shadow), 0 0 20px var(--mbti-warm-glow, rgba(255, 193, 7, 0.1));
}

.flashy-personality .combo-box:focus {
  animation: flashy-focus 0.5s ease;
}

@keyframes flashy-focus {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* Responsive design */
@media (max-width: 1024px) {
  .table-wrapper {
    overflow-x: scroll;
  }
  
  .day-header {
    min-width: 220px;
  }
}

@media (max-width: 768px) {
  .itinerary-table-container {
    padding: 0.5rem;
  }
  
  .table-header h2 {
    font-size: 1.5rem;
  }
  
  .itinerary-table {
    min-width: 700px;
    font-size: 0.85rem;
  }
  
  .itinerary-table th,
  .recommendation-cell,
  .session-label {
    padding: 0.75rem;
  }
  
  .session-header {
    min-width: 120px;
  }
  
  .day-header {
    min-width: 200px;
  }
  
  .combo-box {
    padding: 0.6rem;
    font-size: 0.85rem;
  }
  
  .recommendation-details {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .table-header h2 {
    font-size: 1.25rem;
  }
  
  .itinerary-table {
    min-width: 600px;
    font-size: 0.8rem;
  }
  
  .itinerary-table th,
  .recommendation-cell,
  .session-label {
    padding: 0.5rem;
  }
  
  .session-header {
    min-width: 100px;
  }
  
  .day-header {
    min-width: 180px;
  }
  
  .combo-box {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
  
  .recommendation-details {
    font-size: 0.75rem;
  }
  
  .recommendation-details > div {
    margin-bottom: 0.3rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .combo-box,
  .flashy-personality .combo-box:focus {
    transition: none;
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .combo-box {
    border-width: 3px;
  }
  
  .recommendation-details {
    font-weight: 500;
  }
}

/* Print styles */
@media print {
  .itinerary-table-container {
    padding: 0;
  }
  
  .table-wrapper {
    box-shadow: none;
    overflow: visible;
  }
  
  .itinerary-table {
    min-width: auto;
    width: 100%;
  }
  
  .combo-box {
    border: 1px solid #000;
    background: white;
  }
}
</style>
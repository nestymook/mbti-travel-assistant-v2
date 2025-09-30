<template>
  <div class="responsive-itinerary-layout" :class="layoutClasses">
    <!-- Layout toggle for tablets and up -->
    <div v-if="showLayoutToggle" class="layout-toggle" role="tablist" aria-label="Layout options">
      <button
        type="button"
        class="layout-toggle-btn"
        :class="{ active: currentLayout === 'mobile' }"
        role="tab"
        :aria-selected="currentLayout === 'mobile'"
        :aria-controls="mobileLayoutId"
        @click="setLayout('mobile')"
      >
        <span class="toggle-icon">📱</span>
        <span class="toggle-label">Card View</span>
      </button>
      <button
        type="button"
        class="layout-toggle-btn"
        :class="{ active: currentLayout === 'table' }"
        role="tab"
        :aria-selected="currentLayout === 'table'"
        :aria-controls="tableLayoutId"
        @click="setLayout('table')"
      >
        <span class="toggle-icon">📊</span>
        <span class="toggle-label">Table View</span>
      </button>
    </div>

    <!-- Mobile/Card Layout -->
    <div
      v-show="currentLayout === 'mobile'"
      :id="mobileLayoutId"
      class="mobile-layout"
      role="tabpanel"
      :aria-labelledby="currentLayout === 'mobile' ? 'mobile-tab' : undefined"
    >
      <div class="mobile-day-cards">
        <div
          v-for="day in [1, 2, 3]"
          :key="`mobile-day-${day}`"
          class="mobile-day-card"
          :class="getDayCardClasses(day)"
        >
          <div class="mobile-day-header">
            <h3 class="day-title">
              <span class="day-icon">📅</span>
              Day {{ day }}
            </h3>
          </div>
          
          <div class="mobile-sessions">
            <div
              v-for="session in sessions"
              :key="`mobile-${day}-${session.key}`"
              class="mobile-session-item"
              :class="getSessionClasses(session.type)"
            >
              <div class="mobile-session-header">
                <div class="mobile-session-label">
                  <span class="session-icon">{{ getSessionIcon(session.key) }}</span>
                  <span class="session-text">{{ session.label }}</span>
                </div>
                <div v-if="showTimeInputs && isStructuredPersonality" class="session-time-badge">
                  <span class="time-icon">🕒</span>
                </div>
              </div>
              
              <div class="mobile-session-content">
                <div class="mobile-combo-section">
                  <ResponsiveComboBox
                    :model-value="getOptionLabel(getSelectedRecommendation(day, session.key), session.type)"
                    :options="getCandidateOptions(session.key, day)"
                    :label="`Select ${session.label} for Day ${day}`"
                    :placeholder="`Choose ${session.label.toLowerCase()}...`"
                    :mbti-personality="mbtiPersonality"
                    :is-loading="isLoadingRecommendations"
                    size="medium"
                    variant="default"
                    hide-label
                    @change="onRecommendationChange(session.key, day, $event)"
                  />
                </div>
                
                <div
                  v-if="getSelectedRecommendation(day, session.key)"
                  class="mobile-details-section"
                >
                  <div v-if="session.type === 'tourist_spot'" class="tourist-spot-mobile-details">
                    <TouristSpotDetails
                      :tourist-spot="getSelectedRecommendation(day, session.key) as TouristSpot"
                      :mbti-personality="mbtiPersonality"
                      :show-images="showImages"
                      :show-descriptions="showDescriptions"
                      layout="mobile"
                    />
                  </div>
                  
                  <div v-else-if="session.type === 'restaurant'" class="restaurant-mobile-details">
                    <RestaurantDetails
                      :restaurant="getSelectedRecommendation(day, session.key) as Restaurant"
                      :mbti-personality="mbtiPersonality"
                      :show-detailed-view="false"
                      layout="mobile"
                    />
                  </div>
                </div>
              </div>
              
              <!-- Time inputs for structured personalities -->
              <div
                v-if="showTimeInputs && isStructuredPersonality"
                class="mobile-time-inputs"
              >
                <div class="time-input-group">
                  <label :for="`mobile-start-${day}-${session.key}`" class="time-label">
                    Start Time
                  </label>
                  <input
                    :id="`mobile-start-${day}-${session.key}`"
                    type="time"
                    class="time-input"
                    :value="getTimeValue(day, session.key, 'start')"
                    @input="onTimeChanged(day, session.key, 'start', $event)"
                  />
                </div>
                <div class="time-input-group">
                  <label :for="`mobile-end-${day}-${session.key}`" class="time-label">
                    End Time
                  </label>
                  <input
                    :id="`mobile-end-${day}-${session.key}`"
                    type="time"
                    class="time-input"
                    :value="getTimeValue(day, session.key, 'end')"
                    @input="onTimeChanged(day, session.key, 'end', $event)"
                  />
                </div>
              </div>
              
              <!-- Important checkbox for ENTJ -->
              <div
                v-if="showImportantCheckboxes && mbtiPersonality === 'ENTJ' && session.type === 'tourist_spot'"
                class="mobile-important-section"
              >
                <label class="important-checkbox-label">
                  <input
                    type="checkbox"
                    class="important-checkbox"
                    :checked="getImportantValue(day, session.key)"
                    @change="onImportanceChanged(day, session.key, $event)"
                  />
                  <span class="checkbox-text">
                    <span class="important-icon">⭐</span>
                    Important!
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Layout -->
    <div
      v-show="currentLayout === 'table'"
      :id="tableLayoutId"
      class="table-layout"
      role="tabpanel"
      :aria-labelledby="currentLayout === 'table' ? 'table-tab' : undefined"
    >
      <div class="table-wrapper">
        <div class="table-scroll-container">
          <table class="responsive-table" role="table" :aria-label="`3-day itinerary for ${mbtiPersonality} personality`">
            <thead>
              <tr>
                <th scope="col" class="session-header">Session</th>
                <th scope="col" class="day-header">Day 1</th>
                <th scope="col" class="day-header">Day 2</th>
                <th scope="col" class="day-header">Day 3</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in sessions" :key="`table-${session.key}`" class="session-row">
                <th scope="row" class="session-label">
                  <span class="session-icon">{{ getSessionIcon(session.key) }}</span>
                  <span class="session-text">{{ session.label }}</span>
                </th>
                <td
                  v-for="day in [1, 2, 3]"
                  :key="`table-day-${day}`"
                  class="recommendation-cell"
                  :class="getCellClasses(session.type, day)"
                >
                  <div class="cell-content">
                    <ResponsiveComboBox
                      :model-value="getOptionLabel(getSelectedRecommendation(day, session.key), session.type)"
                      :options="getCandidateOptions(session.key, day)"
                      :label="`Select ${session.label} for Day ${day}`"
                      :placeholder="`Choose ${session.label.toLowerCase()}...`"
                      :mbti-personality="mbtiPersonality"
                      :is-loading="isLoadingRecommendations"
                      size="small"
                      variant="outlined"
                      hide-label
                      @change="onRecommendationChange(session.key, day, $event)"
                    />
                    
                    <div
                      v-if="getSelectedRecommendation(day, session.key)"
                      class="table-details-section"
                    >
                      <div v-if="session.type === 'tourist_spot'" class="tourist-spot-table-details">
                        <TouristSpotDetails
                          :tourist-spot="getSelectedRecommendation(day, session.key) as TouristSpot"
                          :mbti-personality="mbtiPersonality"
                          :show-images="false"
                          :show-descriptions="showDescriptions"
                          layout="table"
                        />
                      </div>
                      
                      <div v-else-if="session.type === 'restaurant'" class="restaurant-table-details">
                        <RestaurantDetails
                          :restaurant="getSelectedRecommendation(day, session.key) as Restaurant"
                          :mbti-personality="mbtiPersonality"
                          :show-detailed-view="false"
                          layout="table"
                        />
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import type { 
  MainItinerary, 
  CandidateTouristSpots, 
  CandidateRestaurants 
} from '../../types/api'
import type { MBTIPersonality } from '../../types/mbti'
import type { TouristSpot } from '../../types/touristSpot'
import type { Restaurant } from '../../types/restaurant'
import ResponsiveComboBox from '../common/ResponsiveComboBox.vue'
import TouristSpotDetails from './TouristSpotDetails.vue'
import RestaurantDetails from './RestaurantDetails.vue'

// Props
interface Props {
  mainItinerary: MainItinerary
  candidateSpots: CandidateTouristSpots
  candidateRestaurants: CandidateRestaurants
  mbtiPersonality: MBTIPersonality
  isLoadingRecommendations?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoadingRecommendations: false
})

// Emits
interface Emits {
  (e: 'recommendation-changed', data: {
    session: string
    day: number
    recommendation: TouristSpot | Restaurant
    type: 'tourist_spot' | 'restaurant'
  }): void
  (e: 'time-changed', data: { day: number; session: string; type: 'start' | 'end'; time: string }): void
  (e: 'importance-changed', data: { day: number; session: string; isImportant: boolean }): void
}

const emit = defineEmits<Emits>()

// Reactive state
const currentLayout = ref<'mobile' | 'table'>('mobile')
const screenWidth = ref(window.innerWidth)

// IDs for accessibility
const mobileLayoutId = 'mobile-layout-panel'
const tableLayoutId = 'table-layout-panel'

// Session configuration
const sessions = [
  { key: 'breakfast', label: 'Breakfast', type: 'restaurant' as const },
  { key: 'morning_session', label: 'Morning Session', type: 'tourist_spot' as const },
  { key: 'lunch', label: 'Lunch', type: 'restaurant' as const },
  { key: 'afternoon_session', label: 'Afternoon Session', type: 'tourist_spot' as const },
  { key: 'dinner', label: 'Dinner', type: 'restaurant' as const },
  { key: 'night_session', label: 'Night Session', type: 'tourist_spot' as const }
]

// Computed properties
const showLayoutToggle = computed(() => screenWidth.value >= 768)

const isStructuredPersonality = computed(() => 
  ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(props.mbtiPersonality)
)

const isColorfulPersonality = computed(() => 
  ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESFP'].includes(props.mbtiPersonality)
)

const isFeelingPersonality = computed(() => 
  ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const showTimeInputs = computed(() => isStructuredPersonality.value)
const showImportantCheckboxes = computed(() => props.mbtiPersonality === 'ENTJ')
const showImages = computed(() => isColorfulPersonality.value)
const showDescriptions = computed(() => ['INFJ', 'ISFJ'].includes(props.mbtiPersonality))

const layoutClasses = computed(() => {
  const classes = [`layout-${currentLayout.value}`]
  
  classes.push(`mbti-${props.mbtiPersonality.toLowerCase()}`)
  
  if (isColorfulPersonality.value) classes.push('colorful-personality')
  if (props.mbtiPersonality === 'ISFJ') classes.push('warm-personality')
  if (props.mbtiPersonality === 'ESTP') classes.push('flashy-personality')
  
  return classes
})

// Helper functions
const getSelectedRecommendation = (day: number, sessionKey: string): TouristSpot | Restaurant | undefined => {
  const dayKey = `day_${day}` as keyof MainItinerary
  const dayData = props.mainItinerary[dayKey]
  return dayData?.[sessionKey as keyof typeof dayData]
}

const getCandidateOptions = (sessionKey: string, day: number) => {
  const dayKey = `day_${day}`
  const sessionCandidateKey = `${dayKey}_${sessionKey}`
  
  if (sessions.find(s => s.key === sessionKey)?.type === 'tourist_spot') {
    return props.candidateSpots[sessionCandidateKey] || []
  } else {
    return props.candidateRestaurants[sessionCandidateKey] || []
  }
}

const getOptionLabel = (option: TouristSpot | Restaurant | undefined, type: 'tourist_spot' | 'restaurant') => {
  if (!option) return ''
  
  if (type === 'tourist_spot') {
    return (option as TouristSpot).tourist_spot || ''
  } else {
    return (option as Restaurant).name || ''
  }
}

const getSessionIcon = (sessionKey: string): string => {
  const iconMap: Record<string, string> = {
    breakfast: '🍳',
    morning_session: '🌅',
    lunch: '🍽️',
    afternoon_session: '☀️',
    dinner: '🍷',
    night_session: '🌙'
  }
  return iconMap[sessionKey] || '📍'
}

const getDayCardClasses = (day: number) => {
  return [`day-${day}`, 'mobile-card']
}

const getSessionClasses = (type: 'tourist_spot' | 'restaurant') => {
  return [`${type}-session`, 'session-item']
}

const getCellClasses = (type: 'tourist_spot' | 'restaurant', day: number) => {
  return [`${type}-cell`, `day-${day}-cell`]
}

const getTimeValue = (day: number, session: string, type: 'start' | 'end'): string => {
  // This would be connected to your time management state
  return ''
}

const getImportantValue = (day: number, session: string): boolean => {
  // This would be connected to your importance state
  return false
}

// Event handlers
const setLayout = (layout: 'mobile' | 'table') => {
  currentLayout.value = layout
  
  // Save preference to localStorage
  localStorage.setItem('itinerary-layout-preference', layout)
}

const onRecommendationChange = (sessionKey: string, day: number, value: string | number | null) => {
  const sessionType = sessions.find(s => s.key === sessionKey)?.type
  if (!sessionType) return
  
  const candidates = getCandidateOptions(sessionKey, day)
  const selectedRecommendation = candidates.find(candidate => {
    return getOptionLabel(candidate, sessionType) === value
  })
  
  if (selectedRecommendation) {
    emit('recommendation-changed', {
      session: sessionKey,
      day,
      recommendation: selectedRecommendation,
      type: sessionType
    })
  }
}

const onTimeChanged = (day: number, session: string, type: 'start' | 'end', event: Event) => {
  const target = event.target as HTMLInputElement
  emit('time-changed', { day, session, type, time: target.value })
}

const onImportanceChanged = (day: number, session: string, event: Event) => {
  const target = event.target as HTMLInputElement
  emit('importance-changed', { day, session, isImportant: target.checked })
}

// Responsive handling
const handleResize = () => {
  screenWidth.value = window.innerWidth
  
  // Auto-switch to mobile layout on small screens
  if (screenWidth.value < 768) {
    currentLayout.value = 'mobile'
  }
}

// Lifecycle
onMounted(() => {
  // Load saved layout preference
  const savedLayout = localStorage.getItem('itinerary-layout-preference') as 'mobile' | 'table'
  if (savedLayout && screenWidth.value >= 768) {
    currentLayout.value = savedLayout
  }
  
  // Set up resize listener
  window.addEventListener('resize', handleResize)
})

// Cleanup
watch(() => {}, () => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
@import '../../styles/components/responsive-table.css';

/* Layout container */
.responsive-itinerary-layout {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-md, 1rem);
}

/* Layout toggle */
.layout-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: var(--spacing-lg, 1.5rem);
  gap: var(--spacing-sm, 0.5rem);
  padding: var(--spacing-sm, 0.5rem);
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
  border-radius: 12px;
  border: 1px solid var(--mbti-border, #dee2e6);
}

.layout-toggle-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 0.5rem);
  padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
  border: 2px solid var(--mbti-primary, #007bff);
  background: transparent;
  color: var(--mbti-primary, #007bff);
  border-radius: 8px;
  cursor: pointer;
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 600;
  transition: all 0.2s ease;
  min-height: var(--touch-target-min, 44px);
}

.layout-toggle-btn.active {
  background: var(--mbti-primary, #007bff);
  color: var(--mbti-surface, #ffffff);
}

.layout-toggle-btn:hover {
  background: var(--mbti-primary, #007bff);
  color: var(--mbti-surface, #ffffff);
  transform: translateY(-1px);
}

.toggle-icon {
  font-size: 1.2em;
}

.toggle-label {
  font-weight: 600;
}

/* Mobile layout */
.mobile-layout {
  width: 100%;
}

.mobile-day-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl, 2rem);
}

.mobile-day-card {
  background: var(--mbti-surface, #ffffff);
  border: 2px solid var(--mbti-border, #dee2e6);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
}

.mobile-day-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 12px var(--mbti-shadow, rgba(0, 0, 0, 0.15));
}

.mobile-day-header {
  background: var(--mbti-primary, #007bff);
  color: var(--mbti-surface, #ffffff);
  padding: var(--spacing-lg, 1.5rem);
  text-align: center;
}

.day-title {
  margin: 0;
  font-size: var(--font-size-xl, 1.25rem);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm, 0.5rem);
}

.day-icon {
  font-size: 1.3em;
}

.mobile-sessions {
  padding: var(--spacing-md, 1rem);
}

.mobile-session-item {
  border-bottom: 1px solid var(--mbti-border, #dee2e6);
  padding: var(--spacing-lg, 1.5rem) 0;
}

.mobile-session-item:last-child {
  border-bottom: none;
}

.mobile-session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md, 1rem);
  padding-bottom: var(--spacing-sm, 0.5rem);
  border-bottom: 1px solid var(--mbti-hover, rgba(0, 123, 255, 0.1));
}

.mobile-session-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 0.5rem);
  font-weight: 700;
  color: var(--mbti-primary, #007bff);
  font-size: var(--font-size-lg, 1.125rem);
}

.session-icon {
  font-size: 1.3em;
}

.session-text {
  font-weight: 700;
}

.time-icon {
  opacity: 0.7;
}

.mobile-session-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg, 1.5rem);
}

.mobile-combo-section {
  flex: 1;
}

.mobile-details-section {
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
  border-radius: 12px;
  padding: var(--spacing-md, 1rem);
  border: 1px solid var(--mbti-border, #dee2e6);
}

/* Time inputs */
.mobile-time-inputs {
  display: flex;
  gap: var(--spacing-md, 1rem);
  margin-top: var(--spacing-md, 1rem);
  padding: var(--spacing-md, 1rem);
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
  border-radius: 8px;
  border: 1px solid var(--mbti-border, #dee2e6);
}

.time-input-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs, 0.25rem);
}

.time-label {
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 600;
  color: var(--mbti-text, #212529);
}

.time-input {
  padding: var(--spacing-sm, 0.5rem);
  border: 1px solid var(--mbti-border, #dee2e6);
  border-radius: 6px;
  background: var(--mbti-surface, #ffffff);
  color: var(--mbti-text, #212529);
  font-size: var(--font-size-sm, 0.875rem);
  min-height: var(--touch-target-min, 44px);
}

.time-input:focus {
  outline: none;
  border-color: var(--mbti-primary, #007bff);
  box-shadow: 0 0 0 2px var(--mbti-focus, rgba(0, 123, 255, 0.25));
}

/* Important checkbox */
.mobile-important-section {
  margin-top: var(--spacing-md, 1rem);
  padding: var(--spacing-sm, 0.5rem);
}

.important-checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 0.5rem);
  cursor: pointer;
  font-weight: 600;
  color: var(--mbti-accent, #28a745);
}

.important-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.checkbox-text {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs, 0.25rem);
}

.important-icon {
  font-size: 1.1em;
}

/* Table layout */
.table-layout {
  width: 100%;
}

.table-wrapper {
  background: var(--mbti-surface, #ffffff);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.table-scroll-container {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.responsive-table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
}

.responsive-table th,
.responsive-table td {
  padding: var(--spacing-md, 1rem);
  text-align: left;
  border-bottom: 1px solid var(--mbti-border, #dee2e6);
  vertical-align: top;
}

.responsive-table th {
  background: var(--mbti-primary, #007bff);
  color: var(--mbti-surface, #ffffff);
  font-weight: 700;
  text-align: center;
  position: sticky;
  top: 0;
  z-index: 10;
}

.session-header {
  background: var(--mbti-secondary, #6c757d) !important;
  min-width: 180px;
  text-align: left !important;
}

.day-header {
  min-width: 300px;
}

.session-label {
  background: var(--mbti-background, #f8f9fa);
  color: var(--mbti-primary, #007bff);
  font-weight: 700;
  border-right: 2px solid var(--mbti-border, #dee2e6);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 0.5rem);
}

.recommendation-cell {
  min-width: 280px;
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md, 1rem);
}

.table-details-section {
  font-size: var(--font-size-sm, 0.875rem);
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
  padding: var(--spacing-sm, 0.5rem);
  border-radius: 6px;
  border: 1px solid var(--mbti-border, #dee2e6);
}

/* Responsive breakpoints */
@media (min-width: 480px) {
  .mobile-session-content {
    flex-direction: row;
    align-items: flex-start;
  }
  
  .mobile-combo-section {
    flex: 1;
    min-width: 250px;
  }
  
  .mobile-details-section {
    flex: 2;
    min-width: 300px;
  }
}

@media (min-width: 768px) {
  .responsive-itinerary-layout {
    padding: var(--spacing-xl, 2rem);
  }
  
  .mobile-day-cards {
    gap: var(--spacing-xxl, 3rem);
  }
}

@media (min-width: 1024px) {
  .day-header {
    min-width: 350px;
  }
  
  .recommendation-cell {
    min-width: 320px;
  }
}

/* Personality-specific enhancements */
.colorful-personality .mobile-day-header {
  background: linear-gradient(135deg, var(--mbti-primary, #007bff), var(--mbti-accent, #28a745));
}

.colorful-personality .mobile-day-card:hover {
  box-shadow: 0 8px 12px var(--mbti-shadow, rgba(0, 0, 0, 0.15)), 
              0 0 20px var(--mbti-accent, rgba(40, 167, 69, 0.2));
}

.warm-personality .mobile-day-card {
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1)), 
              0 0 15px var(--mbti-warm-glow, rgba(255, 193, 7, 0.1));
}

.flashy-personality .mobile-day-card:hover {
  animation: flashy-card-hover 0.5s ease;
}

@keyframes flashy-card-hover {
  0%, 100% { transform: translateY(-2px) scale(1); }
  50% { transform: translateY(-2px) scale(1.02); }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .mobile-day-card,
  .layout-toggle-btn {
    transition: none;
  }
  
  .mobile-day-card:hover {
    transform: none;
  }
  
  .flashy-personality .mobile-day-card:hover {
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .mobile-day-card {
    border-width: 3px;
  }
  
  .layout-toggle-btn {
    border-width: 3px;
  }
  
  .responsive-table th {
    border: 2px solid currentColor;
  }
}

/* Print styles */
@media print {
  .layout-toggle {
    display: none;
  }
  
  .table-layout {
    display: none;
  }
  
  .mobile-layout {
    display: block !important;
  }
  
  .mobile-day-header {
    background: transparent !important;
    color: #000 !important;
    border: 2px solid #000;
  }
  
  .mobile-day-card {
    border: 2px solid #000;
    box-shadow: none;
    break-inside: avoid;
    margin-bottom: var(--spacing-lg, 1.5rem);
  }
}

/* Focus management */
.layout-toggle-btn:focus-visible,
.time-input:focus-visible,
.important-checkbox:focus-visible {
  outline: 2px solid var(--mbti-primary, #007bff);
  outline-offset: 2px;
}

/* Touch feedback */
@media (hover: none) and (pointer: coarse) {
  .layout-toggle-btn:active {
    transform: scale(0.95);
  }
  
  .mobile-day-card:active {
    transform: scale(0.98);
  }
}
</style>
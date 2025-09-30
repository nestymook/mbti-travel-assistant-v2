<template>
  <div 
    v-if="showCustomizations" 
    class="personality-customizations"
    :class="personalityClass"
  >
    <div class="customizations-header">
      <h3>{{ getCustomizationTitle() }}</h3>
      <p class="customization-description">{{ getCustomizationDescription() }}</p>
    </div>

    <!-- Structured Personality Customizations (INTJ, ENTJ, ISTJ, ESTJ) -->
    <div v-if="isStructuredPersonality" class="structured-customizations">
      <div 
        v-for="day in [1, 2, 3]" 
        :key="`day-${day}`" 
        class="day-customizations"
      >
        <h4 class="day-title">Day {{ day }} Time Planning</h4>
        
        <div class="sessions-grid">
          <div 
            v-for="session in sessions" 
            :key="`day-${day}-${session.key}`"
            class="session-customization"
            :class="getSessionClass(session.type)"
          >
            <div class="session-header">
              <span class="session-name">{{ session.label }}</span>
              <span class="session-type-badge" :class="session.type">
                {{ session.type === 'tourist_spot' ? '🏛️' : '🍽️' }}
              </span>
            </div>

            <!-- Time Input Fields for all structured personalities -->
            <div class="time-inputs">
              <div class="time-input-group">
                <label 
                  :for="`start-time-day-${day}-${session.key}`"
                  class="time-label"
                >
                  Target Start Time
                </label>
                <input
                  :id="`start-time-day-${day}-${session.key}`"
                  v-model="customizations[`day_${day}`][session.key].targetStartTime"
                  type="time"
                  class="time-input"
                  :class="{ 'has-value': customizations[`day_${day}`][session.key].targetStartTime }"
                  @input="onTimeChange(day, session.key, 'start', $event)"
                  :aria-label="`Target start time for ${session.label} on Day ${day}`"
                />
              </div>

              <div class="time-input-group">
                <label 
                  :for="`end-time-day-${day}-${session.key}`"
                  class="time-label"
                >
                  Target End Time
                </label>
                <input
                  :id="`end-time-day-${day}-${session.key}`"
                  v-model="customizations[`day_${day}`][session.key].targetEndTime"
                  type="time"
                  class="time-input"
                  :class="{ 'has-value': customizations[`day_${day}`][session.key].targetEndTime }"
                  @input="onTimeChange(day, session.key, 'end', $event)"
                  :aria-label="`Target end time for ${session.label} on Day ${day}`"
                />
              </div>
            </div>

            <!-- Important Checkbox for ENTJ and Tourist Spots only -->
            <div 
              v-if="mbtiPersonality === 'ENTJ' && session.type === 'tourist_spot'"
              class="importance-checkbox"
            >
              <label 
                :for="`important-day-${day}-${session.key}`"
                class="checkbox-label"
              >
                <input
                  :id="`important-day-${day}-${session.key}`"
                  v-model="customizations[`day_${day}`][session.key].isImportant"
                  type="checkbox"
                  class="importance-input"
                  @change="onImportanceChange(day, session.key, $event)"
                  :aria-label="`Mark ${session.label} as important for Day ${day}`"
                />
                <span class="checkbox-text">
                  <strong>Important!</strong> 
                  <span class="importance-description">High priority activity</span>
                </span>
              </label>
            </div>

            <!-- Time Validation Messages -->
            <div 
              v-if="getTimeValidationMessage(day, session.key)"
              class="validation-message"
              role="alert"
            >
              {{ getTimeValidationMessage(day, session.key) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Section -->
    <div v-if="hasAnyCustomizations" class="customizations-summary">
      <h4>Planning Summary</h4>
      <div class="summary-stats">
        <div class="stat-item">
          <span class="stat-label">Sessions with timing:</span>
          <span class="stat-value">{{ getTimedSessionsCount() }}</span>
        </div>
        <div v-if="mbtiPersonality === 'ENTJ'" class="stat-item">
          <span class="stat-label">Important activities:</span>
          <span class="stat-value">{{ getImportantActivitiesCount() }}</span>
        </div>
      </div>
    </div>

    <!-- Feeling Personality Customizations -->
    <FeelingPersonalityCustomizations
      v-if="isFeelingPersonality"
      :mbti-personality="mbtiPersonality"
      :main-itinerary="mainItinerary"
      :candidate-spots="candidateSpots"
      :model-value="feelingCustomizations"
      @update:model-value="onFeelingCustomizationsUpdate"
      @group-notes-changed="onGroupNotesChanged"
      @share-requested="onShareRequested"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, onMounted, ref } from 'vue'
import type { 
  MBTIPersonality, 
  ItineraryCustomization, 
  SessionCustomization,
  MainItinerary,
  CandidateTouristSpots
} from '../../types/mbti'
import { PERSONALITY_CATEGORIES } from '../../types/mbti'
import { ValidationService } from '../../services/validationService'
import FeelingPersonalityCustomizations from './FeelingPersonalityCustomizations.vue'

// Props
interface Props {
  mbtiPersonality: MBTIPersonality
  mainItinerary?: MainItinerary
  candidateSpots?: CandidateTouristSpots
  modelValue?: ItineraryCustomization
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'update:modelValue', value: ItineraryCustomization): void
  (e: 'time-changed', data: {
    day: number
    session: string
    type: 'start' | 'end'
    time: string
  }): void
  (e: 'importance-changed', data: {
    day: number
    session: string
    isImportant: boolean
  }): void
  (e: 'group-notes-changed', data: {
    day: number
    session: string
    notes: string
  }): void
  (e: 'share-requested', data: {
    type: 'complete' | 'day' | 'notes'
    personality: MBTIPersonality
  }): void
}

const emit = defineEmits<Emits>()

// Session configuration
const sessions = [
  { key: 'breakfast', label: 'Breakfast', type: 'restaurant' as const },
  { key: 'morning_session', label: 'Morning Session', type: 'tourist_spot' as const },
  { key: 'lunch', label: 'Lunch', type: 'restaurant' as const },
  { key: 'afternoon_session', label: 'Afternoon Session', type: 'tourist_spot' as const },
  { key: 'dinner', label: 'Dinner', type: 'restaurant' as const },
  { key: 'night_session', label: 'Night Session', type: 'tourist_spot' as const }
]

// Validation service instance
const validationService = ValidationService.getInstance()

// Feeling personality customizations state
const feelingCustomizations = ref<ItineraryCustomization | undefined>()

// Reactive customizations state
const customizations = reactive<{
  day_1: Record<string, SessionCustomization>
  day_2: Record<string, SessionCustomization>
  day_3: Record<string, SessionCustomization>
}>({
  day_1: {},
  day_2: {},
  day_3: {}
})

// Initialize customizations immediately
const initializeCustomizations = () => {
  // Initialize each day's customizations
  ['day_1', 'day_2', 'day_3'].forEach(dayKey => {
    if (!customizations[dayKey as keyof typeof customizations]) {
      customizations[dayKey as keyof typeof customizations] = {}
    }
  })
  
  sessions.forEach(session => {
    [1, 2, 3].forEach(day => {
      const dayKey = `day_${day}` as keyof typeof customizations
      if (!customizations[dayKey][session.key]) {
        customizations[dayKey][session.key] = {
          targetStartTime: '',
          targetEndTime: '',
          isImportant: false,
          groupNotes: '',
          personalNotes: ''
        }
      }
    })
  })
}

// Initialize immediately
initializeCustomizations()



// Computed properties
const isStructuredPersonality = computed(() => 
  PERSONALITY_CATEGORIES.structured.includes(props.mbtiPersonality)
)

const isFeelingPersonality = computed(() => 
  PERSONALITY_CATEGORIES.feeling.includes(props.mbtiPersonality)
)

const showCustomizations = computed(() => 
  isStructuredPersonality.value || isFeelingPersonality.value
)

const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

const hasAnyCustomizations = computed(() => {
  return Object.values(customizations).some(dayCustomizations =>
    Object.values(dayCustomizations).some(session =>
      session.targetStartTime || session.targetEndTime || session.isImportant
    )
  )
})

// Helper functions
const getCustomizationTitle = (): string => {
  const titles: Record<string, string> = {
    INTJ: 'Strategic Time Planning',
    ENTJ: 'Executive Schedule Management',
    ISTJ: 'Detailed Time Organization',
    ESTJ: 'Structured Activity Planning'
  }
  return titles[props.mbtiPersonality] || 'Time Planning'
}

const getCustomizationDescription = (): string => {
  const descriptions: Record<string, string> = {
    INTJ: 'Plan your itinerary with strategic timing to maximize efficiency and minimize disruptions.',
    ENTJ: 'Organize your schedule with executive precision and mark critical activities as important.',
    ISTJ: 'Create a detailed timeline with specific start and end times for each activity.',
    ESTJ: 'Structure your itinerary with clear time boundaries and organized planning.'
  }
  return descriptions[props.mbtiPersonality] || 'Customize your itinerary timing.'
}

const getSessionClass = (sessionType: 'tourist_spot' | 'restaurant'): string => {
  return `session-${sessionType}`
}

// Time validation using ValidationService
const getTimeValidationMessage = (day: number, sessionKey: string): string | null => {
  const dayKey = `day_${day}` as keyof typeof customizations
  const session = customizations[dayKey][sessionKey]
  
  if (!session) return null
  
  const validation = validationService.validateTimeRange(
    session.targetStartTime || '', 
    session.targetEndTime || ''
  )
  
  return validation.isValid ? null : validation.message || null
}

// Event handlers
const onTimeChange = (day: number, sessionKey: string, type: 'start' | 'end', event: Event) => {
  const target = event.target as HTMLInputElement
  const time = target.value
  
  // Format the time for consistency
  const formattedTime = validationService.formatTime(time)
  
  // Update the input value with formatted time
  if (formattedTime !== time) {
    target.value = formattedTime
  }
  
  emit('time-changed', {
    day,
    session: sessionKey,
    type,
    time: formattedTime
  })
  
  emitModelUpdate()
}

const onImportanceChange = (day: number, sessionKey: string, event: Event) => {
  const target = event.target as HTMLInputElement
  const isImportant = target.checked
  
  emit('importance-changed', {
    day,
    session: sessionKey,
    isImportant
  })
  
  emitModelUpdate()
}

const onGroupNotesChanged = (data: { day: number; session: string; notes: string }) => {
  emit('group-notes-changed', data)
}

const onShareRequested = (data: { type: 'complete' | 'day' | 'notes'; personality: MBTIPersonality }) => {
  emit('share-requested', data)
}

const onFeelingCustomizationsUpdate = (value: ItineraryCustomization) => {
  feelingCustomizations.value = value
  emit('update:modelValue', value)
}

const emitModelUpdate = () => {
  const itineraryCustomization: ItineraryCustomization = {
    day_1: customizations.day_1,
    day_2: customizations.day_2,
    day_3: customizations.day_3,
    mbtiPersonality: props.mbtiPersonality,
    lastModified: new Date().toISOString()
  }
  
  emit('update:modelValue', itineraryCustomization)
}

// Statistics
const getTimedSessionsCount = (): number => {
  let count = 0
  Object.values(customizations).forEach(dayCustomizations =>
    Object.values(dayCustomizations).forEach(session => {
      if (session.targetStartTime || session.targetEndTime) {
        count++
      }
    })
  )
  return count
}

const getImportantActivitiesCount = (): number => {
  let count = 0
  Object.values(customizations).forEach(dayCustomizations =>
    Object.values(dayCustomizations).forEach(session => {
      if (session.isImportant) {
        count++
      }
    })
  )
  return count
}

// Initialize on mount
onMounted(() => {
  initializeCustomizations()
  
  // Load existing customizations if provided
  if (props.modelValue) {
    Object.assign(customizations.day_1, props.modelValue.day_1)
    Object.assign(customizations.day_2, props.modelValue.day_2)
    Object.assign(customizations.day_3, props.modelValue.day_3)
    feelingCustomizations.value = props.modelValue
  }
})

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    Object.assign(customizations.day_1, newValue.day_1)
    Object.assign(customizations.day_2, newValue.day_2)
    Object.assign(customizations.day_3, newValue.day_3)
    feelingCustomizations.value = newValue
  }
}, { deep: true })

watch(() => props.mbtiPersonality, () => {
  initializeCustomizations()
})
</script>

<style scoped>
.personality-customizations {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--mbti-surface);
  border: 2px solid var(--mbti-border);
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow);
}

.customizations-header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--mbti-border);
}

.customizations-header h3 {
  color: var(--mbti-primary);
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.customization-description {
  color: var(--mbti-text);
  font-size: 1rem;
  margin: 0;
  line-height: 1.5;
}

.structured-customizations {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.day-customizations {
  background: var(--mbti-background);
  border: 1px solid var(--mbti-border);
  border-radius: 8px;
  padding: 1.5rem;
}

.day-title {
  color: var(--mbti-primary);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 1.5rem 0;
  text-align: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--mbti-border);
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.session-customization {
  background: var(--mbti-surface);
  border: 1px solid var(--mbti-border);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.session-customization:hover {
  border-color: var(--mbti-primary);
  box-shadow: 0 2px 4px var(--mbti-shadow);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--mbti-border);
}

.session-name {
  font-weight: 600;
  color: var(--mbti-primary);
  font-size: 1rem;
}

.session-type-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.session-type-badge.tourist_spot {
  background: var(--mbti-accent);
  color: var(--mbti-surface);
}

.session-type-badge.restaurant {
  background: var(--mbti-secondary);
  color: var(--mbti-surface);
}

.time-inputs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.time-input-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.time-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--mbti-text);
}

.time-input {
  padding: 0.75rem;
  border: 2px solid var(--mbti-border);
  border-radius: 6px;
  background: var(--mbti-surface);
  color: var(--mbti-text);
  font-size: 0.875rem;
  font-family: inherit;
  transition: all 0.3s ease;
}

.time-input:focus {
  outline: none;
  border-color: var(--mbti-primary);
  box-shadow: 0 0 0 3px var(--mbti-focus);
}

.time-input.has-value {
  border-color: var(--mbti-accent);
  background: var(--mbti-hover);
}

.importance-checkbox {
  margin-top: 1rem;
  padding: 0.75rem;
  background: var(--mbti-hover);
  border: 1px solid var(--mbti-accent);
  border-radius: 6px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.importance-input {
  width: 1.25rem;
  height: 1.25rem;
  accent-color: var(--mbti-accent);
  cursor: pointer;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  color: var(--mbti-accent);
  font-weight: 600;
}

.importance-description {
  color: var(--mbti-text);
  font-size: 0.8rem;
  opacity: 0.8;
}

.validation-message {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c33;
  font-size: 0.8rem;
  font-weight: 500;
}

.customizations-summary {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--mbti-hover);
  border: 1px solid var(--mbti-border);
  border-radius: 8px;
}

.customizations-summary h4 {
  color: var(--mbti-primary);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  text-align: center;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--mbti-text);
  opacity: 0.8;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--mbti-accent);
}

/* Personality-specific styling */
.mbti-intj {
  --mbti-focus: rgba(106, 90, 205, 0.3);
}

.mbti-entj {
  --mbti-focus: rgba(255, 69, 0, 0.3);
}

.mbti-entj .importance-checkbox {
  background: linear-gradient(135deg, var(--mbti-hover) 0%, rgba(255, 69, 0, 0.1) 100%);
  border-color: var(--mbti-accent);
}

.mbti-istj {
  --mbti-focus: rgba(70, 130, 180, 0.3);
}

.mbti-estj {
  --mbti-focus: rgba(34, 139, 34, 0.3);
}

/* Responsive design */
@media (max-width: 768px) {
  .personality-customizations {
    padding: 1rem;
  }
  
  .sessions-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .time-inputs {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .summary-stats {
    flex-direction: column;
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .customizations-header h3 {
    font-size: 1.25rem;
  }
  
  .customization-description {
    font-size: 0.875rem;
  }
  
  .day-title {
    font-size: 1.1rem;
  }
  
  .session-customization {
    padding: 0.75rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .session-customization,
  .time-input {
    transition: none;
  }
}

@media (prefers-contrast: high) {
  .time-input {
    border-width: 3px;
  }
  
  .validation-message {
    border-width: 2px;
    font-weight: 600;
  }
}

/* Import warm personality themes */
@import '../../styles/themes/warm-personalities.css';

/* Print styles */
@media print {
  .personality-customizations {
    box-shadow: none;
    border: 1px solid #000;
  }
  
  .time-input {
    border: 1px solid #000;
    background: white;
  }
  
  .importance-checkbox {
    background: white;
    border: 1px solid #000;
  }
}
</style>
<template>
  <div 
    v-if="showFeelingCustomizations" 
    class="feeling-personality-customizations"
    :class="personalityClass"
  >
    <div class="customizations-header">
      <h3>{{ getCustomizationTitle() }}</h3>
      <p class="customization-description">{{ getCustomizationDescription() }}</p>
    </div>

    <!-- Description Display for INFJ and ISFJ -->
    <div 
      v-if="shouldShowDescriptions" 
      class="description-customizations"
    >
      <h4 class="section-title">Tourist Spot Descriptions</h4>
      <p class="section-description">
        Detailed descriptions help you connect emotionally with each destination.
      </p>
      
      <div 
        v-for="day in [1, 2, 3]" 
        :key="`descriptions-day-${day}`" 
        class="day-descriptions"
      >
        <h5 class="day-title">Day {{ day }} Descriptions</h5>
        
        <div class="tourist-spot-descriptions">
          <div 
            v-for="session in touristSpotSessions" 
            :key="`desc-day-${day}-${session.key}`"
            class="spot-description-item"
          >
            <div class="spot-header">
              <span class="spot-icon">{{ session.icon }}</span>
              <span class="spot-name">{{ session.label }}</span>
            </div>
            
            <div class="description-content">
              <div 
                v-if="getSpotDescription(day, session.key)"
                class="description-text"
              >
                {{ getSpotDescription(day, session.key) }}
              </div>
              <div v-else class="no-description">
                <em>Description will be available when you select a tourist spot.</em>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Group Notes for ENFJ and ESFJ -->
    <div 
      v-if="shouldShowGroupNotes" 
      class="group-notes-customizations"
    >
      <h4 class="section-title">Group Notes</h4>
      <p class="section-description">
        Share your thoughts and plans with friends and family for each activity.
      </p>
      
      <div 
        v-for="day in [1, 2, 3]" 
        :key="`group-notes-day-${day}`" 
        class="day-group-notes"
      >
        <h5 class="day-title">Day {{ day }} Group Notes</h5>
        
        <div class="group-notes-grid">
          <div 
            v-for="session in allSessions" 
            :key="`notes-day-${day}-${session.key}`"
            class="session-group-notes"
            :class="getSessionClass(session.type)"
          >
            <div class="session-header">
              <span class="session-icon">{{ session.icon }}</span>
              <span class="session-name">{{ session.label }}</span>
            </div>
            
            <div class="group-notes-input">
              <label 
                :for="`group-notes-day-${day}-${session.key}`"
                class="notes-label"
              >
                Group Notes:
              </label>
              <textarea
                :id="`group-notes-day-${day}-${session.key}`"
                v-model="customizations[`day_${day}` as keyof typeof customizations][session.key].groupNotes"
                class="notes-textarea"
                :placeholder="getGroupNotesPlaceholder(session.label)"
                rows="3"
                @input="onGroupNotesChange(day, session.key, $event)"
                :aria-label="`Group notes for ${session.label} on Day ${day}`"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Share with Friends Link for Social Personalities (ENFJ, ESFJ) -->
    <div 
      v-if="shouldShowShareLink" 
      class="share-customizations"
    >
      <h4 class="section-title">Share Your Itinerary</h4>
      <p class="section-description">
        Share your personalized travel plan with friends and family.
      </p>
      
      <div class="share-options">
        <button 
          class="share-button primary"
          @click="handleShareItinerary"
          :aria-label="'Share your complete itinerary with friends'"
        >
          <span class="share-icon">📤</span>
          Share Complete Itinerary
        </button>
        
        <button 
          class="share-button secondary"
          @click="handleShareDay"
          :aria-label="'Share a specific day with friends'"
        >
          <span class="share-icon">📅</span>
          Share Specific Day
        </button>
        
        <button 
          class="share-button secondary"
          @click="handleShareNotes"
          :aria-label="'Share your group notes with friends'"
        >
          <span class="share-icon">📝</span>
          Share Group Notes
        </button>
      </div>
      
      <div class="share-preview">
        <p class="preview-title">Share Preview:</p>
        <div class="preview-content">
          <strong>{{ mbtiPersonality }} Travel Itinerary for Hong Kong</strong>
          <br>
          <em>3-day personalized travel plan with group notes</em>
        </div>
      </div>
    </div>

    <!-- Summary Section -->
    <div v-if="hasAnyFeelingCustomizations" class="feeling-customizations-summary">
      <h4>Personalization Summary</h4>
      <div class="summary-stats">
        <div v-if="shouldShowDescriptions" class="stat-item">
          <span class="stat-label">Spots with descriptions:</span>
          <span class="stat-value">{{ getDescriptionsCount() }}</span>
        </div>
        <div v-if="shouldShowGroupNotes" class="stat-item">
          <span class="stat-label">Sessions with notes:</span>
          <span class="stat-value">{{ getGroupNotesCount() }}</span>
        </div>
        <div v-if="shouldShowShareLink" class="stat-item">
          <span class="stat-label">Ready to share:</span>
          <span class="stat-value">{{ hasShareableContent ? 'Yes' : 'No' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, onMounted } from 'vue'
import type { 
  MBTIPersonality, 
  ItineraryCustomization, 
  SessionCustomization,
  MainItinerary,
  CandidateTouristSpots
} from '../../types/mbti'
import { PERSONALITY_CATEGORIES } from '../../types/mbti'

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

// Session configurations
const touristSpotSessions = [
  { key: 'morning_session', label: 'Morning Session', icon: '🌅' },
  { key: 'afternoon_session', label: 'Afternoon Session', icon: '☀️' },
  { key: 'night_session', label: 'Night Session', icon: '🌙' }
]

const allSessions = [
  { key: 'breakfast', label: 'Breakfast', type: 'restaurant' as const, icon: '🍳' },
  { key: 'morning_session', label: 'Morning Session', type: 'tourist_spot' as const, icon: '🌅' },
  { key: 'lunch', label: 'Lunch', type: 'restaurant' as const, icon: '🍽️' },
  { key: 'afternoon_session', label: 'Afternoon Session', type: 'tourist_spot' as const, icon: '☀️' },
  { key: 'dinner', label: 'Dinner', type: 'restaurant' as const, icon: '🍷' },
  { key: 'night_session', label: 'Night Session', type: 'tourist_spot' as const, icon: '🌙' }
]

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

// Initialize customizations
const initializeCustomizations = () => {
  ['day_1', 'day_2', 'day_3'].forEach(dayKey => {
    if (!customizations[dayKey as keyof typeof customizations]) {
      customizations[dayKey as keyof typeof customizations] = {}
    }
  })
  
  allSessions.forEach(session => {
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
const isFeelingPersonality = computed(() => 
  PERSONALITY_CATEGORIES.feeling.includes(props.mbtiPersonality)
)

const showFeelingCustomizations = computed(() => isFeelingPersonality.value)

const shouldShowDescriptions = computed(() => 
  ['INFJ', 'ISFJ'].includes(props.mbtiPersonality)
)

const shouldShowGroupNotes = computed(() => 
  ['ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const shouldShowShareLink = computed(() => 
  ['ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

const hasAnyFeelingCustomizations = computed(() => {
  if (shouldShowDescriptions.value) return true
  if (shouldShowGroupNotes.value) {
    return Object.values(customizations).some(dayCustomizations =>
      Object.values(dayCustomizations).some(session => session.groupNotes)
    )
  }
  return shouldShowShareLink.value
})

const hasShareableContent = computed(() => {
  return Object.values(customizations).some(dayCustomizations =>
    Object.values(dayCustomizations).some(session => 
      session.groupNotes || session.personalNotes
    )
  ) || (props.mainItinerary && Object.keys(props.mainItinerary).length > 0)
})

// Helper functions
const getCustomizationTitle = (): string => {
  const titles: Record<string, string> = {
    INFJ: 'Meaningful Travel Insights',
    ISFJ: 'Warm & Personal Experience',
    ENFJ: 'Social Travel Planning',
    ESFJ: 'Group-Friendly Itinerary'
  }
  return titles[props.mbtiPersonality] || 'Feeling-Oriented Customizations'
}

const getCustomizationDescription = (): string => {
  const descriptions: Record<string, string> = {
    INFJ: 'Discover deeper meanings and connections with detailed descriptions of each destination.',
    ISFJ: 'Create a warm, personal travel experience with thoughtful details and comfortable planning.',
    ENFJ: 'Plan and share your journey with friends and family through collaborative notes and sharing.',
    ESFJ: 'Build a social travel experience with group notes and easy sharing options for everyone.'
  }
  return descriptions[props.mbtiPersonality] || 'Customize your travel experience with feeling-oriented features.'
}

const getSessionClass = (sessionType: 'tourist_spot' | 'restaurant'): string => {
  return `session-${sessionType}`
}

const getSpotDescription = (day: number, sessionKey: string): string => {
  if (!props.mainItinerary) return ''
  
  const dayKey = `day_${day}` as keyof MainItinerary
  const dayItinerary = props.mainItinerary[dayKey]
  
  if (!dayItinerary) return ''
  
  const spot = dayItinerary[sessionKey as keyof typeof dayItinerary]
  
  if (spot && 'description' in spot && spot.description) {
    return spot.description
  }
  
  return ''
}

const getGroupNotesPlaceholder = (sessionLabel: string): string => {
  const placeholders: Record<string, string> = {
    'Breakfast': 'Share breakfast plans with your group...',
    'Morning Session': 'What to expect and plan for the morning activity...',
    'Lunch': 'Lunch preferences and group dining notes...',
    'Afternoon Session': 'Afternoon activity coordination and tips...',
    'Dinner': 'Dinner reservations and group preferences...',
    'Night Session': 'Evening plans and group coordination...'
  }
  return placeholders[sessionLabel] || `Add group notes for ${sessionLabel}...`
}

// Event handlers
const onGroupNotesChange = (day: number, sessionKey: string, event: Event) => {
  const target = event.target as HTMLTextAreaElement
  const notes = target.value
  
  emit('group-notes-changed', {
    day,
    session: sessionKey,
    notes
  })
  
  emitModelUpdate()
}

const handleShareItinerary = () => {
  emit('share-requested', {
    type: 'complete',
    personality: props.mbtiPersonality
  })
}

const handleShareDay = () => {
  emit('share-requested', {
    type: 'day',
    personality: props.mbtiPersonality
  })
}

const handleShareNotes = () => {
  emit('share-requested', {
    type: 'notes',
    personality: props.mbtiPersonality
  })
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
const getDescriptionsCount = (): number => {
  let count = 0
  for (let day = 1; day <= 3; day++) {
    touristSpotSessions.forEach(session => {
      if (getSpotDescription(day, session.key)) {
        count++
      }
    })
  }
  return count
}

const getGroupNotesCount = (): number => {
  let count = 0
  Object.values(customizations).forEach(dayCustomizations =>
    Object.values(dayCustomizations).forEach(session => {
      if (session.groupNotes && session.groupNotes.trim()) {
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
  }
})

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    Object.assign(customizations.day_1, newValue.day_1)
    Object.assign(customizations.day_2, newValue.day_2)
    Object.assign(customizations.day_3, newValue.day_3)
  }
}, { deep: true })

watch(() => props.mbtiPersonality, () => {
  initializeCustomizations()
})
</script>

<style scoped>
.feeling-personality-customizations {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--mbti-surface, #ffffff);
  border: 2px solid var(--mbti-border, #e5e7eb);
  border-radius: 12px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.customizations-header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--mbti-border, #e5e7eb);
}

.customizations-header h3 {
  color: var(--mbti-primary, #dc2626);
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.customization-description {
  color: var(--mbti-text, #374151);
  font-size: 1rem;
  margin: 0;
  line-height: 1.5;
}

.section-title {
  color: var(--mbti-primary, #dc2626);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--mbti-primary, #dc2626);
}

.section-description {
  color: var(--mbti-text, #6b7280);
  font-size: 0.9rem;
  margin: 0 0 1.5rem 0;
  line-height: 1.4;
  font-style: italic;
}

/* Description Customizations */
.description-customizations {
  margin-bottom: 2rem;
}

.day-descriptions {
  margin-bottom: 1.5rem;
  background: var(--mbti-background, #f9fafb);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
  padding: 1.5rem;
}

.day-title {
  color: var(--mbti-primary, #dc2626);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  text-align: center;
}

.tourist-spot-descriptions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.spot-description-item {
  background: var(--mbti-surface, #ffffff);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
  padding: 1rem;
}

.spot-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--mbti-border, #e5e7eb);
}

.spot-icon {
  font-size: 1.2rem;
}

.spot-name {
  font-weight: 600;
  color: var(--mbti-primary, #dc2626);
}

.description-content {
  line-height: 1.6;
}

.description-text {
  color: var(--mbti-text, #374151);
  font-size: 0.95rem;
}

.no-description {
  color: var(--mbti-text, #6b7280);
  font-size: 0.9rem;
  font-style: italic;
}

/* Group Notes Customizations */
.group-notes-customizations {
  margin-bottom: 2rem;
}

.day-group-notes {
  margin-bottom: 1.5rem;
  background: var(--mbti-background, #f9fafb);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
  padding: 1.5rem;
}

.group-notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.session-group-notes {
  background: var(--mbti-surface, #ffffff);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.session-group-notes:hover {
  border-color: var(--mbti-primary, #dc2626);
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.session-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.session-icon {
  font-size: 1.1rem;
}

.session-name {
  font-weight: 600;
  color: var(--mbti-primary, #dc2626);
  font-size: 0.95rem;
}

.group-notes-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.notes-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--mbti-text, #374151);
}

.notes-textarea {
  padding: 0.75rem;
  border: 2px solid var(--mbti-border, #e5e7eb);
  border-radius: 6px;
  background: var(--mbti-surface, #ffffff);
  color: var(--mbti-text, #374151);
  font-size: 0.875rem;
  font-family: inherit;
  line-height: 1.4;
  resize: vertical;
  min-height: 80px;
  transition: all 0.3s ease;
}

.notes-textarea:focus {
  outline: none;
  border-color: var(--mbti-primary, #dc2626);
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(220, 38, 38, 0.1));
}

.notes-textarea:not(:placeholder-shown) {
  border-color: var(--mbti-accent, #f59e0b);
  background: var(--mbti-hover, rgba(220, 38, 38, 0.05));
}

/* Share Customizations */
.share-customizations {
  margin-bottom: 2rem;
  background: var(--mbti-background, #f9fafb);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
  padding: 1.5rem;
}

.share-options {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  justify-content: center;
}

.share-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 2px solid var(--mbti-primary, #dc2626);
  border-radius: 8px;
  background: var(--mbti-surface, #ffffff);
  color: var(--mbti-primary, #dc2626);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.share-button:hover {
  background: var(--mbti-primary, #dc2626);
  color: var(--mbti-surface, #ffffff);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.share-button:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(220, 38, 38, 0.3));
}

.share-button.primary {
  background: var(--mbti-primary, #dc2626);
  color: var(--mbti-surface, #ffffff);
}

.share-button.primary:hover {
  background: var(--mbti-secondary, #b91c1c);
}

.share-button.secondary {
  border-color: var(--mbti-accent, #f59e0b);
  color: var(--mbti-accent, #f59e0b);
}

.share-button.secondary:hover {
  background: var(--mbti-accent, #f59e0b);
  color: var(--mbti-surface, #ffffff);
}

.share-icon {
  font-size: 1rem;
}

.share-preview {
  background: var(--mbti-surface, #ffffff);
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 6px;
  padding: 1rem;
}

.preview-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--mbti-text, #6b7280);
  margin: 0 0 0.5rem 0;
}

.preview-content {
  color: var(--mbti-text, #374151);
  font-size: 0.9rem;
  line-height: 1.4;
}

/* Summary Section */
.feeling-customizations-summary {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--mbti-hover, rgba(220, 38, 38, 0.05));
  border: 1px solid var(--mbti-border, #e5e7eb);
  border-radius: 8px;
}

.feeling-customizations-summary h4 {
  color: var(--mbti-primary, #dc2626);
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
  color: var(--mbti-text, #6b7280);
  opacity: 0.8;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--mbti-accent, #f59e0b);
}

/* Session type styling */
.session-tourist_spot {
  border-left: 4px solid var(--mbti-accent, #f59e0b);
}

.session-restaurant {
  border-left: 4px solid var(--mbti-secondary, #b91c1c);
}

/* Responsive design */
@media (max-width: 768px) {
  .feeling-personality-customizations {
    padding: 1rem;
  }
  
  .group-notes-grid {
    grid-template-columns: 1fr;
  }
  
  .share-options {
    flex-direction: column;
    align-items: stretch;
  }
  
  .share-button {
    justify-content: center;
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
  
  .section-title {
    font-size: 1.1rem;
  }
  
  .day-descriptions,
  .day-group-notes {
    padding: 1rem;
  }
  
  .session-group-notes {
    padding: 0.75rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .session-group-notes,
  .share-button {
    transition: none;
  }
  
  .share-button:hover {
    transform: none;
  }
}

@media (prefers-contrast: high) {
  .notes-textarea {
    border-width: 3px;
  }
  
  .share-button {
    border-width: 3px;
    font-weight: 700;
  }
}

/* Print styles */
@media print {
  .feeling-personality-customizations {
    box-shadow: none;
    border: 1px solid #000;
  }
  
  .share-options {
    display: none;
  }
  
  .notes-textarea {
    border: 1px solid #000;
    background: white;
  }
}
</style>
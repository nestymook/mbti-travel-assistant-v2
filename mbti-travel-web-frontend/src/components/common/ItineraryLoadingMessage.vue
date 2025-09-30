<template>
  <div class="itinerary-loading" :class="personalityClasses">
    <LoadingSpinner
      :mbti-personality="mbtiPersonality"
      :size="spinnerSize"
      :show-progress="showProgress"
      :progress="progress"
      :estimated-time="remainingTime"
      :show-dots="true"
      :message="currentMessage"
    />
    
    <div class="loading-details">
      <div class="time-info">
        <div class="elapsed-time">
          <span class="label">Elapsed:</span>
          <span class="value">{{ formatTime(elapsedTime) }}</span>
        </div>
        <div v-if="estimatedTime" class="remaining-time">
          <span class="label">Remaining:</span>
          <span class="value">{{ formatTime(remainingTime) }}</span>
        </div>
      </div>
      
      <div v-if="currentStep" class="current-step">
        <div class="step-indicator">
          <span class="step-number">{{ currentStepIndex + 1 }}</span>
          <span class="step-total">/ {{ totalSteps }}</span>
        </div>
        <div class="step-description">{{ currentStep }}</div>
      </div>
      
      <div class="personality-tip" v-if="personalityTip">
        <div class="tip-icon">💡</div>
        <div class="tip-text">{{ personalityTip }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import LoadingSpinner from './LoadingSpinner.vue'
import type { MBTIPersonality } from '@/types/mbti'
import { ThemeService } from '@/services/themeService'

interface Props {
  mbtiPersonality?: MBTIPersonality
  estimatedTime?: number
  showProgress?: boolean
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  estimatedTime: 100, // Default 100 seconds as per requirements
  showProgress: true,
  size: 'large'
})

const themeService = ThemeService.getInstance()

// State
const startTime = ref<number>(Date.now())
const elapsedTime = ref<number>(0)
const progress = ref<number>(0)
const currentStepIndex = ref<number>(0)

// Timer for updating elapsed time
let timeInterval: number | null = null
let progressInterval: number | null = null

// Loading steps for itinerary generation
const loadingSteps = [
  'Analyzing your MBTI personality type...',
  'Understanding your travel preferences...',
  'Searching for matching tourist attractions...',
  'Finding restaurants that suit your taste...',
  'Optimizing your 3-day schedule...',
  'Adding personality-specific customizations...',
  'Finalizing your personalized itinerary...'
]

// Computed properties
const totalSteps = computed(() => loadingSteps.length)
const currentStep = computed(() => loadingSteps[currentStepIndex.value])
const remainingTime = computed(() => Math.max(0, props.estimatedTime - elapsedTime.value))

const currentMessage = computed(() => {
  const baseMessage = 'Generating Itinerary in progress...'
  if (props.mbtiPersonality) {
    const personalityMessages: Record<MBTIPersonality, string> = {
      // Structured personalities
      INTJ: 'Architecting your strategic travel plan...',
      ENTJ: 'Commanding your executive itinerary...',
      ISTJ: 'Organizing your systematic journey...',
      ESTJ: 'Executing your comprehensive travel plan...',
      
      // Flexible personalities
      INTP: 'Analyzing optimal travel possibilities...',
      ISTP: 'Crafting your practical adventure...',
      ESTP: 'Generating your spontaneous experience...',
      
      // Colorful personalities
      ENTP: 'Creating your innovative journey...',
      INFP: 'Curating your artistic adventure...',
      ENFP: 'Energizing your vibrant experience...',
      ISFP: 'Designing your gentle exploration...',
      ESFP: 'Planning your entertaining adventure...',
      
      // Feeling personalities
      INFJ: 'Inspiring your meaningful journey...',
      ISFJ: 'Nurturing your comfortable experience...',
      ENFJ: 'Harmonizing your social adventure...',
      ESFJ: 'Welcoming your friendly exploration...'
    }
    
    return personalityMessages[props.mbtiPersonality] || baseMessage
  }
  return baseMessage
})

const personalityTip = computed(() => {
  if (!props.mbtiPersonality) return null
  
  const tips: Record<MBTIPersonality, string> = {
    // Structured personalities
    INTJ: 'Your itinerary will include time management features for strategic planning.',
    ENTJ: 'We\'re adding "important" markers for key attractions you shouldn\'t miss.',
    ISTJ: 'Your schedule will be organized with reliable timing and clear structure.',
    ESTJ: 'We\'re creating a comprehensive plan with detailed time allocations.',
    
    // Flexible personalities
    INTP: 'Your itinerary will be presented in a flexible, point-form layout.',
    ISTP: 'We\'re focusing on practical, hands-on experiences for your journey.',
    ESTP: 'Get ready for a flashy, emoji-filled itinerary with exciting visuals!',
    
    // Colorful personalities
    ENTP: 'Your vibrant itinerary will include colorful themes and image previews.',
    INFP: 'We\'re adding artistic touches and image placeholders for inspiration.',
    ENFP: 'Your enthusiastic journey will feature bright colors and visual elements.',
    ISFP: 'Your gentle adventure will include beautiful imagery and soft themes.',
    ESFP: 'Your lively itinerary will be full of color and entertainment options.',
    
    // Feeling personalities
    INFJ: 'Your meaningful journey will include detailed descriptions for deeper connection.',
    ISFJ: 'We\'re using warm tones and adding descriptive details for comfort.',
    ENFJ: 'Your social adventure will include group notes and sharing features.',
    ESFJ: 'We\'re adding friendly features and group planning capabilities.'
  }
  
  return tips[props.mbtiPersonality]
})

const personalityClasses = computed(() => {
  const classes: string[] = []
  
  if (props.mbtiPersonality) {
    classes.push(`itinerary-loading--${props.mbtiPersonality.toLowerCase()}`)
    
    if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
      classes.push('itinerary-loading--colorful')
    }
    
    if (themeService.isWarmPersonality(props.mbtiPersonality)) {
      classes.push('itinerary-loading--warm')
    }
    
    if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
      classes.push('itinerary-loading--flashy')
    }
  }
  
  return classes
})

const spinnerSize = computed(() => {
  return props.size
})

// Format time in MM:SS format
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// Start timers
const startTimers = () => {
  // Update elapsed time every second
  timeInterval = window.setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)
  
  // Update progress and steps
  if (props.showProgress) {
    const stepDuration = props.estimatedTime / totalSteps.value
    
    progressInterval = window.setInterval(() => {
      const elapsed = elapsedTime.value
      const expectedProgress = Math.min(95, (elapsed / props.estimatedTime) * 100)
      
      // Smooth progress update
      if (progress.value < expectedProgress) {
        progress.value = Math.min(expectedProgress, progress.value + 1)
      }
      
      // Update current step
      const expectedStep = Math.floor(elapsed / stepDuration)
      if (expectedStep < totalSteps.value && expectedStep > currentStepIndex.value) {
        currentStepIndex.value = expectedStep
      }
    }, 500)
  }
}

// Stop timers
const stopTimers = () => {
  if (timeInterval) {
    clearInterval(timeInterval)
    timeInterval = null
  }
  
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

// Lifecycle
onMounted(() => {
  startTimers()
})

onUnmounted(() => {
  stopTimers()
})

// Watch for prop changes
watch(() => props.estimatedTime, () => {
  stopTimers()
  startTime.value = Date.now()
  elapsedTime.value = 0
  progress.value = 0
  currentStepIndex.value = 0
  startTimers()
})
</script>

<style scoped>
.itinerary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  max-width: 500px;
  margin: 0 auto;
  text-align: center;
  background: var(--mbti-background, #ffffff);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.loading-details {
  margin-top: 2rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.time-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.elapsed-time,
.remaining-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.label {
  font-size: 0.75rem;
  color: var(--mbti-text, #212529);
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--mbti-primary, #007bff);
  font-family: 'Courier New', monospace;
}

.current-step {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: linear-gradient(135deg, 
    rgba(var(--mbti-primary-rgb, 0, 123, 255), 0.05),
    rgba(var(--mbti-accent-rgb, 40, 167, 69), 0.05)
  );
  border-radius: 8px;
  border-left: 4px solid var(--mbti-primary, #007bff);
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-weight: 600;
  color: var(--mbti-primary, #007bff);
}

.step-number {
  font-size: 1.125rem;
}

.step-total {
  font-size: 0.875rem;
  opacity: 0.7;
}

.step-description {
  font-size: 0.875rem;
  color: var(--mbti-text, #212529);
  line-height: 1.4;
  font-weight: 500;
}

.personality-tip {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: linear-gradient(135deg,
    rgba(var(--mbti-accent-rgb, 40, 167, 69), 0.1),
    rgba(var(--mbti-secondary-rgb, 108, 117, 125), 0.05)
  );
  border-radius: 8px;
  border: 1px solid rgba(var(--mbti-accent-rgb, 40, 167, 69), 0.2);
}

.tip-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.tip-text {
  font-size: 0.875rem;
  color: var(--mbti-text, #212529);
  line-height: 1.4;
  text-align: left;
}

/* Personality-specific styling */
.itinerary-loading--warm {
  background: linear-gradient(135deg, 
    rgba(212, 165, 116, 0.05), 
    rgba(244, 228, 188, 0.05)
  );
  border-color: rgba(212, 165, 116, 0.2);
}

.itinerary-loading--colorful {
  background: linear-gradient(135deg,
    rgba(155, 89, 182, 0.05),
    rgba(52, 152, 219, 0.05),
    rgba(46, 204, 113, 0.05)
  );
  border: 2px solid transparent;
  background-clip: padding-box;
}

.itinerary-loading--flashy {
  background: linear-gradient(45deg,
    rgba(231, 76, 60, 0.05),
    rgba(241, 196, 15, 0.05),
    rgba(155, 89, 182, 0.05),
    rgba(52, 152, 219, 0.05)
  );
  background-size: 400% 400%;
  animation: flashyBackground 4s ease-in-out infinite;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.itinerary-loading--flashy .value {
  background: linear-gradient(45deg, 
    var(--mbti-primary, #007bff), 
    var(--mbti-accent, #28a745)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Responsive design */
@media (max-width: 768px) {
  .itinerary-loading {
    padding: 2rem 1.5rem;
    margin: 1rem;
  }
  
  .time-info {
    flex-direction: column;
    gap: 1rem;
  }
  
  .elapsed-time,
  .remaining-time {
    flex-direction: row;
    gap: 0.5rem;
  }
  
  .value {
    font-size: 1rem;
  }
  
  .personality-tip {
    flex-direction: column;
    text-align: center;
  }
  
  .tip-text {
    text-align: center;
  }
}

/* Animation */
@keyframes flashyBackground {
  0%, 100% {
    background-position: 0% 50%;
  }
  25% {
    background-position: 100% 0%;
  }
  50% {
    background-position: 100% 100%;
  }
  75% {
    background-position: 0% 100%;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .itinerary-loading--flashy {
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .itinerary-loading {
    border: 2px solid currentColor;
  }
  
  .time-info,
  .current-step,
  .personality-tip {
    border: 1px solid currentColor;
  }
}
</style>
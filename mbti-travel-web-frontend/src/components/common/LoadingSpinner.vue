<template>
  <div 
    class="loading-spinner" 
    :class="personalityClasses"
    role="status" 
    :aria-label="ariaLabel"
  >
    <div class="spinner-container">
      <div class="spinner" :class="spinnerClasses"></div>
      <div v-if="showProgress && progress !== undefined" class="progress-ring">
        <svg class="progress-svg" viewBox="0 0 36 36">
          <path
            class="progress-bg"
            d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            class="progress-bar"
            :stroke-dasharray="`${progress}, 100`"
            d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <div class="progress-text">{{ Math.round(progress) }}%</div>
      </div>
    </div>
    
    <div v-if="message" class="loading-content">
      <p class="loading-message">{{ message }}</p>
      <p v-if="estimatedTime" class="estimated-time">
        Estimated time: {{ formatEstimatedTime(estimatedTime) }}
      </p>
      <div v-if="showDots" class="loading-dots">
        <span class="dot" :class="{ active: dotIndex >= 0 }">.</span>
        <span class="dot" :class="{ active: dotIndex >= 1 }">.</span>
        <span class="dot" :class="{ active: dotIndex >= 2 }">.</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import { ThemeService } from '@/services/themeService'

interface Props {
  message?: string
  mbtiPersonality?: MBTIPersonality
  size?: 'small' | 'medium' | 'large'
  variant?: 'default' | 'colorful' | 'warm' | 'flashy'
  showProgress?: boolean
  progress?: number
  estimatedTime?: number // in seconds
  showDots?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  variant: 'default',
  showProgress: false,
  showDots: true
})

const themeService = ThemeService.getInstance()
const dotIndex = ref(0)
let dotInterval: number | null = null

// Computed properties for styling
const personalityClasses = computed(() => {
  const classes: string[] = [`loading-spinner--${props.size}`]
  
  if (props.mbtiPersonality) {
    classes.push(`loading-spinner--${props.mbtiPersonality.toLowerCase()}`)
    
    if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
      classes.push('loading-spinner--colorful')
    }
    
    if (themeService.isWarmPersonality(props.mbtiPersonality)) {
      classes.push('loading-spinner--warm')
    }
    
    if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
      classes.push('loading-spinner--flashy')
    }
  }
  
  if (props.variant !== 'default') {
    classes.push(`loading-spinner--${props.variant}`)
  }
  
  return classes
})

const spinnerClasses = computed(() => {
  const classes: string[] = []
  
  if (props.mbtiPersonality) {
    if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
      classes.push('spinner--colorful')
    }
    
    if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
      classes.push('spinner--flashy')
    }
  }
  
  return classes
})

const ariaLabel = computed(() => {
  if (props.message) {
    return `Loading: ${props.message}`
  }
  return 'Loading content, please wait'
})

// Format estimated time
const formatEstimatedTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
}

// Animated dots effect
const startDotAnimation = () => {
  if (!props.showDots) return
  
  dotInterval = window.setInterval(() => {
    dotIndex.value = (dotIndex.value + 1) % 4
  }, 500)
}

const stopDotAnimation = () => {
  if (dotInterval) {
    clearInterval(dotInterval)
    dotInterval = null
  }
}

// Lifecycle
onMounted(() => {
  startDotAnimation()
})

onUnmounted(() => {
  stopDotAnimation()
})

// Watch for showDots changes
watch(() => props.showDots, (newValue) => {
  if (newValue) {
    startDotAnimation()
  } else {
    stopDotAnimation()
  }
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1.5rem;
}

.spinner-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Spinner sizes */
.loading-spinner--small .spinner {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.loading-spinner--medium .spinner {
  width: 40px;
  height: 40px;
  border-width: 4px;
}

.loading-spinner--large .spinner {
  width: 60px;
  height: 60px;
  border-width: 6px;
}

/* Basic spinner */
.spinner {
  border: 4px solid var(--mbti-secondary, #6c757d);
  border-top: 4px solid var(--mbti-primary, #007bff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  opacity: 0.8;
}

/* Colorful spinner variations */
.spinner--colorful {
  background: conic-gradient(
    from 0deg,
    var(--mbti-primary, #007bff),
    var(--mbti-accent, #28a745),
    var(--mbti-vibrant-accent, #e74c3c),
    var(--mbti-primary, #007bff)
  );
  border: none;
  animation: spin 1.5s linear infinite, colorShift 3s ease-in-out infinite;
}

.spinner--colorful::before {
  content: '';
  position: absolute;
  inset: 4px;
  background: var(--mbti-background, #ffffff);
  border-radius: 50%;
}

/* Flashy spinner for ESTP */
.spinner--flashy {
  border: 4px solid transparent;
  background: linear-gradient(45deg, 
    var(--mbti-primary, #007bff), 
    var(--mbti-accent, #28a745), 
    var(--mbti-vibrant-accent, #e74c3c),
    var(--mbti-creative-highlight, #ffc107)
  );
  background-size: 400% 400%;
  animation: spin 0.8s linear infinite, flashyGradient 2s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(231, 76, 60, 0.3);
}

.spinner--flashy::before {
  content: '';
  position: absolute;
  inset: 4px;
  background: var(--mbti-background, #ffffff);
  border-radius: 50%;
}

/* Progress ring */
.progress-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.progress-svg {
  width: 80px;
  height: 80px;
  transform: rotate(-90deg);
}

.progress-bg {
  fill: none;
  stroke: var(--mbti-secondary, #6c757d);
  stroke-width: 2;
  opacity: 0.3;
}

.progress-bar {
  fill: none;
  stroke: var(--mbti-primary, #007bff);
  stroke-width: 2;
  stroke-linecap: round;
  transition: stroke-dasharray 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(90deg);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--mbti-primary, #007bff);
}

/* Loading content */
.loading-content {
  text-align: center;
  max-width: 300px;
}

.loading-message {
  margin: 0 0 0.5rem 0;
  color: var(--mbti-primary, #007bff);
  font-weight: 500;
  font-size: 1rem;
  line-height: 1.4;
}

.estimated-time {
  margin: 0 0 1rem 0;
  color: var(--mbti-text, #212529);
  font-size: 0.875rem;
  opacity: 0.8;
}

/* Animated dots */
.loading-dots {
  display: flex;
  justify-content: center;
  gap: 0.25rem;
}

.dot {
  font-size: 1.5rem;
  color: var(--mbti-secondary, #6c757d);
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

.dot.active {
  opacity: 1;
  color: var(--mbti-primary, #007bff);
}

/* Personality-specific styling */
.loading-spinner--warm {
  background: linear-gradient(135deg, 
    rgba(212, 165, 116, 0.1), 
    rgba(244, 228, 188, 0.1)
  );
  border-radius: 12px;
}

.loading-spinner--warm .loading-message {
  color: var(--mbti-primary, #d4a574);
}

.loading-spinner--colorful {
  background: linear-gradient(135deg,
    rgba(155, 89, 182, 0.1),
    rgba(52, 152, 219, 0.1),
    rgba(46, 204, 113, 0.1)
  );
  border-radius: 12px;
  animation: colorfulBackground 4s ease-in-out infinite;
}

.loading-spinner--flashy {
  background: linear-gradient(45deg,
    rgba(231, 76, 60, 0.1),
    rgba(241, 196, 15, 0.1),
    rgba(155, 89, 182, 0.1),
    rgba(52, 152, 219, 0.1)
  );
  background-size: 400% 400%;
  border-radius: 16px;
  animation: flashyBackground 3s ease-in-out infinite;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.loading-spinner--flashy .loading-message {
  background: linear-gradient(45deg, 
    var(--mbti-primary, #007bff), 
    var(--mbti-accent, #28a745)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

/* Animations */
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes colorShift {
  0%, 100% {
    filter: hue-rotate(0deg);
  }
  50% {
    filter: hue-rotate(180deg);
  }
}

@keyframes flashyGradient {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

@keyframes colorfulBackground {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

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

/* Responsive design */
@media (max-width: 768px) {
  .loading-spinner {
    padding: 1.5rem;
    gap: 1rem;
  }
  
  .loading-spinner--small .spinner {
    width: 20px;
    height: 20px;
  }
  
  .loading-spinner--medium .spinner {
    width: 32px;
    height: 32px;
  }
  
  .loading-spinner--large .spinner {
    width: 48px;
    height: 48px;
  }
  
  .loading-message {
    font-size: 0.875rem;
  }
  
  .progress-svg {
    width: 60px;
    height: 60px;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .spinner {
    border-color: currentColor;
    border-top-color: transparent;
  }
  
  .loading-message {
    color: currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
  
  .spinner--colorful,
  .spinner--flashy {
    animation: none;
  }
  
  .loading-spinner--colorful,
  .loading-spinner--flashy {
    animation: none;
  }
  
  .dot {
    opacity: 1;
  }
}
</style>

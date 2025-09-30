<template>
  <Transition
    :name="transitionName"
    appear
    @enter="onEnter"
    @leave="onLeave"
  >
    <div
      v-if="visible"
      class="interaction-feedback"
      :class="feedbackClasses"
      :style="positionStyle"
      role="status"
      :aria-live="ariaLive"
    >
      <div class="feedback-content">
        <div v-if="showIcon" class="feedback-icon">
          <component :is="iconComponent" />
        </div>
        <div class="feedback-message">
          <div class="feedback-title" v-if="title">{{ title }}</div>
          <div class="feedback-text">{{ message }}</div>
        </div>
        <button
          v-if="dismissible"
          class="feedback-dismiss"
          @click="dismiss"
          aria-label="Dismiss notification"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 7.293l2.146-2.147a.5.5 0 0 1 .708.708L8.707 8l2.147 2.146a.5.5 0 0 1-.708.708L8 8.707l-2.146 2.147a.5.5 0 0 1-.708-.708L7.293 8 5.146 5.854a.5.5 0 1 1 .708-.708L8 7.293z"/>
          </svg>
        </button>
      </div>
      
      <div v-if="showProgress" class="feedback-progress">
        <div 
          class="progress-bar"
          :style="{ width: `${progress}%` }"
        ></div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, h } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import { ThemeService } from '@/services/themeService'

export type FeedbackType = 'success' | 'error' | 'warning' | 'info' | 'loading'
export type FeedbackPosition = 'top' | 'bottom' | 'center' | 'top-right' | 'bottom-right'

interface Props {
  type: FeedbackType
  message: string
  title?: string
  visible?: boolean
  duration?: number // Auto-dismiss duration in ms (0 = no auto-dismiss)
  position?: FeedbackPosition
  dismissible?: boolean
  showIcon?: boolean
  showProgress?: boolean
  progress?: number
  mbtiPersonality?: MBTIPersonality
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: true,
  duration: 4000,
  position: 'top',
  dismissible: true,
  showIcon: true,
  showProgress: false,
  progress: 0
})

const emit = defineEmits<{
  dismiss: []
  expired: []
}>()

const themeService = ThemeService.getInstance()
let dismissTimer: number | null = null

// Computed properties
const feedbackClasses = computed(() => {
  const classes = [
    `feedback--${props.type}`,
    `feedback--${props.position}`
  ]
  
  if (props.mbtiPersonality) {
    classes.push(`feedback--${props.mbtiPersonality.toLowerCase()}`)
    
    if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
      classes.push('feedback--colorful')
    }
    
    if (themeService.isWarmPersonality(props.mbtiPersonality)) {
      classes.push('feedback--warm')
    }
    
    if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
      classes.push('feedback--flashy')
    }
  }
  
  if (props.customClass) {
    classes.push(props.customClass)
  }
  
  return classes
})

const positionStyle = computed(() => {
  const styles: Record<string, string> = {}
  
  switch (props.position) {
    case 'top':
      styles.top = '1rem'
      styles.left = '50%'
      styles.transform = 'translateX(-50%)'
      break
    case 'bottom':
      styles.bottom = '1rem'
      styles.left = '50%'
      styles.transform = 'translateX(-50%)'
      break
    case 'center':
      styles.top = '50%'
      styles.left = '50%'
      styles.transform = 'translate(-50%, -50%)'
      break
    case 'top-right':
      styles.top = '1rem'
      styles.right = '1rem'
      break
    case 'bottom-right':
      styles.bottom = '1rem'
      styles.right = '1rem'
      break
  }
  
  return styles
})

const transitionName = computed(() => {
  switch (props.position) {
    case 'top':
      return 'slide-down'
    case 'bottom':
      return 'slide-up'
    case 'center':
      return 'fade-scale'
    case 'top-right':
    case 'bottom-right':
      return 'slide-left'
    default:
      return 'fade'
  }
})

const ariaLive = computed(() => {
  return props.type === 'error' ? 'assertive' : 'polite'
})

const iconComponent = computed(() => {
  const icons = {
    success: () => h('svg', {
      width: '20',
      height: '20',
      viewBox: '0 0 20 20',
      fill: 'currentColor'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z',
        'clip-rule': 'evenodd'
      })
    ]),
    
    error: () => h('svg', {
      width: '20',
      height: '20',
      viewBox: '0 0 20 20',
      fill: 'currentColor'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z',
        'clip-rule': 'evenodd'
      })
    ]),
    
    warning: () => h('svg', {
      width: '20',
      height: '20',
      viewBox: '0 0 20 20',
      fill: 'currentColor'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z',
        'clip-rule': 'evenodd'
      })
    ]),
    
    info: () => h('svg', {
      width: '20',
      height: '20',
      viewBox: '0 0 20 20',
      fill: 'currentColor'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z',
        'clip-rule': 'evenodd'
      })
    ]),
    
    loading: () => h('div', {
      class: 'loading-icon'
    })
  }
  
  return icons[props.type] || icons.info
})

// Methods
const dismiss = () => {
  emit('dismiss')
}

const startDismissTimer = () => {
  if (props.duration > 0) {
    dismissTimer = window.setTimeout(() => {
      emit('expired')
    }, props.duration)
  }
}

const clearDismissTimer = () => {
  if (dismissTimer) {
    clearTimeout(dismissTimer)
    dismissTimer = null
  }
}

// Transition hooks
const onEnter = () => {
  startDismissTimer()
}

const onLeave = () => {
  clearDismissTimer()
}

// Lifecycle
onMounted(() => {
  if (props.visible) {
    startDismissTimer()
  }
})

onUnmounted(() => {
  clearDismissTimer()
})
</script>

<style scoped>
.interaction-feedback {
  position: fixed;
  z-index: 1000;
  max-width: 400px;
  min-width: 300px;
  background: var(--mbti-background, #ffffff);
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.feedback-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
}

.feedback-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.loading-icon {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.feedback-message {
  flex: 1;
  min-width: 0;
}

.feedback-title {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
  color: var(--mbti-text, #212529);
}

.feedback-text {
  font-size: 0.875rem;
  line-height: 1.4;
  color: var(--mbti-text, #212529);
  opacity: 0.9;
}

.feedback-dismiss {
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: var(--mbti-text, #212529);
  opacity: 0.6;
  border-radius: 4px;
  transition: opacity 0.2s ease, background-color 0.2s ease;
}

.feedback-dismiss:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
}

.feedback-progress {
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: currentColor;
  transition: width 0.3s ease;
}

/* Type-specific styling */
.feedback--success {
  border-left: 4px solid #28a745;
}

.feedback--success .feedback-icon {
  color: #28a745;
}

.feedback--error {
  border-left: 4px solid #dc3545;
}

.feedback--error .feedback-icon {
  color: #dc3545;
}

.feedback--warning {
  border-left: 4px solid #ffc107;
}

.feedback--warning .feedback-icon {
  color: #f57c00;
}

.feedback--info {
  border-left: 4px solid #17a2b8;
}

.feedback--info .feedback-icon {
  color: #17a2b8;
}

.feedback--loading {
  border-left: 4px solid var(--mbti-primary, #007bff);
}

.feedback--loading .feedback-icon {
  color: var(--mbti-primary, #007bff);
}

/* Personality-specific styling */
.feedback--warm {
  background: linear-gradient(135deg, 
    rgba(212, 165, 116, 0.05), 
    rgba(244, 228, 188, 0.05)
  );
  border-color: rgba(212, 165, 116, 0.3);
}

.feedback--colorful {
  background: linear-gradient(135deg,
    rgba(155, 89, 182, 0.05),
    rgba(52, 152, 219, 0.05),
    rgba(46, 204, 113, 0.05)
  );
}

.feedback--flashy {
  background: linear-gradient(45deg,
    rgba(231, 76, 60, 0.05),
    rgba(241, 196, 15, 0.05),
    rgba(155, 89, 182, 0.05)
  );
  background-size: 200% 200%;
  animation: flashyBackground 3s ease-in-out infinite;
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateX(-50%) translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateX(-50%) translateY(-100%);
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateX(-50%) translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateX(-50%) translateY(100%);
  opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from {
  transform: translate(-50%, -50%) scale(0.9);
  opacity: 0;
}

.fade-scale-leave-to {
  transform: translate(-50%, -50%) scale(0.9);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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

@keyframes flashyBackground {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .interaction-feedback {
    max-width: calc(100vw - 2rem);
    min-width: auto;
    left: 1rem !important;
    right: 1rem !important;
    transform: none !important;
  }
  
  .feedback--top {
    top: 1rem;
  }
  
  .feedback--bottom {
    bottom: 1rem;
  }
  
  .feedback--center {
    top: 50%;
    transform: translateY(-50%) !important;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .loading-icon {
    animation: none;
  }
  
  .feedback--flashy {
    animation: none;
  }
  
  .slide-down-enter-active,
  .slide-down-leave-active,
  .slide-up-enter-active,
  .slide-up-leave-active,
  .slide-left-enter-active,
  .slide-left-leave-active,
  .fade-scale-enter-active,
  .fade-scale-leave-active,
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.2s ease;
  }
}

@media (prefers-contrast: high) {
  .interaction-feedback {
    border: 2px solid currentColor;
  }
  
  .feedback-dismiss:hover {
    background: currentColor;
    color: var(--mbti-background, #ffffff);
  }
}
</style>
<template>
  <div class="combo-box-loading" :class="sizeClass">
    <div class="loading-content">
      <div class="spinner-mini" :class="personalityClass"></div>
      <span class="loading-text">{{ message }}</span>
    </div>
    <div v-if="showProgress" class="progress-bar">
      <div 
        class="progress-fill" 
        :style="{ width: `${progress}%` }"
        :class="personalityClass"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import { ThemeService } from '@/services/themeService'

interface Props {
  message?: string
  mbtiPersonality?: MBTIPersonality
  size?: 'small' | 'medium'
  showProgress?: boolean
  progress?: number
}

const props = withDefaults(defineProps<Props>(), {
  message: 'Updating...',
  size: 'small',
  showProgress: false,
  progress: 0
})

const themeService = ThemeService.getInstance()

const sizeClass = computed(() => `combo-box-loading--${props.size}`)

const personalityClass = computed(() => {
  if (!props.mbtiPersonality) return ''
  
  const classes: string[] = []
  
  if (themeService.isColorfulPersonality(props.mbtiPersonality)) {
    classes.push('colorful')
  }
  
  if (themeService.isWarmPersonality(props.mbtiPersonality)) {
    classes.push('warm')
  }
  
  if (themeService.isFlashyPersonality(props.mbtiPersonality)) {
    classes.push('flashy')
  }
  
  return classes.join(' ')
})
</script>

<style scoped>
.combo-box-loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.combo-box-loading--small {
  padding: 0.375rem;
  gap: 0.375rem;
}

.combo-box-loading--medium {
  padding: 0.75rem;
  gap: 0.75rem;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner-mini {
  width: 12px;
  height: 12px;
  border: 2px solid var(--mbti-secondary, #6c757d);
  border-top: 2px solid var(--mbti-primary, #007bff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

.combo-box-loading--medium .spinner-mini {
  width: 16px;
  height: 16px;
}

.spinner-mini.colorful {
  background: conic-gradient(
    from 0deg,
    var(--mbti-primary, #007bff),
    var(--mbti-accent, #28a745),
    var(--mbti-vibrant-accent, #e74c3c),
    var(--mbti-primary, #007bff)
  );
  border: none;
  animation: spin 1.2s linear infinite, colorShift 2s ease-in-out infinite;
}

.spinner-mini.flashy {
  border: 2px solid transparent;
  background: linear-gradient(45deg, 
    var(--mbti-primary, #007bff), 
    var(--mbti-accent, #28a745), 
    var(--mbti-vibrant-accent, #e74c3c)
  );
  background-size: 200% 200%;
  animation: spin 0.8s linear infinite, flashyGradient 1.5s ease-in-out infinite;
}

.spinner-mini.warm {
  border-top-color: var(--mbti-primary, #d4a574);
  border-right-color: var(--mbti-accent, #b8860b);
}

.loading-text {
  font-size: 0.75rem;
  color: var(--mbti-text, #212529);
  opacity: 0.8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.combo-box-loading--medium .loading-text {
  font-size: 0.875rem;
}

.progress-bar {
  height: 2px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 1px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--mbti-primary, #007bff);
  border-radius: 1px;
  transition: width 0.3s ease;
}

.progress-fill.colorful {
  background: linear-gradient(90deg,
    var(--mbti-primary, #007bff),
    var(--mbti-accent, #28a745),
    var(--mbti-vibrant-accent, #e74c3c)
  );
}

.progress-fill.flashy {
  background: linear-gradient(90deg,
    var(--mbti-primary, #007bff),
    var(--mbti-accent, #28a745),
    var(--mbti-vibrant-accent, #e74c3c),
    var(--mbti-creative-highlight, #ffc107)
  );
  background-size: 200% 100%;
  animation: flashyProgress 1s ease-in-out infinite;
}

.progress-fill.warm {
  background: linear-gradient(90deg,
    var(--mbti-primary, #d4a574),
    var(--mbti-accent, #b8860b)
  );
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

@keyframes flashyProgress {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .spinner-mini {
    animation: none;
  }
  
  .spinner-mini.colorful,
  .spinner-mini.flashy {
    animation: none;
  }
  
  .progress-fill.flashy {
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .combo-box-loading {
    border-color: currentColor;
  }
  
  .spinner-mini {
    border-color: currentColor;
    border-top-color: transparent;
  }
  
  .loading-text {
    color: currentColor;
  }
}
</style>
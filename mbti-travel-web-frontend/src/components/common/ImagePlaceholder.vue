<template>
  <div 
    class="image-placeholder-container"
    :class="[
      `personality-${mbtiPersonality.toLowerCase()}`,
      { 'clickable': clickable },
      placeholderClass
    ]"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
    :tabindex="clickable ? 0 : -1"
    :role="clickable ? 'button' : 'img'"
    :aria-label="ariaLabel"
  >
    <div class="image-placeholder-content">
      <div class="placeholder-icon">
        <slot name="icon">
          <svg 
            width="32" 
            height="32" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            class="default-image-icon"
          >
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
        </slot>
      </div>
      
      <div class="placeholder-text-content">
        <div class="placeholder-title">
          {{ title || 'Image Gallery' }}
        </div>
        <div v-if="subtitle" class="placeholder-subtitle">
          {{ subtitle }}
        </div>
        <div v-if="showClickHint && clickable" class="click-hint">
          Click to view {{ clickHintText }}
        </div>
      </div>
    </div>
    
    <!-- Decorative elements for creative personalities -->
    <div v-if="isColorfulPersonality" class="decorative-elements">
      <div class="sparkle sparkle-1">✨</div>
      <div class="sparkle sparkle-2">🌟</div>
      <div class="sparkle sparkle-3">💫</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'

// Props interface
interface Props {
  mbtiPersonality: MBTIPersonality
  title?: string
  subtitle?: string
  clickable?: boolean
  clickHintText?: string
  showClickHint?: boolean
  size?: 'small' | 'medium' | 'large'
  variant?: 'default' | 'gallery' | 'spot' | 'restaurant'
  ariaLabel?: string
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  title: '',
  subtitle: '',
  clickable: true,
  clickHintText: 'images',
  showClickHint: true,
  size: 'medium',
  variant: 'default',
  ariaLabel: 'Image placeholder'
})

// Emits
interface Emits {
  (e: 'click'): void
  (e: 'image-request', data: { personality: MBTIPersonality; title: string }): void
}

const emit = defineEmits<Emits>()

// Computed properties
const isColorfulPersonality = computed(() => {
  const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP']
  return colorfulTypes.includes(props.mbtiPersonality)
})

const placeholderClass = computed(() => {
  const classes = []
  
  // Size class
  classes.push(`size-${props.size}`)
  
  // Variant class
  classes.push(`variant-${props.variant}`)
  
  // Personality-specific classes
  if (isColorfulPersonality.value) {
    classes.push('colorful-personality')
  }
  
  if (props.mbtiPersonality === 'ESTP') {
    classes.push('estp-flashy')
  }
  
  return classes.join(' ')
})

// Methods
const handleClick = () => {
  if (props.clickable) {
    emit('click')
    emit('image-request', {
      personality: props.mbtiPersonality,
      title: props.title || 'Image Gallery'
    })
  }
}
</script>

<style scoped>
.image-placeholder-container {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  background: linear-gradient(
    135deg,
    var(--mbti-primary, #3b82f6) 0%,
    var(--mbti-accent, #10b981) 100%
  );
  color: white;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Size variants */
.size-small {
  min-height: 80px;
  padding: 0.75rem;
}

.size-medium {
  min-height: 120px;
  padding: 1rem;
}

.size-large {
  min-height: 160px;
  padding: 1.5rem;
}

/* Variant styles */
.variant-gallery {
  aspect-ratio: 16/9;
}

.variant-spot {
  aspect-ratio: 4/3;
}

.variant-restaurant {
  aspect-ratio: 3/2;
}

/* Clickable state */
.clickable {
  cursor: pointer;
}

.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.clickable:focus {
  outline: 3px solid rgba(255, 255, 255, 0.5);
  outline-offset: 2px;
}

.clickable:active {
  transform: translateY(0);
}

/* Content styling */
.image-placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
  z-index: 2;
  position: relative;
}

.placeholder-icon {
  opacity: 0.9;
  transition: all 0.3s ease;
}

.default-image-icon {
  width: 2rem;
  height: 2rem;
}

.size-small .default-image-icon {
  width: 1.5rem;
  height: 1.5rem;
}

.size-large .default-image-icon {
  width: 2.5rem;
  height: 2.5rem;
}

.placeholder-text-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.placeholder-title {
  font-size: 0.9rem;
  font-weight: 600;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
  line-height: 1.3;
}

.size-small .placeholder-title {
  font-size: 0.8rem;
}

.size-large .placeholder-title {
  font-size: 1rem;
}

.placeholder-subtitle {
  font-size: 0.75rem;
  opacity: 0.8;
  font-style: italic;
}

.size-small .placeholder-subtitle {
  font-size: 0.7rem;
}

.click-hint {
  font-size: 0.7rem;
  opacity: 0.7;
  margin-top: 0.25rem;
  transition: opacity 0.3s ease;
}

.clickable:hover .click-hint {
  opacity: 1;
}

/* Personality-specific styling */
.personality-entp {
  background: linear-gradient(135deg, #9b59b6 0%, #f39c12 50%, #e74c3c 100%);
}

.personality-infp {
  background: linear-gradient(135deg, #e91e63 0%, #ff9800 50%, #9c27b0 100%);
}

.personality-enfp {
  background: linear-gradient(135deg, #ff5722 0%, #4caf50 50%, #2196f3 100%);
}

.personality-isfp {
  background: linear-gradient(135deg, #673ab7 0%, #ff4081 50%, #00bcd4 100%);
}

.personality-estp {
  background: linear-gradient(135deg, #e74c3c 0%, #f1c40f 50%, #e67e22 100%);
}

/* Colorful personality enhancements */
.colorful-personality::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  animation: shimmer 3s linear infinite;
  pointer-events: none;
  z-index: 1;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
}

/* ESTP flashy styling */
.estp-flashy {
  animation: flashy-pulse 2s ease-in-out infinite;
}

@keyframes flashy-pulse {
  0%, 100% {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 0 8px 16px rgba(231, 76, 60, 0.3), 0 0 20px rgba(241, 196, 15, 0.2);
  }
}

.estp-flashy:hover {
  animation: flashy-pulse 1s ease-in-out infinite;
}

/* Decorative elements */
.decorative-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.sparkle {
  position: absolute;
  font-size: 1rem;
  opacity: 0.6;
  animation: sparkle-float 4s ease-in-out infinite;
}

.sparkle-1 {
  top: 20%;
  left: 15%;
  animation-delay: 0s;
}

.sparkle-2 {
  top: 70%;
  right: 20%;
  animation-delay: 1.5s;
}

.sparkle-3 {
  top: 40%;
  right: 15%;
  animation-delay: 3s;
}

@keyframes sparkle-float {
  0%, 100% {
    transform: translateY(0) scale(1);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-10px) scale(1.1);
    opacity: 0.8;
  }
}

/* Hover effects for colorful personalities */
.colorful-personality:hover .placeholder-icon {
  transform: scale(1.1);
}

.colorful-personality:hover .sparkle {
  animation-duration: 2s;
}

/* Responsive design */
@media (max-width: 768px) {
  .size-medium {
    min-height: 100px;
    padding: 0.75rem;
  }
  
  .size-large {
    min-height: 120px;
    padding: 1rem;
  }
  
  .placeholder-title {
    font-size: 0.8rem;
  }
  
  .placeholder-subtitle {
    font-size: 0.7rem;
  }
  
  .click-hint {
    font-size: 0.65rem;
  }
}

@media (max-width: 480px) {
  .size-small {
    min-height: 60px;
    padding: 0.5rem;
  }
  
  .size-medium {
    min-height: 80px;
    padding: 0.5rem;
  }
  
  .size-large {
    min-height: 100px;
    padding: 0.75rem;
  }
  
  .default-image-icon {
    width: 1.5rem;
    height: 1.5rem;
  }
  
  .placeholder-title {
    font-size: 0.75rem;
  }
  
  .sparkle {
    font-size: 0.8rem;
  }
}

/* Accessibility enhancements */
@media (prefers-contrast: high) {
  .image-placeholder-container {
    border: 2px solid white;
  }
  
  .placeholder-title,
  .placeholder-subtitle,
  .click-hint {
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  }
}

@media (prefers-reduced-motion: reduce) {
  .colorful-personality::before,
  .estp-flashy,
  .sparkle {
    animation: none;
  }
  
  .clickable:hover {
    transform: none;
  }
  
  .colorful-personality:hover .placeholder-icon {
    transform: none;
  }
}

/* Print styles */
@media print {
  .image-placeholder-container {
    background: #f0f0f0 !important;
    color: #000000 !important;
    box-shadow: none;
  }
  
  .decorative-elements {
    display: none;
  }
}
</style>
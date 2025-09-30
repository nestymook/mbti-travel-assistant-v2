<template>
  <div 
    ref="containerRef"
    :data-lazy-id="componentId"
    class="lazy-component-container"
    :class="{ 'is-loading': isLoading, 'is-loaded': isLoaded, 'has-error': hasError }"
  >
    <!-- Loading state -->
    <div v-if="isLoading && showLoadingState" class="lazy-loading-state">
      <div class="loading-spinner" :class="loadingClass"></div>
      <div v-if="loadingText" class="loading-text">{{ loadingText }}</div>
    </div>
    
    <!-- Error state -->
    <div v-else-if="hasError && showErrorState" class="lazy-error-state">
      <div class="error-icon">⚠️</div>
      <div class="error-message">{{ errorMessage || 'Failed to load component' }}</div>
      <button 
        v-if="allowRetry" 
        @click="retryLoad" 
        class="retry-button"
        :disabled="isRetrying"
      >
        {{ isRetrying ? 'Retrying...' : 'Retry' }}
      </button>
    </div>
    
    <!-- Loaded component -->
    <component 
      v-else-if="isLoaded && loadedComponent" 
      :is="loadedComponent"
      v-bind="componentProps"
      v-on="componentEvents"
    />
    
    <!-- Placeholder when not yet intersecting -->
    <div 
      v-else-if="!hasIntersected && placeholder" 
      class="lazy-placeholder"
      :style="placeholderStyle"
    >
      <slot name="placeholder">
        <div class="placeholder-content">{{ placeholder }}</div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useIntersectionObserver, performanceMonitor } from '@/utils/performance'
import type { Component } from 'vue'

// Props interface
interface Props {
  // Component loading function
  componentLoader: () => Promise<Component>
  // Unique identifier for this lazy component
  componentId: string
  // Props to pass to the loaded component
  componentProps?: Record<string, any>
  // Events to bind to the loaded component
  componentEvents?: Record<string, Function>
  // Loading state configuration
  showLoadingState?: boolean
  loadingText?: string
  loadingClass?: string
  // Error state configuration
  showErrorState?: boolean
  errorMessage?: string
  allowRetry?: boolean
  maxRetries?: number
  // Placeholder configuration
  placeholder?: string
  placeholderStyle?: Record<string, string>
  // Intersection observer options
  rootMargin?: string
  threshold?: number
  // Performance options
  enablePerformanceMonitoring?: boolean
  preloadDelay?: number
}

// Emits interface
interface Emits {
  (e: 'loading'): void
  (e: 'loaded', component: Component): void
  (e: 'error', error: Error): void
  (e: 'retry', attempt: number): void
  (e: 'intersected'): void
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  componentProps: () => ({}),
  componentEvents: () => ({}),
  showLoadingState: true,
  loadingText: '',
  loadingClass: '',
  showErrorState: true,
  errorMessage: '',
  allowRetry: true,
  maxRetries: 3,
  placeholder: '',
  placeholderStyle: () => ({}),
  rootMargin: '50px',
  threshold: 0.1,
  enablePerformanceMonitoring: true,
  preloadDelay: 0
})

// Emits
const emit = defineEmits<Emits>()

// Reactive state
const containerRef = ref<HTMLElement>()
const isLoading = ref(false)
const isLoaded = ref(false)
const hasError = ref(false)
const hasIntersected = ref(false)
const isRetrying = ref(false)
const loadedComponent = ref<Component | null>(null)
const retryCount = ref(0)
const loadStartTime = ref(0)

// Intersection observer setup
const { observe, unobserve, disconnect } = useIntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && entry.target === containerRef.value) {
        hasIntersected.value = true
        emit('intersected')
        
        // Start loading after optional delay
        if (props.preloadDelay > 0) {
          setTimeout(loadComponent, props.preloadDelay)
        } else {
          loadComponent()
        }
        
        // Stop observing once intersected
        unobserve(entry.target)
      }
    })
  },
  {
    rootMargin: props.rootMargin,
    threshold: props.threshold
  }
)

// Load component function
const loadComponent = async () => {
  if (isLoading.value || isLoaded.value) return
  
  isLoading.value = true
  hasError.value = false
  emit('loading')
  
  // Start performance monitoring
  let endTiming: (() => void) | null = null
  if (props.enablePerformanceMonitoring) {
    loadStartTime.value = performance.now()
    endTiming = performanceMonitor.startTiming(`lazy-component-${props.componentId}`)
  }
  
  try {
    const component = await props.componentLoader()
    
    // Ensure component is valid
    if (!component) {
      throw new Error('Component loader returned null or undefined')
    }
    
    loadedComponent.value = component
    isLoaded.value = true
    emit('loaded', component)
    
    // Record successful load time
    if (props.enablePerformanceMonitoring && endTiming) {
      endTiming()
      const loadTime = performance.now() - loadStartTime.value
      console.debug(`Lazy component ${props.componentId} loaded in ${loadTime.toFixed(2)}ms`)
    }
    
  } catch (error) {
    console.error(`Failed to load lazy component ${props.componentId}:`, error)
    hasError.value = true
    emit('error', error as Error)
    
    // Record failed load time
    if (props.enablePerformanceMonitoring && endTiming) {
      endTiming()
    }
  } finally {
    isLoading.value = false
  }
}

// Retry loading function
const retryLoad = async () => {
  if (retryCount.value >= props.maxRetries) {
    console.warn(`Max retries (${props.maxRetries}) reached for component ${props.componentId}`)
    return
  }
  
  retryCount.value++
  isRetrying.value = true
  emit('retry', retryCount.value)
  
  // Reset state
  hasError.value = false
  loadedComponent.value = null
  isLoaded.value = false
  
  // Wait a bit before retrying
  await new Promise(resolve => setTimeout(resolve, 1000 * retryCount.value))
  
  try {
    await loadComponent()
  } finally {
    isRetrying.value = false
  }
}

// Computed properties
const canRetry = computed(() => {
  return props.allowRetry && retryCount.value < props.maxRetries && !isRetrying.value
})

// Watch for component prop changes
watch(() => props.componentProps, () => {
  // Component props changed, we might need to re-render
  // The component itself will handle prop changes
}, { deep: true })

// Lifecycle hooks
onMounted(async () => {
  await nextTick()
  
  if (containerRef.value) {
    observe(containerRef.value)
  }
})

onUnmounted(() => {
  disconnect()
})

// Expose methods for parent components
defineExpose({
  loadComponent,
  retryLoad,
  isLoading: computed(() => isLoading.value),
  isLoaded: computed(() => isLoaded.value),
  hasError: computed(() => hasError.value),
  retryCount: computed(() => retryCount.value)
})
</script>

<style scoped>
.lazy-component-container {
  width: 100%;
  min-height: 50px;
  position: relative;
}

.lazy-loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top: 3px solid var(--mbti-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-spinner.small {
  width: 1.5rem;
  height: 1.5rem;
  border-width: 2px;
}

.loading-spinner.large {
  width: 3rem;
  height: 3rem;
  border-width: 4px;
}

.loading-text {
  color: var(--mbti-text, #6b7280);
  font-size: 0.875rem;
  font-weight: 500;
}

.lazy-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.5rem;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.retry-button {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.retry-button:hover:not(:disabled) {
  background-color: #b91c1c;
}

.retry-button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.lazy-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  color: #6b7280;
  font-size: 0.875rem;
  text-align: center;
}

.placeholder-content {
  font-style: italic;
}

/* Animation keyframes */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Personality-specific styling */
.lazy-component-container.mbti-intj .loading-spinner,
.lazy-component-container.mbti-entj .loading-spinner,
.lazy-component-container.mbti-istj .loading-spinner,
.lazy-component-container.mbti-estj .loading-spinner {
  border-top-color: #1f2937;
}

.lazy-component-container.mbti-intp .loading-spinner,
.lazy-component-container.mbti-istp .loading-spinner {
  border-top-color: #059669;
}

.lazy-component-container.mbti-estp .loading-spinner {
  border-top-color: #e74c3c;
  animation-duration: 0.8s; /* Faster for flashy personality */
}

.lazy-component-container.mbti-entp .loading-spinner,
.lazy-component-container.mbti-infp .loading-spinner,
.lazy-component-container.mbti-enfp .loading-spinner,
.lazy-component-container.mbti-isfp .loading-spinner,
.lazy-component-container.mbti-esfp .loading-spinner {
  border-top-color: #9b59b6;
  background: linear-gradient(45deg, transparent, rgba(155, 89, 182, 0.1));
}

.lazy-component-container.mbti-isfj .loading-spinner {
  border-top-color: #d4a574;
}

.lazy-component-container.mbti-enfj .loading-spinner,
.lazy-component-container.mbti-esfj .loading-spinner {
  border-top-color: #4caf50;
}

.lazy-component-container.mbti-infj .loading-spinner {
  border-top-color: #5e35b1;
}

/* Responsive design */
@media (max-width: 768px) {
  .lazy-loading-state,
  .lazy-error-state,
  .lazy-placeholder {
    padding: 1rem;
  }
  
  .loading-spinner {
    width: 1.5rem;
    height: 1.5rem;
  }
  
  .error-icon {
    font-size: 1.5rem;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .loading-spinner {
    animation: none;
    border-top-color: transparent;
    border-right-color: var(--mbti-primary, #3b82f6);
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .lazy-error-state {
    border-width: 2px;
  }
  
  .retry-button {
    border: 2px solid currentColor;
  }
  
  .lazy-placeholder {
    border-width: 3px;
  }
}

/* Print styles */
@media print {
  .lazy-loading-state,
  .lazy-error-state {
    display: none;
  }
  
  .lazy-placeholder {
    border-style: solid;
    background-color: #f5f5f5;
  }
}
</style>
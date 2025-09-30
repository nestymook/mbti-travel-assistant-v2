<template>
  <div 
    ref="containerRef"
    class="virtual-scroll-container"
    :style="{ height: `${containerHeight}px` }"
    @scroll="handleScroll"
  >
    <!-- Virtual spacer for items above visible area -->
    <div 
      class="virtual-spacer-top"
      :style="{ height: `${offsetY}px` }"
    ></div>
    
    <!-- Visible items -->
    <div 
      class="virtual-items-container"
      :style="{ transform: `translateY(${offsetY}px)` }"
    >
      <div
        v-for="virtualItem in visibleItems"
        :key="getItemKey(virtualItem.item, virtualItem.index)"
        class="virtual-item"
        :class="getItemClass(virtualItem.item, virtualItem.index)"
        :style="{ 
          height: `${virtualItem.height}px`,
          minHeight: `${virtualItem.height}px`
        }"
        :data-index="virtualItem.index"
      >
        <slot 
          :item="virtualItem.item" 
          :index="virtualItem.index"
          :isVisible="true"
        >
          <div class="default-item">
            {{ getItemDisplay(virtualItem.item) }}
          </div>
        </slot>
      </div>
    </div>
    
    <!-- Virtual spacer for items below visible area -->
    <div 
      class="virtual-spacer-bottom"
      :style="{ height: `${totalHeight - offsetY - visibleHeight}px` }"
    ></div>
    
    <!-- Loading indicator for dynamic loading -->
    <div 
      v-if="isLoading && showLoadingIndicator"
      class="virtual-loading"
    >
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ loadingText }}</div>
    </div>
    
    <!-- Empty state -->
    <div 
      v-if="items.length === 0 && !isLoading && showEmptyState"
      class="virtual-empty-state"
    >
      <slot name="empty">
        <div class="empty-icon">📭</div>
        <div class="empty-message">{{ emptyMessage }}</div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useVirtualScroll, throttle, performanceMonitor } from '@/utils/performance'

// Generic type for items
interface VirtualScrollItem {
  [key: string]: any
}

// Props interface
interface Props<T = VirtualScrollItem> {
  // Data
  items: T[]
  itemHeight: number
  containerHeight: number
  
  // Virtual scrolling options
  overscan?: number
  buffer?: number
  
  // Item configuration
  itemKey?: string | ((item: T, index: number) => string | number)
  itemClass?: string | ((item: T, index: number) => string)
  
  // Loading state
  isLoading?: boolean
  showLoadingIndicator?: boolean
  loadingText?: string
  
  // Empty state
  showEmptyState?: boolean
  emptyMessage?: string
  
  // Performance options
  enablePerformanceMonitoring?: boolean
  scrollThrottleMs?: number
  
  // Dynamic loading
  enableInfiniteScroll?: boolean
  infiniteScrollThreshold?: number
  
  // Accessibility
  ariaLabel?: string
  role?: string
}

// Emits interface
interface Emits<T = VirtualScrollItem> {
  (e: 'scroll', event: { scrollTop: number; scrollLeft: number }): void
  (e: 'item-click', item: T, index: number): void
  (e: 'item-focus', item: T, index: number): void
  (e: 'load-more'): void
  (e: 'scroll-end'): void
  (e: 'scroll-start'): void
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  overscan: 5,
  buffer: 10,
  itemKey: 'id',
  itemClass: '',
  isLoading: false,
  showLoadingIndicator: true,
  loadingText: 'Loading more items...',
  showEmptyState: true,
  emptyMessage: 'No items to display',
  enablePerformanceMonitoring: true,
  scrollThrottleMs: 16,
  enableInfiniteScroll: false,
  infiniteScrollThreshold: 200,
  ariaLabel: 'Virtual scroll list',
  role: 'list'
})

// Emits
const emit = defineEmits<Emits>()

// Reactive state
const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)
const isScrolling = ref(false)
const scrollTimeout = ref<ReturnType<typeof setTimeout>>()

// Virtual scroll composable
const itemsRef = computed(() => props.items)
const {
  visibleItems,
  totalHeight,
  offsetY,
  handleScroll: baseHandleScroll
} = useVirtualScroll(itemsRef, {
  itemHeight: props.itemHeight,
  containerHeight: props.containerHeight,
  overscan: props.overscan,
  buffer: props.buffer
})

// Computed properties
const visibleHeight = computed(() => {
  return visibleItems.value.length * props.itemHeight
})

// Helper functions
const getItemKey = (item: any, index: number): string | number => {
  if (typeof props.itemKey === 'function') {
    return props.itemKey(item, index)
  } else if (typeof props.itemKey === 'string' && item[props.itemKey] !== undefined) {
    return item[props.itemKey]
  } else {
    return index
  }
}

const getItemClass = (item: any, index: number): string => {
  let baseClass = 'virtual-list-item'
  
  if (typeof props.itemClass === 'function') {
    baseClass += ' ' + props.itemClass(item, index)
  } else if (typeof props.itemClass === 'string' && props.itemClass) {
    baseClass += ' ' + props.itemClass
  }
  
  return baseClass
}

const getItemDisplay = (item: any): string => {
  if (typeof item === 'string') return item
  if (item.name) return item.name
  if (item.title) return item.title
  if (item.label) return item.label
  return JSON.stringify(item)
}

// Enhanced scroll handler with performance monitoring
const handleScroll = throttle((event: Event) => {
  const target = event.target as HTMLElement
  const newScrollTop = target.scrollTop
  
  // Performance monitoring
  let endTiming: (() => void) | null = null
  if (props.enablePerformanceMonitoring) {
    endTiming = performanceMonitor.startTiming('virtual-scroll-handler')
  }
  
  // Update scroll position
  scrollTop.value = newScrollTop
  
  // Call base handler
  baseHandleScroll(event)
  
  // Emit scroll event
  emit('scroll', {
    scrollTop: newScrollTop,
    scrollLeft: target.scrollLeft
  })
  
  // Handle scrolling state
  isScrolling.value = true
  clearTimeout(scrollTimeout.value)
  scrollTimeout.value = setTimeout(() => {
    isScrolling.value = false
    emit('scroll-end')
  }, 150)
  
  // Infinite scroll detection
  if (props.enableInfiniteScroll) {
    const scrollHeight = target.scrollHeight
    const clientHeight = target.clientHeight
    const scrollBottom = scrollHeight - newScrollTop - clientHeight
    
    if (scrollBottom <= props.infiniteScrollThreshold && !props.isLoading) {
      emit('load-more')
    }
  }
  
  // End performance monitoring
  if (endTiming) {
    endTiming()
  }
}, props.scrollThrottleMs)

// Item interaction handlers
const handleItemClick = (item: any, index: number) => {
  emit('item-click', item, index)
}

const handleItemFocus = (item: any, index: number) => {
  emit('item-focus', item, index)
}

// Scroll to specific item
const scrollToItem = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  const targetScrollTop = index * props.itemHeight
  containerRef.value.scrollTo({
    top: targetScrollTop,
    behavior
  })
}

// Scroll to top
const scrollToTop = (behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  containerRef.value.scrollTo({
    top: 0,
    behavior
  })
}

// Scroll to bottom
const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  containerRef.value.scrollTo({
    top: containerRef.value.scrollHeight,
    behavior
  })
}

// Watch for items changes
watch(() => props.items.length, (newLength, oldLength) => {
  if (newLength !== oldLength && props.enablePerformanceMonitoring) {
    performanceMonitor.recordMetric('virtual-scroll-items-count', newLength)
  }
})

// Lifecycle hooks
onMounted(async () => {
  await nextTick()
  
  if (containerRef.value) {
    // Set up accessibility attributes
    containerRef.value.setAttribute('aria-label', props.ariaLabel)
    containerRef.value.setAttribute('role', props.role)
    
    // Initial scroll event
    emit('scroll-start')
  }
})

onUnmounted(() => {
  clearTimeout(scrollTimeout.value)
})

// Expose methods for parent components
defineExpose({
  scrollToItem,
  scrollToTop,
  scrollToBottom,
  containerRef,
  visibleItems: computed(() => visibleItems.value),
  totalHeight: computed(() => totalHeight.value),
  scrollTop: computed(() => scrollTop.value),
  isScrolling: computed(() => isScrolling.value)
})
</script>

<style scoped>
.virtual-scroll-container {
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  width: 100%;
  scrollbar-width: thin;
  scrollbar-color: var(--mbti-primary, #3b82f6) transparent;
}

.virtual-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background-color: var(--mbti-primary, #3b82f6);
  border-radius: 4px;
  opacity: 0.7;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  opacity: 1;
}

.virtual-spacer-top,
.virtual-spacer-bottom {
  width: 100%;
  pointer-events: none;
}

.virtual-items-container {
  position: relative;
  width: 100%;
}

.virtual-item {
  width: 100%;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--mbti-border, #e5e7eb);
  transition: background-color 0.15s ease;
  cursor: pointer;
}

.virtual-item:hover {
  background-color: var(--mbti-hover, #f3f4f6);
}

.virtual-item:focus-within {
  outline: 2px solid var(--mbti-primary, #3b82f6);
  outline-offset: -2px;
  background-color: var(--mbti-focus-bg, #eff6ff);
}

.virtual-item:last-child {
  border-bottom: none;
}

.default-item {
  padding: 1rem;
  width: 100%;
  font-size: 0.875rem;
  color: var(--mbti-text, #374151);
}

.virtual-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background-color: var(--mbti-surface, #ffffff);
  border-top: 1px solid var(--mbti-border, #e5e7eb);
}

.loading-spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid var(--mbti-border, #e5e7eb);
  border-top: 2px solid var(--mbti-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: var(--mbti-text-secondary, #6b7280);
  font-size: 0.875rem;
}

.virtual-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--mbti-text-secondary, #6b7280);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-message {
  font-size: 1rem;
  font-weight: 500;
}

/* Animation keyframes */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Personality-specific styling */
.virtual-scroll-container.mbti-estp .virtual-item:hover {
  background: linear-gradient(135deg, var(--mbti-hover, #f3f4f6) 0%, rgba(231, 76, 60, 0.1) 100%);
  transform: translateX(2px);
}

.virtual-scroll-container.mbti-enfp .virtual-item,
.virtual-scroll-container.mbti-infp .virtual-item,
.virtual-scroll-container.mbti-entp .virtual-item,
.virtual-scroll-container.mbti-isfp .virtual-item,
.virtual-scroll-container.mbti-esfp .virtual-item {
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.virtual-scroll-container.mbti-enfp .virtual-item:hover,
.virtual-scroll-container.mbti-infp .virtual-item:hover,
.virtual-scroll-container.mbti-entp .virtual-item:hover,
.virtual-scroll-container.mbti-isfp .virtual-item:hover,
.virtual-scroll-container.mbti-esfp .virtual-item:hover {
  border-left-color: var(--mbti-primary, #3b82f6);
  background: linear-gradient(90deg, var(--mbti-hover, #f3f4f6) 0%, rgba(155, 89, 182, 0.05) 100%);
}

.virtual-scroll-container.mbti-isfj .virtual-item {
  background: linear-gradient(135deg, transparent 0%, rgba(212, 165, 116, 0.02) 100%);
}

/* Responsive design */
@media (max-width: 768px) {
  .virtual-scroll-container {
    scrollbar-width: auto;
  }
  
  .virtual-scroll-container::-webkit-scrollbar {
    width: 12px;
  }
  
  .default-item {
    padding: 0.75rem;
  }
  
  .virtual-empty-state {
    padding: 2rem 1rem;
  }
  
  .empty-icon {
    font-size: 2rem;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .virtual-item {
    border-bottom-width: 2px;
  }
  
  .virtual-item:focus-within {
    outline-width: 3px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .virtual-item {
    transition: none;
  }
  
  .loading-spinner {
    animation: none;
    border-top-color: transparent;
    border-right-color: var(--mbti-primary, #3b82f6);
  }
  
  .virtual-scroll-container.mbti-estp .virtual-item:hover {
    transform: none;
  }
}

/* Print styles */
@media print {
  .virtual-scroll-container {
    overflow: visible;
    height: auto !important;
  }
  
  .virtual-spacer-top,
  .virtual-spacer-bottom {
    display: none;
  }
  
  .virtual-loading {
    display: none;
  }
}
</style>
<template>
  <div class="recommendation-combo-box" :class="personalityClass">
    <label 
      :for="comboBoxId" 
      class="combo-box-label"
      :class="{ 'sr-only': !showLabel }"
    >
      {{ label }}
    </label>
    
    <div class="combo-box-container" ref="comboBoxContainer">
      <button
        :id="comboBoxId"
        ref="comboBoxButton"
        type="button"
        class="combo-box-button"
        :class="{ 'is-open': isOpen, 'has-selection': hasSelection }"
        :aria-expanded="isOpen"
        :aria-haspopup="'listbox'"
        :aria-labelledby="labelId"
        :aria-describedby="descriptionId"
        :disabled="isLoading || options.length === 0"
        @click="toggleDropdown"
        @keydown="handleButtonKeydown"
      >
        <span class="combo-box-text">
          {{ displayText }}
        </span>
        <span class="combo-box-icon" :class="{ 'is-rotated': isOpen }">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4.427 6.427a.75.75 0 011.06 0L8 8.94l2.513-2.513a.75.75 0 111.06 1.06l-3.043 3.044a.75.75 0 01-1.06 0L4.427 7.487a.75.75 0 010-1.06z"/>
          </svg>
        </span>
      </button>

      <ul
        v-show="isOpen"
        ref="listbox"
        class="combo-box-listbox"
        role="listbox"
        :aria-labelledby="labelId"
        :aria-activedescendant="activeDescendant"
        @keydown="handleListKeydown"
        tabindex="-1"
      >
        <li
          v-if="isLoading"
          class="combo-box-option combo-box-loading"
          role="option"
          aria-disabled="true"
        >
          <div class="loading-spinner"></div>
          <span>Loading options...</span>
        </li>
        
        <li
          v-else-if="options.length === 0"
          class="combo-box-option combo-box-empty"
          role="option"
          aria-disabled="true"
        >
          No options available
        </li>
        
        <!-- Virtual scrolling for large lists -->
        <VirtualScrollList
          v-else-if="options.length > virtualScrollThreshold"
          :items="options"
          :item-height="itemHeight"
          :container-height="maxDropdownHeight"
          :enable-performance-monitoring="true"
          class="virtual-options-list"
          @item-click="selectOption"
        >
          <template #default="{ item: option, index }">
            <div
              :id="`${comboBoxId}-option-${index}`"
              class="combo-box-option virtual-option"
              :class="{ 
                'is-selected': isSelected(option), 
                'is-focused': focusedIndex === index 
              }"
              role="option"
              :aria-selected="isSelected(option)"
              @mouseenter="setFocusedIndex(index)"
            >
              <div class="option-content">
                <RestaurantComboBoxItem
                  v-if="type === 'restaurant' && isRestaurant(option)"
                  :restaurant="option"
                  :mbti-personality="mbtiPersonality"
                  :show-detailed-info="true"
                />
                <TouristSpotComboBoxItem
                  v-else-if="type === 'tourist-spot' && isTouristSpot(option)"
                  :tourist-spot="option"
                  :mbti-personality="mbtiPersonality"
                  :show-detailed-info="true"
                />
                <div v-else class="fallback-content">
                  <div class="option-name">{{ getOptionName(option) }}</div>
                  <div v-if="getOptionSubtext(option)" class="option-subtext">
                    {{ getOptionSubtext(option) }}
                  </div>
                </div>
              </div>
              
              <div v-if="isSelected(option)" class="option-checkmark">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
                </svg>
              </div>
            </div>
          </template>
        </VirtualScrollList>
        
        <!-- Regular list for smaller option sets -->
        <template v-else>
          <li
            v-for="(option, index) in options"
            :key="getOptionKey(option)"
            :id="`${comboBoxId}-option-${index}`"
            class="combo-box-option"
            :class="{ 
              'is-selected': isSelected(option), 
              'is-focused': focusedIndex === index 
            }"
            role="option"
            :aria-selected="isSelected(option)"
            @click="selectOption(option)"
            @mouseenter="setFocusedIndex(index)"
          >
            <div class="option-content">
              <RestaurantComboBoxItem
                v-if="type === 'restaurant' && isRestaurant(option)"
                :restaurant="option"
                :mbti-personality="mbtiPersonality"
                :show-detailed-info="true"
              />
              <TouristSpotComboBoxItem
                v-else-if="type === 'tourist-spot' && isTouristSpot(option)"
                :tourist-spot="option"
                :mbti-personality="mbtiPersonality"
                :show-detailed-info="true"
              />
              <div v-else class="fallback-content">
                <div class="option-name">{{ getOptionName(option) }}</div>
                <div v-if="getOptionSubtext(option)" class="option-subtext">
                  {{ getOptionSubtext(option) }}
                </div>
              </div>
            </div>
            
            <div v-if="isSelected(option)" class="option-checkmark">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
              </svg>
            </div>
          </li>
        </template>
      </ul>
    </div>

    <div 
      v-if="description" 
      :id="descriptionId" 
      class="combo-box-description"
    >
      {{ description }}
    </div>

    <div 
      v-if="errorMessage" 
      class="combo-box-error"
      role="alert"
      :aria-live="'polite'"
    >
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { TouristSpot } from '@/types/touristSpot'
import type { Restaurant } from '@/types/restaurant'
import type { MBTIPersonality } from '@/types/mbti'
import VirtualScrollList from '@/components/common/VirtualScrollList.vue'
import RestaurantComboBoxItem from './RestaurantComboBoxItem.vue'
import TouristSpotComboBoxItem from './TouristSpotComboBoxItem.vue'

// Props interface
interface Props {
  modelValue: TouristSpot | Restaurant | null
  options: (TouristSpot | Restaurant)[]
  type: 'tourist-spot' | 'restaurant'
  mbtiPersonality: MBTIPersonality
  label?: string
  showLabel?: boolean
  description?: string
  placeholder?: string
  isLoading?: boolean
  errorMessage?: string
  disabled?: boolean
  
  // Performance options
  virtualScrollThreshold?: number
  itemHeight?: number
  maxDropdownHeight?: number
}

// Emits interface
interface Emits {
  (e: 'update:modelValue', value: TouristSpot | Restaurant | null): void
  (e: 'selection-changed', value: TouristSpot | Restaurant | null): void
  (e: 'focus'): void
  (e: 'blur'): void
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  label: '',
  showLabel: true,
  description: '',
  placeholder: 'Select an option...',
  isLoading: false,
  errorMessage: '',
  disabled: false,
  virtualScrollThreshold: 20,
  itemHeight: 60,
  maxDropdownHeight: 300
})

// Emits
const emit = defineEmits<Emits>()

// Reactive state
const isOpen = ref(false)
const focusedIndex = ref(-1)
const comboBoxContainer = ref<HTMLElement>()
const comboBoxButton = ref<HTMLButtonElement>()
const listbox = ref<HTMLUListElement>()

// Computed properties
const comboBoxId = computed(() => `combo-box-${Math.random().toString(36).substr(2, 9)}`)
const labelId = computed(() => `${comboBoxId.value}-label`)
const descriptionId = computed(() => `${comboBoxId.value}-description`)

const personalityClass = computed(() => `mbti-${props.mbtiPersonality.toLowerCase()}`)

const hasSelection = computed(() => props.modelValue !== null)

const displayText = computed(() => {
  if (props.modelValue) {
    return getOptionName(props.modelValue)
  }
  return props.placeholder
})

const activeDescendant = computed(() => {
  if (focusedIndex.value >= 0 && focusedIndex.value < props.options.length) {
    return `${comboBoxId.value}-option-${focusedIndex.value}`
  }
  return undefined
})

// Type guards
const isRestaurant = (option: TouristSpot | Restaurant): option is Restaurant => {
  return 'mealType' in option && 'sentiment' in option
}

const isTouristSpot = (option: TouristSpot | Restaurant): option is TouristSpot => {
  return 'tourist_spot' in option && 'mbti' in option
}

// Helper functions
const getOptionKey = (option: TouristSpot | Restaurant): string => {
  if (isRestaurant(option)) {
    return option.id
  } else {
    return `${option.tourist_spot}-${option.district}`
  }
}

const getOptionName = (option: TouristSpot | Restaurant): string => {
  if (isRestaurant(option)) {
    return option.name
  } else {
    return option.tourist_spot
  }
}

const getOptionSubtext = (option: TouristSpot | Restaurant): string => {
  if (isRestaurant(option)) {
    return option.mealType.join(', ')
  } else {
    return option.area
  }
}

const formatPriceRange = (priceRange: string): string => {
  const priceMap: Record<string, string> = {
    'budget': '$',
    'moderate': '$$',
    'expensive': '$$$',
    'luxury': '$$$$'
  }
  return priceMap[priceRange] || priceRange
}

const isSelected = (option: TouristSpot | Restaurant): boolean => {
  if (!props.modelValue) return false
  return getOptionKey(option) === getOptionKey(props.modelValue)
}

// Dropdown management
const toggleDropdown = () => {
  if (props.disabled || props.isLoading) return
  
  if (isOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

const openDropdown = async () => {
  isOpen.value = true
  focusedIndex.value = props.modelValue ? 
    props.options.findIndex(option => isSelected(option)) : 
    0
  
  await nextTick()
  listbox.value?.focus()
  emit('focus')
}

const closeDropdown = () => {
  isOpen.value = false
  focusedIndex.value = -1
  comboBoxButton.value?.focus()
  emit('blur')
}

const selectOption = (option: TouristSpot | Restaurant) => {
  emit('update:modelValue', option)
  emit('selection-changed', option)
  closeDropdown()
}

const setFocusedIndex = (index: number) => {
  focusedIndex.value = index
}

// Keyboard navigation
const handleButtonKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowDown':
    case 'ArrowUp':
      event.preventDefault()
      openDropdown()
      break
    case 'Enter':
    case ' ':
      event.preventDefault()
      toggleDropdown()
      break
    case 'Escape':
      if (isOpen.value) {
        event.preventDefault()
        closeDropdown()
      }
      break
  }
}

const handleListKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      focusedIndex.value = Math.min(focusedIndex.value + 1, props.options.length - 1)
      break
    case 'ArrowUp':
      event.preventDefault()
      focusedIndex.value = Math.max(focusedIndex.value - 1, 0)
      break
    case 'Enter':
    case ' ':
      event.preventDefault()
      if (focusedIndex.value >= 0 && focusedIndex.value < props.options.length) {
        const option = props.options[focusedIndex.value]
        if (option) {
          selectOption(option)
        }
      }
      break
    case 'Escape':
      event.preventDefault()
      closeDropdown()
      break
    case 'Home':
      event.preventDefault()
      focusedIndex.value = 0
      break
    case 'End':
      event.preventDefault()
      focusedIndex.value = props.options.length - 1
      break
    default:
      // Handle character navigation
      if (event.key.length === 1) {
        handleCharacterNavigation(event.key.toLowerCase())
      }
      break
  }
}

const handleCharacterNavigation = (char: string) => {
  const startIndex = focusedIndex.value + 1
  const searchOptions = [...props.options.slice(startIndex), ...props.options.slice(0, startIndex)]
  
  const matchIndex = searchOptions.findIndex(option => 
    getOptionName(option).toLowerCase().startsWith(char)
  )
  
  if (matchIndex !== -1) {
    focusedIndex.value = (startIndex + matchIndex) % props.options.length
  }
}

// Click outside handler
const handleClickOutside = (event: Event) => {
  if (comboBoxContainer.value && !comboBoxContainer.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

// Watchers
watch(() => props.options, () => {
  // Reset focused index when options change
  focusedIndex.value = -1
})

watch(() => props.modelValue, () => {
  // Update focused index when selection changes
  if (props.modelValue && isOpen.value) {
    focusedIndex.value = props.options.findIndex(option => isSelected(option))
  }
})

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.recommendation-combo-box {
  position: relative;
  width: 100%;
}

.combo-box-label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-color, #374151);
  font-size: 0.875rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.combo-box-container {
  position: relative;
}

.combo-box-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: white;
  border: 2px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 44px; /* Touch-friendly minimum */
}

.combo-box-button:hover:not(:disabled) {
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.combo-box-button:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.combo-box-button:disabled {
  background-color: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.combo-box-button.is-open {
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.combo-box-button.has-selection {
  color: var(--text-color, #111827);
  font-weight: 500;
}

.combo-box-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.combo-box-icon {
  margin-left: 0.5rem;
  transition: transform 0.2s ease;
  color: #6b7280;
}

.combo-box-icon.is-rotated {
  transform: rotate(180deg);
}

.combo-box-listbox {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  margin-top: 0.25rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  max-height: 16rem;
  overflow-y: auto;
  list-style: none;
  padding: 0;
  margin: 0;
}

.combo-box-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.15s ease;
  border-bottom: 1px solid #f3f4f6;
}

.combo-box-option:last-child {
  border-bottom: none;
}

.combo-box-option:hover,
.combo-box-option.is-focused {
  background-color: var(--secondary-color, #f3f4f6);
}

.combo-box-option.is-selected {
  background-color: var(--primary-color, #3b82f6);
  color: white;
}

.combo-box-option.is-selected:hover,
.combo-box-option.is-selected.is-focused {
  background-color: var(--primary-color, #2563eb);
}

.combo-box-loading,
.combo-box-empty {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  cursor: default;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid #e5e7eb;
  border-top: 2px solid var(--primary-color, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-subtext {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.combo-box-option.is-selected .option-subtext {
  color: rgba(255, 255, 255, 0.8);
}

.fallback-content {
  width: 100%;
}

.option-checkmark {
  margin-left: 0.5rem;
  color: white;
}

.combo-box-description {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.combo-box-error {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #dc2626;
}

/* MBTI Personality-specific styling */
.mbti-intj,
.mbti-entj,
.mbti-istj,
.mbti-estj {
  --primary-color: #1f2937;
  --secondary-color: #f9fafb;
}

.mbti-intp,
.mbti-istp,
.mbti-estp {
  --primary-color: #059669;
  --secondary-color: #ecfdf5;
}

.mbti-entp,
.mbti-infp,
.mbti-enfp,
.mbti-isfp {
  --primary-color: #7c3aed;
  --secondary-color: #f3e8ff;
}

.mbti-infj,
.mbti-isfj,
.mbti-enfj,
.mbti-esfj {
  --primary-color: #dc2626;
  --secondary-color: #fef2f2;
}

.mbti-isfj {
  --primary-color: #d97706;
  --secondary-color: #fef3c7;
}

.mbti-estp .combo-box-button,
.mbti-estp .combo-box-listbox {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
  font-weight: bold;
}

.mbti-estp .combo-box-option:hover,
.mbti-estp .combo-box-option.is-focused {
  background-color: rgba(251, 191, 36, 0.8);
}

/* Responsive design */
@media (max-width: 768px) {
  .combo-box-button {
    padding: 1rem;
    font-size: 1rem;
  }
  
  .combo-box-listbox {
    max-height: 12rem;
  }
  
  .combo-box-option {
    padding: 1rem;
  }
  

}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .combo-box-button {
    border-width: 3px;
  }
  
  .combo-box-option.is-selected {
    outline: 2px solid currentColor;
    outline-offset: -2px;
  }
}

/* Virtual scrolling styles */
.virtual-options-list {
  width: 100%;
  border-radius: 0;
}

.virtual-option {
  border-bottom: 1px solid #f3f4f6;
}

.virtual-option:last-child {
  border-bottom: none;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .combo-box-button,
  .combo-box-icon,
  .combo-box-option {
    transition: none;
  }
  
  .loading-spinner {
    animation: none;
  }
}
</style>
<template>
  <div class="responsive-combo-box" :class="comboBoxClasses">
    <!-- Label for accessibility -->
    <label 
      v-if="label" 
      :for="inputId" 
      class="combo-box-label"
      :class="{ 'sr-only': hideLabel }"
    >
      {{ label }}
      <span v-if="required" class="required-indicator" aria-label="required">*</span>
    </label>
    
    <!-- Native select for better mobile experience -->
    <div class="combo-box-wrapper" :class="{ 'has-error': hasError, 'is-loading': isLoading }">
      <select
        :id="inputId"
        v-model="selectedValue"
        class="combo-box-select"
        :class="selectClasses"
        :disabled="disabled || isLoading"
        :aria-describedby="hasError ? `${inputId}-error` : undefined"
        :aria-invalid="hasError"
        :aria-required="required"
        @change="handleChange"
        @focus="handleFocus"
        @blur="handleBlur"
      >
        <option v-if="placeholder" value="" disabled>
          {{ placeholder }}
        </option>
        <option
          v-for="option in options"
          :key="getOptionKey(option)"
          :value="getOptionValue(option)"
          :disabled="isOptionDisabled(option)"
        >
          {{ getOptionLabel(option) }}
        </option>
      </select>
      
      <!-- Custom dropdown arrow -->
      <div class="combo-box-arrow" :class="{ 'is-loading': isLoading }">
        <svg
          v-if="!isLoading"
          class="arrow-icon"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="m6 8 4 4 4-4"
          />
        </svg>
        <div v-else class="loading-spinner" aria-hidden="true"></div>
      </div>
    </div>
    
    <!-- Error message -->
    <div
      v-if="hasError && errorMessage"
      :id="`${inputId}-error`"
      class="combo-box-error"
      role="alert"
      aria-live="polite"
    >
      {{ errorMessage }}
    </div>
    
    <!-- Help text -->
    <div
      v-if="helpText"
      :id="`${inputId}-help`"
      class="combo-box-help"
    >
      {{ helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import type { MBTIPersonality } from '../../types/mbti'

// Props
interface Props {
  modelValue: string | number | null
  options: Array<any>
  label?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  hideLabel?: boolean
  errorMessage?: string
  helpText?: string
  isLoading?: boolean
  mbtiPersonality?: MBTIPersonality
  optionKey?: string
  optionValue?: string
  optionLabel?: string
  optionDisabled?: string
  size?: 'small' | 'medium' | 'large'
  variant?: 'default' | 'outlined' | 'filled'
}

const props = withDefaults(defineProps<Props>(), {
  label: '',
  placeholder: 'Select an option...',
  disabled: false,
  required: false,
  hideLabel: false,
  errorMessage: '',
  helpText: '',
  isLoading: false,
  optionKey: 'id',
  optionValue: 'value',
  optionLabel: 'label',
  optionDisabled: 'disabled',
  size: 'medium',
  variant: 'default'
})

// Emits
interface Emits {
  (e: 'update:modelValue', value: string | number | null): void
  (e: 'change', value: string | number | null, option: any): void
  (e: 'focus', event: FocusEvent): void
  (e: 'blur', event: FocusEvent): void
}

const emit = defineEmits<Emits>()

// Reactive state
const isFocused = ref(false)
const inputId = ref(`combo-box-${Math.random().toString(36).substr(2, 9)}`)

// Computed properties
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const hasError = computed(() => Boolean(props.errorMessage))

const comboBoxClasses = computed(() => {
  const classes = ['responsive-combo-box']
  
  if (props.mbtiPersonality) {
    classes.push(`mbti-${props.mbtiPersonality.toLowerCase()}`)
    
    // Add personality-specific classes
    const colorfulTypes = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESFP']
    const warmTypes = ['ISFJ']
    const flashyTypes = ['ESTP']
    
    if (colorfulTypes.includes(props.mbtiPersonality)) {
      classes.push('colorful-personality')
    }
    if (warmTypes.includes(props.mbtiPersonality)) {
      classes.push('warm-personality')
    }
    if (flashyTypes.includes(props.mbtiPersonality)) {
      classes.push('flashy-personality')
    }
  }
  
  classes.push(`size-${props.size}`)
  classes.push(`variant-${props.variant}`)
  
  if (hasError.value) classes.push('has-error')
  if (props.disabled) classes.push('is-disabled')
  if (props.isLoading) classes.push('is-loading')
  if (isFocused.value) classes.push('is-focused')
  
  return classes
})

const selectClasses = computed(() => {
  const classes = []
  
  if (hasError.value) classes.push('error')
  if (props.disabled || props.isLoading) classes.push('disabled')
  
  return classes
})

// Helper functions
const getOptionKey = (option: any): string | number => {
  if (typeof option === 'string' || typeof option === 'number') {
    return option
  }
  return option[props.optionKey] || option.id || option.key || JSON.stringify(option)
}

const getOptionValue = (option: any): string | number => {
  if (typeof option === 'string' || typeof option === 'number') {
    return option
  }
  return option[props.optionValue] || option.value || option[props.optionKey] || option.id
}

const getOptionLabel = (option: any): string => {
  if (typeof option === 'string' || typeof option === 'number') {
    return String(option)
  }
  return option[props.optionLabel] || option.label || option.name || String(option[props.optionKey] || option.id)
}

const isOptionDisabled = (option: any): boolean => {
  if (typeof option === 'string' || typeof option === 'number') {
    return false
  }
  return Boolean(option[props.optionDisabled] || option.disabled)
}

// Event handlers
const handleChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const value = target.value === '' ? null : target.value
  
  // Find the selected option object
  const selectedOption = props.options.find(option => 
    String(getOptionValue(option)) === String(value)
  )
  
  emit('change', value, selectedOption)
}

const handleFocus = (event: FocusEvent) => {
  isFocused.value = true
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  isFocused.value = false
  emit('blur', event)
}

// Watch for external value changes
watch(() => props.modelValue, async (newValue) => {
  if (newValue !== selectedValue.value) {
    await nextTick()
    // Ensure the select element reflects the new value
    const selectElement = document.getElementById(inputId.value) as HTMLSelectElement
    if (selectElement && selectElement.value !== String(newValue || '')) {
      selectElement.value = String(newValue || '')
    }
  }
})
</script>

<style scoped>
/* Base responsive combo box styles */
.responsive-combo-box {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm, 0.5rem);
  width: 100%;
}

.combo-box-label {
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 600;
  color: var(--mbti-text, #212529);
  margin-bottom: var(--spacing-xs, 0.25rem);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs, 0.25rem);
}

.required-indicator {
  color: #dc3545;
  font-weight: 700;
}

.combo-box-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.combo-box-select {
  width: 100%;
  padding: var(--spacing-md, 1rem);
  border: 2px solid var(--mbti-border, #dee2e6);
  border-radius: 8px;
  background: var(--mbti-surface, #ffffff);
  color: var(--mbti-text, #212529);
  font-size: var(--font-size-base, 1rem);
  font-family: inherit;
  line-height: 1.5;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  min-height: var(--touch-target-comfortable, 48px);
  padding-right: 3rem; /* Space for custom arrow */
}

.combo-box-select:hover:not(:disabled) {
  border-color: var(--mbti-primary, #007bff);
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.combo-box-select:focus {
  outline: none;
  border-color: var(--mbti-primary, #007bff);
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(0, 123, 255, 0.25));
}

.combo-box-select:disabled {
  background: var(--mbti-disabled-bg, #f8f9fa);
  color: var(--mbti-disabled-text, #6c757d);
  cursor: not-allowed;
  opacity: 0.7;
}

.combo-box-select.error {
  border-color: #dc3545;
}

.combo-box-select.error:focus {
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.25);
}

/* Custom arrow */
.combo-box-arrow {
  position: absolute;
  right: var(--spacing-md, 1rem);
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.arrow-icon {
  width: 16px;
  height: 16px;
  color: var(--mbti-secondary, #6c757d);
  transition: transform 0.2s ease;
}

.is-focused .arrow-icon {
  transform: rotate(180deg);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--mbti-border, #dee2e6);
  border-top-color: var(--mbti-primary, #007bff);
  border-radius: 50%;
  animation: combo-spin 1s linear infinite;
}

@keyframes combo-spin {
  to {
    transform: rotate(360deg);
  }
}

/* Error message */
.combo-box-error {
  font-size: var(--font-size-sm, 0.875rem);
  color: #dc3545;
  margin-top: var(--spacing-xs, 0.25rem);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs, 0.25rem);
}

.combo-box-error::before {
  content: '⚠️';
  font-size: 0.9em;
}

/* Help text */
.combo-box-help {
  font-size: var(--font-size-xs, 0.75rem);
  color: var(--mbti-secondary, #6c757d);
  margin-top: var(--spacing-xs, 0.25rem);
  line-height: 1.4;
}

/* Size variants */
.size-small .combo-box-select {
  padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
  font-size: var(--font-size-sm, 0.875rem);
  min-height: var(--touch-target-min, 44px);
  padding-right: 2.5rem;
}

.size-small .combo-box-arrow {
  right: var(--spacing-sm, 0.5rem);
  width: 16px;
  height: 16px;
}

.size-small .arrow-icon,
.size-small .loading-spinner {
  width: 14px;
  height: 14px;
}

.size-large .combo-box-select {
  padding: var(--spacing-lg, 1.5rem);
  font-size: var(--font-size-lg, 1.125rem);
  min-height: 56px;
  padding-right: 3.5rem;
}

.size-large .combo-box-arrow {
  right: var(--spacing-lg, 1.5rem);
  width: 24px;
  height: 24px;
}

.size-large .arrow-icon,
.size-large .loading-spinner {
  width: 20px;
  height: 20px;
}

/* Variant styles */
.variant-outlined .combo-box-select {
  background: transparent;
  border-width: 2px;
}

.variant-filled .combo-box-select {
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
  border: 1px solid transparent;
}

.variant-filled .combo-box-select:hover:not(:disabled) {
  background: var(--mbti-hover, rgba(0, 123, 255, 0.1));
  border-color: var(--mbti-primary, #007bff);
}

/* Personality-specific enhancements */
.colorful-personality .combo-box-select {
  background: linear-gradient(135deg, var(--mbti-surface, #ffffff) 0%, rgba(255, 255, 255, 0.8) 100%);
}

.colorful-personality .combo-box-select:focus {
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(0, 123, 255, 0.25)), 
              0 0 15px var(--mbti-accent, #28a745);
}

.warm-personality .combo-box-wrapper {
  box-shadow: 0 0 10px var(--mbti-warm-glow, rgba(255, 193, 7, 0.1));
  border-radius: 8px;
}

.flashy-personality .combo-box-select:focus {
  animation: flashy-combo-focus 0.5s ease;
}

@keyframes flashy-combo-focus {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* Responsive breakpoints */
@media (max-width: 480px) {
  .combo-box-select {
    font-size: var(--font-size-base, 1rem);
    padding: var(--spacing-md, 1rem);
    min-height: var(--touch-target-comfortable, 48px);
  }
  
  .combo-box-label {
    font-size: var(--font-size-base, 1rem);
  }
}

@media (min-width: 768px) {
  .combo-box-select {
    padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
    min-height: var(--touch-target-min, 44px);
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .combo-box-select,
  .arrow-icon,
  .loading-spinner {
    transition: none;
    animation: none;
  }
  
  .flashy-personality .combo-box-select:focus {
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .combo-box-select {
    border-width: 3px;
  }
  
  .combo-box-select:focus {
    border-width: 3px;
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }
  
  .combo-box-error {
    font-weight: 600;
  }
}

/* Print styles */
@media print {
  .combo-box-select {
    border: 1px solid #000;
    background: white !important;
    color: #000 !important;
  }
  
  .combo-box-arrow {
    display: none;
  }
}

/* Focus management for keyboard navigation */
.combo-box-select:focus-visible {
  outline: 2px solid var(--mbti-primary, #007bff);
  outline-offset: 2px;
}

/* Screen reader only content */
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

/* Touch feedback for mobile */
@media (hover: none) and (pointer: coarse) {
  .combo-box-select:active {
    background-color: var(--mbti-hover, rgba(0, 123, 255, 0.1));
    transform: scale(0.98);
  }
}

/* Loading state */
.is-loading .combo-box-select {
  pointer-events: none;
  opacity: 0.7;
}

.is-loading .combo-box-arrow .arrow-icon {
  display: none;
}

/* Error state wrapper */
.has-error .combo-box-wrapper {
  position: relative;
}

.has-error .combo-box-wrapper::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid #dc3545;
  border-radius: 8px;
  pointer-events: none;
  opacity: 0.3;
}
</style>
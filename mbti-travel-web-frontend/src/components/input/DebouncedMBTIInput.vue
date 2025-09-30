<template>
  <div class="debounced-mbti-input" :class="{ 'has-error': hasError, 'is-valid': isValid }">
    <label 
      :for="inputId" 
      class="input-label"
      :class="{ 'sr-only': !showLabel }"
    >
      {{ label }}
    </label>
    
    <div class="input-container">
      <input
        :id="inputId"
        ref="inputRef"
        v-model="localValue"
        type="text"
        class="mbti-input"
        :class="inputClass"
        :placeholder="placeholder"
        :disabled="disabled || isLoading"
        :maxlength="4"
        :aria-describedby="hasError ? `${inputId}-error` : undefined"
        :aria-invalid="hasError"
        autocomplete="off"
        spellcheck="false"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
        @keydown="handleKeydown"
        @paste="handlePaste"
      />
      
      <!-- Input status indicators -->
      <div class="input-indicators">
        <!-- Loading indicator -->
        <div v-if="isLoading" class="loading-indicator">
          <div class="loading-spinner"></div>
        </div>
        
        <!-- Validation indicator -->
        <div v-else-if="showValidationIndicator" class="validation-indicator">
          <svg 
            v-if="isValid" 
            class="valid-icon" 
            width="20" 
            height="20" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
          
          <svg 
            v-else-if="hasError && localValue.length > 0" 
            class="error-icon" 
            width="20" 
            height="20" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        
        <!-- Clear button -->
        <button
          v-if="showClearButton && localValue.length > 0 && !disabled"
          type="button"
          class="clear-button"
          :aria-label="clearButtonLabel"
          @click="clearInput"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Character counter -->
    <div v-if="showCharacterCounter" class="character-counter">
      {{ localValue.length }}/4
    </div>
    
    <!-- Error message -->
    <div 
      v-if="hasError && errorMessage" 
      :id="`${inputId}-error`"
      class="error-message"
      role="alert"
      :aria-live="'polite'"
    >
      {{ errorMessage }}
    </div>
    
    <!-- Validation suggestions -->
    <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-container">
      <div class="suggestions-label">Did you mean:</div>
      <div class="suggestions-list">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          type="button"
          class="suggestion-button"
          @click="applySuggestion(suggestion)"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>
    
    <!-- Help text -->
    <div v-if="helpText" class="help-text">
      {{ helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { debounce, performanceMonitor } from '@/utils/performance'
import { ValidationService } from '@/services/validationService'
import type { MBTIPersonality } from '@/types/mbti'

// Props interface
interface Props {
  modelValue: string
  label?: string
  showLabel?: boolean
  placeholder?: string
  disabled?: boolean
  isLoading?: boolean
  
  // Validation options
  validateOnInput?: boolean
  validateOnBlur?: boolean
  debounceMs?: number
  
  // UI options
  showValidationIndicator?: boolean
  showClearButton?: boolean
  showCharacterCounter?: boolean
  showSuggestions?: boolean
  
  // Accessibility
  clearButtonLabel?: string
  helpText?: string
  
  // Styling
  inputClass?: string
  
  // Performance options
  enablePerformanceMonitoring?: boolean
}

// Emits interface
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'validation-changed', isValid: boolean, errors: string[]): void
  (e: 'input', value: string): void
  (e: 'focus'): void
  (e: 'blur'): void
  (e: 'clear'): void
  (e: 'suggestion-applied', suggestion: string): void
}

// Props with defaults
const props = withDefaults(defineProps<Props>(), {
  label: 'MBTI Personality Type',
  showLabel: true,
  placeholder: 'E.g. ENFP, INTJ, INFJ...',
  disabled: false,
  isLoading: false,
  validateOnInput: true,
  validateOnBlur: true,
  debounceMs: 300,
  showValidationIndicator: true,
  showClearButton: true,
  showCharacterCounter: true,
  showSuggestions: true,
  clearButtonLabel: 'Clear input',
  helpText: '',
  inputClass: '',
  enablePerformanceMonitoring: true
})

// Emits
const emit = defineEmits<Emits>()

// Reactive state
const inputRef = ref<HTMLInputElement>()
const localValue = ref(props.modelValue)
const validationErrors = ref<string[]>([])
const suggestions = ref<string[]>([])
const isFocused = ref(false)
const hasBeenBlurred = ref(false)

// Validation service
const validationService = ValidationService.getInstance()

// Computed properties
const inputId = computed(() => `mbti-input-${Math.random().toString(36).substr(2, 9)}`)

const hasError = computed(() => {
  return validationErrors.value.length > 0 && 
         (hasBeenBlurred.value || (props.validateOnInput && localValue.value.length > 0))
})

const isValid = computed(() => {
  return localValue.value.length === 4 && 
         validationErrors.value.length === 0 && 
         hasBeenBlurred.value
})

const errorMessage = computed(() => {
  return hasError.value ? validationErrors.value[0] : ''
})

// Debounced validation function
const debouncedValidation = debounce(async (value: string) => {
  let endTiming: (() => void) | null = null
  
  if (props.enablePerformanceMonitoring) {
    endTiming = performanceMonitor.startTiming('mbti-input-validation')
  }
  
  try {
    const result = validationService.validateMBTICode(value)
    validationErrors.value = result.errors
    
    // Generate suggestions for invalid input
    if (!result.isValid && value.length > 0) {
      suggestions.value = generateSuggestions(value)
    } else {
      suggestions.value = []
    }
    
    emit('validation-changed', result.isValid, result.errors)
  } catch (error) {
    console.error('Validation error:', error)
    validationErrors.value = ['Validation failed']
  } finally {
    if (endTiming) {
      endTiming()
    }
  }
}, props.debounceMs)

// Input handlers
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  let value = target.value.toUpperCase()
  
  // Filter out non-alphabetic characters
  value = value.replace(/[^A-Z]/g, '')
  
  // Limit to 4 characters
  if (value.length > 4) {
    value = value.substring(0, 4)
  }
  
  localValue.value = value
  emit('update:modelValue', value)
  emit('input', value)
  
  // Trigger validation if enabled
  if (props.validateOnInput) {
    debouncedValidation(value)
  }
}

const handleBlur = () => {
  isFocused.value = false
  hasBeenBlurred.value = true
  emit('blur')
  
  // Trigger validation on blur if enabled
  if (props.validateOnBlur) {
    debouncedValidation(localValue.value)
  }
}

const handleFocus = () => {
  isFocused.value = true
  emit('focus')
}

const handleKeydown = (event: KeyboardEvent) => {
  // Allow navigation and editing keys
  const allowedKeys = [
    'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
    'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
    'Home', 'End'
  ]
  
  if (allowedKeys.includes(event.key)) {
    return
  }
  
  // Allow Ctrl/Cmd combinations
  if (event.ctrlKey || event.metaKey) {
    return
  }
  
  // Only allow alphabetic characters
  if (!/^[A-Za-z]$/.test(event.key)) {
    event.preventDefault()
    return
  }
  
  // Prevent input if already at max length
  if (localValue.value.length >= 4) {
    event.preventDefault()
  }
}

const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault()
  
  const pastedText = event.clipboardData?.getData('text') || ''
  const cleanedText = pastedText.toUpperCase().replace(/[^A-Z]/g, '').substring(0, 4)
  
  if (cleanedText) {
    localValue.value = cleanedText
    emit('update:modelValue', cleanedText)
    emit('input', cleanedText)
    
    if (props.validateOnInput) {
      debouncedValidation(cleanedText)
    }
  }
}

// Utility functions
const clearInput = () => {
  localValue.value = ''
  emit('update:modelValue', '')
  emit('clear')
  validationErrors.value = []
  suggestions.value = []
  
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const applySuggestion = (suggestion: string) => {
  localValue.value = suggestion
  emit('update:modelValue', suggestion)
  emit('suggestion-applied', suggestion)
  
  // Validate the suggestion
  if (props.validateOnInput) {
    debouncedValidation(suggestion)
  }
  
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const generateSuggestions = (input: string): string[] => {
  const validTypes: MBTIPersonality[] = [
    'INTJ', 'INTP', 'ENTJ', 'ENTP',
    'INFJ', 'INFP', 'ENFJ', 'ENFP',
    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
    'ISTP', 'ISFP', 'ESTP', 'ESFP'
  ]
  
  if (input.length === 0) return []
  
  // Find close matches based on character similarity
  const suggestions = validTypes.filter(type => {
    if (input.length === 1) {
      return type.startsWith(input)
    } else if (input.length === 2) {
      return type.startsWith(input) || 
             (type[0] === input[0] && type.includes(input[1]))
    } else if (input.length === 3) {
      return type.startsWith(input) ||
             (type.substring(0, 2) === input.substring(0, 2) && type.includes(input[2]))
    } else {
      // For 4 characters, find types with similar character patterns
      const inputChars = input.split('')
      const typeChars = type.split('')
      const matches = inputChars.filter((char, index) => typeChars[index] === char).length
      return matches >= 2
    }
  })
  
  // Sort by similarity and return top 3
  return suggestions
    .sort((a, b) => {
      const aScore = calculateSimilarity(input, a)
      const bScore = calculateSimilarity(input, b)
      return bScore - aScore
    })
    .slice(0, 3)
}

const calculateSimilarity = (input: string, target: string): number => {
  let score = 0
  const minLength = Math.min(input.length, target.length)
  
  for (let i = 0; i < minLength; i++) {
    if (input[i] === target[i]) {
      score += 2 // Position match is worth more
    } else if (target.includes(input[i])) {
      score += 1 // Character present but wrong position
    }
  }
  
  return score
}

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== localValue.value) {
    localValue.value = newValue
    if (props.validateOnInput && newValue) {
      debouncedValidation(newValue)
    }
  }
})

// Lifecycle hooks
onMounted(() => {
  // Initial validation if there's a value
  if (localValue.value && props.validateOnInput) {
    debouncedValidation(localValue.value)
  }
})

onUnmounted(() => {
  // Cancel any pending debounced calls
  debouncedValidation.cancel?.()
})

// Expose methods for parent components
defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  clear: clearInput,
  validate: () => debouncedValidation(localValue.value),
  inputRef
})
</script>

<style scoped>
.debounced-mbti-input {
  width: 100%;
  max-width: 400px;
}

.input-label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--mbti-text, #374151);
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

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.mbti-input {
  width: 100%;
  padding: 0.75rem 3rem 0.75rem 1rem;
  border: 2px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: white;
  transition: all 0.2s ease;
  min-height: 48px; /* Touch-friendly */
}

.mbti-input:focus {
  outline: none;
  border-color: var(--mbti-primary, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.mbti-input:disabled {
  background-color: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.mbti-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
}

/* Validation states */
.has-error .mbti-input {
  border-color: #dc2626;
  background-color: #fef2f2;
}

.has-error .mbti-input:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.2);
}

.is-valid .mbti-input {
  border-color: #059669;
  background-color: #f0fdf4;
}

.is-valid .mbti-input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.2);
}

.input-indicators {
  position: absolute;
  right: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-indicator {
  display: flex;
  align-items: center;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid #e5e7eb;
  border-top: 2px solid var(--mbti-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.validation-indicator {
  display: flex;
  align-items: center;
}

.valid-icon {
  color: #059669;
}

.error-icon {
  color: #dc2626;
}

.clear-button {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: color 0.2s ease;
}

.clear-button:hover {
  color: #374151;
}

.clear-button:focus {
  outline: 2px solid var(--mbti-primary, #3b82f6);
  outline-offset: 2px;
}

.character-counter {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
  text-align: right;
}

.error-message {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.suggestions-container {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.suggestions-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.suggestions-list {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.suggestion-button {
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--mbti-primary, #3b82f6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-button:hover {
  background-color: var(--mbti-primary, #3b82f6);
  color: white;
  border-color: var(--mbti-primary, #3b82f6);
}

.suggestion-button:focus {
  outline: 2px solid var(--mbti-primary, #3b82f6);
  outline-offset: 2px;
}

.help-text {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

/* Animation keyframes */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .mbti-input {
    font-size: 1rem;
    padding: 1rem 3rem 1rem 1rem;
  }
  
  .suggestions-list {
    justify-content: center;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .mbti-input {
    border-width: 3px;
  }
  
  .suggestion-button {
    border-width: 2px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .mbti-input,
  .suggestion-button,
  .clear-button {
    transition: none;
  }
  
  .loading-spinner {
    animation: none;
    border-top-color: transparent;
    border-right-color: var(--mbti-primary, #3b82f6);
  }
}

/* Print styles */
@media print {
  .suggestions-container,
  .loading-indicator,
  .clear-button {
    display: none;
  }
  
  .mbti-input {
    border-color: #000;
    background: white;
  }
}
</style>
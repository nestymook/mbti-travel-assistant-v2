<template>
  <div class="mbti-input-form">
    <div class="form-header">
      <h1>Hong Kong MBTI Travel Planner</h1>
      <h2>Welcome to MBTI Travel Planner for traveling Hong Kong</h2>
    </div>

    <form @submit.prevent="handleSubmit" class="input-form">
      <div class="input-group">
        <input
          v-model="inputValue"
          type="text"
          class="mbti-input"
          :class="{ error: hasError }"
          placeholder="E.g. ENFP, INTJ, INFJ..."
          maxlength="4"
          :disabled="isLoading"
          @input="handleInput"
          @focus="clearError"
          autocomplete="off"
          spellcheck="false"
        />

        <ErrorMessage
          v-if="errorMessage"
          :message="errorMessage"
          :dismissible="true"
          @dismiss="clearError"
        />
      </div>

      <button 
        type="submit" 
        class="submit-button" 
        :disabled="isLoading || !inputValue.trim()"
        :aria-label="isLoading ? 'Generating itinerary...' : 'Generate 3-day itinerary'"
      >
        {{ isLoading ? 'Generating...' : 'Get my 3 days itinerary!' }}
      </button>

      <LoadingSpinner 
        v-if="isLoading" 
        message="Generating Itinerary in progress..." 
      />
    </form>

    <div class="test-link">
      <a 
        :href="MBTI_TEST_URL" 
        target="_blank" 
        rel="noopener noreferrer"
        aria-label="Take MBTI personality test on 16personalities.com"
      >
        Don't know your MBTI type? Take the test here
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ValidationService } from '@/services'
import { MBTI_TEST_URL } from '@/utils'
import ErrorMessage from '@/components/common/ErrorMessage.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

interface Props {
  modelValue: string
  isLoading: boolean
  errorMessage?: string
}

interface Emits {
  'update:modelValue': [value: string]
  submit: [mbtiCode: string]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const validationService = ValidationService.getInstance()
const realTimeValidation = ref<string>('')

const inputValue = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})

const hasError = computed(() => !!props.errorMessage)

// Watch for input changes to provide real-time validation feedback
watch(inputValue, (newValue) => {
  if (newValue && newValue.length > 0) {
    const validation = validationService.validateRealTimeInput(newValue)
    realTimeValidation.value = validation.message || ''
  } else {
    realTimeValidation.value = ''
  }
}, { immediate: true })

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  let value = target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 4)
  
  // Update the input field value
  target.value = value
  
  // Emit the formatted value
  emit('update:modelValue', value)
}

function handleSubmit() {
  if (props.isLoading || !inputValue.value.trim()) {
    return
  }

  const validation = validationService.validateMBTICode(inputValue.value)
  if (validation.isValid) {
    emit('submit', inputValue.value.toUpperCase())
  }
}

function clearError() {
  // Error clearing will be handled by parent component
  realTimeValidation.value = ''
}
</script>

<style scoped>
/* Mobile-first responsive input form */
.mbti-input-form {
  width: 100%;
  max-width: 500px;
  background: var(--mbti-surface, #ffffff);
  padding: var(--spacing-lg, 1.5rem);
  border-radius: 16px;
  box-shadow: 0 4px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
  border: 1px solid var(--mbti-border, #dee2e6);
}

.mbti-input-form:hover {
  box-shadow: 0 8px 16px var(--mbti-shadow, rgba(0, 0, 0, 0.15));
  transform: translateY(-2px);
}

.form-header {
  text-align: center;
  margin-bottom: var(--spacing-xl, 2rem);
}

.form-header h1 {
  color: var(--mbti-primary, #007bff);
  margin-bottom: var(--spacing-md, 1rem);
  font-size: var(--font-size-2xl, 1.5rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.form-header h2 {
  color: var(--mbti-secondary, #6c757d);
  margin-bottom: 0;
  font-size: var(--font-size-base, 1rem);
  font-weight: 400;
  line-height: 1.5;
}

.input-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg, 1.5rem);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm, 0.5rem);
}

.mbti-input {
  width: 100%;
  padding: var(--spacing-lg, 1.5rem);
  font-size: var(--font-size-xl, 1.25rem);
  border: 3px solid var(--mbti-border, #dee2e6);
  border-radius: 12px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.3em;
  transition: all 0.3s ease;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace;
  font-weight: 700;
  background: var(--mbti-surface, #ffffff);
  color: var(--mbti-text, #212529);
  min-height: var(--touch-target-comfortable, 48px);
}

.mbti-input::placeholder {
  color: var(--mbti-secondary, #6c757d);
  opacity: 0.7;
  font-weight: 500;
  letter-spacing: 0.1em;
}

.mbti-input:hover:not(:disabled) {
  border-color: var(--mbti-primary, #007bff);
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.mbti-input:focus {
  outline: none;
  border-color: var(--mbti-primary, #007bff);
  box-shadow: 0 0 0 4px var(--mbti-focus, rgba(0, 123, 255, 0.25));
  transform: translateY(-1px);
}

.mbti-input.error {
  border-color: #dc3545;
  box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.25);
}

.mbti-input:disabled {
  background-color: var(--mbti-disabled-bg, #f8f9fa);
  color: var(--mbti-disabled-text, #6c757d);
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
}

.submit-button {
  width: 100%;
  padding: var(--spacing-lg, 1.5rem);
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: 700;
  color: var(--mbti-surface, #ffffff);
  background: var(--mbti-primary, #007bff);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  min-height: var(--touch-target-comfortable, 48px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm, 0.5rem);
  text-transform: none;
  letter-spacing: 0.02em;
}

.submit-button:hover:not(:disabled) {
  background: var(--mbti-accent, #28a745);
  transform: translateY(-3px);
  box-shadow: 0 6px 12px var(--mbti-shadow, rgba(0, 0, 0, 0.2));
}

.submit-button:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px var(--mbti-shadow, rgba(0, 0, 0, 0.2));
}

.submit-button:disabled {
  background: var(--mbti-disabled-bg, #6c757d);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.7;
}

.test-link {
  text-align: center;
  margin-top: var(--spacing-lg, 1.5rem);
  padding-top: var(--spacing-lg, 1.5rem);
  border-top: 1px solid var(--mbti-border, #dee2e6);
}

.test-link a {
  color: var(--mbti-primary, #007bff);
  text-decoration: none;
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 500;
  transition: all 0.3s ease;
  padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
  border-radius: 6px;
  display: inline-block;
}

.test-link a:hover {
  text-decoration: underline;
  color: var(--mbti-accent, #28a745);
  background: var(--mbti-hover, rgba(0, 123, 255, 0.05));
}

.test-link a:focus {
  outline: 2px solid var(--mbti-primary, #007bff);
  outline-offset: 2px;
  border-radius: 6px;
}

/* Small devices (landscape phones, 480px and up) */
@media (min-width: 480px) {
  .mbti-input-form {
    padding: var(--spacing-xl, 2rem);
  }
  
  .form-header h1 {
    font-size: var(--font-size-3xl, 1.875rem);
  }
  
  .form-header h2 {
    font-size: var(--font-size-lg, 1.125rem);
  }
  
  .mbti-input {
    font-size: var(--font-size-2xl, 1.5rem);
    letter-spacing: 0.25em;
  }
  
  .submit-button {
    font-size: var(--font-size-xl, 1.25rem);
  }
}

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) {
  .form-header h1 {
    font-size: var(--font-size-4xl, 2.25rem);
  }
  
  .form-header h2 {
    font-size: var(--font-size-xl, 1.25rem);
  }
  
  .mbti-input {
    padding: var(--spacing-xl, 2rem);
    font-size: var(--font-size-2xl, 1.5rem);
  }
  
  .submit-button {
    padding: var(--spacing-xl, 2rem);
    font-size: var(--font-size-xl, 1.25rem);
  }
  
  .test-link a {
    font-size: var(--font-size-base, 1rem);
  }
}

/* Large devices (desktops, 1024px and up) */
@media (min-width: 1024px) {
  .mbti-input-form {
    max-width: 600px;
  }
  
  .form-header h1 {
    font-size: 2.5rem;
  }
}

/* Loading state animation */
.submit-button:disabled::after {
  content: '';
  position: absolute;
  top: 50%;
  right: var(--spacing-lg, 1.5rem);
  width: 20px;
  height: 20px;
  margin-top: -10px;
  border: 2px solid transparent;
  border-top: 2px solid rgba(255, 255, 255, 0.7);
  border-radius: 50%;
  animation: button-spin 1s linear infinite;
}

@keyframes button-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .mbti-input-form,
  .mbti-input,
  .submit-button,
  .test-link a {
    transition: none;
  }
  
  .mbti-input-form:hover {
    transform: none;
  }
  
  .mbti-input:focus,
  .submit-button:hover:not(:disabled),
  .submit-button:active:not(:disabled) {
    transform: none;
  }
  
  .submit-button:disabled::after {
    animation: none;
  }
}

@media (prefers-contrast: high) {
  .mbti-input-form {
    border-width: 2px;
  }
  
  .mbti-input {
    border-width: 4px;
  }
  
  .submit-button {
    border: 2px solid currentColor;
  }
  
  .test-link a {
    border: 1px solid currentColor;
  }
}

/* Print styles */
@media print {
  .mbti-input-form {
    box-shadow: none;
    border: 2px solid #000;
  }
  
  .mbti-input,
  .submit-button {
    border: 1px solid #000;
    background: white !important;
    color: #000 !important;
  }
  
  .test-link a {
    color: #000 !important;
  }
}

/* Focus management for keyboard navigation */
.mbti-input:focus-visible,
.submit-button:focus-visible,
.test-link a:focus-visible {
  outline: 3px solid var(--mbti-primary, #007bff);
  outline-offset: 2px;
}

/* Touch feedback for mobile */
@media (hover: none) and (pointer: coarse) {
  .mbti-input:active {
    background-color: var(--mbti-hover, rgba(0, 123, 255, 0.05));
    transform: scale(0.98);
  }
  
  .submit-button:active:not(:disabled) {
    transform: scale(0.95);
  }
  
  .test-link a:active {
    background-color: var(--mbti-hover, rgba(0, 123, 255, 0.1));
    transform: scale(0.95);
  }
}

/* High-DPI display optimizations */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .mbti-input-form {
    box-shadow: 0 2px 3px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  }
  
  .mbti-input-form:hover {
    box-shadow: 0 4px 8px var(--mbti-shadow, rgba(0, 0, 0, 0.15));
  }
}
</style>

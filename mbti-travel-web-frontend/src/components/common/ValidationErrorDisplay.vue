<template>
  <div class="validation-error-display">
    <!-- Field-specific errors -->
    <div 
      v-for="error in fieldErrors" 
      :key="error.field"
      class="validation-error-item"
      :class="`validation-error-item--${error.type}`"
    >
      <ErrorMessage
        :message="error.message"
        :title="getErrorTitle(error)"
        :suggestion="getErrorSuggestion(error)"
        severity="warning"
        variant="inline"
        :dismissible="false"
        :actions="getErrorActions(error)"
        @action="handleErrorAction"
      />
    </div>

    <!-- Form-level errors -->
    <div v-if="formErrors.length > 0" class="form-errors">
      <ErrorMessage
        v-for="error in formErrors"
        :key="error.message"
        :message="error.message"
        title="Form Validation Error"
        severity="error"
        variant="banner"
        :dismissible="true"
        @dismiss="dismissFormError(error)"
      />
    </div>

    <!-- Validation summary -->
    <div 
      v-if="showSummary && (fieldErrors.length > 0 || formErrors.length > 0)"
      class="validation-summary"
    >
      <div class="validation-summary-header">
        <span class="validation-summary-icon">📋</span>
        <h3 class="validation-summary-title">Validation Summary</h3>
      </div>
      <ul class="validation-summary-list">
        <li 
          v-for="error in allErrors" 
          :key="`${error.field}-${error.type}`"
          class="validation-summary-item"
        >
          <button 
            @click="focusField(error.field)"
            class="validation-summary-link"
          >
            {{ error.field }}: {{ error.message }}
          </button>
        </li>
      </ul>
    </div>

    <!-- Quick fix suggestions -->
    <div 
      v-if="quickFixes.length > 0" 
      class="quick-fixes"
    >
      <div class="quick-fixes-header">
        <span class="quick-fixes-icon">💡</span>
        <h4 class="quick-fixes-title">Quick Fixes</h4>
      </div>
      <div class="quick-fixes-list">
        <button
          v-for="fix in quickFixes"
          :key="fix.id"
          @click="applyQuickFix(fix)"
          class="quick-fix-button"
          :disabled="fix.loading"
        >
          <span v-if="fix.loading" class="quick-fix-loading">⏳</span>
          <span class="quick-fix-icon">{{ fix.icon }}</span>
          <span class="quick-fix-text">{{ fix.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ErrorMessage from './ErrorMessage.vue'
import type { 
  FormValidationError, 
  ValidationError,
  ErrorNotificationAction 
} from '@/types/error'

export interface QuickFix {
  id: string
  label: string
  icon: string
  action: () => void | Promise<void>
  loading?: boolean
  field?: string
  value?: unknown
}

interface Props {
  fieldErrors?: FormValidationError[]
  formErrors?: ValidationError[]
  showSummary?: boolean
  showQuickFixes?: boolean
}

interface Emits {
  'fix-applied': [fix: QuickFix]
  'error-dismissed': [error: ValidationError]
  'field-focus': [field: string]
}

const props = withDefaults(defineProps<Props>(), {
  fieldErrors: () => [],
  formErrors: () => [],
  showSummary: true,
  showQuickFixes: true
})

const emit = defineEmits<Emits>()

// Reactive state for quick fixes
const quickFixesState = ref<Record<string, boolean>>({})

// Computed properties
const allErrors = computed(() => [
  ...props.fieldErrors,
  ...props.formErrors.map(error => ({
    field: error.field || 'form',
    message: error.message,
    type: 'custom' as const,
    value: undefined
  }))
])

const quickFixes = computed<QuickFix[]>(() => {
  if (!props.showQuickFixes) return []

  const fixes: QuickFix[] = []

  props.fieldErrors.forEach(error => {
    // Add quick fixes based on error type and field
    const fieldFixes = generateQuickFixesForError(error)
    fixes.push(...fieldFixes)
  })

  return fixes
})

/**
 * Get error title based on error type
 */
function getErrorTitle(error: FormValidationError): string {
  switch (error.type) {
    case 'required':
      return 'Required Field'
    case 'format':
      return 'Invalid Format'
    case 'length':
      return 'Length Validation'
    case 'custom':
      return 'Validation Error'
    default:
      return 'Validation Error'
  }
}

/**
 * Get error suggestion based on error details
 */
function getErrorSuggestion(error: FormValidationError): string | undefined {
  switch (error.type) {
    case 'required':
      return `Please provide a value for ${error.field}`
    
    case 'format':
      if (error.field.toLowerCase().includes('mbti')) {
        return 'Please enter a valid 4-letter MBTI code (e.g., ENFP, INTJ)'
      }
      if (error.field.toLowerCase().includes('email')) {
        return 'Please enter a valid email address (e.g., user@example.com)'
      }
      return 'Please check the format of your input'
    
    case 'length':
      if (error.field.toLowerCase().includes('mbti')) {
        return 'MBTI personality type must be exactly 4 characters'
      }
      return 'Please check the length of your input'
    
    default:
      return undefined
  }
}

/**
 * Get error actions based on error type
 */
function getErrorActions(error: FormValidationError): ErrorNotificationAction[] {
  const actions: ErrorNotificationAction[] = []

  // Add focus action
  actions.push({
    label: 'Go to field',
    action: () => focusField(error.field),
    style: 'secondary'
  })

  // Add specific actions based on error type
  if (error.type === 'format' && error.field.toLowerCase().includes('mbti')) {
    actions.push({
      label: 'Show valid types',
      action: () => showMBTIHelp(),
      style: 'secondary'
    })
  }

  return actions
}

/**
 * Generate quick fixes for specific error
 */
function generateQuickFixesForError(error: FormValidationError): QuickFix[] {
  const fixes: QuickFix[] = []

  switch (error.type) {
    case 'format':
      if (error.field.toLowerCase().includes('mbti')) {
        // Suggest common MBTI types
        const commonTypes = ['ENFP', 'INTJ', 'INFJ', 'ENTP']
        commonTypes.forEach(type => {
          fixes.push({
            id: `mbti-${type}`,
            label: `Use ${type}`,
            icon: '🎯',
            action: () => applyMBTIType(error.field, type),
            field: error.field,
            value: type
          })
        })
      }
      break

    case 'required':
      // Add placeholder suggestions
      if (error.field.toLowerCase().includes('mbti')) {
        fixes.push({
          id: `placeholder-${error.field}`,
          label: 'Use ENFP (example)',
          icon: '💡',
          action: () => applyMBTIType(error.field, 'ENFP'),
          field: error.field,
          value: 'ENFP'
        })
      }
      break

    case 'length':
      if (error.field.toLowerCase().includes('mbti') && error.value) {
        const value = String(error.value)
        if (value.length < 4) {
          // Suggest completing the MBTI type
          const suggestions = suggestMBTICompletion(value)
          suggestions.forEach((suggestion, index) => {
            fixes.push({
              id: `complete-${error.field}-${index}`,
              label: `Complete as ${suggestion}`,
              icon: '✨',
              action: () => applyMBTIType(error.field, suggestion),
              field: error.field,
              value: suggestion
            })
          })
        }
      }
      break
  }

  return fixes
}

/**
 * Apply quick fix
 */
async function applyQuickFix(fix: QuickFix): Promise<void> {
  try {
    // Set loading state
    quickFixesState.value[fix.id] = true

    // Execute the fix
    await fix.action()

    // Emit event
    emit('fix-applied', fix)

    // Focus the field if specified
    if (fix.field) {
      focusField(fix.field)
    }
  } catch (error) {
    console.error('Quick fix failed:', error)
  } finally {
    // Clear loading state
    quickFixesState.value[fix.id] = false
  }
}

/**
 * Apply MBTI type to field
 */
function applyMBTIType(field: string, type: string): void {
  // This would need to be implemented based on the specific form
  // For now, we'll emit an event that the parent can handle
  emit('fix-applied', {
    id: `mbti-${field}`,
    label: `Set ${field} to ${type}`,
    icon: '🎯',
    action: () => {},
    field,
    value: type
  })
}

/**
 * Suggest MBTI completion based on partial input
 */
function suggestMBTICompletion(partial: string): string[] {
  const allTypes = [
    'INTJ', 'INTP', 'ENTJ', 'ENTP',
    'INFJ', 'INFP', 'ENFJ', 'ENFP',
    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
    'ISTP', 'ISFP', 'ESTP', 'ESFP'
  ]

  return allTypes
    .filter(type => type.startsWith(partial.toUpperCase()))
    .slice(0, 3) // Limit to 3 suggestions
}

/**
 * Focus on specific field
 */
function focusField(field: string): void {
  emit('field-focus', field)
  
  // Try to focus the field element
  const element = document.querySelector(`[name="${field}"], #${field}, .field-${field} input`)
  if (element && 'focus' in element) {
    (element as HTMLElement).focus()
  }
}

/**
 * Show MBTI help
 */
function showMBTIHelp(): void {
  // This could open a modal or navigate to help page
  window.open('https://www.16personalities.com', '_blank')
}

/**
 * Dismiss form error
 */
function dismissFormError(error: ValidationError): void {
  emit('error-dismissed', error)
}

/**
 * Handle error action
 */
function handleErrorAction(action: ErrorNotificationAction): void {
  if (typeof action.action === 'function') {
    action.action()
  }
}
</script>

<style scoped>
.validation-error-display {
  margin: 1rem 0;
}

.validation-error-item {
  margin-bottom: 0.5rem;
}

.validation-error-item--required {
  border-left: 3px solid #f59e0b;
}

.validation-error-item--format {
  border-left: 3px solid #ef4444;
}

.validation-error-item--length {
  border-left: 3px solid #8b5cf6;
}

.validation-error-item--custom {
  border-left: 3px solid #6b7280;
}

.form-errors {
  margin-bottom: 1rem;
}

.validation-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.validation-summary-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.validation-summary-icon {
  font-size: 1.25rem;
}

.validation-summary-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: #374151;
}

.validation-summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.validation-summary-item {
  margin-bottom: 0.5rem;
}

.validation-summary-link {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.875rem;
  padding: 0;
  text-align: left;
}

.validation-summary-link:hover {
  color: #1d4ed8;
}

.quick-fixes {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.quick-fixes-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.quick-fixes-icon {
  font-size: 1.25rem;
}

.quick-fixes-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: #0c4a6e;
}

.quick-fixes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.quick-fix-button {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background: #0ea5e9;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-fix-button:hover:not(:disabled) {
  background: #0284c7;
  transform: translateY(-1px);
}

.quick-fix-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.quick-fix-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.quick-fix-icon {
  font-size: 1rem;
}

.quick-fix-text {
  font-size: 0.8125rem;
}

/* Responsive design */
@media (max-width: 640px) {
  .quick-fixes-list {
    flex-direction: column;
  }
  
  .quick-fix-button {
    justify-content: center;
  }
  
  .validation-summary-link {
    display: block;
    padding: 0.25rem 0;
  }
}

/* Focus styles for accessibility */
.quick-fix-button:focus,
.validation-summary-link:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .validation-summary,
  .quick-fixes {
    border-width: 2px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .quick-fix-button {
    transition: none;
  }
  
  .quick-fix-button:hover:not(:disabled) {
    transform: none;
  }
  
  .quick-fix-loading {
    animation: none;
  }
}
</style>
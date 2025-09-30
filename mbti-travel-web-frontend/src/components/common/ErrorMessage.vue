<template>
  <div 
    class="error-message" 
    :class="[
      `error-message--${severity}`,
      `error-message--${variant}`,
      { 'error-message--dismissible': dismissible }
    ]"
    role="alert"
    :aria-live="severity === 'error' ? 'assertive' : 'polite'"
  >
    <div class="error-content">
      <span class="error-icon" :aria-hidden="true">{{ getErrorIcon() }}</span>
      <div class="error-details">
        <div class="error-title" v-if="title">{{ title }}</div>
        <div class="error-text">{{ message }}</div>
        <div class="error-suggestion" v-if="suggestion">
          {{ suggestion }}
        </div>
        <div class="error-actions" v-if="actions && actions.length > 0">
          <button
            v-for="action in actions"
            :key="action.label"
            @click="handleAction(action)"
            :class="[
              'error-action-button',
              `error-action-button--${action.style || 'secondary'}`
            ]"
            :disabled="action.loading"
          >
            <span v-if="action.loading" class="action-loading">⏳</span>
            {{ action.label }}
          </button>
        </div>
      </div>
    </div>
    <button 
      v-if="dismissible" 
      @click="$emit('dismiss')" 
      class="dismiss-button"
      aria-label="Dismiss error message"
    >
      ✕
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ErrorNotificationAction } from '@/types/error'

interface Props {
  message: string
  title?: string
  suggestion?: string
  severity?: 'info' | 'warning' | 'error' | 'success'
  variant?: 'inline' | 'banner' | 'toast'
  dismissible?: boolean
  actions?: ErrorNotificationAction[]
}

interface Emits {
  dismiss: []
  action: [action: ErrorNotificationAction]
}

const props = withDefaults(defineProps<Props>(), {
  severity: 'error',
  variant: 'inline',
  dismissible: true,
  actions: () => []
})

const emit = defineEmits<Emits>()

function getErrorIcon(): string {
  switch (props.severity) {
    case 'success':
      return '✅'
    case 'warning':
      return '⚠️'
    case 'info':
      return 'ℹ️'
    case 'error':
    default:
      return '❌'
  }
}

function handleAction(action: ErrorNotificationAction): void {
  emit('action', action)
  if (typeof action.action === 'function') {
    action.action()
  }
}
</script>

<style scoped>
.error-message {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* Severity variants */
.error-message--error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.error-message--warning {
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fed7aa;
}

.error-message--info {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.error-message--success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

/* Display variants */
.error-message--banner {
  border-radius: 0;
  margin: 0;
  border-left: none;
  border-right: none;
}

.error-message--toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.error-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  flex: 1;
}

.error-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.error-details {
  flex: 1;
  min-width: 0;
}

.error-title {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.error-text {
  font-weight: 500;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.error-suggestion {
  font-size: 0.8125rem;
  opacity: 0.8;
  line-height: 1.4;
  margin-bottom: 0.75rem;
}

.error-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
  justify-content: center;
}

.error-action-button {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  border: 1px solid transparent;
}

.error-action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-action-button--primary {
  background: #dc2626 !important;
  color: white !important;
  border-color: #dc2626 !important;
}

.error-action-button--primary:hover:not(:disabled) {
  background: #b91c1c !important;
  color: white !important;
  transform: translateY(-1px);
}

.error-action-button--secondary {
  background: transparent !important;
  color: #374151 !important;
  border-color: #d1d5db !important;
}

.error-action-button--secondary:hover:not(:disabled) {
  background: #f3f4f6 !important;
  color: #374151 !important;
  transform: translateY(-1px);
}

.error-action-button--danger {
  background: #dc2626;
  color: white;
}

.error-action-button--danger:hover:not(:disabled) {
  background: #b91c1c;
}

.action-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dismiss-button {
  background: none;
  border: none;
  color: currentColor;
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
  flex-shrink: 0;
  opacity: 0.7;
  line-height: 1;
}

.dismiss-button:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

/* Responsive design */
@media (max-width: 640px) {
  .error-message--toast {
    left: 1rem;
    right: 1rem;
    max-width: none;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .error-action-button {
    justify-content: center;
  }
}

/* Animation for toast messages */
.error-message--toast {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Focus styles for accessibility */
.error-action-button:focus,
.dismiss-button:focus {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .error-message {
    border-width: 2px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .error-message,
  .error-action-button,
  .dismiss-button {
    transition: none;
  }
  
  .error-message--toast {
    animation: none;
  }
  
  .action-loading {
    animation: none;
  }
}
</style>

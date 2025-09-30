<template>
  <div class="error-notification-system">
    <!-- Toast notifications -->
    <Teleport to="body">
      <div class="toast-container">
        <TransitionGroup name="toast" tag="div">
          <ErrorMessage
            v-for="notification in toastNotifications"
            :key="notification.id"
            :message="notification.message"
            :title="notification.title"
            :severity="notification.severity"
            variant="toast"
            :dismissible="true"
            :actions="notification.actions"
            @dismiss="dismissNotification(notification.id)"
            @action="handleNotificationAction"
          />
        </TransitionGroup>
      </div>
    </Teleport>

    <!-- Banner notifications -->
    <div v-if="bannerNotifications.length > 0" class="banner-container">
      <TransitionGroup name="banner" tag="div">
        <ErrorMessage
          v-for="notification in bannerNotifications"
          :key="notification.id"
          :message="notification.message"
          :title="notification.title"
          :severity="notification.severity"
          variant="banner"
          :dismissible="true"
          :actions="notification.actions"
          @dismiss="dismissNotification(notification.id)"
          @action="handleNotificationAction"
        />
      </TransitionGroup>
    </div>

    <!-- Modal notifications -->
    <Teleport to="body">
      <div
        v-for="notification in modalNotifications"
        :key="notification.id"
        class="modal-overlay"
        @click.self="dismissNotification(notification.id)"
      >
        <div class="modal-content" role="dialog" :aria-labelledby="`modal-title-${notification.id}`">
          <div class="modal-header">
            <h2 :id="`modal-title-${notification.id}`" class="modal-title">
              {{ notification.title }}
            </h2>
            <button
              @click="dismissNotification(notification.id)"
              class="modal-close"
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          <div class="modal-body">
            <ErrorMessage
              :message="notification.message"
              :severity="notification.severity"
              variant="inline"
              :dismissible="false"
              :actions="notification.actions"
              @action="handleNotificationAction"
            />
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Global error overlay for critical errors -->
    <Teleport to="body">
      <div
        v-if="criticalError"
        class="critical-error-overlay"
        role="dialog"
        aria-labelledby="critical-error-title"
        aria-modal="true"
      >
        <div class="critical-error-content">
          <div class="critical-error-icon">🚨</div>
          <h1 id="critical-error-title" class="critical-error-title">
            Critical Error
          </h1>
          <p class="critical-error-message">
            {{ criticalError.message }}
          </p>
          <div class="critical-error-actions">
            <button
              @click="reloadApplication"
              class="critical-error-button critical-error-button--primary"
            >
              Reload Application
            </button>
            <button
              @click="clearAndRestart"
              class="critical-error-button critical-error-button--secondary"
            >
              Clear Data & Restart
            </button>
            <button
              v-if="criticalError.technicalDetails"
              @click="showTechnicalDetails = !showTechnicalDetails"
              class="critical-error-button critical-error-button--tertiary"
            >
              {{ showTechnicalDetails ? 'Hide' : 'Show' }} Technical Details
            </button>
          </div>
          <div
            v-if="showTechnicalDetails && criticalError.technicalDetails"
            class="technical-details"
          >
            <h3 class="technical-details-title">Technical Details</h3>
            <pre class="technical-details-content">{{ formatTechnicalDetails(criticalError.technicalDetails) }}</pre>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Network status indicator -->
    <div
      v-if="showNetworkStatus && !isOnline"
      class="network-status-indicator"
    >
      <span class="network-status-icon">📡</span>
      <span class="network-status-text">Offline</span>
      <button
        @click="checkConnection"
        class="network-status-button"
        :disabled="checkingConnection"
      >
        {{ checkingConnection ? 'Checking...' : 'Retry' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useNetworkStatus } from '@/composables/useNetworkStatus'
import { errorRecovery } from '@/utils/globalErrorHandler'
import ErrorMessage from './ErrorMessage.vue'
import type { ErrorNotification, ErrorNotificationAction, AppError } from '@/types/error'

interface Props {
  showNetworkStatus?: boolean
  maxToastNotifications?: number
  autoCloseDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  showNetworkStatus: true,
  maxToastNotifications: 5,
  autoCloseDelay: 5000
})

// Composables
const { activeNotifications, dismissNotification: dismissGlobalNotification } = useErrorHandler()
const { isOnline, testConnectivity } = useNetworkStatus()

// Local state
const showTechnicalDetails = ref(false)
const checkingConnection = ref(false)

// Computed properties
const toastNotifications = computed(() =>
  activeNotifications.value
    .filter(n => n.type === 'toast')
    .slice(0, props.maxToastNotifications)
)

const bannerNotifications = computed(() =>
  activeNotifications.value.filter(n => n.type === 'banner')
)

const modalNotifications = computed(() =>
  activeNotifications.value.filter(n => n.type === 'modal')
)

const criticalError = computed(() => {
  const criticalNotifications = activeNotifications.value.filter(n => 
    n.severity === 'error' && 
    (n.message.includes('critical') || n.message.includes('Critical'))
  )
  return criticalNotifications.length > 0 ? criticalNotifications[0] : null
})

/**
 * Dismiss notification
 */
function dismissNotification(id: string): void {
  dismissGlobalNotification(id)
}

/**
 * Handle notification action
 */
function handleNotificationAction(action: ErrorNotificationAction): void {
  if (typeof action.action === 'function') {
    action.action()
  }
}

/**
 * Reload application
 */
function reloadApplication(): void {
  errorRecovery.reloadPage()
}

/**
 * Clear data and restart
 */
function clearAndRestart(): void {
  errorRecovery.restartApplication()
}

/**
 * Check network connection
 */
async function checkConnection(): Promise<void> {
  checkingConnection.value = true
  try {
    await testConnectivity()
  } finally {
    checkingConnection.value = false
  }
}

/**
 * Format technical details for display
 */
function formatTechnicalDetails(details: unknown): string {
  if (typeof details === 'string') {
    return details
  }
  
  try {
    return JSON.stringify(details, null, 2)
  } catch (error) {
    return String(details)
  }
}

// Auto-close notifications
onMounted(() => {
  const interval = setInterval(() => {
    const now = Date.now()
    activeNotifications.value.forEach(notification => {
      if (notification.autoClose && notification.duration) {
        const createdAt = new Date(notification.id.split('_')[1]).getTime()
        if (now - createdAt > notification.duration) {
          dismissNotification(notification.id)
        }
      }
    })
  }, 1000)

  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.error-notification-system {
  position: relative;
  z-index: 1000;
}

/* Toast container */
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1050;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
  pointer-events: none;
}

.toast-container > * {
  pointer-events: auto;
}

/* Banner container */
.banner-container {
  position: relative;
  z-index: 1040;
}

/* Modal overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1060;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: #111827;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0.25rem;
  border-radius: 4px;
  transition: color 0.2s ease;
}

.modal-close:hover {
  color: #374151;
}

.modal-body {
  padding: 1rem 1.5rem 1.5rem;
}

/* Critical error overlay */
.critical-error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(220, 38, 38, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1070;
  padding: 1rem;
}

.critical-error-content {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.critical-error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.critical-error-title {
  font-size: 2rem;
  font-weight: 700;
  color: #dc2626;
  margin: 0 0 1rem;
}

.critical-error-message {
  font-size: 1.125rem;
  color: #374151;
  margin: 0 0 2rem;
  line-height: 1.6;
}

.critical-error-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.critical-error-button {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  font-size: 1rem;
}

.critical-error-button--primary {
  background: #dc2626;
  color: white;
}

.critical-error-button--primary:hover {
  background: #b91c1c;
}

.critical-error-button--secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.critical-error-button--secondary:hover {
  background: #e5e7eb;
}

.critical-error-button--tertiary {
  background: transparent;
  color: #6b7280;
  text-decoration: underline;
}

.critical-error-button--tertiary:hover {
  color: #374151;
}

/* Technical details */
.technical-details {
  text-align: left;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.technical-details-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: #374151;
}

.technical-details-content {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  font-size: 0.8125rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #374151;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

/* Network status indicator */
.network-status-indicator {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  background: #fbbf24;
  color: #92400e;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1030;
}

.network-status-icon {
  font-size: 1.25rem;
}

.network-status-text {
  font-weight: 500;
}

.network-status-button {
  background: #92400e;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.network-status-button:hover:not(:disabled) {
  background: #78350f;
}

.network-status-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Transitions */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.banner-enter-active,
.banner-leave-active {
  transition: all 0.3s ease;
}

.banner-enter-from,
.banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Responsive design */
@media (max-width: 640px) {
  .toast-container {
    left: 1rem;
    right: 1rem;
    max-width: none;
  }
  
  .modal-overlay {
    padding: 0.5rem;
  }
  
  .critical-error-content {
    padding: 1.5rem;
  }
  
  .critical-error-actions {
    flex-direction: column;
  }
  
  .network-status-indicator {
    left: 0.5rem;
    right: 0.5rem;
    bottom: 0.5rem;
    justify-content: center;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .modal-content,
  .critical-error-content {
    border: 2px solid #000;
  }
  
  .network-status-indicator {
    border: 2px solid #92400e;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active,
  .banner-enter-active,
  .banner-leave-active,
  .critical-error-button,
  .modal-close,
  .network-status-button {
    transition: none;
  }
}

/* Focus styles for accessibility */
.modal-close:focus,
.critical-error-button:focus,
.network-status-button:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
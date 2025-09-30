// Network connectivity and offline detection composable
import { ref, readonly, onMounted, onUnmounted } from 'vue'
import { useErrorHandler } from './useErrorHandler'

// Network status state
const isOnline = ref(navigator.onLine)
const connectionType = ref<string>('unknown')
const effectiveType = ref<string>('unknown')
const downlink = ref<number>(0)
const rtt = ref<number>(0)
const saveData = ref<boolean>(false)

// Network change listeners
let onlineListener: (() => void) | null = null
let offlineListener: (() => void) | null = null
let connectionChangeListener: (() => void) | null = null

export function useNetworkStatus() {
  const { handleError, showErrorNotification } = useErrorHandler()

  /**
   * Initialize network status monitoring
   */
  function initializeNetworkMonitoring(): void {
    // Update initial network status
    updateNetworkStatus()

    // Set up event listeners
    onlineListener = () => {
      isOnline.value = true
      updateNetworkStatus()
      handleOnlineStatusChange(true)
    }

    offlineListener = () => {
      isOnline.value = false
      updateNetworkStatus()
      handleOnlineStatusChange(false)
    }

    connectionChangeListener = () => {
      updateNetworkStatus()
    }

    // Add event listeners
    window.addEventListener('online', onlineListener)
    window.addEventListener('offline', offlineListener)

    // Monitor connection changes if supported
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      connection?.addEventListener('change', connectionChangeListener)
    }
  }

  /**
   * Clean up network monitoring
   */
  function cleanupNetworkMonitoring(): void {
    if (onlineListener) {
      window.removeEventListener('online', onlineListener)
      onlineListener = null
    }

    if (offlineListener) {
      window.removeEventListener('offline', offlineListener)
      offlineListener = null
    }

    if (connectionChangeListener && 'connection' in navigator) {
      const connection = (navigator as any).connection
      connection?.removeEventListener('change', connectionChangeListener)
      connectionChangeListener = null
    }
  }

  /**
   * Update network status information
   */
  function updateNetworkStatus(): void {
    isOnline.value = navigator.onLine

    // Get connection information if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      if (connection) {
        connectionType.value = connection.type || 'unknown'
        effectiveType.value = connection.effectiveType || 'unknown'
        downlink.value = connection.downlink || 0
        rtt.value = connection.rtt || 0
        saveData.value = connection.saveData || false
      }
    }
  }

  /**
   * Handle online/offline status changes
   */
  function handleOnlineStatusChange(online: boolean): void {
    if (online) {
      showErrorNotification({
        type: 'network_error',
        message: 'Connection restored',
        offline: false,
        timestamp: new Date().toISOString()
      })
    } else {
      showErrorNotification({
        type: 'network_error',
        message: 'Connection lost. Please check your internet connection.',
        offline: true,
        timestamp: new Date().toISOString()
      })
    }
  }

  /**
   * Test network connectivity by making a request
   */
  async function testConnectivity(): Promise<boolean> {
    if (!navigator.onLine) {
      return false
    }

    try {
      // Use a lightweight endpoint or create a test endpoint
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
        signal: AbortSignal.timeout(5000) // 5 second timeout
      })
      return response.ok
    } catch (error) {
      console.warn('Connectivity test failed:', error)
      return false
    }
  }

  /**
   * Get network quality assessment
   */
  function getNetworkQuality(): 'excellent' | 'good' | 'fair' | 'poor' | 'unknown' {
    if (!isOnline.value) {
      return 'poor'
    }

    if (effectiveType.value === '4g' && downlink.value > 10) {
      return 'excellent'
    } else if (effectiveType.value === '4g' || (effectiveType.value === '3g' && downlink.value > 1.5)) {
      return 'good'
    } else if (effectiveType.value === '3g' || effectiveType.value === '2g') {
      return 'fair'
    } else if (downlink.value < 0.5) {
      return 'poor'
    }

    return 'unknown'
  }

  /**
   * Check if connection is suitable for heavy operations
   */
  function isSuitableForHeavyOperations(): boolean {
    if (!isOnline.value) {
      return false
    }

    // Don't perform heavy operations on slow connections or when save data is enabled
    if (saveData.value) {
      return false
    }

    const quality = getNetworkQuality()
    return quality === 'excellent' || quality === 'good'
  }

  /**
   * Get connection speed estimate
   */
  function getConnectionSpeed(): string {
    if (!isOnline.value) {
      return 'Offline'
    }

    if (downlink.value === 0) {
      return 'Unknown'
    }

    if (downlink.value >= 10) {
      return 'Fast'
    } else if (downlink.value >= 1.5) {
      return 'Moderate'
    } else {
      return 'Slow'
    }
  }

  /**
   * Wait for network to come online
   */
  function waitForOnline(timeout: number = 30000): Promise<boolean> {
    return new Promise((resolve) => {
      if (isOnline.value) {
        resolve(true)
        return
      }

      const timeoutId = setTimeout(() => {
        cleanup()
        resolve(false)
      }, timeout)

      const onlineHandler = () => {
        cleanup()
        resolve(true)
      }

      const cleanup = () => {
        clearTimeout(timeoutId)
        window.removeEventListener('online', onlineHandler)
      }

      window.addEventListener('online', onlineHandler)
    })
  }

  /**
   * Retry operation when network becomes available
   */
  async function retryWhenOnline<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    timeout: number = 30000
  ): Promise<T> {
    let retries = 0

    while (retries < maxRetries) {
      try {
        // Wait for network if offline
        if (!isOnline.value) {
          const networkAvailable = await waitForOnline(timeout)
          if (!networkAvailable) {
            throw new Error('Network timeout: Unable to establish connection')
          }
        }

        // Test actual connectivity
        const hasConnectivity = await testConnectivity()
        if (!hasConnectivity) {
          throw new Error('Network connectivity test failed')
        }

        // Attempt the operation
        return await operation()
      } catch (error) {
        retries++
        
        if (retries >= maxRetries) {
          throw error
        }

        // Wait before retrying with exponential backoff
        const delay = Math.min(1000 * Math.pow(2, retries - 1), 10000)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }

    throw new Error('Max retries exceeded')
  }

  /**
   * Get network status summary
   */
  function getNetworkStatusSummary() {
    return {
      isOnline: isOnline.value,
      connectionType: connectionType.value,
      effectiveType: effectiveType.value,
      downlink: downlink.value,
      rtt: rtt.value,
      saveData: saveData.value,
      quality: getNetworkQuality(),
      speed: getConnectionSpeed(),
      suitableForHeavyOps: isSuitableForHeavyOperations()
    }
  }

  // Auto-initialize when composable is used
  onMounted(() => {
    initializeNetworkMonitoring()
  })

  onUnmounted(() => {
    cleanupNetworkMonitoring()
  })

  return {
    // Reactive state
    isOnline: readonly(isOnline),
    connectionType: readonly(connectionType),
    effectiveType: readonly(effectiveType),
    downlink: readonly(downlink),
    rtt: readonly(rtt),
    saveData: readonly(saveData),

    // Methods
    initializeNetworkMonitoring,
    cleanupNetworkMonitoring,
    updateNetworkStatus,
    testConnectivity,
    getNetworkQuality,
    isSuitableForHeavyOperations,
    getConnectionSpeed,
    waitForOnline,
    retryWhenOnline,
    getNetworkStatusSummary
  }
}
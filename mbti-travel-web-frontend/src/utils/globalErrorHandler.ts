// Global error handler setup for Vue application
import type { App } from 'vue'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { AppError, ErrorContext } from '@/types/error'

// Global error handler instance
let globalErrorHandler: ReturnType<typeof useErrorHandler> | null = null

/**
 * Set up global error handling for Vue application
 */
export function setupGlobalErrorHandling(app: App): void {
  // Initialize global error handler
  globalErrorHandler = useErrorHandler()

  // Vue error handler for component errors
  app.config.errorHandler = (error: unknown, instance, info) => {
    console.error('Vue Error Handler:', { error, instance, info })
    
    const context: Partial<ErrorContext> = {
      additionalData: {
        vueErrorInfo: info,
        componentName: instance?.$options.name || 'Unknown',
        componentStack: instance?.$parent ? 'Has parent' : 'Root component'
      }
    }

    globalErrorHandler?.handleError(error, context)
  }

  // Global unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason)
    
    const context: Partial<ErrorContext> = {
      additionalData: {
        type: 'unhandledrejection',
        promise: event.promise
      }
    }

    globalErrorHandler?.handleError(event.reason, context)
    
    // Prevent the default browser behavior (logging to console)
    event.preventDefault()
  })

  // Global error handler for uncaught exceptions
  window.addEventListener('error', (event) => {
    console.error('Global Error Handler:', event.error)
    
    const context: Partial<ErrorContext> = {
      additionalData: {
        type: 'uncaughtexception',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        message: event.message
      }
    }

    globalErrorHandler?.handleError(event.error || new Error(event.message), context)
  })

  // Network error monitoring
  setupNetworkErrorMonitoring()

  // Performance error monitoring
  setupPerformanceErrorMonitoring()

  // Console error interception (for development)
  if (import.meta.env.DEV) {
    setupConsoleErrorInterception()
  }
}

/**
 * Set up network error monitoring
 */
function setupNetworkErrorMonitoring(): void {
  // Monitor fetch failures
  const originalFetch = window.fetch
  window.fetch = async (...args) => {
    try {
      const response = await originalFetch(...args)
      
      // Handle HTTP error responses
      if (!response.ok) {
        const error: AppError = {
          type: 'api_error',
          status: response.status,
          message: `HTTP ${response.status}: ${response.statusText}`,
          retryable: response.status >= 500 || response.status === 408 || response.status === 429,
          timestamp: new Date().toISOString()
        }
        
        globalErrorHandler?.handleError(error, {
          additionalData: {
            url: args[0],
            method: typeof args[1] === 'object' ? args[1]?.method : 'GET',
            status: response.status,
            statusText: response.statusText
          }
        })
      }
      
      return response
    } catch (error) {
      // Network error (no response)
      const networkError: AppError = {
        type: 'network_error',
        message: error instanceof Error ? error.message : 'Network request failed',
        offline: !navigator.onLine,
        timestamp: new Date().toISOString()
      }
      
      globalErrorHandler?.handleError(networkError, {
        additionalData: {
          url: args[0],
          method: typeof args[1] === 'object' ? args[1]?.method : 'GET'
        }
      })
      
      throw error
    }
  }

  // Monitor XMLHttpRequest failures
  const originalXHROpen = XMLHttpRequest.prototype.open
  const originalXHRSend = XMLHttpRequest.prototype.send

  XMLHttpRequest.prototype.open = function(method, url, ...args) {
    this._method = method
    this._url = url
    return originalXHROpen.call(this, method, url, ...args)
  }

  XMLHttpRequest.prototype.send = function(...args) {
    this.addEventListener('error', () => {
      const networkError: AppError = {
        type: 'network_error',
        message: 'XMLHttpRequest failed',
        offline: !navigator.onLine,
        timestamp: new Date().toISOString()
      }
      
      globalErrorHandler?.handleError(networkError, {
        additionalData: {
          method: this._method,
          url: this._url,
          status: this.status,
          statusText: this.statusText
        }
      })
    })

    this.addEventListener('load', () => {
      if (this.status >= 400) {
        const apiError: AppError = {
          type: 'api_error',
          status: this.status,
          message: `HTTP ${this.status}: ${this.statusText}`,
          retryable: this.status >= 500 || this.status === 408 || this.status === 429,
          timestamp: new Date().toISOString()
        }
        
        globalErrorHandler?.handleError(apiError, {
          additionalData: {
            method: this._method,
            url: this._url,
            status: this.status,
            statusText: this.statusText,
            responseText: this.responseText
          }
        })
      }
    })

    return originalXHRSend.call(this, ...args)
  }
}

/**
 * Set up performance error monitoring
 */
function setupPerformanceErrorMonitoring(): void {
  // Monitor long tasks
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 50) { // Tasks longer than 50ms
            const performanceError: AppError = {
              type: 'application_error',
              message: `Long task detected: ${entry.duration.toFixed(2)}ms`,
              severity: entry.duration > 100 ? 'high' : 'medium',
              recoverable: true,
              timestamp: new Date().toISOString()
            }
            
            globalErrorHandler?.handleError(performanceError, {
              additionalData: {
                type: 'performance',
                entryType: entry.entryType,
                duration: entry.duration,
                startTime: entry.startTime
              }
            })
          }
        }
      })
      
      observer.observe({ entryTypes: ['longtask'] })
    } catch (error) {
      console.warn('Performance monitoring not supported:', error)
    }
  }

  // Monitor memory usage (if available)
  if ('memory' in performance) {
    setInterval(() => {
      const memory = (performance as any).memory
      if (memory.usedJSHeapSize > memory.jsHeapSizeLimit * 0.9) {
        const memoryError: AppError = {
          type: 'application_error',
          message: 'High memory usage detected',
          severity: 'high',
          recoverable: false,
          timestamp: new Date().toISOString()
        }
        
        globalErrorHandler?.handleError(memoryError, {
          additionalData: {
            type: 'memory',
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit
          }
        })
      }
    }, 30000) // Check every 30 seconds
  }
}

/**
 * Set up console error interception for development
 */
function setupConsoleErrorInterception(): void {
  const originalConsoleError = console.error
  const originalConsoleWarn = console.warn

  console.error = (...args) => {
    // Call original console.error
    originalConsoleError(...args)
    
    // Handle as application error
    const message = args.map(arg => 
      typeof arg === 'string' ? arg : JSON.stringify(arg)
    ).join(' ')
    
    const consoleError: AppError = {
      type: 'application_error',
      message: `Console Error: ${message}`,
      severity: 'medium',
      recoverable: true,
      timestamp: new Date().toISOString()
    }
    
    globalErrorHandler?.handleError(consoleError, {
      additionalData: {
        type: 'console',
        level: 'error',
        args
      }
    })
  }

  console.warn = (...args) => {
    // Call original console.warn
    originalConsoleWarn(...args)
    
    // Handle as application warning (only for specific patterns)
    const message = args.map(arg => 
      typeof arg === 'string' ? arg : JSON.stringify(arg)
    ).join(' ')
    
    // Only handle Vue warnings and other critical warnings
    if (message.includes('[Vue warn]') || message.includes('deprecated')) {
      const consoleWarning: AppError = {
        type: 'application_error',
        message: `Console Warning: ${message}`,
        severity: 'low',
        recoverable: true,
        timestamp: new Date().toISOString()
      }
      
      globalErrorHandler?.handleError(consoleWarning, {
        additionalData: {
          type: 'console',
          level: 'warn',
          args
        }
      })
    }
  }
}

/**
 * Get global error handler instance
 */
export function getGlobalErrorHandler(): ReturnType<typeof useErrorHandler> | null {
  return globalErrorHandler
}

/**
 * Manually report error to global handler
 */
export function reportError(error: unknown, context?: Partial<ErrorContext>): void {
  if (globalErrorHandler) {
    globalErrorHandler.handleError(error, context)
  } else {
    console.error('Global error handler not initialized:', error)
  }
}

/**
 * Create error boundary for Vue components
 */
export function createErrorBoundary() {
  return {
    errorCaptured(error: unknown, instance: any, info: string) {
      console.error('Error Boundary:', { error, instance, info })
      
      const context: Partial<ErrorContext> = {
        additionalData: {
          errorBoundary: true,
          componentName: instance?.$options.name || 'Unknown',
          errorInfo: info
        }
      }
      
      globalErrorHandler?.handleError(error, context)
      
      // Return false to stop the error from propagating further
      return false
    }
  }
}

/**
 * Error recovery utilities
 */
export const errorRecovery = {
  /**
   * Reload current page
   */
  reloadPage(): void {
    window.location.reload()
  },

  /**
   * Navigate to safe page
   */
  navigateToSafePage(): void {
    window.location.href = '/'
  },

  /**
   * Clear application state
   */
  clearApplicationState(): void {
    // Clear localStorage
    try {
      localStorage.clear()
    } catch (error) {
      console.warn('Failed to clear localStorage:', error)
    }

    // Clear sessionStorage
    try {
      sessionStorage.clear()
    } catch (error) {
      console.warn('Failed to clear sessionStorage:', error)
    }

    // Clear cookies (basic approach)
    document.cookie.split(";").forEach(cookie => {
      const eqPos = cookie.indexOf("=")
      const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`
    })
  },

  /**
   * Restart application
   */
  restartApplication(): void {
    this.clearApplicationState()
    this.reloadPage()
  }
}

// Export types for use in other files
export type { AppError, ErrorContext } from '@/types/error'
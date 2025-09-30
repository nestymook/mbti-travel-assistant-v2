// Composable for managing user interaction feedback
import { ref, reactive, nextTick } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'
import type { FeedbackType, FeedbackPosition } from '@/components/common/InteractionFeedback.vue'

export interface FeedbackMessage {
  id: string
  type: FeedbackType
  message: string
  title?: string
  duration?: number
  position?: FeedbackPosition
  dismissible?: boolean
  showIcon?: boolean
  showProgress?: boolean
  progress?: number
  mbtiPersonality?: MBTIPersonality
  customClass?: string
  visible: boolean
  timestamp: number
}

export interface FeedbackOptions {
  title?: string
  duration?: number
  position?: FeedbackPosition
  dismissible?: boolean
  showIcon?: boolean
  showProgress?: boolean
  progress?: number
  mbtiPersonality?: MBTIPersonality
  customClass?: string
}

export function useFeedback() {
  const messages = ref<FeedbackMessage[]>([])
  const nextId = ref(0)

  // Generate unique ID for each message
  const generateId = (): string => {
    return `feedback_${Date.now()}_${++nextId.value}`
  }

  // Add a new feedback message
  const addMessage = (
    type: FeedbackType,
    message: string,
    options: FeedbackOptions = {}
  ): string => {
    const id = generateId()
    
    const feedbackMessage: FeedbackMessage = {
      id,
      type,
      message,
      title: options.title,
      duration: options.duration ?? (type === 'error' ? 6000 : 4000),
      position: options.position ?? 'top-right',
      dismissible: options.dismissible ?? true,
      showIcon: options.showIcon ?? true,
      showProgress: options.showProgress ?? false,
      progress: options.progress ?? 0,
      mbtiPersonality: options.mbtiPersonality,
      customClass: options.customClass,
      visible: true,
      timestamp: Date.now()
    }
    
    messages.value.push(feedbackMessage)
    
    // Auto-dismiss if duration is set
    if (feedbackMessage.duration > 0) {
      setTimeout(() => {
        dismissMessage(id)
      }, feedbackMessage.duration)
    }
    
    return id
  }

  // Dismiss a specific message
  const dismissMessage = (id: string) => {
    const index = messages.value.findIndex(msg => msg.id === id)
    if (index !== -1) {
      messages.value[index].visible = false
      
      // Remove from array after transition
      setTimeout(() => {
        const currentIndex = messages.value.findIndex(msg => msg.id === id)
        if (currentIndex !== -1) {
          messages.value.splice(currentIndex, 1)
        }
      }, 300)
    }
  }

  // Update message progress
  const updateProgress = (id: string, progress: number, message?: string) => {
    const msg = messages.value.find(m => m.id === id)
    if (msg) {
      msg.progress = Math.min(100, Math.max(0, progress))
      if (message) {
        msg.message = message
      }
    }
  }

  // Clear all messages
  const clearAll = () => {
    messages.value.forEach(msg => {
      msg.visible = false
    })
    
    setTimeout(() => {
      messages.value.length = 0
    }, 300)
  }

  // Clear messages of specific type
  const clearByType = (type: FeedbackType) => {
    messages.value
      .filter(msg => msg.type === type)
      .forEach(msg => dismissMessage(msg.id))
  }

  // Convenience methods for different message types
  const success = (message: string, options?: FeedbackOptions): string => {
    return addMessage('success', message, options)
  }

  const error = (message: string, options?: FeedbackOptions): string => {
    return addMessage('error', message, {
      duration: 6000,
      ...options
    })
  }

  const warning = (message: string, options?: FeedbackOptions): string => {
    return addMessage('warning', message, options)
  }

  const info = (message: string, options?: FeedbackOptions): string => {
    return addMessage('info', message, options)
  }

  const loading = (message: string, options?: FeedbackOptions): string => {
    return addMessage('loading', message, {
      duration: 0, // Don't auto-dismiss loading messages
      dismissible: false,
      showProgress: true,
      ...options
    })
  }

  // Personality-specific feedback methods
  const personalityFeedback = {
    // Structured personalities - detailed feedback
    structured: (type: FeedbackType, message: string, personality: MBTIPersonality, options?: FeedbackOptions) => {
      return addMessage(type, message, {
        title: `${personality} Update`,
        showProgress: true,
        mbtiPersonality: personality,
        ...options
      })
    },

    // Flexible personalities - casual feedback
    flexible: (type: FeedbackType, message: string, personality: MBTIPersonality, options?: FeedbackOptions) => {
      return addMessage(type, message, {
        position: 'bottom',
        showIcon: false,
        mbtiPersonality: personality,
        ...options
      })
    },

    // Colorful personalities - vibrant feedback
    colorful: (type: FeedbackType, message: string, personality: MBTIPersonality, options?: FeedbackOptions) => {
      return addMessage(type, message, {
        position: 'center',
        customClass: 'feedback-colorful-animation',
        mbtiPersonality: personality,
        ...options
      })
    },

    // Feeling personalities - warm feedback
    feeling: (type: FeedbackType, message: string, personality: MBTIPersonality, options?: FeedbackOptions) => {
      return addMessage(type, message, {
        title: 'Friendly Update',
        duration: 5000,
        mbtiPersonality: personality,
        ...options
      })
    }
  }

  // Common feedback scenarios
  const scenarios = {
    // API call feedback
    apiCall: {
      start: (operation: string, personality?: MBTIPersonality) => {
        return loading(`${operation} in progress...`, {
          mbtiPersonality: personality,
          showProgress: true
        })
      },
      
      success: (operation: string, personality?: MBTIPersonality) => {
        return success(`${operation} completed successfully!`, {
          mbtiPersonality: personality
        })
      },
      
      error: (operation: string, errorMsg: string, personality?: MBTIPersonality) => {
        return error(`${operation} failed: ${errorMsg}`, {
          title: 'Operation Failed',
          mbtiPersonality: personality
        })
      }
    },

    // Form validation feedback
    validation: {
      invalid: (field: string, reason: string, personality?: MBTIPersonality) => {
        return warning(`${field}: ${reason}`, {
          title: 'Validation Error',
          position: 'top',
          mbtiPersonality: personality
        })
      },
      
      valid: (field: string, personality?: MBTIPersonality) => {
        return success(`${field} is valid`, {
          duration: 2000,
          mbtiPersonality: personality
        })
      }
    },

    // Data update feedback
    dataUpdate: {
      saving: (item: string, personality?: MBTIPersonality) => {
        return loading(`Saving ${item}...`, {
          mbtiPersonality: personality
        })
      },
      
      saved: (item: string, personality?: MBTIPersonality) => {
        return success(`${item} saved successfully`, {
          mbtiPersonality: personality
        })
      },
      
      updated: (item: string, personality?: MBTIPersonality) => {
        return info(`${item} updated`, {
          duration: 3000,
          mbtiPersonality: personality
        })
      }
    },

    // Combo box feedback
    comboBox: {
      loading: (item: string, personality?: MBTIPersonality) => {
        return loading(`Loading ${item} options...`, {
          position: 'bottom-right',
          duration: 0,
          mbtiPersonality: personality
        })
      },
      
      updated: (item: string, personality?: MBTIPersonality) => {
        return success(`${item} selection updated`, {
          duration: 2000,
          position: 'bottom-right',
          mbtiPersonality: personality
        })
      },
      
      error: (item: string, personality?: MBTIPersonality) => {
        return error(`Failed to load ${item} options`, {
          position: 'bottom-right',
          mbtiPersonality: personality
        })
      }
    }
  }

  return {
    // State
    messages,
    
    // Core methods
    addMessage,
    dismissMessage,
    updateProgress,
    clearAll,
    clearByType,
    
    // Convenience methods
    success,
    error,
    warning,
    info,
    loading,
    
    // Personality-specific methods
    personalityFeedback,
    
    // Common scenarios
    scenarios
  }
}

// Global feedback instance for app-wide notifications
let globalFeedback: ReturnType<typeof useFeedback> | null = null

export function useGlobalFeedback() {
  if (!globalFeedback) {
    globalFeedback = useFeedback()
  }
  return globalFeedback
}

// Feedback manager for handling multiple feedback contexts
export class FeedbackManager {
  private contexts: Map<string, ReturnType<typeof useFeedback>> = new Map()
  
  getContext(name: string): ReturnType<typeof useFeedback> {
    if (!this.contexts.has(name)) {
      this.contexts.set(name, useFeedback())
    }
    return this.contexts.get(name)!
  }
  
  clearContext(name: string) {
    const context = this.contexts.get(name)
    if (context) {
      context.clearAll()
      this.contexts.delete(name)
    }
  }
  
  clearAllContexts() {
    this.contexts.forEach(context => context.clearAll())
    this.contexts.clear()
  }
}

// Global feedback manager instance
export const feedbackManager = new FeedbackManager()
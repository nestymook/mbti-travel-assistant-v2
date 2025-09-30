// Composable for managing loading states with progress indicators
import { ref, computed, type Ref } from 'vue'
import type { MBTIPersonality } from '@/types/mbti'

export interface LoadingState {
  isLoading: boolean
  message?: string
  progress?: number
  estimatedTime?: number
  startTime?: number
  error?: string
}

export interface LoadingOptions {
  message?: string
  estimatedTime?: number
  showProgress?: boolean
  progressSteps?: string[]
}

export function useLoadingState(initialState: Partial<LoadingState> = {}) {
  // Reactive state
  const loadingState = ref<LoadingState>({
    isLoading: false,
    message: undefined,
    progress: undefined,
    estimatedTime: undefined,
    startTime: undefined,
    error: undefined,
    ...initialState
  })

  // Computed properties
  const isLoading = computed(() => loadingState.value.isLoading)
  const hasError = computed(() => !!loadingState.value.error)
  const elapsedTime = computed(() => {
    if (!loadingState.value.startTime) return 0
    return Math.floor((Date.now() - loadingState.value.startTime) / 1000)
  })

  const remainingTime = computed(() => {
    if (!loadingState.value.estimatedTime || !loadingState.value.progress) return undefined
    
    const elapsed = elapsedTime.value
    const progressRatio = loadingState.value.progress / 100
    
    if (progressRatio <= 0) return loadingState.value.estimatedTime
    
    const estimatedTotal = elapsed / progressRatio
    return Math.max(0, Math.floor(estimatedTotal - elapsed))
  })

  // Progress tracking
  let progressInterval: number | null = null
  let currentStep = 0

  // Start loading
  const startLoading = (options: LoadingOptions = {}) => {
    loadingState.value = {
      isLoading: true,
      message: options.message || 'Loading...',
      progress: options.showProgress ? 0 : undefined,
      estimatedTime: options.estimatedTime,
      startTime: Date.now(),
      error: undefined
    }

    // Start progress simulation if enabled
    if (options.showProgress && options.estimatedTime) {
      startProgressSimulation(options.estimatedTime, options.progressSteps)
    }
  }

  // Stop loading
  const stopLoading = () => {
    loadingState.value.isLoading = false
    loadingState.value.startTime = undefined
    stopProgressSimulation()
  }

  // Update loading message
  const updateMessage = (message: string) => {
    if (loadingState.value.isLoading) {
      loadingState.value.message = message
    }
  }

  // Update progress manually
  const updateProgress = (progress: number, message?: string) => {
    if (loadingState.value.isLoading) {
      loadingState.value.progress = Math.min(100, Math.max(0, progress))
      if (message) {
        loadingState.value.message = message
      }
    }
  }

  // Set error state
  const setError = (error: string) => {
    loadingState.value.error = error
    loadingState.value.isLoading = false
    stopProgressSimulation()
  }

  // Clear error
  const clearError = () => {
    loadingState.value.error = undefined
  }

  // Progress simulation for long-running operations
  const startProgressSimulation = (estimatedTime: number, steps?: string[]) => {
    if (!steps || steps.length === 0) {
      // Simple linear progress
      const increment = 100 / (estimatedTime * 10) // Update every 100ms
      
      progressInterval = window.setInterval(() => {
        if (loadingState.value.progress !== undefined && loadingState.value.progress < 95) {
          loadingState.value.progress = Math.min(95, loadingState.value.progress + increment)
        }
      }, 100)
    } else {
      // Step-based progress
      const stepDuration = estimatedTime / steps.length
      currentStep = 0
      
      const updateStep = () => {
        if (currentStep < steps.length) {
          const progress = (currentStep / steps.length) * 100
          updateProgress(progress, steps[currentStep])
          currentStep++
          
          if (currentStep < steps.length) {
            setTimeout(updateStep, stepDuration * 1000)
          }
        }
      }
      
      updateStep()
    }
  }

  const stopProgressSimulation = () => {
    if (progressInterval) {
      clearInterval(progressInterval)
      progressInterval = null
    }
    currentStep = 0
  }

  // Preset loading configurations for common operations
  const presets = {
    itineraryGeneration: {
      message: 'Generating your personalized itinerary...',
      estimatedTime: 100, // 100 seconds as per requirements
      showProgress: true,
      progressSteps: [
        'Analyzing your MBTI personality...',
        'Finding matching tourist spots...',
        'Selecting restaurants for your taste...',
        'Optimizing your 3-day schedule...',
        'Adding personality-specific customizations...',
        'Finalizing your itinerary...'
      ]
    },
    
    comboBoxUpdate: {
      message: 'Updating recommendations...',
      estimatedTime: 3,
      showProgress: false
    },
    
    authentication: {
      message: 'Authenticating...',
      estimatedTime: 5,
      showProgress: true
    },
    
    dataValidation: {
      message: 'Validating input...',
      estimatedTime: 2,
      showProgress: false
    }
  }

  // Start loading with preset configuration
  const startWithPreset = (presetName: keyof typeof presets) => {
    const preset = presets[presetName]
    startLoading(preset)
  }

  // Async operation wrapper
  const withLoading = async <T>(
    operation: () => Promise<T>,
    options: LoadingOptions = {}
  ): Promise<T> => {
    try {
      startLoading(options)
      const result = await operation()
      
      // Complete progress if it was being tracked
      if (loadingState.value.progress !== undefined) {
        updateProgress(100, 'Complete!')
        // Brief delay to show completion
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      stopLoading()
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred'
      setError(errorMessage)
      throw error
    }
  }

  // Async operation wrapper with preset
  const withPreset = async <T>(
    operation: () => Promise<T>,
    presetName: keyof typeof presets
  ): Promise<T> => {
    const preset = presets[presetName]
    return withLoading(operation, preset)
  }

  return {
    // State
    loadingState: loadingState as Ref<LoadingState>,
    isLoading,
    hasError,
    elapsedTime,
    remainingTime,
    
    // Actions
    startLoading,
    stopLoading,
    updateMessage,
    updateProgress,
    setError,
    clearError,
    
    // Presets
    presets,
    startWithPreset,
    
    // Async wrappers
    withLoading,
    withPreset
  }
}

// Global loading state for app-wide loading indicators
let globalLoadingState: ReturnType<typeof useLoadingState> | null = null

export function useGlobalLoadingState() {
  if (!globalLoadingState) {
    globalLoadingState = useLoadingState()
  }
  return globalLoadingState
}

// Loading state for specific MBTI personality contexts
export function useMBTILoadingState(personality?: MBTIPersonality) {
  const loadingState = useLoadingState()
  
  // Personality-specific loading messages
  const personalityMessages = {
    // Structured personalities - detailed progress
    INTJ: 'Architecting your perfect itinerary...',
    ENTJ: 'Commanding the best travel experience...',
    ISTJ: 'Organizing your reliable travel plan...',
    ESTJ: 'Executing your comprehensive itinerary...',
    
    // Flexible personalities - casual approach
    INTP: 'Analyzing travel possibilities...',
    ISTP: 'Crafting your practical adventure...',
    ESTP: 'Creating your spontaneous journey...',
    
    // Colorful personalities - creative messaging
    ENTP: 'Innovating your creative adventure...',
    INFP: 'Curating your artistic journey...',
    ENFP: 'Energizing your vibrant experience...',
    ISFP: 'Designing your gentle exploration...',
    ESFP: 'Entertaining your lively adventure...',
    
    // Feeling personalities - warm messaging
    INFJ: 'Inspiring your meaningful journey...',
    ISFJ: 'Nurturing your comfortable experience...',
    ENFJ: 'Harmonizing your social adventure...',
    ESFJ: 'Welcoming your friendly exploration...'
  }
  
  const startPersonalityLoading = (options: LoadingOptions = {}) => {
    const personalityMessage = personality ? personalityMessages[personality] : undefined
    
    loadingState.startLoading({
      ...options,
      message: options.message || personalityMessage || 'Loading...'
    })
  }
  
  return {
    ...loadingState,
    startPersonalityLoading,
    personalityMessages
  }
}
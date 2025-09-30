import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useLoadingState, useGlobalLoadingState, useMBTILoadingState } from '../useLoadingState'
import type { MBTIPersonality } from '@/types/mbti'

describe('useLoadingState', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Basic Loading State', () => {
    it('initializes with default state', () => {
      const { loadingState, isLoading, hasError } = useLoadingState()
      
      expect(isLoading.value).toBe(false)
      expect(hasError.value).toBe(false)
      expect(loadingState.value.message).toBeUndefined()
      expect(loadingState.value.progress).toBeUndefined()
    })

    it('initializes with custom initial state', () => {
      const { loadingState } = useLoadingState({
        isLoading: true,
        message: 'Initial loading...'
      })
      
      expect(loadingState.value.isLoading).toBe(true)
      expect(loadingState.value.message).toBe('Initial loading...')
    })

    it('starts loading correctly', () => {
      const { startLoading, isLoading, loadingState } = useLoadingState()
      
      startLoading({
        message: 'Loading data...',
        estimatedTime: 30
      })
      
      expect(isLoading.value).toBe(true)
      expect(loadingState.value.message).toBe('Loading data...')
      expect(loadingState.value.estimatedTime).toBe(30)
      expect(loadingState.value.startTime).toBeDefined()
    })

    it('stops loading correctly', () => {
      const { startLoading, stopLoading, isLoading } = useLoadingState()
      
      startLoading({ message: 'Loading...' })
      expect(isLoading.value).toBe(true)
      
      stopLoading()
      expect(isLoading.value).toBe(false)
    })
  })

  describe('Progress Management', () => {
    it('starts with progress when showProgress is true', () => {
      const { startLoading, loadingState } = useLoadingState()
      
      startLoading({
        message: 'Loading...',
        showProgress: true,
        estimatedTime: 60
      })
      
      expect(loadingState.value.progress).toBe(0)
    })

    it('updates progress manually', () => {
      const { startLoading, updateProgress, loadingState } = useLoadingState()
      
      startLoading({ message: 'Loading...', showProgress: true })
      updateProgress(50, 'Half way there...')
      
      expect(loadingState.value.progress).toBe(50)
      expect(loadingState.value.message).toBe('Half way there...')
    })

    it('clamps progress between 0 and 100', () => {
      const { startLoading, updateProgress, loadingState } = useLoadingState()
      
      startLoading({ message: 'Loading...', showProgress: true })
      
      updateProgress(-10)
      expect(loadingState.value.progress).toBe(0)
      
      updateProgress(150)
      expect(loadingState.value.progress).toBe(100)
    })

    it('simulates progress automatically', () => {
      const { startLoading, loadingState } = useLoadingState()
      
      startLoading({
        message: 'Loading...',
        showProgress: true,
        estimatedTime: 10
      })
      
      // Advance time and check progress increases
      vi.advanceTimersByTime(1000)
      expect(loadingState.value.progress).toBeGreaterThan(0)
      expect(loadingState.value.progress).toBeLessThan(95)
    })
  })

  describe('Step-based Progress', () => {
    it('progresses through steps correctly', () => {
      const { startLoading, loadingState } = useLoadingState()
      
      const steps = ['Step 1', 'Step 2', 'Step 3']
      startLoading({
        message: 'Loading...',
        showProgress: true,
        estimatedTime: 6,
        progressSteps: steps
      })
      
      expect(loadingState.value.message).toBe('Step 1')
      
      // Advance time to next step
      vi.advanceTimersByTime(2000)
      expect(loadingState.value.message).toBe('Step 2')
      
      vi.advanceTimersByTime(2000)
      expect(loadingState.value.message).toBe('Step 3')
    })
  })

  describe('Error Handling', () => {
    it('sets error state correctly', () => {
      const { startLoading, setError, hasError, loadingState, isLoading } = useLoadingState()
      
      startLoading({ message: 'Loading...' })
      setError('Something went wrong')
      
      expect(hasError.value).toBe(true)
      expect(loadingState.value.error).toBe('Something went wrong')
      expect(isLoading.value).toBe(false)
    })

    it('clears error state', () => {
      const { setError, clearError, hasError, loadingState } = useLoadingState()
      
      setError('Error message')
      expect(hasError.value).toBe(true)
      
      clearError()
      expect(hasError.value).toBe(false)
      expect(loadingState.value.error).toBeUndefined()
    })
  })

  describe('Time Calculations', () => {
    it('calculates elapsed time correctly', () => {
      const { startLoading, elapsedTime } = useLoadingState()
      
      startLoading({ message: 'Loading...' })
      
      vi.advanceTimersByTime(5000)
      expect(elapsedTime.value).toBe(5)
    })

    it('calculates remaining time correctly', () => {
      const { startLoading, updateProgress, remainingTime, elapsedTime } = useLoadingState()
      
      startLoading({
        message: 'Loading...',
        estimatedTime: 100,
        showProgress: true
      })
      
      // Simulate 25 seconds elapsed and 25% progress
      vi.advanceTimersByTime(25000)
      updateProgress(25)
      
      // With 25% done in 25 seconds, estimated total is 100 seconds
      // So remaining should be around 75 seconds
      const remaining = remainingTime.value
      expect(remaining).toBeGreaterThan(70)
      expect(remaining).toBeLessThan(80)
    })
  })

  describe('Preset Configurations', () => {
    it('uses itinerary generation preset correctly', () => {
      const { startWithPreset, loadingState } = useLoadingState()
      
      startWithPreset('itineraryGeneration')
      
      // The preset starts with the first step message
      expect(loadingState.value.message).toBe('Analyzing your MBTI personality...')
      expect(loadingState.value.estimatedTime).toBe(100)
      expect(loadingState.value.progress).toBe(0)
    })

    it('uses combo box update preset correctly', () => {
      const { startWithPreset, loadingState } = useLoadingState()
      
      startWithPreset('comboBoxUpdate')
      
      expect(loadingState.value.message).toBe('Updating recommendations...')
      expect(loadingState.value.estimatedTime).toBe(3)
      expect(loadingState.value.progress).toBeUndefined()
    })
  })

  describe('Async Operation Wrappers', () => {
    it('wraps async operations with loading state', async () => {
      const { withLoading, isLoading } = useLoadingState()
      
      const mockOperation = vi.fn().mockResolvedValue('success')
      
      expect(isLoading.value).toBe(false)
      
      const promise = withLoading(mockOperation, {
        message: 'Processing...'
      })
      
      expect(isLoading.value).toBe(true)
      
      const result = await promise
      
      expect(result).toBe('success')
      expect(isLoading.value).toBe(false)
      expect(mockOperation).toHaveBeenCalledOnce()
    })

    it('handles async operation errors', async () => {
      const { withLoading, hasError, loadingState } = useLoadingState()
      
      const mockOperation = vi.fn().mockRejectedValue(new Error('Operation failed'))
      
      await expect(
        withLoading(mockOperation, { message: 'Processing...' })
      ).rejects.toThrow('Operation failed')
      
      expect(hasError.value).toBe(true)
      expect(loadingState.value.error).toBe('Operation failed')
    })

    it('completes progress on successful operation', async () => {
      const { withLoading, loadingState } = useLoadingState()
      
      const mockOperation = vi.fn().mockResolvedValue('success')
      
      const promise = withLoading(mockOperation, {
        message: 'Processing...',
        showProgress: true
      })
      
      // Fast-forward any timers
      vi.runAllTimers()
      
      await promise
      
      // After completion, loading should be stopped
      expect(loadingState.value.isLoading).toBe(false)
    })

    it('uses preset wrapper correctly', async () => {
      const { withPreset, loadingState } = useLoadingState()
      
      const mockOperation = vi.fn().mockResolvedValue('success')
      
      const promise = withPreset(mockOperation, 'authentication')
      
      // Fast-forward any timers
      vi.runAllTimers()
      
      const result = await promise
      
      expect(result).toBe('success')
      expect(loadingState.value.isLoading).toBe(false)
    })
  })

  describe('Global Loading State', () => {
    it('returns same instance on multiple calls', () => {
      const instance1 = useGlobalLoadingState()
      const instance2 = useGlobalLoadingState()
      
      expect(instance1).toBe(instance2)
    })
  })

  describe('MBTI Loading State', () => {
    it('uses personality-specific messages', () => {
      const { startPersonalityLoading, loadingState } = useMBTILoadingState('INTJ')
      
      startPersonalityLoading()
      
      expect(loadingState.value.message).toBe('Architecting your perfect itinerary...')
    })

    it('falls back to default message for unknown personality', () => {
      const { startPersonalityLoading, loadingState } = useMBTILoadingState()
      
      startPersonalityLoading()
      
      expect(loadingState.value.message).toBe('Loading...')
    })

    it('allows message override', () => {
      const { startPersonalityLoading, loadingState } = useMBTILoadingState('ENFP')
      
      startPersonalityLoading({ message: 'Custom message' })
      
      expect(loadingState.value.message).toBe('Custom message')
    })

    it('provides personality messages for all MBTI types', () => {
      const { personalityMessages } = useMBTILoadingState()
      
      const mbtiTypes: MBTIPersonality[] = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP',
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
      ]
      
      mbtiTypes.forEach(type => {
        expect(personalityMessages[type]).toBeDefined()
        expect(typeof personalityMessages[type]).toBe('string')
        expect(personalityMessages[type].length).toBeGreaterThan(0)
      })
    })
  })

  describe('Message Updates', () => {
    it('updates message during loading', () => {
      const { startLoading, updateMessage, loadingState } = useLoadingState()
      
      startLoading({ message: 'Initial message' })
      expect(loadingState.value.message).toBe('Initial message')
      
      updateMessage('Updated message')
      expect(loadingState.value.message).toBe('Updated message')
    })

    it('does not update message when not loading', () => {
      const { updateMessage, loadingState } = useLoadingState()
      
      updateMessage('Should not update')
      expect(loadingState.value.message).toBeUndefined()
    })
  })
})
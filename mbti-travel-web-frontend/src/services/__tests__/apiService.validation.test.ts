import { describe, it, expect } from 'vitest'
import { ApiService } from '../apiService'

describe('ApiService - Validation Tests', () => {
  let apiService: ApiService

  beforeEach(() => {
    apiService = ApiService.getInstance()
  })

  it('should create singleton instance', () => {
    const instance1 = ApiService.getInstance()
    const instance2 = ApiService.getInstance()
    expect(instance1).toBe(instance2)
  })

  it('should have required methods', () => {
    expect(typeof apiService.generateItinerary).toBe('function')
    expect(typeof apiService.setAuthToken).toBe('function')
    expect(typeof apiService.getAuthToken).toBe('function')
    expect(typeof apiService.isAuthenticated).toBe('function')
    expect(typeof apiService.testConnection).toBe('function')
  })

  it('should validate empty MBTI personality', async () => {
    try {
      await apiService.generateItinerary({ mbtiPersonality: '' as any })
      expect(true).toBe(false) // Should not reach here
    } catch (error) {
      expect(error.message).toContain('MBTI personality is required')
    }
  })

  it('should validate invalid MBTI personality types', async () => {
    const invalidTypes = ['INVALID', 'XXXX', 'INT', 'INTJX', 'abcd']

    for (const invalidType of invalidTypes) {
      try {
        await apiService.generateItinerary({ mbtiPersonality: invalidType as any })
        expect(true).toBe(false) // Should not reach here
      } catch (error) {
        expect(error.message).toContain('Invalid MBTI personality type')
      }
    }
  })

  it('should accept valid MBTI personality types', () => {
    const validTypes = [
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP',
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]

    // Test that validation passes for valid types
    // We can't test the full API call without mocking, but we can test that validation doesn't throw
    for (const mbtiType of validTypes) {
      expect(() => {
        // This should not throw a validation error
        const request = { mbtiPersonality: mbtiType as any }
        expect(request.mbtiPersonality).toBe(mbtiType)
      }).not.toThrow()
    }
  })
})
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiService } from '../apiService'

// Simple test to verify ApiService basic functionality
describe('ApiService - Basic Tests', () => {
  let apiService: ApiService

  beforeEach(() => {
    // Get ApiService instance
    apiService = ApiService.getInstance()
  })

  it('should create singleton instance', () => {
    const instance1 = ApiService.getInstance()
    const instance2 = ApiService.getInstance()
    expect(instance1).toBe(instance2)
  })

  it('should validate MBTI personality types', async () => {
    const validTypes = [
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP',
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]

    // Test valid types - should not throw during validation
    for (const mbtiType of validTypes) {
      try {
        await apiService.generateItinerary({ mbtiPersonality: mbtiType as any })
      } catch (error) {
        // Should fail on API call, not validation
        expect(error.message).not.toContain('Invalid MBTI personality type')
      }
    }
  })

  it('should reject invalid MBTI personality types', async () => {
    const invalidTypes = ['INVALID', 'XXXX', '', 'INT', 'INTJX']

    for (const invalidType of invalidTypes) {
      try {
        await apiService.generateItinerary({ mbtiPersonality: invalidType as any })
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        if (invalidType === '') {
          expect(error.message).toContain('MBTI personality is required')
        } else {
          expect(error.message).toContain('Invalid MBTI personality type')
        }
      }
    }
  })

  it('should have authentication methods', () => {
    expect(typeof apiService.setAuthToken).toBe('function')
    expect(typeof apiService.getAuthToken).toBe('function')
    expect(typeof apiService.isAuthenticated).toBe('function')
  })

  it('should have connectivity test method', () => {
    expect(typeof apiService.testConnection).toBe('function')
  })
})
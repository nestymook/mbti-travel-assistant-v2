import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ThemeService } from '../themeService'
import type { MBTIPersonality } from '@/types/mbti'

// Mock DOM methods
const mockSetProperty = vi.fn()
const mockGetPropertyValue = vi.fn()
const mockGetComputedStyle = vi.fn()
const mockClassListAdd = vi.fn()
const mockClassListRemove = vi.fn()

Object.defineProperty(document, 'documentElement', {
  value: {
    style: {
      setProperty: mockSetProperty
    }
  },
  writable: true
})

Object.defineProperty(window, 'getComputedStyle', {
  value: mockGetComputedStyle,
  writable: true
})

Object.defineProperty(document, 'body', {
  value: {
    classList: {
      add: mockClassListAdd,
      remove: mockClassListRemove
    }
  },
  writable: true
})

// Mock Array.from for classList
vi.spyOn(Array, 'from').mockReturnValue([])

// Mock window.dispatchEvent
Object.defineProperty(window, 'dispatchEvent', {
  value: vi.fn(),
  writable: true
})

describe('ThemeService - Colorful Personalities', () => {
  let themeService: ThemeService

  beforeEach(() => {
    // Reset singleton instance
    ;(ThemeService as any).instance = null
    themeService = ThemeService.getInstance()
    
    // Reset mocks
    mockSetProperty.mockClear()
    mockGetPropertyValue.mockClear()
    mockGetComputedStyle.mockClear()
    mockClassListAdd.mockClear()
    mockClassListRemove.mockClear()
    vi.clearAllMocks()
    
    // Mock getComputedStyle return
    mockGetComputedStyle.mockReturnValue({
      getPropertyValue: mockGetPropertyValue
    })
    
    mockGetPropertyValue.mockReturnValue('#007bff')
  })

  afterEach(() => {
    themeService.resetTheme()
  })

  describe('Colorful Personality Detection', () => {
    it('correctly identifies colorful personalities', () => {
      const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP', 'ESFP']
      const nonColorfulTypes: MBTIPersonality[] = ['INTJ', 'INTP', 'ENTJ', 'INFJ', 'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP']

      colorfulTypes.forEach(personality => {
        expect(themeService.isColorfulPersonality(personality)).toBe(true)
      })

      nonColorfulTypes.forEach(personality => {
        expect(themeService.isColorfulPersonality(personality)).toBe(false)
      })
    })

    it('correctly identifies personalities that should show images', () => {
      const imageTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP']
      const nonImageTypes: MBTIPersonality[] = ['INTJ', 'INTP', 'ENTJ', 'INFJ', 'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ESFP']

      imageTypes.forEach(personality => {
        expect(themeService.shouldShowImages(personality)).toBe(true)
      })

      nonImageTypes.forEach(personality => {
        expect(themeService.shouldShowImages(personality)).toBe(false)
      })
    })
  })

  describe('Vibrant Color Enhancements', () => {
    it('provides vibrant enhancements for ENTP', () => {
      const enhancements = themeService.getVibrantEnhancements('ENTP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#e74c3c',
        '--mbti-creative-highlight': '#3498db',
        '--mbti-gradient-start': '#9b59b6',
        '--mbti-gradient-end': '#f39c12'
      })
    })

    it('provides vibrant enhancements for INFP', () => {
      const enhancements = themeService.getVibrantEnhancements('INFP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#9c27b0',
        '--mbti-creative-highlight': '#4caf50',
        '--mbti-gradient-start': '#e91e63',
        '--mbti-gradient-end': '#ff9800'
      })
    })

    it('provides vibrant enhancements for ENFP', () => {
      const enhancements = themeService.getVibrantEnhancements('ENFP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#2196f3',
        '--mbti-creative-highlight': '#ffc107',
        '--mbti-gradient-start': '#ff5722',
        '--mbti-gradient-end': '#4caf50'
      })
    })

    it('provides vibrant enhancements for ISFP', () => {
      const enhancements = themeService.getVibrantEnhancements('ISFP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#00bcd4',
        '--mbti-creative-highlight': '#ff9800',
        '--mbti-gradient-start': '#673ab7',
        '--mbti-gradient-end': '#ff4081'
      })
    })

    it('provides vibrant enhancements for ESTP', () => {
      const enhancements = themeService.getVibrantEnhancements('ESTP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#ffc107',
        '--mbti-creative-highlight': '#e91e63',
        '--mbti-gradient-start': '#e74c3c',
        '--mbti-gradient-end': '#f1c40f'
      })
    })

    it('provides vibrant enhancements for ESFP', () => {
      const enhancements = themeService.getVibrantEnhancements('ESFP')
      
      expect(enhancements).toEqual({
        '--mbti-vibrant-accent': '#e91e63',
        '--mbti-creative-highlight': '#4caf50',
        '--mbti-gradient-start': '#ffc107',
        '--mbti-gradient-end': '#e91e63'
      })
    })

    it('returns empty object for non-colorful personalities', () => {
      const enhancements = themeService.getVibrantEnhancements('INTJ')
      expect(enhancements).toEqual({})
    })
  })

  describe('Colorful Theme Application', () => {
    it('applies vibrant enhancements when applying colorful personality theme', () => {
      themeService.applyMBTITheme('ENFP')

      // Verify base theme properties are set
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#ff5722')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#d84315')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#4caf50')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-theme-type', 'colorful')

      // Verify vibrant enhancements are applied
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-vibrant-accent', '#2196f3')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-creative-highlight', '#ffc107')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-gradient-start', '#ff5722')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-gradient-end', '#4caf50')
    })

    it('does not apply vibrant enhancements for non-colorful personalities', () => {
      themeService.applyMBTITheme('INTJ')

      // Verify base theme properties are set
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#2c3e50')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#34495e')

      // Verify vibrant enhancements are not applied
      expect(mockSetProperty).not.toHaveBeenCalledWith('--mbti-vibrant-accent', expect.any(String))
      expect(mockSetProperty).not.toHaveBeenCalledWith('--mbti-creative-highlight', expect.any(String))
      expect(mockSetProperty).not.toHaveBeenCalledWith('--mbti-gradient-start', expect.any(String))
      expect(mockSetProperty).not.toHaveBeenCalledWith('--mbti-gradient-end', expect.any(String))
    })
  })

  describe('Personality Color Schemes', () => {
    it('provides correct color scheme for ENTP', () => {
      const colors = themeService.getPersonalityColors('ENTP')
      
      expect(colors.name).toBe('ENTP - The Debater')
      expect(colors.description).toBe('Creative and innovative styling')
      expect(colors.primary).toBe('#9b59b6')
      expect(colors.secondary).toBe('#8e44ad')
      expect(colors.accent).toBe('#f39c12')
      expect(colors.colorful).toBe(true)
      expect(colors.warm).toBe(false)
    })

    it('provides correct color scheme for INFP', () => {
      const colors = themeService.getPersonalityColors('INFP')
      
      expect(colors.name).toBe('INFP - The Mediator')
      expect(colors.description).toBe('Artistic and expressive design')
      expect(colors.primary).toBe('#e91e63')
      expect(colors.secondary).toBe('#ad1457')
      expect(colors.accent).toBe('#ff9800')
      expect(colors.colorful).toBe(true)
      expect(colors.warm).toBe(false)
    })

    it('provides correct color scheme for ENFP', () => {
      const colors = themeService.getPersonalityColors('ENFP')
      
      expect(colors.name).toBe('ENFP - The Campaigner')
      expect(colors.description).toBe('Enthusiastic and vibrant styling')
      expect(colors.primary).toBe('#ff5722')
      expect(colors.secondary).toBe('#d84315')
      expect(colors.accent).toBe('#4caf50')
      expect(colors.colorful).toBe(true)
      expect(colors.warm).toBe(false)
    })

    it('provides correct color scheme for ISFP', () => {
      const colors = themeService.getPersonalityColors('ISFP')
      
      expect(colors.name).toBe('ISFP - The Adventurer')
      expect(colors.description).toBe('Gentle and artistic design')
      expect(colors.primary).toBe('#673ab7')
      expect(colors.secondary).toBe('#512da8')
      expect(colors.accent).toBe('#ff4081')
      expect(colors.colorful).toBe(true)
      expect(colors.warm).toBe(false)
    })
  })

  describe('Theme Integration', () => {
    it('correctly identifies current personality after theme application', () => {
      themeService.applyMBTITheme('ENFP')
      expect(themeService.getCurrentPersonality()).toBe('ENFP')
    })

    it('resets colorful enhancements when theme is reset', () => {
      themeService.applyMBTITheme('ENFP')
      themeService.resetTheme()

      // Verify default theme is applied
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#007bff')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#6c757d')
      expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#28a745')
    })

    it('dispatches theme change event with colorful personality', () => {
      const eventSpy = vi.spyOn(window, 'dispatchEvent')
      
      themeService.applyMBTITheme('ENFP')
      
      expect(eventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'mbti-theme-changed',
          detail: expect.objectContaining({
            personality: 'ENFP',
            theme: expect.objectContaining({
              colorful: true
            })
          })
        })
      )
    })
  })
})
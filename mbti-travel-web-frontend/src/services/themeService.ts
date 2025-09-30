// Theme service for MBTI personality-based styling
import type { MBTIPersonality, PersonalityTheme, PersonalityThemeMap } from '../types/mbti'
import { memoize } from '../utils/performance'

export class ThemeService {
  private static instance: ThemeService
  private currentPersonality: MBTIPersonality | null = null
  private originalTheme: PersonalityTheme | null = null

  private constructor() {
    this.initializeDefaultTheme()
  }

  public static getInstance(): ThemeService {
    if (!ThemeService.instance) {
      ThemeService.instance = new ThemeService()
    }
    return ThemeService.instance
  }

  /**
   * Apply MBTI personality-specific theme
   */
  applyMBTITheme(personality: MBTIPersonality): void {
    // Store original theme if not already stored
    if (!this.originalTheme) {
      this.originalTheme = this.getCurrentTheme()
    }

    const theme = this.getPersonalityColors(personality)
    this.setCSSVariables(theme)
    this.applyPersonalityClass(personality)
    this.currentPersonality = personality

    // Dispatch custom event for theme change
    this.dispatchThemeChangeEvent(personality, theme)
  }

  /**
   * Get personality-specific color scheme (memoized for performance)
   */
  getPersonalityColors = memoize((personality: MBTIPersonality): PersonalityTheme => {
    const personalityThemes: PersonalityThemeMap = {
      // Structured personalities - Professional themes
      INTJ: {
        name: 'INTJ - The Architect',
        description: 'Professional and strategic design',
        primary: '#2c3e50',
        secondary: '#34495e',
        accent: '#3498db',
        background: '#ecf0f1',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ENTJ: {
        name: 'ENTJ - The Commander',
        description: 'Bold and commanding presence',
        primary: '#8e44ad',
        secondary: '#9b59b6',
        accent: '#e74c3c',
        background: '#f8f9fa',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ISTJ: {
        name: 'ISTJ - The Logistician',
        description: 'Reliable and traditional styling',
        primary: '#34495e',
        secondary: '#7f8c8d',
        accent: '#27ae60',
        background: '#ecf0f1',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ESTJ: {
        name: 'ESTJ - The Executive',
        description: 'Strong and decisive design',
        primary: '#c0392b',
        secondary: '#e74c3c',
        accent: '#f39c12',
        background: '#fdf2e9',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },

      // Flexible personalities - Casual themes
      INTP: {
        name: 'INTP - The Thinker',
        description: 'Clean and analytical design',
        primary: '#16a085',
        secondary: '#1abc9c',
        accent: '#3498db',
        background: '#f0f8ff',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ISTP: {
        name: 'ISTP - The Virtuoso',
        description: 'Practical and understated styling',
        primary: '#7f8c8d',
        secondary: '#95a5a6',
        accent: '#e67e22',
        background: '#f8f9fa',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ESTP: {
        name: 'ESTP - The Entrepreneur',
        description: 'Dynamic and energetic design',
        primary: '#e74c3c',
        secondary: '#c0392b',
        accent: '#f1c40f',
        background: '#fff5f5',
        text: '#2c3e50',
        warm: false,
        colorful: true
      },

      // Colorful personalities - Vibrant themes
      ENTP: {
        name: 'ENTP - The Debater',
        description: 'Creative and innovative styling',
        primary: '#9b59b6',
        secondary: '#8e44ad',
        accent: '#f39c12',
        background: '#fdf2e9',
        text: '#2c3e50',
        warm: false,
        colorful: true
      },
      INFP: {
        name: 'INFP - The Mediator',
        description: 'Artistic and expressive design',
        primary: '#e91e63',
        secondary: '#ad1457',
        accent: '#ff9800',
        background: '#fce4ec',
        text: '#2c3e50',
        warm: false,
        colorful: true
      },
      ENFP: {
        name: 'ENFP - The Campaigner',
        description: 'Enthusiastic and vibrant styling',
        primary: '#ff5722',
        secondary: '#d84315',
        accent: '#4caf50',
        background: '#fff3e0',
        text: '#2c3e50',
        warm: false,
        colorful: true
      },
      ISFP: {
        name: 'ISFP - The Adventurer',
        description: 'Gentle and artistic design',
        primary: '#673ab7',
        secondary: '#512da8',
        accent: '#ff4081',
        background: '#f3e5f5',
        text: '#2c3e50',
        warm: false,
        colorful: true
      },

      // Feeling personalities - Warm themes
      INFJ: {
        name: 'INFJ - The Advocate',
        description: 'Thoughtful and inspiring design',
        primary: '#5e35b1',
        secondary: '#4527a0',
        accent: '#26a69a',
        background: '#ede7f6',
        text: '#2c3e50',
        warm: false,
        colorful: false
      },
      ISFJ: {
        name: 'ISFJ - The Protector',
        description: 'Warm and nurturing styling',
        primary: '#d4a574',
        secondary: '#f4e4bc',
        accent: '#b8860b',
        background: '#fdf5e6',
        text: '#8b4513',
        warm: true,
        colorful: false
      },
      ENFJ: {
        name: 'ENFJ - The Protagonist',
        description: 'Inspiring and harmonious design',
        primary: '#4caf50',
        secondary: '#388e3c',
        accent: '#ff9800',
        background: '#e8f5e8',
        text: '#2c3e50',
        warm: true,
        colorful: false
      },
      ESFJ: {
        name: 'ESFJ - The Consul',
        description: 'Friendly and welcoming styling',
        primary: '#ff7043',
        secondary: '#d84315',
        accent: '#4caf50',
        background: '#fbe9e7',
        text: '#2c3e50',
        warm: true,
        colorful: false
      },
      ESFP: {
        name: 'ESFP - The Entertainer',
        description: 'Cheerful and lively design',
        primary: '#ffc107',
        secondary: '#ff8f00',
        accent: '#e91e63',
        background: '#fffde7',
        text: '#2c3e50',
        warm: false,
        colorful: true
      }
    }

    return personalityThemes[personality]
  }, 50, 10 * 60 * 1000) // Cache for 10 minutes

  /**
   * Reset theme to default
   */
  resetTheme(): void {
    // Remove personality-specific CSS class
    if (this.currentPersonality) {
      this.removePersonalityClass(this.currentPersonality)
    }

    // Always reset to default theme
    const defaultTheme = this.getDefaultTheme()
    this.setCSSVariables(defaultTheme)

    // Clear stored state
    this.currentPersonality = null
    this.originalTheme = null

    // Dispatch reset event
    this.dispatchThemeResetEvent()
  }

  /**
   * Check if personality uses colorful themes
   */
  isColorfulPersonality(personality: MBTIPersonality): boolean {
    const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP', 'ESFP']
    return colorfulTypes.includes(personality)
  }

  /**
   * Check if personality should show image placeholders
   */
  shouldShowImages(personality: MBTIPersonality): boolean {
    const imageTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP']
    return imageTypes.includes(personality)
  }

  /**
   * Get vibrant color enhancements for colorful personalities
   */
  getVibrantEnhancements(personality: MBTIPersonality): Record<string, string> {
    const enhancements: Record<MBTIPersonality, Record<string, string>> = {
      'ENTP': {
        '--mbti-vibrant-accent': '#e74c3c',
        '--mbti-creative-highlight': '#3498db',
        '--mbti-gradient-start': '#9b59b6',
        '--mbti-gradient-end': '#f39c12'
      },
      'INFP': {
        '--mbti-vibrant-accent': '#9c27b0',
        '--mbti-creative-highlight': '#4caf50',
        '--mbti-gradient-start': '#e91e63',
        '--mbti-gradient-end': '#ff9800'
      },
      'ENFP': {
        '--mbti-vibrant-accent': '#2196f3',
        '--mbti-creative-highlight': '#ffc107',
        '--mbti-gradient-start': '#ff5722',
        '--mbti-gradient-end': '#4caf50'
      },
      'ISFP': {
        '--mbti-vibrant-accent': '#00bcd4',
        '--mbti-creative-highlight': '#ff9800',
        '--mbti-gradient-start': '#673ab7',
        '--mbti-gradient-end': '#ff4081'
      },
      'ESTP': {
        '--mbti-vibrant-accent': '#ffc107',
        '--mbti-creative-highlight': '#e91e63',
        '--mbti-gradient-start': '#e74c3c',
        '--mbti-gradient-end': '#f1c40f'
      },
      'ESFP': {
        '--mbti-vibrant-accent': '#e91e63',
        '--mbti-creative-highlight': '#4caf50',
        '--mbti-gradient-start': '#ffc107',
        '--mbti-gradient-end': '#e91e63'
      }
    }
    
    return enhancements[personality] || {}
  }

  /**
   * Check if personality uses warm tones
   */
  isWarmPersonality(personality: MBTIPersonality): boolean {
    const warmTypes: MBTIPersonality[] = ['ISFJ', 'ENFJ', 'ESFJ']
    return warmTypes.includes(personality)
  }

  /**
   * Check if personality uses flashy styling (ESTP specific)
   */
  isFlashyPersonality(personality: MBTIPersonality): boolean {
    return personality === 'ESTP'
  }

  /**
   * Get current applied personality
   */
  getCurrentPersonality(): MBTIPersonality | null {
    return this.currentPersonality
  }

  /**
   * Get current theme configuration
   */
  getCurrentTheme(): PersonalityTheme {
    const root = document.documentElement
    const computedStyle = getComputedStyle(root)

    return {
      name: 'Current Theme',
      primary: computedStyle.getPropertyValue('--mbti-primary').trim() || '#007bff',
      secondary: computedStyle.getPropertyValue('--mbti-secondary').trim() || '#6c757d',
      accent: computedStyle.getPropertyValue('--mbti-accent').trim() || '#28a745',
      background: computedStyle.getPropertyValue('--mbti-background').trim() || '#ffffff',
      text: computedStyle.getPropertyValue('--mbti-text').trim() || '#212529'
    }
  }

  /**
   * Get default theme
   */
  private getDefaultTheme(): PersonalityTheme {
    return {
      name: 'Default Theme',
      primary: '#007bff',
      secondary: '#6c757d',
      accent: '#28a745',
      background: '#ffffff',
      text: '#212529'
    }
  }

  /**
   * Initialize default theme on service creation
   */
  private initializeDefaultTheme(): void {
    const defaultTheme = this.getDefaultTheme()
    this.setCSSVariables(defaultTheme)
  }

  /**
   * Apply CSS variables for theme
   */
  private setCSSVariables(theme: PersonalityTheme): void {
    const root = document.documentElement
    root.style.setProperty('--mbti-primary', theme.primary)
    root.style.setProperty('--mbti-secondary', theme.secondary)
    root.style.setProperty('--mbti-accent', theme.accent)
    root.style.setProperty('--mbti-background', theme.background)
    root.style.setProperty('--mbti-text', theme.text)

    // Set additional theme properties
    if (theme.warm) {
      root.style.setProperty('--mbti-theme-type', 'warm')
    }
    if (theme.colorful) {
      root.style.setProperty('--mbti-theme-type', 'colorful')
      
      // Apply vibrant enhancements for colorful personalities
      if (this.currentPersonality) {
        const enhancements = this.getVibrantEnhancements(this.currentPersonality)
        Object.entries(enhancements).forEach(([property, value]) => {
          root.style.setProperty(property, value)
        })
      }
    }
  }

  /**
   * Apply personality-specific CSS class
   */
  private applyPersonalityClass(personality: MBTIPersonality): void {
    const body = document.body
    const className = `mbti-${personality.toLowerCase()}`

    // Remove any existing MBTI classes
    this.removeAllPersonalityClasses()

    // Add new personality class
    body.classList.add(className)
  }

  /**
   * Remove personality-specific CSS class
   */
  private removePersonalityClass(personality: MBTIPersonality): void {
    const body = document.body
    const className = `mbti-${personality.toLowerCase()}`
    body.classList.remove(className)
  }

  /**
   * Remove all personality CSS classes
   */
  private removeAllPersonalityClasses(): void {
    const body = document.body
    const mbtiClasses = Array.from(body.classList).filter(className =>
      className.startsWith('mbti-')
    )
    mbtiClasses.forEach(className => body.classList.remove(className))
  }

  /**
   * Dispatch theme change event
   */
  private dispatchThemeChangeEvent(personality: MBTIPersonality, theme: PersonalityTheme): void {
    const event = new CustomEvent('mbti-theme-changed', {
      detail: {
        personality,
        theme,
        timestamp: new Date().toISOString()
      }
    })
    window.dispatchEvent(event)
  }

  /**
   * Dispatch theme reset event
   */
  private dispatchThemeResetEvent(): void {
    const event = new CustomEvent('mbti-theme-reset', {
      detail: {
        timestamp: new Date().toISOString()
      }
    })
    window.dispatchEvent(event)
  }
}

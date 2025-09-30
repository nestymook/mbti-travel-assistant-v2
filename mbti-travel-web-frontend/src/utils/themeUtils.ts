// Theme utility functions and helpers
import { ThemeService } from '@/services'
import type { MBTIPersonality } from '@/types/mbti'

/**
 * Initialize theme service and set up event listeners
 */
export function initializeThemeSystem(): ThemeService {
  const themeService = ThemeService.getInstance()
  
  // Set up theme change event listener
  window.addEventListener('mbti-theme-changed', (event: Event) => {
    const customEvent = event as CustomEvent
    const { personality, theme } = customEvent.detail
    console.log(`Theme changed to ${personality}:`, theme)
    
    // Add theme transition class for smooth animations
    document.body.classList.add('theme-transition')
    
    // Remove transition class after animation completes
    setTimeout(() => {
      document.body.classList.remove('theme-transition')
    }, 300)
  })
  
  // Set up theme reset event listener
  window.addEventListener('mbti-theme-reset', (event: Event) => {
    const customEvent = event as CustomEvent
    console.log('Theme reset at:', customEvent.detail.timestamp)
    
    // Add theme transition class for smooth animations
    document.body.classList.add('theme-transition')
    
    // Remove transition class after animation completes
    setTimeout(() => {
      document.body.classList.remove('theme-transition')
    }, 300)
  })
  
  return themeService
}

/**
 * Apply theme with additional personality-specific enhancements
 */
export function applyPersonalityTheme(personality: MBTIPersonality): void {
  const themeService = ThemeService.getInstance()
  
  // Apply base theme
  themeService.applyMBTITheme(personality)
  
  // Add personality-specific CSS classes
  const body = document.body
  
  // Remove existing personality enhancement classes
  body.classList.remove('color-structured', 'color-flexible', 'color-colorful', 'color-feeling')
  body.classList.remove('warm-tones', 'warm-glow', 'colorful-gradient', 'flashy-style')
  
  // Add category-specific classes
  if (isStructuredPersonality(personality)) {
    body.classList.add('color-structured')
  } else if (isFlexiblePersonality(personality)) {
    body.classList.add('color-flexible')
  } else if (themeService.isColorfulPersonality(personality)) {
    body.classList.add('color-colorful', 'colorful-gradient')
  } else if (themeService.isWarmPersonality(personality)) {
    body.classList.add('color-feeling', 'warm-glow')
  }
  
  // Add warm tones for ISFJ
  if (themeService.isWarmPersonality(personality)) {
    body.classList.add('warm-tones')
  }
  
  // Add flashy styling for ESTP
  if (themeService.isFlashyPersonality(personality)) {
    body.classList.add('flashy-style')
  }
}

/**
 * Reset theme and remove all personality-specific classes
 */
export function resetPersonalityTheme(): void {
  const themeService = ThemeService.getInstance()
  
  // Reset theme service
  themeService.resetTheme()
  
  // Remove all personality enhancement classes
  const body = document.body
  body.classList.remove(
    'color-structured', 'color-flexible', 'color-colorful', 'color-feeling',
    'warm-tones', 'warm-glow', 'colorful-gradient', 'flashy-style'
  )
}

/**
 * Get theme configuration for a personality
 */
export function getPersonalityThemeConfig(personality: MBTIPersonality) {
  const themeService = ThemeService.getInstance()
  const theme = themeService.getPersonalityColors(personality)
  
  return {
    theme,
    isColorful: themeService.isColorfulPersonality(personality),
    isWarm: themeService.isWarmPersonality(personality),
    isFlashy: themeService.isFlashyPersonality(personality),
    category: getPersonalityCategory(personality)
  }
}

/**
 * Check if personality is structured type
 */
export function isStructuredPersonality(personality: MBTIPersonality): boolean {
  const structuredTypes: MBTIPersonality[] = ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ']
  return structuredTypes.includes(personality)
}

/**
 * Check if personality is flexible type
 */
export function isFlexiblePersonality(personality: MBTIPersonality): boolean {
  const flexibleTypes: MBTIPersonality[] = ['INTP', 'ISTP', 'ESTP']
  return flexibleTypes.includes(personality)
}

/**
 * Get personality category
 */
export function getPersonalityCategory(personality: MBTIPersonality): string {
  if (isStructuredPersonality(personality)) return 'structured'
  if (isFlexiblePersonality(personality)) return 'flexible'
  
  const themeService = ThemeService.getInstance()
  if (themeService.isColorfulPersonality(personality)) return 'colorful'
  if (themeService.isWarmPersonality(personality)) return 'feeling'
  
  return 'default'
}

/**
 * Create CSS custom properties object for a personality
 */
export function createPersonalityCSSProperties(personality: MBTIPersonality): Record<string, string> {
  const themeService = ThemeService.getInstance()
  const theme = themeService.getPersonalityColors(personality)
  
  return {
    '--mbti-primary': theme.primary,
    '--mbti-secondary': theme.secondary,
    '--mbti-accent': theme.accent,
    '--mbti-background': theme.background,
    '--mbti-text': theme.text,
    '--mbti-theme-type': getPersonalityCategory(personality)
  }
}

/**
 * Apply inline styles for a personality theme
 */
export function applyInlinePersonalityStyles(element: HTMLElement, personality: MBTIPersonality): void {
  const cssProperties = createPersonalityCSSProperties(personality)
  
  Object.entries(cssProperties).forEach(([property, value]) => {
    element.style.setProperty(property, value)
  })
}

/**
 * Get contrast ratio between two colors (simplified)
 */
export function getContrastRatio(color1: string, color2: string): number {
  // This is a simplified implementation
  // In a real application, you would use a proper color contrast calculation
  const getLuminance = (color: string): number => {
    // Convert hex to RGB and calculate relative luminance
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16) / 255
    const g = parseInt(hex.substr(2, 2), 16) / 255
    const b = parseInt(hex.substr(4, 2), 16) / 255
    
    const sRGB = [r, g, b].map(c => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    
    return 0.2126 * (sRGB[0] || 0) + 0.7152 * (sRGB[1] || 0) + 0.0722 * (sRGB[2] || 0)
  }
  
  const lum1 = getLuminance(color1)
  const lum2 = getLuminance(color2)
  
  const brightest = Math.max(lum1, lum2)
  const darkest = Math.min(lum1, lum2)
  
  return (brightest + 0.05) / (darkest + 0.05)
}

/**
 * Check if theme meets WCAG accessibility standards
 */
export function isThemeAccessible(personality: MBTIPersonality): boolean {
  const themeService = ThemeService.getInstance()
  const theme = themeService.getPersonalityColors(personality)
  
  // Check contrast ratio between text and background
  const contrastRatio = getContrastRatio(theme.text, theme.background)
  
  // WCAG AA standard requires 4.5:1 for normal text
  return contrastRatio >= 4.5
}

/**
 * Get theme preview data for UI components
 */
export function getThemePreview(personality: MBTIPersonality) {
  const themeService = ThemeService.getInstance()
  const theme = themeService.getPersonalityColors(personality)
  const config = getPersonalityThemeConfig(personality)
  
  return {
    personality,
    theme,
    config,
    accessible: isThemeAccessible(personality),
    cssProperties: createPersonalityCSSProperties(personality),
    previewClasses: [
      `mbti-${personality.toLowerCase()}`,
      `color-${config.category}`,
      ...(config.isWarm ? ['warm-tones', 'warm-glow'] : []),
      ...(config.isColorful ? ['colorful-gradient'] : []),
      ...(config.isFlashy ? ['flashy-style'] : [])
    ]
  }
}

/**
 * Export theme utilities object
 */
export const ThemeUtils = {
  initialize: initializeThemeSystem,
  apply: applyPersonalityTheme,
  reset: resetPersonalityTheme,
  getConfig: getPersonalityThemeConfig,
  getPreview: getThemePreview,
  isAccessible: isThemeAccessible,
  createCSSProperties: createPersonalityCSSProperties,
  applyInlineStyles: applyInlinePersonalityStyles,
  getContrastRatio,
  isStructured: isStructuredPersonality,
  isFlexible: isFlexiblePersonality,
  getCategory: getPersonalityCategory
}
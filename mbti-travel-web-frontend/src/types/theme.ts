import type { MBTIPersonality } from './mbti'

// Theme and customization configuration types
export interface ThemeConfig {
  name: string
  displayName: string
  colors: ColorPalette
  typography: TypographyConfig
  spacing: SpacingConfig
  borderRadius: BorderRadiusConfig
  shadows: ShadowConfig
}

export interface ColorPalette {
  primary: string
  secondary: string
  accent: string
  background: string
  surface: string
  text: {
    primary: string
    secondary: string
    disabled: string
    inverse: string
  }
  status: {
    success: string
    warning: string
    error: string
    info: string
  }
  border: string
  divider: string
}

export interface TypographyConfig {
  fontFamily: {
    primary: string
    secondary: string
    monospace: string
  }
  fontSize: {
    xs: string
    sm: string
    base: string
    lg: string
    xl: string
    '2xl': string
    '3xl': string
    '4xl': string
  }
  fontWeight: {
    light: number
    normal: number
    medium: number
    semibold: number
    bold: number
  }
  lineHeight: {
    tight: number
    normal: number
    relaxed: number
  }
}

export interface SpacingConfig {
  xs: string
  sm: string
  md: string
  lg: string
  xl: string
  '2xl': string
  '3xl': string
  '4xl': string
}

export interface BorderRadiusConfig {
  none: string
  sm: string
  md: string
  lg: string
  xl: string
  full: string
}

export interface ShadowConfig {
  sm: string
  md: string
  lg: string
  xl: string
  inner: string
  none: string
}

// MBTI personality-specific theme configurations
export interface PersonalityThemeConfig {
  personality: MBTIPersonality
  theme: ThemeConfig
  customizations: {
    useWarmTones: boolean
    useColorfulAccents: boolean
    useFlashyAnimations: boolean
    preferMinimalDesign: boolean
  }
  uiElements: {
    buttonStyle: 'rounded' | 'sharp' | 'pill'
    cardStyle: 'flat' | 'elevated' | 'outlined'
    transitionSpeed: 'slow' | 'normal' | 'fast'
  }
}

// Theme application and management
export interface ThemeState {
  currentTheme: ThemeConfig
  personalityTheme?: PersonalityThemeConfig
  isDarkMode: boolean
  isHighContrast: boolean
  customOverrides?: Partial<ThemeConfig>
}

export interface ThemePreferences {
  preferredTheme?: string
  autoDetectPersonality: boolean
  respectSystemTheme: boolean
  highContrastMode: boolean
  reducedMotion: boolean
  customColors?: Partial<ColorPalette>
}

// CSS custom properties mapping
export interface CSSCustomProperties {
  [key: `--${string}`]: string
}

// Theme utility types
export type ThemeMode = 'light' | 'dark' | 'auto'
export type ColorScheme = 'warm' | 'cool' | 'neutral' | 'vibrant'
export type PersonalityColorCategory = 'structured' | 'flexible' | 'colorful' | 'feeling'

// Default theme configurations
export interface DefaultThemes {
  light: ThemeConfig
  dark: ThemeConfig
  highContrast: ThemeConfig
}

// Theme validation
export interface ThemeValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
  accessibility: {
    contrastRatio: number
    wcagCompliant: boolean
    colorBlindFriendly: boolean
  }
}
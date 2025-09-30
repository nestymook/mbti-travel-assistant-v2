import type { 
  MBTIPersonality, 
  PersonalityCategories, 
  PersonalityConfigMap,
  PersonalityThemeMap,
  PersonalityTheme,
  CustomizationConfig
} from './mbti'

// MBTI personality constants
export const VALID_MBTI_TYPES: MBTIPersonality[] = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

// Personality categorization
export const PERSONALITY_CATEGORIES: PersonalityCategories = {
  structured: ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'],
  flexible: ['INTP', 'ISTP', 'ESTP'],
  colorful: ['ENTP', 'INFP', 'ENFP', 'ISFP'],
  feeling: ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ']
}

// Default customization configurations for each personality type
export const PERSONALITY_CUSTOMIZATIONS: PersonalityConfigMap = {
  // Structured personalities
  INTJ: {
    showTimeInputs: true,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ENTJ: {
    showTimeInputs: true,
    showImportantCheckboxes: true,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ISTJ: {
    showTimeInputs: true,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ESTJ: {
    showTimeInputs: true,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  
  // Flexible personalities
  INTP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: true,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ISTP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: true,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ESTP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: true,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: true,
    useFlashyStyle: true,
    useWarmTones: false
  },
  
  // Colorful personalities
  ENTP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: true,
    useFlashyStyle: false,
    useWarmTones: false
  },
  INFP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: true,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ENFP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: true,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ISFP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: true,
    useFlashyStyle: false,
    useWarmTones: false
  },
  
  // Feeling personalities
  INFJ: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: true,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ISFJ: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: true,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: true
  },
  ENFJ: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: true,
    showShareLink: true,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  ESFJ: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: true,
    showShareLink: true,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  },
  
  // Default for ESFP (not specified in requirements)
  ESFP: {
    showTimeInputs: false,
    showImportantCheckboxes: false,
    showPointForm: false,
    showDescriptions: false,
    showGroupNotes: false,
    showShareLink: false,
    showImages: false,
    useFlashyStyle: false,
    useWarmTones: false
  }
}

// Default personality themes
export const PERSONALITY_THEMES: PersonalityThemeMap = {
  // Structured personalities - Professional themes
  INTJ: {
    name: 'INTJ Professional',
    primary: '#2c3e50',
    secondary: '#34495e',
    accent: '#3498db',
    background: '#ecf0f1',
    text: '#2c3e50'
  },
  ENTJ: {
    name: 'ENTJ Executive',
    primary: '#8e44ad',
    secondary: '#9b59b6',
    accent: '#e74c3c',
    background: '#f8f9fa',
    text: '#2c3e50'
  },
  ISTJ: {
    name: 'ISTJ Traditional',
    primary: '#34495e',
    secondary: '#7f8c8d',
    accent: '#27ae60',
    background: '#ecf0f1',
    text: '#2c3e50'
  },
  ESTJ: {
    name: 'ESTJ Corporate',
    primary: '#2980b9',
    secondary: '#3498db',
    accent: '#f39c12',
    background: '#f8f9fa',
    text: '#2c3e50'
  },
  
  // Flexible personalities - Minimalist themes
  INTP: {
    name: 'INTP Minimalist',
    primary: '#95a5a6',
    secondary: '#bdc3c7',
    accent: '#e67e22',
    background: '#ffffff',
    text: '#2c3e50'
  },
  ISTP: {
    name: 'ISTP Practical',
    primary: '#7f8c8d',
    secondary: '#95a5a6',
    accent: '#16a085',
    background: '#f8f9fa',
    text: '#2c3e50'
  },
  ESTP: {
    name: 'ESTP Dynamic',
    primary: '#e74c3c',
    secondary: '#c0392b',
    accent: '#f1c40f',
    background: '#fff5f5',
    text: '#2c3e50',
    colorful: true
  },
  
  // Colorful personalities - Vibrant themes
  ENTP: {
    name: 'ENTP Creative',
    primary: '#9b59b6',
    secondary: '#8e44ad',
    accent: '#f39c12',
    background: '#fdf2e9',
    text: '#2c3e50',
    colorful: true
  },
  INFP: {
    name: 'INFP Dreamy',
    primary: '#e91e63',
    secondary: '#ad1457',
    accent: '#00bcd4',
    background: '#fce4ec',
    text: '#2c3e50',
    colorful: true
  },
  ENFP: {
    name: 'ENFP Enthusiastic',
    primary: '#ff9800',
    secondary: '#f57c00',
    accent: '#4caf50',
    background: '#fff3e0',
    text: '#2c3e50',
    colorful: true
  },
  ISFP: {
    name: 'ISFP Artistic',
    primary: '#673ab7',
    secondary: '#512da8',
    accent: '#ff5722',
    background: '#f3e5f5',
    text: '#2c3e50',
    colorful: true
  },
  
  // Feeling personalities - Warm themes
  INFJ: {
    name: 'INFJ Insightful',
    primary: '#5d4037',
    secondary: '#6d4c41',
    accent: '#009688',
    background: '#efebe9',
    text: '#3e2723'
  },
  ISFJ: {
    name: 'ISFJ Nurturing',
    primary: '#d4a574',
    secondary: '#f4e4bc',
    accent: '#b8860b',
    background: '#fdf5e6',
    text: '#8b4513',
    warm: true
  },
  ENFJ: {
    name: 'ENFJ Inspiring',
    primary: '#4caf50',
    secondary: '#66bb6a',
    accent: '#ff9800',
    background: '#e8f5e8',
    text: '#2e7d32'
  },
  ESFJ: {
    name: 'ESFJ Caring',
    primary: '#ff7043',
    secondary: '#ff8a65',
    accent: '#26c6da',
    background: '#fbe9e7',
    text: '#d84315'
  },
  
  // Default for ESFP
  ESFP: {
    name: 'ESFP Spontaneous',
    primary: '#ff6b6b',
    secondary: '#ff8e8e',
    accent: '#4ecdc4',
    background: '#fff0f0',
    text: '#2c3e50'
  }
}

// API configuration constants
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
  MBTI_TEST_URL: 'https://www.16personalities.com'
} as const

// Validation constants
export const VALIDATION_CONFIG = {
  MBTI: {
    MIN_LENGTH: 4,
    MAX_LENGTH: 4,
    PATTERN: /^[A-Z]{4}$/,
    DEBOUNCE_MS: 300
  },
  FORM: {
    DEBOUNCE_MS: 500,
    VALIDATE_ON_CHANGE: true,
    VALIDATE_ON_BLUR: true,
    SHOW_ERRORS_IMMEDIATELY: false
  }
} as const

// UI constants
export const UI_CONFIG = {
  LOADING_TIMEOUT: 100000, // 100 seconds as specified in requirements
  ANIMATION_DURATION: 300,
  TOAST_DURATION: 5000,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024
} as const

// Error messages
export const ERROR_MESSAGES = {
  MBTI: {
    REQUIRED: 'MBTI personality type is required',
    INVALID: 'Please input correct MBTI Personality!',
    FORMAT: 'Please enter a valid 4-letter MBTI code (e.g., ENFP, INTJ, INFJ...)'
  },
  API: {
    NETWORK: 'Network error. Please check your connection and try again.',
    TIMEOUT: 'Request timed out. Please try again.',
    SERVER: 'Server error. Please try again later.',
    UNAUTHORIZED: 'Please log in to continue.',
    FORBIDDEN: 'You do not have permission to perform this action.'
  },
  GENERAL: {
    UNKNOWN: 'An unexpected error occurred. Please try again.',
    LOADING: 'Generating Itinerary in progress...'
  }
} as const

// Session types
export const SESSION_TYPES = {
  BREAKFAST: 'breakfast',
  MORNING_SESSION: 'morning_session',
  LUNCH: 'lunch',
  AFTERNOON_SESSION: 'afternoon_session',
  DINNER: 'dinner',
  NIGHT_SESSION: 'night_session'
} as const

// Day numbers
export const DAY_NUMBERS = [1, 2, 3] as const

// Export utility functions
export const getPersonalityCategory = (personality: MBTIPersonality): keyof PersonalityCategories | null => {
  for (const [category, personalities] of Object.entries(PERSONALITY_CATEGORIES)) {
    if (personalities.includes(personality)) {
      return category as keyof PersonalityCategories
    }
  }
  return null
}

export const getPersonalityCustomization = (personality: MBTIPersonality): CustomizationConfig => {
  return PERSONALITY_CUSTOMIZATIONS[personality]
}

export const getPersonalityTheme = (personality: MBTIPersonality): PersonalityTheme => {
  return PERSONALITY_THEMES[personality]
}

export const isValidMBTI = (input: string): input is MBTIPersonality => {
  return VALID_MBTI_TYPES.includes(input as MBTIPersonality)
}
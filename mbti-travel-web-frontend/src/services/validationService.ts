// Validation service for MBTI input and business logic
import type { 
  MBTIValidationResult,
  MBTIValidationConfig 
} from '@/types'

import type { 
  MBTIPersonality, 
} from '@/types/mbti'

export class ValidationService {
  private static instance: ValidationService
  private readonly validMBTITypes: MBTIPersonality[] = [
    'INTJ', 'INTP', 'ENTJ', 'ENTP',
    'INFJ', 'INFP', 'ENFJ', 'ENFP',
    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
    'ISTP', 'ISFP', 'ESTP', 'ESFP',
  ]

  private readonly validationConfig: MBTIValidationConfig = {
    required: true,
    minLength: 4,
    maxLength: 4,
    allowedCharacters: /^[A-Z]{4}$/,
    validTypes: this.validMBTITypes,
    caseSensitive: false,
    autoFormat: true
  }

  // MBTI dimension mappings for intelligent suggestions
  private readonly dimensionMappings = {
    energySource: { E: 'Extraversion', I: 'Introversion' },
    informationProcessing: { S: 'Sensing', N: 'Intuition' },
    decisionMaking: { T: 'Thinking', F: 'Feeling' },
    lifestyle: { J: 'Judging', P: 'Perceiving' }
  }

  private constructor() {}

  public static getInstance(): ValidationService {
    if (!ValidationService.instance) {
      ValidationService.instance = new ValidationService()
    }
    return ValidationService.instance
  }

  /**
   * Comprehensive MBTI code validation with detailed feedback
   */
  validateMBTICode(code: string): MBTIValidationResult {
    // Handle empty input
    if (!code || code.trim().length === 0) {
      return {
        isValid: false,
        message: 'Please enter your MBTI personality type',
        suggestions: this.getPopularMBTITypes(),
        errorCode: 'REQUIRED'
      }
    }

    const trimmedCode = code.trim().toUpperCase()
    
    // Check for invalid characters first (more specific error)
    const hasInvalidChars = /[^A-Z]/.test(trimmedCode)
    if (hasInvalidChars) {
      const sanitized = this.sanitizeInput(trimmedCode).slice(0, 4)
      return {
        isValid: false,
        message: 'MBTI code must contain only letters (A-Z)',
        formattedValue: sanitized,
        suggestions: this.findSimilarPatterns(sanitized),
        errorCode: 'INVALID_FORMAT'
      }
    }

    // Check length requirements after character validation
    if (trimmedCode.length > this.validationConfig.maxLength) {
      return {
        isValid: false,
        message: 'MBTI code must be exactly 4 characters',
        formattedValue: trimmedCode.slice(0, 4),
        errorCode: 'TOO_LONG'
      }
    }

    const formattedCode = trimmedCode

    if (formattedCode.length < this.validationConfig.minLength) {
      return {
        isValid: false,
        message: `MBTI code must be exactly 4 characters (currently ${formattedCode.length})`,
        formattedValue: formattedCode,
        suggestions: this.findPartialMatches(formattedCode),
        errorCode: 'TOO_SHORT'
      }
    }

    // Check if it's a valid MBTI type
    if (!this.validMBTITypes.includes(formattedCode as MBTIPersonality)) {
      const closestMatch = this.findClosestMatch(formattedCode)
      return {
        isValid: false,
        message: 'Please input correct MBTI Personality!',
        formattedValue: formattedCode,
        suggestedValue: closestMatch,
        suggestions: this.findMultipleMatches(formattedCode),
        confidence: this.calculateMatchConfidence(formattedCode, closestMatch),
        errorCode: 'INVALID_TYPE'
      }
    }

    // Valid MBTI code
    return {
      isValid: true,
      formattedValue: formattedCode,
      detectedType: formattedCode as MBTIPersonality,
      confidence: 1.0
    }
  }

  /**
   * Real-time input validation for character limits and format checking
   */
  validateRealTimeInput(input: string): {
    isValid: boolean
    formattedValue: string
    message?: string
    canContinue: boolean
  } {
    const trimmedInput = input.trim().toUpperCase()
    
    // Allow empty input during typing
    if (trimmedInput.length === 0) {
      return {
        isValid: false,
        formattedValue: '',
        canContinue: true
      }
    }

    // Check length constraints first
    if (trimmedInput.length > 4) {
      return {
        isValid: false,
        formattedValue: trimmedInput.slice(0, 4),
        message: 'Maximum 4 characters allowed',
        canContinue: false
      }
    }

    // Check for invalid characters
    const hasInvalidChars = /[^A-Z]/.test(trimmedInput)
    if (hasInvalidChars) {
      const sanitized = this.sanitizeInput(trimmedInput)
      return {
        isValid: false,
        formattedValue: sanitized,
        message: 'Only letters A-Z are allowed',
        canContinue: true
      }
    }

    const formatted = trimmedInput

    // Partial validation for incomplete input
    if (formatted.length < 4) {
      const partialMatches = this.findPartialMatches(formatted)
      return {
        isValid: false,
        formattedValue: formatted,
        message: partialMatches.length > 0 ? 
          `Continue typing... (${partialMatches.length} possible matches)` : 
          'Continue typing...',
        canContinue: true
      }
    }

    // Complete 4-character input - validate against MBTI types
    const isValidType = this.validMBTITypes.includes(formatted as MBTIPersonality)
    return {
      isValid: isValidType,
      formattedValue: formatted,
      message: isValidType ? undefined : 'Invalid MBTI type',
      canContinue: true
    }
  }

  /**
   * Get all valid MBTI personality types
   */
  getValidMBTITypes(): MBTIPersonality[] {
    return [...this.validMBTITypes]
  }

  /**
   * Format and normalize MBTI input
   */
  formatMBTIInput(input: string): string {
    if (!input) return ''
    
    return input
      .trim()
      .toUpperCase()
      .replace(/[^A-Z]/g, '') // Remove non-alphabetic characters
      .slice(0, 4) // Limit to 4 characters
  }

  /**
   * Sanitize input by removing invalid characters
   */
  private sanitizeInput(input: string): string {
    if (!input) return ''
    return input.replace(/[^A-Z]/g, '')
  }

  /**
   * Find the closest matching MBTI type using Levenshtein distance
   */
  private findClosestMatch(input: string): string | undefined {
    if (!input || input.length !== 4) return undefined

    let bestMatch: string | undefined
    let bestDistance = Infinity

    for (const validType of this.validMBTITypes) {
      const distance = this.calculateLevenshteinDistance(input, validType)
      if (distance < bestDistance) {
        bestDistance = distance
        bestMatch = validType
      }
    }

    // Only return matches that are reasonably close (max 2 character differences)
    return bestDistance <= 2 ? bestMatch : undefined
  }

  /**
   * Find multiple potential matches for suggestions
   */
  private findMultipleMatches(input: string): MBTIPersonality[] {
    if (!input || input.length !== 4) return []

    const matches: Array<{ type: MBTIPersonality; distance: number }> = []

    for (const validType of this.validMBTITypes) {
      const distance = this.calculateLevenshteinDistance(input, validType)
      if (distance <= 2) { // Allow up to 2 character differences
        matches.push({ type: validType, distance })
      }
    }

    // Sort by distance (closest first) and return top 3
    return matches
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 3)
      .map(match => match.type)
  }

  /**
   * Find partial matches for incomplete input
   */
  private findPartialMatches(partial: string): MBTIPersonality[] {
    if (!partial || partial.length === 0) return []

    return this.validMBTITypes.filter(type => 
      type.startsWith(partial)
    ).slice(0, 5) // Limit to 5 suggestions
  }

  /**
   * Find similar patterns based on character positions
   */
  private findSimilarPatterns(input: string): MBTIPersonality[] {
    if (!input || input.length === 0) return []
    
    const suggestions: MBTIPersonality[] = []
    
    for (const validType of this.validMBTITypes) {
      let matches = 0
      const minLength = Math.min(input.length, validType.length)
      
      for (let i = 0; i < minLength; i++) {
        if (input[i] === validType[i]) {
          matches++
        }
      }
      
      // If at least half the characters match in position
      if (matches >= minLength / 2) {
        suggestions.push(validType)
      }
    }
    
    return suggestions.slice(0, 3)
  }

  /**
   * Get popular MBTI types for initial suggestions
   */
  private getPopularMBTITypes(): MBTIPersonality[] {
    // Return some commonly known types as examples
    return ['ENFP', 'INTJ', 'INFJ', 'ENTP', 'ISFJ']
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private calculateLevenshteinDistance(str1: string, str2: string): number {
    if (!str1 || !str2) return Math.max(str1?.length || 0, str2?.length || 0)
    
    // Simple character-by-character comparison for MBTI codes
    if (str1 === str2) return 0
    if (str1.length !== 4 || str2.length !== 4) {
      return Math.abs(str1.length - str2.length) + 2
    }
    
    let distance = 0
    for (let i = 0; i < 4; i++) {
      if (str1.charAt(i) !== str2.charAt(i)) {
        distance++
      }
    }
    
    return distance
  }

  /**
   * Calculate confidence score for a match
   */
  private calculateMatchConfidence(input: string, match?: string): number {
    if (!match || !input || input.length !== 4) return 0

    const distance = this.calculateLevenshteinDistance(input, match)
    const maxDistance = Math.max(input.length, match.length)
    
    return Math.max(0, (maxDistance - distance) / maxDistance)
  }

  /**
   * Get user-friendly error messages with suggestions
   */
  getUserFriendlyMessage(result: MBTIValidationResult): string {
    if (result.isValid) {
      return `Valid MBTI type: ${result.detectedType}`
    }

    switch (result.errorCode) {
      case 'REQUIRED':
        return 'Please enter your MBTI personality type (e.g., ENFP, INTJ, INFJ...)'
      
      case 'TOO_SHORT':
        return `Please enter all 4 letters of your MBTI type (you have ${result.formattedValue?.length || 0})`
      
      case 'TOO_LONG':
        return 'MBTI types are exactly 4 letters long'
      
      case 'INVALID_FORMAT':
        return 'Please use only letters A-Z (e.g., ENFP, not enfp or EN1P)'
      
      case 'INVALID_TYPE':
        if (result.suggestedValue) {
          return `"${result.formattedValue}" is not a valid MBTI type. Did you mean "${result.suggestedValue}"?`
        }
        return 'Please input correct MBTI Personality!'
      
      default:
        return result.message || 'Please enter a valid MBTI personality type'
    }
  }

  /**
   * Get validation configuration
   */
  getValidationConfig(): MBTIValidationConfig {
    return { ...this.validationConfig }
  }

  /**
   * Check if a personality type belongs to a specific category
   */
  isStructuredPersonality(type: MBTIPersonality): boolean {
    return ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(type)
  }

  isFlexiblePersonality(type: MBTIPersonality): boolean {
    return ['INTP', 'ISTP', 'ESTP'].includes(type)
  }

  isColorfulPersonality(type: MBTIPersonality): boolean {
    return ['ENTP', 'INFP', 'ENFP', 'ISFP'].includes(type)
  }

  isFeelingPersonality(type: MBTIPersonality): boolean {
    return ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'].includes(type)
  }

  /**
   * Get personality category for a given type
   */
  getPersonalityCategory(type: MBTIPersonality): string {
    if (this.isStructuredPersonality(type)) return 'structured'
    if (this.isFlexiblePersonality(type)) return 'flexible'
    if (this.isColorfulPersonality(type)) return 'colorful'
    if (this.isFeelingPersonality(type)) return 'feeling'
    return 'default'
  }

  /**
   * Validate time input format (HH:MM)
   */
  validateTimeFormat(time: string): { isValid: boolean; message?: string } {
    if (!time || time.trim().length === 0) {
      return { isValid: true } // Empty time is valid (optional)
    }

    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/
    if (!timeRegex.test(time)) {
      return {
        isValid: false,
        message: 'Please enter time in HH:MM format (e.g., 09:30, 14:45)'
      }
    }

    return { isValid: true }
  }

  /**
   * Validate time range (start time must be before end time)
   */
  validateTimeRange(startTime: string, endTime: string): { isValid: boolean; message?: string } {
    // If either time is empty, skip range validation
    if (!startTime || !endTime) {
      return { isValid: true }
    }

    // First validate individual time formats
    const startValidation = this.validateTimeFormat(startTime)
    if (!startValidation.isValid) {
      return { isValid: false, message: `Start time: ${startValidation.message}` }
    }

    const endValidation = this.validateTimeFormat(endTime)
    if (!endValidation.isValid) {
      return { isValid: false, message: `End time: ${endValidation.message}` }
    }

    // Parse times for comparison
    const start = this.parseTime(startTime)
    const end = this.parseTime(endTime)

    if (start >= end) {
      return {
        isValid: false,
        message: 'End time must be after start time'
      }
    }

    // Check minimum duration (30 minutes)
    const durationMinutes = (end.getTime() - start.getTime()) / (1000 * 60)
    if (durationMinutes < 30) {
      return {
        isValid: false,
        message: 'Activities should be at least 30 minutes long'
      }
    }

    // Check maximum duration (8 hours)
    if (durationMinutes > 480) {
      return {
        isValid: false,
        message: 'Activities should not exceed 8 hours'
      }
    }

    return { isValid: true }
  }

  /**
   * Parse time string to Date object for comparison
   */
  private parseTime(timeString: string): Date {
    const [hours, minutes] = timeString.split(':').map(Number)
    const date = new Date()
    date.setHours(hours, minutes, 0, 0)
    return date
  }

  /**
   * Format time for display (ensure consistent format)
   */
  formatTime(time: string): string {
    if (!time) return ''
    
    const validation = this.validateTimeFormat(time)
    if (!validation.isValid) return time

    // Ensure consistent HH:MM format
    const [hours, minutes] = time.split(':')
    return `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}`
  }

  /**
   * Get suggested time ranges for different session types
   */
  getSuggestedTimeRanges(sessionType: 'breakfast' | 'morning_session' | 'lunch' | 'afternoon_session' | 'dinner' | 'night_session'): {
    startTime: string
    endTime: string
    description: string
  } {
    const suggestions = {
      breakfast: { startTime: '08:00', endTime: '09:30', description: 'Typical breakfast hours' },
      morning_session: { startTime: '10:00', endTime: '12:00', description: 'Morning activity time' },
      lunch: { startTime: '12:30', endTime: '14:00', description: 'Lunch hours' },
      afternoon_session: { startTime: '14:30', endTime: '17:00', description: 'Afternoon activity time' },
      dinner: { startTime: '18:00', endTime: '20:00', description: 'Dinner hours' },
      night_session: { startTime: '20:30', endTime: '22:00', description: 'Evening activity time' }
    }

    return suggestions[sessionType] || { startTime: '', endTime: '', description: '' }
  }
}

import { describe, it, expect, beforeEach } from 'vitest'
import { ValidationService } from '../validationService'
import type { MBTIPersonality, MBTIValidationResult } from '../../types'

describe('ValidationService', () => {
  let validationService: ValidationService

  beforeEach(() => {
    validationService = ValidationService.getInstance()
  })

  describe('getInstance', () => {
    it('should return the same instance (singleton)', () => {
      const instance1 = ValidationService.getInstance()
      const instance2 = ValidationService.getInstance()
      expect(instance1).toBe(instance2)
    })
  })

  describe('validateMBTICode', () => {
    it('should validate correct MBTI codes', () => {
      const validCodes: MBTIPersonality[] = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP',
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
      ]

      validCodes.forEach(code => {
        const result = validationService.validateMBTICode(code)
        expect(result.isValid).toBe(true)
        expect(result.detectedType).toBe(code)
        expect(result.formattedValue).toBe(code)
        expect(result.confidence).toBe(1.0)
      })
    })

    it('should handle empty input', () => {
      const result = validationService.validateMBTICode('')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('REQUIRED')
      expect(result.message).toBe('Please enter your MBTI personality type')
      expect(result.suggestions).toBeDefined()
      expect(result.suggestions!.length).toBeGreaterThan(0)
    })

    it('should handle whitespace-only input', () => {
      const result = validationService.validateMBTICode('   ')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('REQUIRED')
    })

    it('should handle input that is too short', () => {
      const result = validationService.validateMBTICode('INT')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('TOO_SHORT')
      expect(result.formattedValue).toBe('INT')
      expect(result.suggestions).toBeDefined()
      expect(result.suggestions!.length).toBeGreaterThan(0)
    })

    it('should handle input that is too long', () => {
      const result = validationService.validateMBTICode('INTJP')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('TOO_LONG')
      expect(result.formattedValue).toBe('INTJ')
    })

    it('should handle invalid characters', () => {
      const result = validationService.validateMBTICode('IN1J')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('INVALID_FORMAT')
      expect(result.formattedValue).toBe('INJ')
    })

    it('should handle invalid MBTI types', () => {
      const result = validationService.validateMBTICode('ABCD')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('INVALID_TYPE')
      expect(result.message).toBe('Please input correct MBTI Personality!')
      expect(result.formattedValue).toBe('ABCD')
    })

    it('should provide suggestions for similar invalid types', () => {
      const result = validationService.validateMBTICode('INTG') // G instead of J
      expect(result.isValid).toBe(false)
      expect(result.suggestedValue).toBe('INTJ')
      expect(result.suggestions).toContain('INTJ')
      expect(result.confidence).toBeGreaterThan(0)
    })

    it('should handle lowercase input', () => {
      const result = validationService.validateMBTICode('intj')
      expect(result.isValid).toBe(true)
      expect(result.detectedType).toBe('INTJ')
      expect(result.formattedValue).toBe('INTJ')
    })

    it('should handle mixed case input', () => {
      const result = validationService.validateMBTICode('InTj')
      expect(result.isValid).toBe(true)
      expect(result.detectedType).toBe('INTJ')
      expect(result.formattedValue).toBe('INTJ')
    })
  })

  describe('validateRealTimeInput', () => {
    it('should allow empty input during typing', () => {
      const result = validationService.validateRealTimeInput('')
      expect(result.isValid).toBe(false)
      expect(result.canContinue).toBe(true)
      expect(result.formattedValue).toBe('')
      expect(result.message).toBeUndefined()
    })

    it('should handle partial input', () => {
      const result = validationService.validateRealTimeInput('IN')
      expect(result.isValid).toBe(false)
      expect(result.canContinue).toBe(true)
      expect(result.formattedValue).toBe('IN')
      expect(result.message).toContain('Continue typing')
    })

    it('should reject invalid characters', () => {
      const result = validationService.validateRealTimeInput('IN1')
      expect(result.isValid).toBe(false)
      expect(result.canContinue).toBe(true)
      expect(result.formattedValue).toBe('IN')
      expect(result.message).toBe('Only letters A-Z are allowed')
    })

    it('should limit input to 4 characters', () => {
      const result = validationService.validateRealTimeInput('INTJP')
      expect(result.isValid).toBe(false)
      expect(result.canContinue).toBe(false)
      expect(result.formattedValue).toBe('INTJ')
      expect(result.message).toBe('Maximum 4 characters allowed')
    })

    it('should validate complete 4-character input', () => {
      const result = validationService.validateRealTimeInput('INTJ')
      expect(result.isValid).toBe(true)
      expect(result.canContinue).toBe(true)
      expect(result.formattedValue).toBe('INTJ')
      expect(result.message).toBeUndefined()
    })

    it('should reject invalid 4-character combinations', () => {
      const result = validationService.validateRealTimeInput('ABCD')
      expect(result.isValid).toBe(false)
      expect(result.canContinue).toBe(true)
      expect(result.formattedValue).toBe('ABCD')
      expect(result.message).toBe('Invalid MBTI type')
    })
  })

  describe('formatMBTIInput', () => {
    it('should format input correctly', () => {
      expect(validationService.formatMBTIInput('intj')).toBe('INTJ')
      expect(validationService.formatMBTIInput('  INTJ  ')).toBe('INTJ')
      expect(validationService.formatMBTIInput('in1tj')).toBe('INTJ')
      expect(validationService.formatMBTIInput('intjp')).toBe('INTJ')
      expect(validationService.formatMBTIInput('')).toBe('')
    })

    it('should handle special characters', () => {
      expect(validationService.formatMBTIInput('I-N-T-J')).toBe('INTJ')
      expect(validationService.formatMBTIInput('I.N.T.J')).toBe('INTJ')
      expect(validationService.formatMBTIInput('I N T J')).toBe('INTJ')
    })
  })

  describe('getValidMBTITypes', () => {
    it('should return all 16 valid MBTI types', () => {
      const types = validationService.getValidMBTITypes()
      expect(types).toHaveLength(16)
      expect(types).toContain('INTJ')
      expect(types).toContain('ENFP')
      expect(types).toContain('ISFJ')
      expect(types).toContain('ESTP')
    })

    it('should return a copy of the array', () => {
      const types1 = validationService.getValidMBTITypes()
      const types2 = validationService.getValidMBTITypes()
      expect(types1).not.toBe(types2) // Different array instances
      expect(types1).toEqual(types2) // Same content
    })
  })

  describe('getUserFriendlyMessage', () => {
    it('should provide friendly messages for different error types', () => {
      const requiredError: MBTIValidationResult = {
        isValid: false,
        errorCode: 'REQUIRED',
        message: 'Please enter your MBTI personality type'
      }
      expect(validationService.getUserFriendlyMessage(requiredError))
        .toContain('Please enter your MBTI personality type')

      const tooShortError: MBTIValidationResult = {
        isValid: false,
        errorCode: 'TOO_SHORT',
        formattedValue: 'IN'
      }
      expect(validationService.getUserFriendlyMessage(tooShortError))
        .toContain('Please enter all 4 letters')

      const invalidTypeError: MBTIValidationResult = {
        isValid: false,
        errorCode: 'INVALID_TYPE',
        formattedValue: 'ABCD',
        suggestedValue: 'INTJ'
      }
      expect(validationService.getUserFriendlyMessage(invalidTypeError))
        .toContain('Did you mean "INTJ"?')
    })

    it('should handle valid results', () => {
      const validResult: MBTIValidationResult = {
        isValid: true,
        detectedType: 'INTJ'
      }
      expect(validationService.getUserFriendlyMessage(validResult))
        .toBe('Valid MBTI type: INTJ')
    })
  })

  describe('personality categorization', () => {
    it('should correctly identify structured personalities', () => {
      expect(validationService.isStructuredPersonality('INTJ')).toBe(true)
      expect(validationService.isStructuredPersonality('ENTJ')).toBe(true)
      expect(validationService.isStructuredPersonality('ISTJ')).toBe(true)
      expect(validationService.isStructuredPersonality('ESTJ')).toBe(true)
      expect(validationService.isStructuredPersonality('ENFP')).toBe(false)
    })

    it('should correctly identify flexible personalities', () => {
      expect(validationService.isFlexiblePersonality('INTP')).toBe(true)
      expect(validationService.isFlexiblePersonality('ISTP')).toBe(true)
      expect(validationService.isFlexiblePersonality('ESTP')).toBe(true)
      expect(validationService.isFlexiblePersonality('INTJ')).toBe(false)
    })

    it('should correctly identify colorful personalities', () => {
      expect(validationService.isColorfulPersonality('ENTP')).toBe(true)
      expect(validationService.isColorfulPersonality('INFP')).toBe(true)
      expect(validationService.isColorfulPersonality('ENFP')).toBe(true)
      expect(validationService.isColorfulPersonality('ISFP')).toBe(true)
      expect(validationService.isColorfulPersonality('INTJ')).toBe(false)
    })

    it('should correctly identify feeling personalities', () => {
      expect(validationService.isFeelingPersonality('INFJ')).toBe(true)
      expect(validationService.isFeelingPersonality('ISFJ')).toBe(true)
      expect(validationService.isFeelingPersonality('ENFJ')).toBe(true)
      expect(validationService.isFeelingPersonality('ESFJ')).toBe(true)
      expect(validationService.isFeelingPersonality('INTJ')).toBe(false)
    })

    it('should get correct personality categories', () => {
      expect(validationService.getPersonalityCategory('INTJ')).toBe('structured')
      expect(validationService.getPersonalityCategory('INTP')).toBe('flexible')
      expect(validationService.getPersonalityCategory('ENFP')).toBe('colorful')
      expect(validationService.getPersonalityCategory('INFJ')).toBe('feeling')
    })
  })

  describe('getValidationConfig', () => {
    it('should return validation configuration', () => {
      const config = validationService.getValidationConfig()
      expect(config.minLength).toBe(4)
      expect(config.maxLength).toBe(4)
      expect(config.required).toBe(true)
      expect(config.caseSensitive).toBe(false)
      expect(config.autoFormat).toBe(true)
      expect(config.validTypes).toHaveLength(16)
    })

    it('should return a copy of the configuration', () => {
      const config1 = validationService.getValidationConfig()
      const config2 = validationService.getValidationConfig()
      expect(config1).not.toBe(config2)
      expect(config1).toEqual(config2)
    })
  })

  describe('edge cases and error handling', () => {
    it('should handle null and undefined input', () => {
      // @ts-expect-error Testing runtime behavior
      const nullResult = validationService.validateMBTICode(null)
      expect(nullResult.isValid).toBe(false)
      expect(nullResult.errorCode).toBe('REQUIRED')

      // @ts-expect-error Testing runtime behavior
      const undefinedResult = validationService.validateMBTICode(undefined)
      expect(undefinedResult.isValid).toBe(false)
      expect(undefinedResult.errorCode).toBe('REQUIRED')
    })

    it('should handle very long input', () => {
      const longInput = 'INTJINTJINTJINTJ'
      const result = validationService.validateMBTICode(longInput)
      expect(result.formattedValue).toBe('INTJ')
    })

    it('should handle input with numbers and symbols', () => {
      const result = validationService.validateMBTICode('I1N2T3J4!@#$')
      expect(result.isValid).toBe(false)
      expect(result.errorCode).toBe('INVALID_FORMAT')
      expect(result.formattedValue).toBe('INTJ') // Should be sanitized in the result
    })

    it('should provide multiple suggestions for ambiguous input', () => {
      const result = validationService.validateMBTICode('XNTJ')
      expect(result.isValid).toBe(false)
      expect(result.suggestions).toBeDefined()
      expect(result.suggestions!.length).toBeGreaterThan(0)
    })
  })

  describe('performance and consistency', () => {
    it('should consistently validate the same input', () => {
      const input = 'INTJ'
      const results = Array.from({ length: 10 }, () => 
        validationService.validateMBTICode(input)
      )
      
      results.forEach(result => {
        expect(result.isValid).toBe(true)
        expect(result.detectedType).toBe('INTJ')
      })
    })

    it('should handle rapid successive validations', () => {
      const inputs = ['I', 'IN', 'INT', 'INTJ']
      const results = inputs.map(input => 
        validationService.validateRealTimeInput(input)
      )
      
      expect(results[0].canContinue).toBe(true)
      expect(results[1].canContinue).toBe(true)
      expect(results[2].canContinue).toBe(true)
      expect(results[3].isValid).toBe(true)
    })
  })
})
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ThemeService } from '../themeService'
import type { MBTIPersonality } from '../../types'

// Mock DOM methods
const mockSetProperty = vi.fn()
const mockGetPropertyValue = vi.fn()
const mockGetComputedStyle = vi.fn()
const mockAddEventListener = vi.fn()
const mockDispatchEvent = vi.fn()
const mockClassListAdd = vi.fn()
const mockClassListRemove = vi.fn()

// Setup DOM mocks
Object.defineProperty(document, 'documentElement', {
    value: {
        style: {
            setProperty: mockSetProperty
        }
    },
    writable: true
})

Object.defineProperty(document, 'body', {
    value: {
        classList: {
            add: mockClassListAdd,
            remove: mockClassListRemove,
            contains: vi.fn().mockReturnValue(false)
        }
    },
    writable: true
})

Object.defineProperty(window, 'getComputedStyle', {
    value: mockGetComputedStyle,
    writable: true
})

Object.defineProperty(window, 'addEventListener', {
    value: mockAddEventListener,
    writable: true
})

Object.defineProperty(window, 'dispatchEvent', {
    value: mockDispatchEvent,
    writable: true
})

describe('ThemeService', () => {
    let themeService: ThemeService

    beforeEach(() => {
        // Reset all mocks
        vi.clearAllMocks()

        // Reset singleton instance
        // @ts-ignore - accessing private static property for testing
        ThemeService.instance = undefined

        // Setup default getComputedStyle mock
        mockGetComputedStyle.mockReturnValue({
            getPropertyValue: mockGetPropertyValue.mockReturnValue('#007bff')
        })

        themeService = ThemeService.getInstance()
    })

    afterEach(() => {
        vi.clearAllMocks()
    })

    describe('Singleton Pattern', () => {
        it('should return the same instance when called multiple times', () => {
            const instance1 = ThemeService.getInstance()
            const instance2 = ThemeService.getInstance()

            expect(instance1).toBe(instance2)
        })

        it('should initialize default theme on creation', () => {
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#007bff')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#6c757d')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#28a745')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-background', '#ffffff')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-text', '#212529')
        })
    })

    describe('applyMBTITheme', () => {
        it('should apply INTJ theme correctly', () => {
            themeService.applyMBTITheme('INTJ')

            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#2c3e50')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#34495e')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#3498db')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-background', '#ecf0f1')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-text', '#2c3e50')
        })

        it('should apply ISFJ warm theme correctly', () => {
            themeService.applyMBTITheme('ISFJ')

            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#d4a574')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#f4e4bc')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#b8860b')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-background', '#fdf5e6')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-text', '#8b4513')
        })

        it('should apply ENFP colorful theme correctly', () => {
            themeService.applyMBTITheme('ENFP')

            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#ff5722')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#d84315')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#4caf50')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-background', '#fff3e0')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-text', '#2c3e50')
        })

        it('should add personality CSS class to body', () => {
            themeService.applyMBTITheme('INTJ')

            expect(mockClassListAdd).toHaveBeenCalledWith('mbti-intj')
        })

        it('should dispatch theme change event', () => {
            themeService.applyMBTITheme('INTJ')

            expect(mockDispatchEvent).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'mbti-theme-changed',
                    detail: expect.objectContaining({
                        personality: 'INTJ',
                        theme: expect.objectContaining({
                            name: 'INTJ - The Architect',
                            primary: '#2c3e50'
                        })
                    })
                })
            )
        })

        it('should store current personality', () => {
            themeService.applyMBTITheme('ENFP')

            expect(themeService.getCurrentPersonality()).toBe('ENFP')
        })
    })

    describe('getPersonalityColors', () => {
        it('should return correct theme for all 16 MBTI types', () => {
            const personalities: MBTIPersonality[] = [
                'INTJ', 'INTP', 'ENTJ', 'ENTP',
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                'ISTP', 'ISFP', 'ESTP', 'ESFP'
            ]

            personalities.forEach(personality => {
                const theme = themeService.getPersonalityColors(personality)

                expect(theme).toHaveProperty('name')
                expect(theme).toHaveProperty('primary')
                expect(theme).toHaveProperty('secondary')
                expect(theme).toHaveProperty('accent')
                expect(theme).toHaveProperty('background')
                expect(theme).toHaveProperty('text')
                expect(theme.name).toContain(personality)
            })
        })

        it('should return warm theme for ISFJ', () => {
            const theme = themeService.getPersonalityColors('ISFJ')

            expect(theme.warm).toBe(true)
            expect(theme.text).toBe('#8b4513') // Brown text for warm theme
        })

        it('should return colorful theme for creative types', () => {
            const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP']

            colorfulTypes.forEach(personality => {
                const theme = themeService.getPersonalityColors(personality)
                expect(theme.colorful).toBe(true)
            })
        })
    })

    describe('resetTheme', () => {
        it('should reset to default theme', () => {
            // First apply a theme
            themeService.applyMBTITheme('INTJ')
            vi.clearAllMocks()

            // Setup mock to return default values for getCurrentTheme
            mockGetPropertyValue
                .mockReturnValueOnce('#007bff')  // primary
                .mockReturnValueOnce('#6c757d')  // secondary
                .mockReturnValueOnce('#28a745')  // accent
                .mockReturnValueOnce('#ffffff')  // background
                .mockReturnValueOnce('#212529')  // text

            // Then reset
            themeService.resetTheme()

            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-primary', '#007bff')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-secondary', '#6c757d')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-accent', '#28a745')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-background', '#ffffff')
            expect(mockSetProperty).toHaveBeenCalledWith('--mbti-text', '#212529')
        })

        it('should remove personality CSS class', () => {
            themeService.applyMBTITheme('INTJ')
            themeService.resetTheme()

            expect(mockClassListRemove).toHaveBeenCalledWith('mbti-intj')
        })

        it('should dispatch theme reset event', () => {
            themeService.applyMBTITheme('INTJ')
            vi.clearAllMocks()

            themeService.resetTheme()

            expect(mockDispatchEvent).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'mbti-theme-reset'
                })
            )
        })

        it('should clear current personality', () => {
            themeService.applyMBTITheme('INTJ')
            themeService.resetTheme()

            expect(themeService.getCurrentPersonality()).toBeNull()
        })
    })

    describe('Personality Type Checks', () => {
        describe('isColorfulPersonality', () => {
            it('should return true for colorful personalities', () => {
                const colorfulTypes: MBTIPersonality[] = ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESTP', 'ESFP']

                colorfulTypes.forEach(personality => {
                    expect(themeService.isColorfulPersonality(personality)).toBe(true)
                })
            })

            it('should return false for non-colorful personalities', () => {
                const nonColorfulTypes: MBTIPersonality[] = ['INTJ', 'INTP', 'ENTJ', 'INFJ', 'ENFJ', 'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP']

                nonColorfulTypes.forEach(personality => {
                    expect(themeService.isColorfulPersonality(personality)).toBe(false)
                })
            })
        })

        describe('isWarmPersonality', () => {
            it('should return true for warm personalities', () => {
                const warmTypes: MBTIPersonality[] = ['ISFJ', 'ENFJ', 'ESFJ']

                warmTypes.forEach(personality => {
                    expect(themeService.isWarmPersonality(personality)).toBe(true)
                })
            })

            it('should return false for non-warm personalities', () => {
                const nonWarmTypes: MBTIPersonality[] = ['INTJ', 'INTP', 'ENTJ', 'ENTP', 'INFJ', 'INFP', 'ENFP', 'ISTJ', 'ESTJ', 'ISTP', 'ISFP', 'ESTP', 'ESFP']

                nonWarmTypes.forEach(personality => {
                    expect(themeService.isWarmPersonality(personality)).toBe(false)
                })
            })
        })

        describe('isFlashyPersonality', () => {
            it('should return true only for ESTP', () => {
                expect(themeService.isFlashyPersonality('ESTP')).toBe(true)
            })

            it('should return false for all other personalities', () => {
                const nonFlashyTypes: MBTIPersonality[] = [
                    'INTJ', 'INTP', 'ENTJ', 'ENTP',
                    'INFJ', 'INFP', 'ENFJ', 'ENFP',
                    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                    'ISTP', 'ISFP', 'ESFP'
                ]

                nonFlashyTypes.forEach(personality => {
                    expect(themeService.isFlashyPersonality(personality)).toBe(false)
                })
            })
        })
    })

    describe('getCurrentTheme', () => {
        it('should return current theme from CSS variables', () => {
            mockGetPropertyValue
                .mockReturnValueOnce('#2c3e50')  // primary
                .mockReturnValueOnce('#34495e')  // secondary
                .mockReturnValueOnce('#3498db')  // accent
                .mockReturnValueOnce('#ecf0f1')  // background
                .mockReturnValueOnce('#2c3e50')  // text

            const currentTheme = themeService.getCurrentTheme()

            expect(currentTheme).toEqual({
                name: 'Current Theme',
                primary: '#2c3e50',
                secondary: '#34495e',
                accent: '#3498db',
                background: '#ecf0f1',
                text: '#2c3e50'
            })
        })

        it('should return default values when CSS variables are empty', () => {
            mockGetPropertyValue.mockReturnValue('')

            const currentTheme = themeService.getCurrentTheme()

            expect(currentTheme).toEqual({
                name: 'Current Theme',
                primary: '#007bff',
                secondary: '#6c757d',
                accent: '#28a745',
                background: '#ffffff',
                text: '#212529'
            })
        })
    })

    describe('Theme State Management', () => {
        it('should track current personality correctly', () => {
            expect(themeService.getCurrentPersonality()).toBeNull()

            themeService.applyMBTITheme('ENFP')
            expect(themeService.getCurrentPersonality()).toBe('ENFP')

            themeService.applyMBTITheme('INTJ')
            expect(themeService.getCurrentPersonality()).toBe('INTJ')

            themeService.resetTheme()
            expect(themeService.getCurrentPersonality()).toBeNull()
        })

        it('should preserve original theme when applying multiple themes', () => {
            // Apply first theme
            themeService.applyMBTITheme('INTJ')

            // Apply second theme
            themeService.applyMBTITheme('ENFP')

            // Setup mock to return default values for getCurrentTheme during reset
            mockGetPropertyValue
                .mockReturnValueOnce('#007bff')  // primary
                .mockReturnValueOnce('#6c757d')  // secondary
                .mockReturnValueOnce('#28a745')  // accent
                .mockReturnValueOnce('#ffffff')  // background
                .mockReturnValueOnce('#212529')  // text

            // Reset should go back to default, not INTJ
            themeService.resetTheme()

            expect(mockSetProperty).toHaveBeenLastCalledWith('--mbti-text', '#212529')
        })
    })

    describe('CSS Class Management', () => {
        it('should remove existing MBTI classes when applying new theme', () => {
            // Mock classList to simulate existing classes
            const mockClassListArray = ['some-class', 'mbti-intj', 'another-class']
            Object.defineProperty(document.body.classList, Symbol.iterator, {
                value: function* () {
                    for (const className of mockClassListArray) {
                        yield className
                    }
                }
            })

            themeService.applyMBTITheme('ENFP')

            expect(mockClassListRemove).toHaveBeenCalledWith('mbti-intj')
            expect(mockClassListAdd).toHaveBeenCalledWith('mbti-enfp')
        })
    })

    describe('Event Dispatching', () => {
        it('should dispatch theme change event with correct details', () => {
            const personality: MBTIPersonality = 'INFJ'
            themeService.applyMBTITheme(personality)

            expect(mockDispatchEvent).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'mbti-theme-changed',
                    detail: expect.objectContaining({
                        personality: 'INFJ',
                        theme: expect.objectContaining({
                            name: 'INFJ - The Advocate',
                            primary: '#5e35b1'
                        }),
                        timestamp: expect.any(String)
                    })
                })
            )
        })

        it('should dispatch theme reset event with timestamp', () => {
            themeService.applyMBTITheme('INTJ')
            themeService.resetTheme()

            expect(mockDispatchEvent).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: 'mbti-theme-reset',
                    detail: expect.objectContaining({
                        timestamp: expect.any(String)
                    })
                })
            )
        })
    })

    describe('Edge Cases', () => {
        it('should handle multiple theme applications gracefully', () => {
            themeService.applyMBTITheme('INTJ')
            themeService.applyMBTITheme('ENFP')
            themeService.applyMBTITheme('ISFJ')

            expect(themeService.getCurrentPersonality()).toBe('ISFJ')
        })

        it('should handle reset without prior theme application', () => {
            expect(() => themeService.resetTheme()).not.toThrow()
            expect(themeService.getCurrentPersonality()).toBeNull()
        })

        it('should handle multiple resets gracefully', () => {
            themeService.applyMBTITheme('INTJ')
            themeService.resetTheme()

            expect(() => themeService.resetTheme()).not.toThrow()
            expect(themeService.getCurrentPersonality()).toBeNull()
        })
    })
})
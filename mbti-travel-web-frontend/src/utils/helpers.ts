// Helper utility functions
import type { MBTIPersonality } from '@/types/mbti'
import { PERSONALITY_CATEGORIES } from './constants'

export function isStructuredPersonality(personality: MBTIPersonality): boolean {
  return PERSONALITY_CATEGORIES.structured.includes(personality)
}

export function isFlexiblePersonality(personality: MBTIPersonality): boolean {
  return PERSONALITY_CATEGORIES.flexible.includes(personality)
}

export function isColorfulPersonality(personality: MBTIPersonality): boolean {
  return PERSONALITY_CATEGORIES.colorful.includes(personality)
}

export function isFeelingPersonality(personality: MBTIPersonality): boolean {
  return PERSONALITY_CATEGORIES.feeling.includes(personality)
}

export function getPersonalityDisplayName(personality: MBTIPersonality): string {
  // TODO: Add personality display names mapping
  return personality
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

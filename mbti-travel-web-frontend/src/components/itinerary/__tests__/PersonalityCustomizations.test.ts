import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PersonalityCustomizations from '../PersonalityCustomizations.vue'
import type { MBTIPersonality } from '../../../types/mbti'

// Mock ValidationService
vi.mock('../../../services/validationService', () => ({
  ValidationService: {
    getInstance: () => ({
      validateTimeRange: vi.fn().mockReturnValue({ isValid: true }),
      formatTime: vi.fn().mockImplementation((time: string) => time),
      getSuggestedTimeRanges: vi.fn().mockReturnValue({
        startTime: '09:00',
        endTime: '10:30',
        description: 'Test time range'
      })
    })
  }
}))

describe('PersonalityCustomizations', () => {
  const createWrapper = (mbtiPersonality: MBTIPersonality = 'INTJ') => {
    return mount(PersonalityCustomizations, {
      props: {
        mbtiPersonality
      }
    })
  }

  describe('Structured Personality Types', () => {
    it('should render customizations for INTJ personality', () => {
      const wrapper = createWrapper('INTJ')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.structured-customizations').exists()).toBe(true)
      expect(wrapper.text()).toContain('Strategic Time Planning')
    })

    it('should render customizations for ENTJ personality', () => {
      const wrapper = createWrapper('ENTJ')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.structured-customizations').exists()).toBe(true)
      expect(wrapper.text()).toContain('Executive Schedule Management')
    })

    it('should render customizations for ISTJ personality', () => {
      const wrapper = createWrapper('ISTJ')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.structured-customizations').exists()).toBe(true)
      expect(wrapper.text()).toContain('Detailed Time Organization')
    })

    it('should render customizations for ESTJ personality', () => {
      const wrapper = createWrapper('ESTJ')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(true)
      expect(wrapper.find('.structured-customizations').exists()).toBe(true)
      expect(wrapper.text()).toContain('Structured Activity Planning')
    })

    it('should render time input fields for all sessions', () => {
      const wrapper = createWrapper('INTJ')
      
      // Should have 6 sessions × 3 days × 2 time inputs = 36 time inputs
      const timeInputs = wrapper.findAll('input[type="time"]')
      expect(timeInputs).toHaveLength(36)
      
      // Check for start and end time labels
      expect(wrapper.text()).toContain('Target Start Time')
      expect(wrapper.text()).toContain('Target End Time')
    })

    it('should render importance checkboxes only for ENTJ and tourist spots', () => {
      const wrapper = createWrapper('ENTJ')
      
      // Should have checkboxes for tourist spots only (morning_session, afternoon_session, night_session)
      // 3 tourist spot sessions × 3 days = 9 checkboxes
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      expect(checkboxes).toHaveLength(9)
      
      // Check for importance labels
      expect(wrapper.text()).toContain('Important!')
      expect(wrapper.text()).toContain('High priority activity')
    })

    it('should not render importance checkboxes for non-ENTJ personalities', () => {
      const wrapper = createWrapper('INTJ')
      
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      expect(checkboxes).toHaveLength(0)
    })

    it('should render day customizations for all 3 days', () => {
      const wrapper = createWrapper('INTJ')
      
      expect(wrapper.text()).toContain('Day 1 Time Planning')
      expect(wrapper.text()).toContain('Day 2 Time Planning')
      expect(wrapper.text()).toContain('Day 3 Time Planning')
    })

    it('should render session types with appropriate badges', () => {
      const wrapper = createWrapper('INTJ')
      
      // Check for session names
      expect(wrapper.text()).toContain('Breakfast')
      expect(wrapper.text()).toContain('Morning Session')
      expect(wrapper.text()).toContain('Lunch')
      expect(wrapper.text()).toContain('Afternoon Session')
      expect(wrapper.text()).toContain('Dinner')
      expect(wrapper.text()).toContain('Night Session')
      
      // Check for session type badges (emojis)
      expect(wrapper.text()).toContain('🏛️') // Tourist spot emoji
      expect(wrapper.text()).toContain('🍽️') // Restaurant emoji
    })
  })

  describe('Non-Structured Personality Types', () => {
    it('should not render customizations for ENFP personality', () => {
      const wrapper = createWrapper('ENFP')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(false)
    })

    it('should not render customizations for INTP personality', () => {
      const wrapper = createWrapper('INTP')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(false)
    })

    it('should not render customizations for ISFJ personality', () => {
      const wrapper = createWrapper('ISFJ')
      
      expect(wrapper.find('.personality-customizations').exists()).toBe(false)
    })
  })

  describe('Event Handling', () => {
    it('should emit time-changed event when time input changes', async () => {
      const wrapper = createWrapper('INTJ')
      
      const timeInput = wrapper.find('input[type="time"]')
      await timeInput.setValue('09:30')
      await timeInput.trigger('input')
      
      expect(wrapper.emitted('time-changed')).toBeTruthy()
      const emittedEvent = wrapper.emitted('time-changed')?.[0]?.[0] as any
      expect(emittedEvent).toMatchObject({
        day: expect.any(Number),
        session: expect.any(String),
        type: expect.any(String),
        time: '09:30'
      })
    })

    it('should emit importance-changed event when checkbox changes', async () => {
      const wrapper = createWrapper('ENTJ')
      
      const checkbox = wrapper.find('input[type="checkbox"]')
      await checkbox.setChecked(true)
      await checkbox.trigger('change')
      
      expect(wrapper.emitted('importance-changed')).toBeTruthy()
      const emittedEvent = wrapper.emitted('importance-changed')?.[0]?.[0] as any
      expect(emittedEvent).toMatchObject({
        day: expect.any(Number),
        session: expect.any(String),
        isImportant: true
      })
    })

    it('should emit update:modelValue when customizations change', async () => {
      const wrapper = createWrapper('INTJ')
      
      const timeInput = wrapper.find('input[type="time"]')
      await timeInput.setValue('09:30')
      await timeInput.trigger('input')
      
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const emittedValue = wrapper.emitted('update:modelValue')?.[0]?.[0] as any
      expect(emittedValue).toMatchObject({
        day_1: expect.any(Object),
        day_2: expect.any(Object),
        day_3: expect.any(Object),
        mbtiPersonality: 'INTJ',
        lastModified: expect.any(String)
      })
    })
  })

  describe('Validation', () => {
    it('should have validation message comments in template', () => {
      const wrapper = createWrapper('INTJ')
      
      // Check that the validation message comments are present
      // The actual validation logic is tested in the ValidationService tests
      const template = wrapper.html()
      expect(template).toContain('<!-- Time Validation Messages -->')
      expect(template).toContain('<!--v-if-->')
    })
  })

  describe('Summary Statistics', () => {
    it('should show planning summary when customizations exist', async () => {
      const wrapper = createWrapper('INTJ')
      
      // Add some time inputs
      const timeInput = wrapper.find('input[type="time"]')
      await timeInput.setValue('09:30')
      await timeInput.trigger('input')
      
      await wrapper.vm.$nextTick()
      
      // The summary should appear when there are customizations
      expect(wrapper.text()).toContain('Planning Summary')
      expect(wrapper.text()).toContain('Sessions with timing:')
    })

    it('should show important activities count for ENTJ', async () => {
      const wrapper = createWrapper('ENTJ')
      
      // Check an importance checkbox
      const checkbox = wrapper.find('input[type="checkbox"]')
      await checkbox.setChecked(true)
      await checkbox.trigger('change')
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.text()).toContain('Important activities:')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for time inputs', () => {
      const wrapper = createWrapper('INTJ')
      
      const timeInputs = wrapper.findAll('input[type="time"]')
      timeInputs.forEach(input => {
        expect(input.attributes('aria-label')).toBeTruthy()
        expect(input.attributes('aria-label')).toMatch(/Target (start|end) time for .+ on Day \d/)
      })
    })

    it('should have proper ARIA labels for importance checkboxes', () => {
      const wrapper = createWrapper('ENTJ')
      
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      checkboxes.forEach(checkbox => {
        expect(checkbox.attributes('aria-label')).toBeTruthy()
        expect(checkbox.attributes('aria-label')).toMatch(/Mark .+ as important for Day \d/)
      })
    })

    it('should have validation messages with role="alert"', () => {
      const wrapper = createWrapper('INTJ')
      
      // Check that validation messages have proper role when they exist
      const validationMessages = wrapper.findAll('.validation-message')
      validationMessages.forEach(message => {
        expect(message.attributes('role')).toBe('alert')
      })
    })
  })

  describe('Responsive Design', () => {
    it('should have responsive CSS classes', () => {
      const wrapper = createWrapper('INTJ')
      
      expect(wrapper.find('.sessions-grid').exists()).toBe(true)
      expect(wrapper.find('.time-inputs').exists()).toBe(true)
      // Summary stats only appear when there are customizations
      expect(wrapper.find('.customizations-summary').exists()).toBe(false)
    })
  })

  describe('Personality-Specific Styling', () => {
    it('should apply MBTI-specific CSS classes', () => {
      const wrapper = createWrapper('INTJ')
      
      expect(wrapper.find('.mbti-intj').exists()).toBe(true)
    })

    it('should apply different classes for different personalities', () => {
      const entjWrapper = createWrapper('ENTJ')
      const istjWrapper = createWrapper('ISTJ')
      const estjWrapper = createWrapper('ESTJ')
      
      expect(entjWrapper.find('.mbti-entj').exists()).toBe(true)
      expect(istjWrapper.find('.mbti-istj').exists()).toBe(true)
      expect(estjWrapper.find('.mbti-estj').exists()).toBe(true)
    })
  })
})
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ErrorMessage from '../ErrorMessage.vue'
import type { ErrorNotificationAction } from '@/types/error'

describe('ErrorMessage', () => {
  it('renders basic error message', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test error message'
      }
    })

    expect(wrapper.text()).toContain('Test error message')
    expect(wrapper.find('.error-message--error').exists()).toBe(true)
    expect(wrapper.find('.error-icon').text()).toBe('❌')
  })

  it('renders with different severity levels', async () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        severity: 'warning'
      }
    })

    expect(wrapper.find('.error-message--warning').exists()).toBe(true)
    expect(wrapper.find('.error-icon').text()).toBe('⚠️')

    await wrapper.setProps({ severity: 'success' })
    expect(wrapper.find('.error-message--success').exists()).toBe(true)
    expect(wrapper.find('.error-icon').text()).toBe('✅')

    await wrapper.setProps({ severity: 'info' })
    expect(wrapper.find('.error-message--info').exists()).toBe(true)
    expect(wrapper.find('.error-icon').text()).toBe('ℹ️')
  })

  it('renders with title and suggestion', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test error message',
        title: 'Error Title',
        suggestion: 'Try this suggestion'
      }
    })

    expect(wrapper.find('.error-title').text()).toBe('Error Title')
    expect(wrapper.find('.error-suggestion').text()).toBe('Try this suggestion')
  })

  it('renders with different variants', async () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        variant: 'banner'
      }
    })

    expect(wrapper.find('.error-message--banner').exists()).toBe(true)

    await wrapper.setProps({ variant: 'toast' })
    expect(wrapper.find('.error-message--toast').exists()).toBe(true)
  })

  it('shows dismiss button when dismissible', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        dismissible: true
      }
    })

    expect(wrapper.find('.dismiss-button').exists()).toBe(true)
  })

  it('hides dismiss button when not dismissible', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        dismissible: false
      }
    })

    expect(wrapper.find('.dismiss-button').exists()).toBe(false)
  })

  it('emits dismiss event when dismiss button is clicked', async () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        dismissible: true
      }
    })

    await wrapper.find('.dismiss-button').trigger('click')
    expect(wrapper.emitted('dismiss')).toHaveLength(1)
  })

  it('renders action buttons', () => {
    const actions: ErrorNotificationAction[] = [
      {
        label: 'Retry',
        action: vi.fn(),
        style: 'primary'
      },
      {
        label: 'Cancel',
        action: vi.fn(),
        style: 'secondary'
      }
    ]

    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        actions
      }
    })

    const actionButtons = wrapper.findAll('.error-action-button')
    expect(actionButtons).toHaveLength(2)
    expect(actionButtons[0].text()).toBe('Retry')
    expect(actionButtons[1].text()).toBe('Cancel')
    expect(actionButtons[0].classes()).toContain('error-action-button--primary')
    expect(actionButtons[1].classes()).toContain('error-action-button--secondary')
  })

  it('handles action button clicks', async () => {
    const mockAction = vi.fn()
    const actions: ErrorNotificationAction[] = [
      {
        label: 'Test Action',
        action: mockAction,
        style: 'primary'
      }
    ]

    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        actions
      }
    })

    await wrapper.find('.error-action-button').trigger('click')
    expect(mockAction).toHaveBeenCalledOnce()
    expect(wrapper.emitted('action')).toHaveLength(1)
  })

  it('shows loading state for actions', () => {
    const actions: ErrorNotificationAction[] = [
      {
        label: 'Loading Action',
        action: vi.fn(),
        style: 'primary',
        loading: true
      }
    ]

    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        actions
      }
    })

    const actionButton = wrapper.find('.error-action-button')
    expect(actionButton.attributes('disabled')).toBeDefined()
    expect(wrapper.find('.action-loading').exists()).toBe(true)
  })

  it('has proper accessibility attributes', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test error message',
        severity: 'error'
      }
    })

    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.attributes('role')).toBe('alert')
    expect(errorMessage.attributes('aria-live')).toBe('assertive')

    const dismissButton = wrapper.find('.dismiss-button')
    expect(dismissButton.attributes('aria-label')).toBe('Dismiss error message')
  })

  it('uses polite aria-live for non-error severities', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test info message',
        severity: 'info'
      }
    })

    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.attributes('aria-live')).toBe('polite')
  })

  it('applies correct CSS classes for different combinations', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        severity: 'warning',
        variant: 'banner',
        dismissible: true
      }
    })

    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.classes()).toContain('error-message--warning')
    expect(errorMessage.classes()).toContain('error-message--banner')
    expect(errorMessage.classes()).toContain('error-message--dismissible')
  })
})
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ErrorNotificationSystem from '../ErrorNotificationSystem.vue'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { ErrorNotification } from '@/types/error'

// Mock the composables
vi.mock('@/composables/useErrorHandler', () => ({
  useErrorHandler: vi.fn()
}))

vi.mock('@/composables/useNetworkStatus', () => ({
  useNetworkStatus: vi.fn(() => ({
    isOnline: { value: true },
    testConnectivity: vi.fn()
  }))
}))

describe('ErrorNotificationSystem', () => {
  let mockErrorHandler: any
  let mockNotifications: ErrorNotification[]

  beforeEach(() => {
    mockNotifications = []
    mockErrorHandler = {
      activeNotifications: { value: mockNotifications },
      dismissNotification: vi.fn((id: string) => {
        const index = mockNotifications.findIndex(n => n.id === id)
        if (index > -1) {
          mockNotifications.splice(index, 1)
        }
      })
    }
    
    vi.mocked(useErrorHandler).mockReturnValue(mockErrorHandler)
  })

  it('renders without errors when no notifications', () => {
    const wrapper = mount(ErrorNotificationSystem)
    expect(wrapper.exists()).toBe(true)
  })

  it('displays toast notifications', async () => {
    const toastNotification: ErrorNotification = {
      id: 'toast-1',
      type: 'toast',
      severity: 'error',
      title: 'Error Title',
      message: 'Error message',
      autoClose: true
    }

    mockNotifications.push(toastNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    expect(wrapper.find('.toast-container').exists()).toBe(true)
    expect(wrapper.text()).toContain('Error message')
  })

  it('displays banner notifications', async () => {
    const bannerNotification: ErrorNotification = {
      id: 'banner-1',
      type: 'banner',
      severity: 'warning',
      title: 'Warning Title',
      message: 'Warning message',
      autoClose: false
    }

    mockNotifications.push(bannerNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    expect(wrapper.find('.banner-container').exists()).toBe(true)
    expect(wrapper.text()).toContain('Warning message')
  })

  it('displays modal notifications', async () => {
    const modalNotification: ErrorNotification = {
      id: 'modal-1',
      type: 'modal',
      severity: 'error',
      title: 'Modal Title',
      message: 'Modal message',
      autoClose: false
    }

    mockNotifications.push(modalNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.modal-title').text()).toBe('Modal Title')
    expect(wrapper.text()).toContain('Modal message')
  })

  it('shows critical error overlay for critical errors', async () => {
    const criticalNotification: ErrorNotification = {
      id: 'critical-1',
      type: 'toast',
      severity: 'error',
      title: 'Critical Error',
      message: 'A critical error occurred',
      autoClose: false
    }

    mockNotifications.push(criticalNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    expect(wrapper.find('.critical-error-overlay').exists()).toBe(true)
    expect(wrapper.find('.critical-error-title').text()).toBe('Critical Error')
    expect(wrapper.text()).toContain('A critical error occurred')
  })

  it('dismisses notifications when dismiss is called', async () => {
    const notification: ErrorNotification = {
      id: 'test-1',
      type: 'toast',
      severity: 'info',
      title: 'Info',
      message: 'Info message',
      autoClose: false
    }

    mockNotifications.push(notification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    // Find and trigger dismiss on ErrorMessage component
    const errorMessage = wrapper.findComponent({ name: 'ErrorMessage' })
    await errorMessage.vm.$emit('dismiss')

    expect(mockErrorHandler.dismissNotification).toHaveBeenCalledWith('test-1')
  })

  it('handles modal close button click', async () => {
    const modalNotification: ErrorNotification = {
      id: 'modal-1',
      type: 'modal',
      severity: 'error',
      title: 'Modal Title',
      message: 'Modal message',
      autoClose: false
    }

    mockNotifications.push(modalNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    const closeButton = wrapper.find('.modal-close')
    await closeButton.trigger('click')

    expect(mockErrorHandler.dismissNotification).toHaveBeenCalledWith('modal-1')
  })

  it('handles modal overlay click to close', async () => {
    const modalNotification: ErrorNotification = {
      id: 'modal-1',
      type: 'modal',
      severity: 'error',
      title: 'Modal Title',
      message: 'Modal message',
      autoClose: false
    }

    mockNotifications.push(modalNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    const overlay = wrapper.find('.modal-overlay')
    await overlay.trigger('click')

    expect(mockErrorHandler.dismissNotification).toHaveBeenCalledWith('modal-1')
  })

  it('limits toast notifications to maxToastNotifications', async () => {
    // Add more notifications than the limit
    for (let i = 0; i < 10; i++) {
      mockNotifications.push({
        id: `toast-${i}`,
        type: 'toast',
        severity: 'info',
        title: `Toast ${i}`,
        message: `Message ${i}`,
        autoClose: true
      })
    }

    const wrapper = mount(ErrorNotificationSystem, {
      props: {
        maxToastNotifications: 3
      }
    })
    await nextTick()

    const toastMessages = wrapper.findAllComponents({ name: 'ErrorMessage' })
    expect(toastMessages.length).toBeLessThanOrEqual(3)
  })

  it('shows network status indicator when offline', async () => {
    // Mock network status as offline
    const mockNetworkStatus = {
      isOnline: { value: false },
      testConnectivity: vi.fn()
    }
    
    vi.doMock('@/composables/useNetworkStatus', () => ({
      useNetworkStatus: () => mockNetworkStatus
    }))

    const wrapper = mount(ErrorNotificationSystem, {
      props: {
        showNetworkStatus: true
      }
    })
    await nextTick()

    expect(wrapper.find('.network-status-indicator').exists()).toBe(true)
    expect(wrapper.text()).toContain('Offline')
  })

  it('handles critical error actions', async () => {
    const criticalNotification: ErrorNotification = {
      id: 'critical-1',
      type: 'toast',
      severity: 'error',
      title: 'Critical Error',
      message: 'A critical error occurred',
      autoClose: false
    }

    mockNotifications.push(criticalNotification)
    
    // Mock window.location.reload
    const mockReload = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true
    })

    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    const reloadButton = wrapper.find('.critical-error-button--primary')
    await reloadButton.trigger('click')

    expect(mockReload).toHaveBeenCalled()
  })

  it('shows technical details when requested', async () => {
    const criticalNotification: ErrorNotification = {
      id: 'critical-1',
      type: 'toast',
      severity: 'error',
      title: 'Critical Error',
      message: 'A critical error occurred',
      autoClose: false,
      // Add technical details
      actions: []
    }

    // Add technical details to the notification
    ;(criticalNotification as any).technicalDetails = { stack: 'Error stack trace' }

    mockNotifications.push(criticalNotification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    const showDetailsButton = wrapper.find('.critical-error-button--tertiary')
    await showDetailsButton.trigger('click')

    expect(wrapper.find('.technical-details').exists()).toBe(true)
  })

  it('handles notification actions', async () => {
    const mockAction = vi.fn()
    const notification: ErrorNotification = {
      id: 'action-test',
      type: 'toast',
      severity: 'warning',
      title: 'Action Test',
      message: 'Test message',
      autoClose: false,
      actions: [{
        label: 'Test Action',
        action: mockAction,
        style: 'primary'
      }]
    }

    mockNotifications.push(notification)
    const wrapper = mount(ErrorNotificationSystem)
    await nextTick()

    const errorMessage = wrapper.findComponent({ name: 'ErrorMessage' })
    await errorMessage.vm.$emit('action', notification.actions![0])

    expect(mockAction).toHaveBeenCalled()
  })
})
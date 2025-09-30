// Test setup file for Vitest
import { vi } from 'vitest'
import '@testing-library/jest-dom'

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    DEV: true,
    VITE_API_BASE_URL: 'http://localhost:8080',
    VITE_COGNITO_USER_POOL_ID: 'test-pool-id',
    VITE_COGNITO_CLIENT_ID: 'test-client-id',
    VITE_MBTI_TEST_URL: 'https://www.16personalities.com'
  }
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('localStorage', localStorageMock)

// Mock navigator
Object.defineProperty(window, 'navigator', {
  value: {
    onLine: true
  },
  writable: true
})

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: ''
})

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    pathname: '/',
    protocol: 'http:'
  },
  writable: true
})
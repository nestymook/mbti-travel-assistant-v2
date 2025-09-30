# Developer Guide

This comprehensive guide provides everything developers need to know to work effectively with the MBTI Travel Web Frontend project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Architecture Overview](#architecture-overview)
- [Code Standards](#code-standards)
- [Testing Strategy](#testing-strategy)
- [Performance Guidelines](#performance-guidelines)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 18+** and **npm 9+**
- **Git** for version control
- **VS Code** (recommended) with suggested extensions
- **AWS CLI** (for deployment)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd mbti-travel-web-frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.development

# Start development server
npm run dev
```

### VS Code Extensions

Install these recommended extensions for the best development experience:

```json
{
  "recommendations": [
    "vue.volar",
    "vue.vscode-typescript-vue-plugin",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

### Project Structure Deep Dive

```
src/
├── components/           # Vue components
│   ├── common/          # Reusable UI components
│   │   ├── LoadingSpinner.vue
│   │   ├── ErrorMessage.vue
│   │   ├── VirtualScrollList.vue
│   │   └── LazyComponent.vue
│   ├── input/           # MBTI input components
│   │   ├── MBTIInputForm.vue
│   │   ├── DebouncedMBTIInput.vue
│   │   └── ValidationMessage.vue
│   └── itinerary/       # Itinerary display components
│       ├── ItineraryHeader.vue
│       ├── ItineraryTable.vue
│       ├── ItineraryPointForm.vue
│       ├── RecommendationComboBox.vue
│       └── PersonalityCustomizations.vue
├── views/               # Page-level components
│   ├── InputPage.vue
│   ├── ItineraryPage.vue
│   └── LoginPage.vue
├── services/            # Business logic and API services
│   ├── authService.ts
│   ├── apiService.ts
│   ├── themeService.ts
│   └── validationService.ts
├── stores/              # Pinia state management
│   ├── authStore.ts
│   ├── itineraryStore.ts
│   └── themeStore.ts
├── types/               # TypeScript type definitions
│   ├── api.ts
│   ├── mbti.ts
│   ├── restaurant.ts
│   └── touristSpot.ts
├── composables/         # Vue composition functions
│   ├── useTheme.ts
│   ├── useErrorHandler.ts
│   ├── usePerformanceOptimizations.ts
│   └── useDebouncedApi.ts
├── utils/               # Utility functions
│   ├── constants.ts
│   ├── helpers.ts
│   ├── formatters.ts
│   └── performance.ts
├── styles/              # CSS and styling
│   ├── main.css
│   ├── themes/
│   └── components/
├── router/              # Vue Router configuration
│   └── index.ts
├── config/              # Configuration files
│   ├── environment.ts
│   └── auth.ts
└── __tests__/           # Test files
    ├── unit/
    ├── integration/
    ├── e2e/
    └── accessibility/
```

## Development Workflow

### Branch Strategy

We follow a Git Flow branching model:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Individual feature branches
- **hotfix/***: Critical production fixes
- **release/***: Release preparation branches

### Feature Development Process

1. **Create Feature Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. **Development**
```bash
# Start development server
npm run dev

# Run tests in watch mode
npm run test:watch

# Check types continuously
npm run type-check -- --watch
```

3. **Code Quality Checks**
```bash
# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Run all tests
npm run test

# Check test coverage
npm run test:coverage
```

4. **Commit Changes**
```bash
# Stage changes
git add .

# Commit with conventional commit format
git commit -m "feat: add MBTI personality theme customization"
```

5. **Create Pull Request**
```bash
git push origin feature/your-feature-name
# Create PR through GitHub interface
```

### Conventional Commits

Use conventional commit format for all commits:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(auth): implement JWT token refresh logic"
git commit -m "fix(api): handle network timeout errors gracefully"
git commit -m "docs: update API integration guide"
git commit -m "perf(components): optimize virtual scrolling performance"
```

## Architecture Overview

### Component Architecture

The application follows a hierarchical component structure:

```
App.vue
├── Router View
    ├── InputPage.vue
    │   ├── MBTIInputForm.vue
    │   │   ├── DebouncedMBTIInput.vue
    │   │   └── ValidationMessage.vue
    │   └── LoadingSpinner.vue
    └── ItineraryPage.vue
        ├── ItineraryHeader.vue
        ├── ItineraryTable.vue (or ItineraryPointForm.vue)
        │   └── RecommendationComboBox.vue
        ├── PersonalityCustomizations.vue
        └── ErrorMessage.vue
```

### State Management

We use Pinia for state management with the following stores:

#### Auth Store
```typescript
// stores/authStore.ts
export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const currentToken = ref<string | null>(null)
  const user = ref<any>(null)

  const initialize = async () => { /* ... */ }
  const getToken = async () => { /* ... */ }
  const signOut = async () => { /* ... */ }

  return {
    isAuthenticated: readonly(isAuthenticated),
    currentToken: readonly(currentToken),
    user: readonly(user),
    initialize,
    getToken,
    signOut
  }
})
```

#### Itinerary Store
```typescript
// stores/itineraryStore.ts
export const useItineraryStore = defineStore('itinerary', () => {
  const currentItinerary = ref<ItineraryResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const generateItinerary = async (request: ItineraryRequest) => { /* ... */ }
  const updateSelection = (selection: SelectionUpdate) => { /* ... */ }
  const clearItinerary = () => { /* ... */ }

  return {
    currentItinerary: readonly(currentItinerary),
    isLoading: readonly(isLoading),
    error: readonly(error),
    generateItinerary,
    updateSelection,
    clearItinerary
  }
})
```

#### Theme Store
```typescript
// stores/themeStore.ts
export const useThemeStore = defineStore('theme', () => {
  const currentPersonality = ref<MBTIPersonality | null>(null)
  const currentTheme = ref<PersonalityTheme | null>(null)

  const applyPersonalityTheme = (personality: MBTIPersonality) => { /* ... */ }
  const resetTheme = () => { /* ... */ }

  return {
    currentPersonality: readonly(currentPersonality),
    currentTheme: readonly(currentTheme),
    applyPersonalityTheme,
    resetTheme
  }
})
```

### Service Layer

Services handle business logic and external integrations:

#### API Service Pattern
```typescript
// services/baseService.ts
export abstract class BaseService {
  protected client: AxiosInstance

  constructor(baseURL: string) {
    this.client = axios.create({ baseURL })
    this.setupInterceptors()
  }

  protected abstract setupInterceptors(): void
  protected abstract handleError(error: AxiosError): Error
}

// services/apiService.ts
export class ApiService extends BaseService {
  async generateItinerary(request: ItineraryRequest): Promise<ItineraryResponse> {
    try {
      const response = await this.client.post<ItineraryResponse>('/generate-itinerary', request)
      return response.data
    } catch (error) {
      throw this.handleError(error as AxiosError)
    }
  }

  protected setupInterceptors(): void {
    // Request interceptor for auth
    this.client.interceptors.request.use(async (config) => {
      const authStore = useAuthStore()
      const token = await authStore.getToken()
      config.headers.Authorization = `Bearer ${token}`
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.handleError(error))
    )
  }

  protected handleError(error: AxiosError): Error {
    if (!error.response) {
      return new NetworkError('Network connection failed')
    }
    return new ApiError(error.response.data?.message || 'API request failed', error.response.status)
  }
}
```

## Code Standards

### TypeScript Guidelines

#### Type Definitions
```typescript
// Always define interfaces for complex objects
interface ComponentProps {
  /** Required prop with JSDoc description */
  requiredProp: string
  /** Optional prop with default value */
  optionalProp?: boolean
  /** Union type for specific values */
  variant?: 'primary' | 'secondary' | 'danger'
  /** Generic type for flexibility */
  data?: Record<string, any>
}

// Use type aliases for unions
type MBTIPersonality = 
  | 'INTJ' | 'INTP' | 'ENTJ' | 'ENTP'
  | 'INFJ' | 'INFP' | 'ENFJ' | 'ENFP'
  | 'ISTJ' | 'ISFJ' | 'ESTJ' | 'ESFJ'
  | 'ISTP' | 'ISFP' | 'ESTP' | 'ESFP'

// Use enums for constants
enum LoadingState {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error'
}
```

#### Generic Types
```typescript
// Generic service interface
interface ApiResponse<T> {
  data: T
  metadata: {
    requestId: string
    timestamp: string
  }
  error?: {
    code: string
    message: string
  }
}

// Generic composable
function useAsyncData<T>(
  fetcher: () => Promise<T>,
  options?: {
    immediate?: boolean
    onError?: (error: Error) => void
  }
) {
  const data = ref<T | null>(null)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const execute = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      data.value = await fetcher()
    } catch (err) {
      error.value = err as Error
      options?.onError?.(err as Error)
    } finally {
      isLoading.value = false
    }
  }

  return {
    data: readonly(data),
    isLoading: readonly(isLoading),
    error: readonly(error),
    execute
  }
}
```

### Vue Component Guidelines

#### Composition API Pattern
```vue
<template>
  <div class="component-name" :class="componentClasses">
    <slot name="header" :data="headerData" />
    
    <div class="component-name__content">
      <slot :data="slotData" />
    </div>
    
    <slot name="footer" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits, defineSlots } from 'vue'

// Props interface
interface Props {
  modelValue: string
  variant?: 'primary' | 'secondary'
  disabled?: boolean
}

// Emits interface
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

// Slots interface
interface Slots {
  header(props: { data: any }): any
  default(props: { data: any }): any
  footer(): any
}

// Define props with defaults
const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  disabled: false
})

// Define emits
const emit = defineEmits<Emits>()

// Define slots (for TypeScript support)
defineSlots<Slots>()

// Computed properties
const componentClasses = computed(() => ({
  [`component-name--${props.variant}`]: true,
  'component-name--disabled': props.disabled
}))

const headerData = computed(() => ({
  title: 'Component Header',
  variant: props.variant
}))

const slotData = computed(() => ({
  value: props.modelValue,
  disabled: props.disabled
}))

// Methods
const handleChange = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped>
.component-name {
  /* Base styles */
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.component-name--primary {
  /* Primary variant styles */
  background-color: var(--color-primary);
}

.component-name--secondary {
  /* Secondary variant styles */
  background-color: var(--color-secondary);
}

.component-name--disabled {
  /* Disabled state styles */
  opacity: 0.5;
  pointer-events: none;
}

.component-name__content {
  /* Content area styles */
  flex: 1;
}

/* Responsive design */
@media (min-width: 768px) {
  .component-name {
    flex-direction: row;
  }
}
</style>
```

#### Composable Pattern
```typescript
// composables/useFormValidation.ts
export function useFormValidation<T extends Record<string, any>>(
  initialValues: T,
  validationRules: Record<keyof T, (value: any) => string | null>
) {
  const values = ref<T>({ ...initialValues })
  const errors = ref<Partial<Record<keyof T, string>>>({})
  const isValid = ref(false)

  const validate = (field?: keyof T) => {
    const fieldsToValidate = field ? [field] : Object.keys(validationRules) as (keyof T)[]
    
    fieldsToValidate.forEach(fieldName => {
      const rule = validationRules[fieldName]
      const error = rule(values.value[fieldName])
      
      if (error) {
        errors.value[fieldName] = error
      } else {
        delete errors.value[fieldName]
      }
    })
    
    isValid.value = Object.keys(errors.value).length === 0
  }

  const setValue = (field: keyof T, value: any) => {
    values.value[field] = value
    validate(field)
  }

  const reset = () => {
    values.value = { ...initialValues }
    errors.value = {}
    isValid.value = false
  }

  // Validate on initialization
  validate()

  return {
    values: readonly(values),
    errors: readonly(errors),
    isValid: readonly(isValid),
    setValue,
    validate,
    reset
  }
}

// Usage in component
const { values, errors, isValid, setValue } = useFormValidation(
  { mbtiCode: '', email: '' },
  {
    mbtiCode: (value: string) => {
      if (!value) return 'MBTI code is required'
      if (!/^[A-Z]{4}$/.test(value)) return 'Invalid MBTI format'
      return null
    },
    email: (value: string) => {
      if (!value) return 'Email is required'
      if (!/\S+@\S+\.\S+/.test(value)) return 'Invalid email format'
      return null
    }
  }
)
```

### CSS Guidelines

#### BEM Methodology
```css
/* Block */
.itinerary-table {
  display: table;
  width: 100%;
  border-collapse: collapse;
}

/* Element */
.itinerary-table__header {
  background-color: var(--color-primary);
  color: white;
  font-weight: bold;
}

.itinerary-table__cell {
  padding: 1rem;
  border: 1px solid var(--color-border);
  text-align: left;
}

.itinerary-table__combo-box {
  width: 100%;
  min-height: 2.5rem;
}

/* Modifier */
.itinerary-table--compact {
  font-size: 0.875rem;
}

.itinerary-table--compact .itinerary-table__cell {
  padding: 0.5rem;
}

.itinerary-table__cell--highlighted {
  background-color: var(--color-highlight);
}

/* State */
.itinerary-table.is-loading {
  opacity: 0.6;
  pointer-events: none;
}

.itinerary-table__cell.is-selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(var(--color-primary-rgb), 0.2);
}
```

#### CSS Custom Properties
```css
:root {
  /* Color system */
  --color-primary: #3498db;
  --color-primary-rgb: 52, 152, 219;
  --color-secondary: #2ecc71;
  --color-accent: #e74c3c;
  --color-background: #f8f9fa;
  --color-surface: #ffffff;
  --color-text: #2c3e50;
  --color-text-muted: #6c757d;
  --color-border: #dee2e6;
  --color-error: #dc3545;
  --color-warning: #ffc107;
  --color-success: #28a745;
  
  /* Typography */
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-family-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  --spacing-3xl: 4rem;
  
  /* Layout */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 0.75rem;
  --border-radius-xl: 1rem;
  --border-width: 1px;
  --border-width-thick: 2px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
  --transition-slow: 500ms ease;
  
  /* Z-index scale */
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-fixed: 1030;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #1a1a1a;
    --color-surface: #2d2d2d;
    --color-text: #ffffff;
    --color-text-muted: #a0a0a0;
    --color-border: #404040;
  }
}
```

## Testing Strategy

### Unit Testing

#### Component Testing
```typescript
// src/components/__tests__/MBTIInputForm.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import MBTIInputForm from '@/components/input/MBTIInputForm.vue'

describe('MBTIInputForm', () => {
  const createWrapper = (props = {}) => {
    return mount(MBTIInputForm, {
      props: {
        modelValue: '',
        ...props
      },
      global: {
        plugins: [createTestingPinia({ createSpy: vi.fn })]
      }
    })
  }

  it('renders correctly', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('[data-testid="mbti-input"]').exists()).toBe(true)
  })

  it('validates MBTI input correctly', async () => {
    const wrapper = createWrapper()
    const input = wrapper.find('input')
    
    await input.setValue('ENFP')
    expect(wrapper.emitted('validation-change')).toEqual([[true]])
    
    await input.setValue('INVALID')
    expect(wrapper.emitted('validation-change')).toEqual([[true], [false]])
  })

  it('emits submit event with valid input', async () => {
    const wrapper = createWrapper()
    const form = wrapper.find('form')
    const input = wrapper.find('input')
    
    await input.setValue('INTJ')
    await form.trigger('submit')
    
    expect(wrapper.emitted('submit')).toEqual([['INTJ']])
  })

  it('shows loading state correctly', async () => {
    const wrapper = createWrapper({ isLoading: true })
    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('displays error message', async () => {
    const errorMessage = 'Invalid MBTI code'
    const wrapper = createWrapper({ errorMessage })
    expect(wrapper.text()).toContain(errorMessage)
  })
})
```

#### Service Testing
```typescript
// src/services/__tests__/apiService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { ApiService, ApiError, NetworkError } from '@/services/apiService'

vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('ApiService', () => {
  let apiService: ApiService

  beforeEach(() => {
    vi.clearAllMocks()
    apiService = new ApiService('http://localhost:3000')
  })

  it('generates itinerary successfully', async () => {
    const mockResponse = {
      data: {
        main_itinerary: { /* mock data */ },
        candidate_tourist_spots: { /* mock data */ },
        candidate_restaurants: { /* mock data */ }
      }
    }

    mockedAxios.create.mockReturnValue({
      post: vi.fn().mockResolvedValue(mockResponse)
    } as any)

    const request = { mbti_personality: 'ENFP' }
    const result = await apiService.generateItinerary(request)

    expect(result).toEqual(mockResponse.data)
  })

  it('handles API errors correctly', async () => {
    const mockError = {
      response: {
        status: 400,
        data: { message: 'Invalid request' }
      }
    }

    mockedAxios.create.mockReturnValue({
      post: vi.fn().mockRejectedValue(mockError)
    } as any)

    const request = { mbti_personality: 'INVALID' }
    
    await expect(apiService.generateItinerary(request))
      .rejects.toThrow(ApiError)
  })

  it('handles network errors correctly', async () => {
    const mockError = { message: 'Network Error' }

    mockedAxios.create.mockReturnValue({
      post: vi.fn().mockRejectedValue(mockError)
    } as any)

    const request = { mbti_personality: 'ENFP' }
    
    await expect(apiService.generateItinerary(request))
      .rejects.toThrow(NetworkError)
  })
})
```

### Integration Testing

```typescript
// src/__tests__/integration/auth-flow.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import App from '@/App.vue'
import { routes } from '@/router'

describe('Authentication Flow Integration', () => {
  let router: any
  let wrapper: any

  beforeEach(async () => {
    router = createRouter({
      history: createWebHistory(),
      routes
    })

    wrapper = mount(App, {
      global: {
        plugins: [
          router,
          createTestingPinia({ createSpy: vi.fn })
        ]
      }
    })

    await router.isReady()
  })

  it('redirects to login when not authenticated', async () => {
    await router.push('/itinerary')
    await wrapper.vm.$nextTick()
    
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('allows access to protected routes when authenticated', async () => {
    // Mock authentication
    const authStore = useAuthStore()
    authStore.isAuthenticated = true
    authStore.currentToken = 'mock-token'

    await router.push('/itinerary')
    await wrapper.vm.$nextTick()
    
    expect(router.currentRoute.value.path).toBe('/itinerary')
  })
})
```

### E2E Testing

```typescript
// src/__tests__/e2e/user-journey.test.ts
import { test, expect } from '@playwright/test'

test.describe('MBTI Travel Planner User Journey', () => {
  test('complete user flow from input to itinerary', async ({ page }) => {
    // Navigate to application
    await page.goto('/')
    
    // Verify landing page
    await expect(page.locator('h1')).toContainText('Hong Kong MBTI Travel Planner')
    
    // Input MBTI personality
    await page.fill('[data-testid="mbti-input"]', 'ENFP')
    await page.click('[data-testid="generate-button"]')
    
    // Wait for loading to complete
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible()
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible({ timeout: 120000 })
    
    // Verify itinerary page
    await expect(page.locator('h2')).toContainText('3-Day Itinerary for ENFP Personality')
    
    // Test combo box interaction
    await page.click('[data-testid="restaurant-combo-box"]')
    await page.click('[data-testid="restaurant-option-1"]')
    
    // Verify selection updated
    await expect(page.locator('[data-testid="selected-restaurant"]')).toContainText('Alternative Restaurant')
    
    // Test back navigation
    await page.click('[data-testid="back-button"]')
    await expect(page.locator('h1')).toContainText('Hong Kong MBTI Travel Planner')
  })

  test('handles validation errors correctly', async ({ page }) => {
    await page.goto('/')
    
    // Try invalid input
    await page.fill('[data-testid="mbti-input"]', 'INVALID')
    await page.click('[data-testid="generate-button"]')
    
    // Verify error message
    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText('Please input correct MBTI Personality!')
  })

  test('responsive design works correctly', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    
    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible()
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible()
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible()
  })
})
```

## Performance Guidelines

### Code Splitting

```typescript
// router/index.ts - Route-based code splitting
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Input',
    component: () => import('@/views/InputPage.vue')
  },
  {
    path: '/itinerary',
    name: 'Itinerary',
    component: () => import('@/views/ItineraryPage.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue')
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
```

### Lazy Loading Components

```vue
<template>
  <div>
    <!-- Lazy load heavy components -->
    <Suspense>
      <template #default>
        <HeavyComponent v-if="showHeavyComponent" />
      </template>
      <template #fallback>
        <LoadingSpinner />
      </template>
    </Suspense>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

// Lazy load heavy component
const HeavyComponent = defineAsyncComponent({
  loader: () => import('@/components/HeavyComponent.vue'),
  delay: 200,
  timeout: 3000,
  errorComponent: () => import('@/components/common/ErrorMessage.vue'),
  loadingComponent: LoadingSpinner
})
</script>
```

### Performance Monitoring

```typescript
// composables/usePerformanceMonitoring.ts
export function usePerformanceMonitoring() {
  const measureComponentRender = (componentName: string) => {
    const startTime = performance.now()
    
    onMounted(() => {
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      console.log(`[PERF] ${componentName} render time: ${renderTime.toFixed(2)}ms`)
      
      // Send to analytics if enabled
      if (environment.features.analytics) {
        // Analytics implementation
      }
    })
  }

  const measureApiCall = async <T>(
    apiCall: () => Promise<T>,
    endpoint: string
  ): Promise<T> => {
    const startTime = performance.now()
    
    try {
      const result = await apiCall()
      const endTime = performance.now()
      const duration = endTime - startTime
      
      console.log(`[PERF] API call ${endpoint}: ${duration.toFixed(2)}ms`)
      
      return result
    } catch (error) {
      const endTime = performance.now()
      const duration = endTime - startTime
      
      console.log(`[PERF] API call ${endpoint} failed: ${duration.toFixed(2)}ms`)
      throw error
    }
  }

  return {
    measureComponentRender,
    measureApiCall
  }
}
```

## Security Best Practices

### Input Sanitization

```typescript
// utils/sanitization.ts
export class InputSanitizer {
  /**
   * Sanitize MBTI personality input
   */
  static sanitizeMBTI(input: string): string {
    return input
      .trim()
      .toUpperCase()
      .replace(/[^A-Z]/g, '')
      .slice(0, 4)
  }

  /**
   * Sanitize HTML content
   */
  static sanitizeHtml(input: string): string {
    const div = document.createElement('div')
    div.textContent = input
    return div.innerHTML
  }

  /**
   * Validate and sanitize URL
   */
  static sanitizeUrl(url: string): string | null {
    try {
      const parsed = new URL(url)
      const allowedProtocols = ['http:', 'https:']
      
      if (!allowedProtocols.includes(parsed.protocol)) {
        return null
      }
      
      return parsed.toString()
    } catch {
      return null
    }
  }

  /**
   * Sanitize user preferences
   */
  static sanitizePreferences(preferences: any): any {
    const allowedBudgets = ['low', 'medium', 'high']
    const allowedInterests = [
      'culture', 'food', 'nightlife', 'nature',
      'shopping', 'history', 'art', 'sports'
    ]

    return {
      budget: allowedBudgets.includes(preferences?.budget) 
        ? preferences.budget 
        : 'medium',
      interests: Array.isArray(preferences?.interests)
        ? preferences.interests
            .filter(i => allowedInterests.includes(i))
            .slice(0, 10)
        : [],
      dietary_restrictions: Array.isArray(preferences?.dietary_restrictions)
        ? preferences.dietary_restrictions
            .map(r => this.sanitizeHtml(r))
            .slice(0, 5)
        : []
    }
  }
}
```

### Content Security Policy

```typescript
// utils/csp.ts
export const generateCSPHeader = (environment: string): string => {
  const basePolicy = {
    'default-src': ["'self'"],
    'script-src': [
      "'self'",
      "'unsafe-inline'", // Required for Vue development
      'https://www.googletagmanager.com'
    ],
    'style-src': [
      "'self'",
      "'unsafe-inline'", // Required for dynamic styling
      'https://fonts.googleapis.com'
    ],
    'font-src': [
      "'self'",
      'https://fonts.gstatic.com'
    ],
    'img-src': [
      "'self'",
      'data:',
      'https:'
    ],
    'connect-src': [
      "'self'",
      environment === 'production' 
        ? 'https://api.mbti-travel.com'
        : 'http://localhost:*'
    ],
    'frame-ancestors': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"]
  }

  return Object.entries(basePolicy)
    .map(([directive, sources]) => `${directive} ${sources.join(' ')}`)
    .join('; ')
}
```

## Troubleshooting

### Common Development Issues

#### 1. TypeScript Errors

**Problem**: Type errors in components
**Solution**:
```bash
# Check TypeScript configuration
npx vue-tsc --noEmit

# Update Vue TypeScript plugin
npm update @vue/typescript-plugin

# Clear TypeScript cache
rm -rf node_modules/.cache
```

#### 2. Hot Module Replacement Issues

**Problem**: HMR not working in development
**Solution**:
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    hmr: {
      overlay: false // Disable error overlay if needed
    }
  }
})
```

#### 3. Build Performance Issues

**Problem**: Slow build times
**Solution**:
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          utils: ['axios', 'lodash-es']
        }
      }
    }
  }
})
```

#### 4. Memory Issues

**Problem**: Out of memory during build
**Solution**:
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### Debugging Tools

#### Vue DevTools Setup

```typescript
// main.ts
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)

// Enable Vue DevTools in development
if (import.meta.env.DEV) {
  app.config.performance = true
}

app.mount('#app')
```

#### Debug Utilities

```typescript
// utils/debug.ts
export class DebugUtils {
  static logComponentRender(componentName: string, props: any) {
    if (import.meta.env.DEV) {
      console.group(`🔄 ${componentName} Render`)
      console.log('Props:', props)
      console.log('Timestamp:', new Date().toISOString())
      console.groupEnd()
    }
  }

  static logApiCall(endpoint: string, request: any, response: any) {
    if (import.meta.env.DEV) {
      console.group(`🌐 API Call: ${endpoint}`)
      console.log('Request:', request)
      console.log('Response:', response)
      console.log('Timestamp:', new Date().toISOString())
      console.groupEnd()
    }
  }

  static logStateChange(storeName: string, oldState: any, newState: any) {
    if (import.meta.env.DEV) {
      console.group(`📦 State Change: ${storeName}`)
      console.log('Old State:', oldState)
      console.log('New State:', newState)
      console.log('Timestamp:', new Date().toISOString())
      console.groupEnd()
    }
  }
}
```

---

This comprehensive developer guide provides all the essential information and best practices for working effectively with the MBTI Travel Web Frontend project. It covers everything from basic setup to advanced debugging techniques, ensuring developers can contribute effectively to the project.
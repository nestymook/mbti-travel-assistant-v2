# MBTI Travel Web Frontend

A Vue 3 + TypeScript web application that provides an interactive interface for the MBTI Travel Assistant, delivering personalized 3-day Hong Kong travel itineraries based on MBTI personality types.

## 🚀 **BACKEND DEPLOYED TO AWS AGENTCORE** ✅

**Backend Status**: FULLY OPERATIONAL  
**Agent ARN**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_assistant_mcp-skv6fd785E`  
**Authentication**: JWT with Cognito User Pool `us-east-1_wBAxW7yd4`  
**Model**: Amazon Nova Pro 300K  
**Ready for Frontend Integration**: ✅

## 🌟 Features

- **Personality-Driven UI**: Dynamic interface customizations for all 16 MBTI personality types
- **Interactive Itinerary Planning**: 3-day × 6-session travel itineraries with alternative recommendations
- **Real-time Validation**: MBTI input validation with user-friendly feedback
- **Responsive Design**: Mobile-first design that works across all devices
- **JWT Authentication**: Secure authentication with AWS Cognito integration
- **Performance Optimized**: Code splitting, lazy loading, and virtual scrolling
- **Accessibility Compliant**: WCAG 2.1 AA compliant with full keyboard navigation

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- AWS account with Cognito User Pool configured
- Access to MBTI Travel Assistant MCP backend service

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mbti-travel-web-frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.development

# Configure environment variables (see Configuration section)
# Edit .env.development with your settings

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

## 📋 Configuration

### Environment Variables

Create `.env.development` file with the following variables:

```env
# API Configuration - ✅ DEPLOYED BACKEND
VITE_API_BASE_URL=https://bedrock-agentcore.us-east-1.amazonaws.com/runtime/mbti_travel_assistant_mcp-skv6fd785E
VITE_API_TIMEOUT=100000

# Authentication (AWS Cognito) - ✅ CONFIGURED
VITE_COGNITO_USER_POOL_ID=us-east-1_wBAxW7yd4
VITE_COGNITO_CLIENT_ID=26k0pnja579pdpb1pt6savs27e
VITE_COGNITO_DOMAIN=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wBAxW7yd4

# External Services
VITE_MBTI_TEST_URL=https://www.16personalities.com/free-personality-test

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG_MODE=true
```

### Production Configuration

For production deployment, create `.env.production`:

```env
# ✅ PRODUCTION BACKEND DEPLOYED TO AWS AGENTCORE
VITE_API_BASE_URL=https://bedrock-agentcore.us-east-1.amazonaws.com/runtime/mbti_travel_assistant_mcp-skv6fd785E
VITE_API_TIMEOUT=60000
VITE_COGNITO_USER_POOL_ID=us-east-1_wBAxW7yd4
VITE_COGNITO_CLIENT_ID=26k0pnja579pdpb1pt6savs27e
VITE_COGNITO_DOMAIN=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wBAxW7yd4
VITE_MBTI_TEST_URL=https://www.16personalities.com/free-personality-test
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG_MODE=false
```

## 🏗️ Project Structure

```
src/
├── components/           # Vue components
│   ├── common/          # Reusable components
│   ├── input/           # MBTI input components
│   └── itinerary/       # Itinerary display components
├── views/               # Page components
├── services/            # API and business logic services
├── stores/              # Pinia state management
├── types/               # TypeScript type definitions
├── styles/              # CSS and theme files
├── utils/               # Utility functions
├── composables/         # Vue composition functions
└── router/              # Vue Router configuration
```

## 🎨 MBTI Personality Customizations

The application provides unique UI customizations for each of the 16 MBTI personality types:

### Structured Types (INTJ, ENTJ, ISTJ, ESTJ)
- Time input fields for each session
- Target start/end time planning
- ENTJ: Additional "important!" checkboxes

### Flexible Types (INTP, ISTP, ESTP)
- Point form layout instead of table
- ESTP: Flashy styling with emojis and image placeholders

### Colorful Types (ENTP, INFP, ENFP, ISFP)
- Vibrant color schemes
- Image placeholders for visual appeal
- Creative personality-focused styling

### Feeling Types (INFJ, ISFJ, ENFJ, ESFJ)
- INFJ/ISFJ: Description fields for emotional connection
- ENFJ/ESFJ: Group notes and sharing features
- ISFJ: Warm color tones

## 🛠️ Development

### Available Scripts

```bash
# Development
npm run dev              # Start development server
npm run dev:host         # Start with network access

# Building
npm run build            # Production build
npm run build:staging    # Staging build
npm run preview          # Preview production build

# Testing
npm run test             # Run unit tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Run tests with coverage
npm run test:e2e         # Run end-to-end tests

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Fix ESLint issues
npm run type-check       # TypeScript type checking
npm run format           # Format code with Prettier

# Deployment
npm run deploy:staging   # Deploy to staging
npm run deploy:prod      # Deploy to production
```

### Development Guidelines

#### Code Style
- Follow Vue 3 Composition API patterns
- Use TypeScript for all new code
- Follow ESLint and Prettier configurations
- Write comprehensive JSDoc comments

#### Component Development
```vue
<template>
  <div class="component-name" :class="componentClasses">
    <!-- Component template -->
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'

// Props interface
interface Props {
  modelValue: string
  disabled?: boolean
}

// Emits interface
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<Emits>()

// Computed properties
const componentClasses = computed(() => ({
  'component-name--disabled': props.disabled
}))
</script>

<style scoped>
.component-name {
  /* Component styles */
}
</style>
```

#### Service Development
```typescript
// services/exampleService.ts
import { ApiError, NetworkError } from '@/types/errors'

export class ExampleService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * Example service method
   * @param param - Method parameter
   * @returns Promise with result
   * @throws {ApiError} When API request fails
   * @throws {NetworkError} When network is unavailable
   */
  async exampleMethod(param: string): Promise<ExampleResult> {
    try {
      // Implementation
    } catch (error) {
      throw new ApiError('Service method failed', error)
    }
  }
}
```

### Testing Strategy

#### Unit Tests
```typescript
// Component test example
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ExampleComponent from '@/components/ExampleComponent.vue'

describe('ExampleComponent', () => {
  it('renders correctly', () => {
    const wrapper = mount(ExampleComponent, {
      props: { modelValue: 'test' }
    })
    expect(wrapper.text()).toContain('test')
  })

  it('emits update event', async () => {
    const wrapper = mount(ExampleComponent)
    await wrapper.find('input').setValue('new value')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})
```

#### Integration Tests
```typescript
// API integration test example
import { describe, it, expect, beforeEach } from 'vitest'
import { ApiService } from '@/services/apiService'

describe('ApiService Integration', () => {
  let apiService: ApiService

  beforeEach(() => {
    apiService = new ApiService('http://localhost:3000')
  })

  it('handles authentication correctly', async () => {
    // Test implementation
  })
})
```

## 🔧 API Integration

### Authentication Setup

```typescript
// services/authService.ts
import { CognitoAuth } from '@/utils/cognito'

const authService = new CognitoAuth({
  userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  clientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
  domain: import.meta.env.VITE_COGNITO_DOMAIN
})

// Get current user token
const token = await authService.getCurrentToken()

// Refresh token if needed
const refreshedToken = await authService.refreshToken()
```

### API Service Usage

```typescript
// Using the API service
import { apiService } from '@/services/apiService'

try {
  const response = await apiService.generateItinerary({
    mbtiPersonality: 'ENFP',
    preferences: {
      budget: 'medium',
      interests: ['culture', 'food']
    }
  })
  
  console.log('Itinerary:', response.main_itinerary)
} catch (error) {
  if (error instanceof ApiError) {
    // Handle API errors
    console.error('API Error:', error.message)
  } else if (error instanceof NetworkError) {
    // Handle network errors
    console.error('Network Error:', error.message)
  }
}
```

### Error Handling

```typescript
// Global error handler
import { createApp } from 'vue'
import { ErrorHandler } from '@/utils/errorHandler'

const app = createApp(App)

app.config.errorHandler = (error, instance, info) => {
  ErrorHandler.handleGlobalError(error, instance, info)
}

// Component-level error handling
import { useErrorHandler } from '@/composables/useErrorHandler'

const { handleError, clearError, error } = useErrorHandler()

try {
  await riskyOperation()
} catch (err) {
  handleError(err, 'Failed to perform operation')
}
```

## 🎨 Theme System

### MBTI Theme Configuration

```typescript
// Theme configuration for MBTI personalities
const mbtiThemes: Record<MBTIPersonality, PersonalityTheme> = {
  ENFP: {
    primary: '#ff6b6b',
    secondary: '#4ecdc4',
    accent: '#45b7d1',
    background: '#f8f9fa',
    text: '#2c3e50',
    colorful: true
  },
  INTJ: {
    primary: '#2c3e50',
    secondary: '#34495e',
    accent: '#3498db',
    background: '#ecf0f1',
    text: '#2c3e50',
    structured: true
  }
  // ... other personalities
}
```

### Using Themes in Components

```vue
<template>
  <div class="themed-component" :style="themeStyles">
    <!-- Component content -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const props = defineProps<{
  mbtiPersonality: MBTIPersonality
}>()

const { getPersonalityTheme } = useTheme()

const themeStyles = computed(() => {
  const theme = getPersonalityTheme(props.mbtiPersonality)
  return {
    '--primary-color': theme.primary,
    '--secondary-color': theme.secondary,
    '--accent-color': theme.accent,
    '--background-color': theme.background,
    '--text-color': theme.text
  }
})
</script>

<style scoped>
.themed-component {
  background-color: var(--background-color);
  color: var(--text-color);
  border: 2px solid var(--primary-color);
}
</style>
```

## 📱 Responsive Design

### Breakpoints

```css
/* CSS custom properties for breakpoints */
:root {
  --breakpoint-xs: 320px;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}

/* Media query mixins */
@media (min-width: 640px) {
  /* Small screens and up */
}

@media (min-width: 768px) {
  /* Medium screens and up */
}

@media (min-width: 1024px) {
  /* Large screens and up */
}
```

### Mobile-First Approach

```vue
<style scoped>
/* Mobile first (default) */
.itinerary-table {
  display: block;
  overflow-x: auto;
}

/* Tablet and up */
@media (min-width: 768px) {
  .itinerary-table {
    display: table;
    overflow-x: visible;
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .itinerary-table {
    max-width: 1200px;
    margin: 0 auto;
  }
}
</style>
```

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deployment

```bash
# Build for production
npm run build

# Deploy to staging
npm run deploy:staging

# Deploy to production (requires confirmation)
npm run deploy:prod
```

## 🧪 Testing

### Running Tests

```bash
# Unit tests
npm run test

# Watch mode for development
npm run test:watch

# Coverage report
npm run test:coverage

# End-to-end tests
npm run test:e2e
```

### Test Structure

```
src/__tests__/
├── unit/                # Unit tests
├── integration/         # Integration tests
├── e2e/                # End-to-end tests
├── accessibility/       # Accessibility tests
└── performance/         # Performance tests
```

## 🔍 Troubleshooting

### Common Issues

#### Authentication Issues
```bash
# Check Cognito configuration
npm run test:auth

# Verify JWT token
npm run debug:token
```

#### Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run type-check
```

#### API Connection Issues
```bash
# Test API connectivity
npm run test:api

# Check environment variables
npm run debug:env
```

### Debug Mode

Enable debug mode in development:

```env
VITE_ENABLE_DEBUG_MODE=true
```

This enables:
- Console logging for API requests
- Component render tracking
- Performance monitoring
- Error stack traces

## 📚 Documentation

### Project Documentation

- **[Component Documentation](./docs/COMPONENTS.md)** - Comprehensive guide to all Vue components with props, events, and usage examples
- **[MBTI Customizations](./docs/MBTI_CUSTOMIZATIONS.md)** - Complete documentation of personality-based UI customizations and theme system
- **[API Integration Guide](./docs/API_INTEGRATION.md)** - Authentication, error handling, and API integration best practices
- **[Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)** - Environment configuration, build process, and deployment instructions
- **[Developer Guide](./docs/DEVELOPER_GUIDE.md)** - Development workflow, architecture overview, and coding standards

### External Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [MBTI Personality Types](https://www.16personalities.com/articles/our-theory)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Workflow

1. **Setup**: Follow installation instructions
2. **Development**: Use `npm run dev` for hot reloading
3. **Testing**: Run `npm run test:watch` during development
4. **Linting**: Run `npm run lint:fix` before committing
5. **Type Checking**: Ensure `npm run type-check` passes
6. **Building**: Test with `npm run build` before PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Vue.js team for the excellent framework
- AWS team for Cognito and Bedrock services
- 16Personalities for MBTI insights
- Contributors and maintainers

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Node Version**: 18+  
**Vue Version**: 3.4+
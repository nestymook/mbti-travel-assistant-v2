# Design Document

## Overview

The MBTI Travel Web Frontend is a Vue 3 + TypeScript single-page application that provides an interactive interface for the MBTI Travel Assistant. The application will be built using modern web technologies with a focus on responsive design, accessibility, and personality-driven user experience customization.

The frontend integrates with the existing `mbti_travel_assistant_mcp` backend service, which provides comprehensive 3-day Hong Kong travel itineraries based on MBTI personality types. The application features JWT-based authentication, real-time API integration, and extensive MBTI personality-specific UI customizations.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Environment                       │
├─────────────────────────────────────────────────────────────┤
│  Vue 3 + TypeScript Application (SPA)                      │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Input Page    │  │  Itinerary Page │                  │
│  │   Component     │  │   Component     │                  │
│  └─────────────────┘  └─────────────────┘                  │
│  ┌─────────────────────────────────────────────────────────┤
│  │           Shared Services Layer                         │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  │ Auth Service│ │ API Service │ │Theme Service│       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │
│  └─────────────────────────────────────────────────────────┤
├─────────────────────────────────────────────────────────────┤
│                    HTTP/HTTPS Layer                         │
├─────────────────────────────────────────────────────────────┤
│              MBTI Travel Assistant MCP                      │
│                 (Backend Service)                           │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Frontend Framework**: Vue 3 with Composition API
- **Language**: TypeScript for type safety
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: CSS3 with CSS Variables for dynamic theming
- **HTTP Client**: Axios for API communication
- **Authentication**: JWT token handling with Cognito integration
- **Routing**: Vue Router for SPA navigation
- **State Management**: Pinia for centralized state management

### Project Structure

```
mbti-travel-web-frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── LoadingSpinner.vue
│   │   │   ├── ErrorMessage.vue
│   │   │   └── BackButton.vue
│   │   ├── input/
│   │   │   ├── MBTIInputForm.vue
│   │   │   └── ValidationMessage.vue
│   │   └── itinerary/
│   │       ├── ItineraryHeader.vue
│   │       ├── ItineraryTable.vue
│   │       ├── ItineraryPointForm.vue
│   │       ├── RecommendationComboBox.vue
│   │       ├── PersonalityCustomizations.vue
│   │       └── RestaurantDetails.vue
│   ├── views/
│   │   ├── InputPage.vue
│   │   ├── ItineraryPage.vue
│   │   └── LoginPage.vue
│   ├── services/
│   │   ├── authService.ts
│   │   ├── apiService.ts
│   │   ├── themeService.ts
│   │   └── validationService.ts
│   ├── types/
│   │   ├── api.ts
│   │   ├── mbti.ts
│   │   ├── restaurant.ts
│   │   └── touristSpot.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── itineraryStore.ts
│   │   └── themeStore.ts
│   ├── styles/
│   │   ├── main.css
│   │   ├── themes/
│   │   │   ├── mbti-themes.css
│   │   │   └── personality-colors.css
│   │   └── components/
│   │       ├── input-form.css
│   │       └── itinerary-table.css
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── formatters.ts
│   ├── router/
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Components and Interfaces

### Core Components

#### 1. InputPage.vue
**Purpose**: Main landing page for MBTI personality input
**Key Features**:
- Centered flex layout with responsive design
- MBTI input validation with real-time feedback
- Loading state management during API calls
- Integration with external MBTI test link

**Props**: None (root page component)
**Emits**: Navigation events to itinerary page

#### 2. ItineraryPage.vue
**Purpose**: Display personalized 3-day itinerary with MBTI customizations
**Key Features**:
- Dynamic header with personality highlighting
- Conditional rendering based on MBTI type (table vs. point form)
- Integration with personality-specific customizations
- Back navigation functionality

**Props**:
```typescript
interface ItineraryPageProps {
  mbtiPersonality: string;
  itineraryData: ItineraryResponse;
}
```

#### 3. MBTIInputForm.vue
**Purpose**: Reusable form component for MBTI input
**Key Features**:
- Input validation with character limits
- Real-time MBTI code validation
- Accessibility support with proper labels
- Error state management

**Props**:
```typescript
interface MBTIInputFormProps {
  modelValue: string;
  isLoading: boolean;
  errorMessage?: string;
}
```

**Emits**:
```typescript
interface MBTIInputFormEmits {
  'update:modelValue': (value: string) => void;
  'submit': (mbtiCode: string) => void;
}
```

#### 4. ItineraryTable.vue
**Purpose**: Tabular display of 3-day itinerary with combo boxes
**Key Features**:
- Dynamic table generation with 3 days × 6 sessions
- Combo box integration for alternative selections
- Personality-specific styling and customizations
- Responsive design for mobile devices

**Props**:
```typescript
interface ItineraryTableProps {
  mainItinerary: MainItinerary;
  candidateSpots: CandidateTouristSpots;
  candidateRestaurants: CandidateRestaurants;
  mbtiPersonality: string;
}
```

#### 5. RecommendationComboBox.vue
**Purpose**: Dropdown selection for tourist spots and restaurants
**Key Features**:
- Dynamic option loading from candidates
- Real-time data updates on selection change
- Accessibility support with proper ARIA labels
- Custom styling based on MBTI personality

**Props**:
```typescript
interface RecommendationComboBoxProps {
  modelValue: TouristSpot | Restaurant;
  options: (TouristSpot | Restaurant)[];
  type: 'tourist-spot' | 'restaurant';
  mbtiPersonality: string;
}
```

### Service Layer

#### 1. AuthService
**Purpose**: Handle JWT authentication and token management
**Key Methods**:
```typescript
class AuthService {
  validateToken(token: string): Promise<boolean>;
  refreshToken(): Promise<string>;
  redirectToLogin(): void;
  getCurrentUser(): UserContext | null;
  isAuthenticated(): boolean;
}
```

#### 2. ApiService
**Purpose**: HTTP client for MBTI travel assistant API integration
**Key Methods**:
```typescript
class ApiService {
  generateItinerary(request: ItineraryRequest): Promise<ItineraryResponse>;
  setAuthToken(token: string): void;
  handleApiError(error: AxiosError): ApiError;
}
```

#### 3. ThemeService
**Purpose**: Dynamic theme management based on MBTI personality
**Key Methods**:
```typescript
class ThemeService {
  applyMBTITheme(personality: string): void;
  getPersonalityColors(personality: string): PersonalityTheme;
  resetTheme(): void;
  isColorfulPersonality(personality: string): boolean;
}
```

#### 4. ValidationService
**Purpose**: MBTI input validation and business logic
**Key Methods**:
```typescript
class ValidationService {
  validateMBTICode(code: string): ValidationResult;
  getValidMBTITypes(): string[];
  formatMBTIInput(input: string): string;
}
```

## Data Models

### TypeScript Interfaces

#### Core API Types
```typescript
// Main itinerary response structure
interface ItineraryResponse {
  main_itinerary: MainItinerary;
  candidate_tourist_spots: CandidateTouristSpots;
  candidate_restaurants: CandidateRestaurants;
  metadata: ItineraryResponseMetadata;
  error?: ItineraryErrorInfo;
}

// Main itinerary structure
interface MainItinerary {
  day_1: DayItinerary;
  day_2: DayItinerary;
  day_3: DayItinerary;
}

// Daily itinerary structure
interface DayItinerary {
  morning_session: TouristSpot;
  afternoon_session: TouristSpot;
  night_session: TouristSpot;
  breakfast: Restaurant;
  lunch: Restaurant;
  dinner: Restaurant;
}

// Tourist spot data structure
interface TouristSpot {
  tourist_spot: string;
  mbti: string;
  description?: string;
  remarks?: string;
  address: string;
  district: string;
  area: string;
  operating_hours_mon_fri: string;
  operating_hours_sat_sun: string;
  operating_hours_public_holiday: string;
  full_day: boolean;
}

// Restaurant data structure
interface Restaurant {
  id: string;
  name: string;
  address: string;
  mealType: string[];
  sentiment: {
    likes: number;
    dislikes: number;
    neutral: number;
  };
  locationCategory: string;
  district: string;
  priceRange: string;
  operatingHours: {
    'Mon - Fri': string;
    'Sat - Sun': string;
    'Public Holiday': string;
  };
}
```

#### MBTI Personality Types
```typescript
type MBTIPersonality = 
  | 'INTJ' | 'INTP' | 'ENTJ' | 'ENTP'
  | 'INFJ' | 'INFP' | 'ENFJ' | 'ENFP'
  | 'ISTJ' | 'ISFJ' | 'ESTJ' | 'ESFJ'
  | 'ISTP' | 'ISFP' | 'ESTP' | 'ESFP';

// Personality categorization for UI customizations
interface PersonalityCategories {
  structured: MBTIPersonality[]; // INTJ, ENTJ, ISTJ, ESTJ
  flexible: MBTIPersonality[];   // INTP, ISTP, ESTP
  colorful: MBTIPersonality[];   // ENTP, INFP, ENFP, ISFP
  feeling: MBTIPersonality[];    // INFJ, ISFJ, ENFJ, ESFJ
}
```

#### Theme and Styling Types
```typescript
interface PersonalityTheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
  warm?: boolean;
  colorful?: boolean;
}

interface CustomizationConfig {
  showTimeInputs: boolean;
  showImportantCheckboxes: boolean;
  showPointForm: boolean;
  showDescriptions: boolean;
  showGroupNotes: boolean;
  showShareLink: boolean;
  showImages: boolean;
  useFlashyStyle: boolean;
  useWarmTones: boolean;
}
```

## Error Handling

### Error Categories and Responses

#### 1. Authentication Errors
```typescript
interface AuthError {
  type: 'auth_error';
  message: string;
  action: 'redirect_to_login' | 'refresh_token' | 'contact_support';
}
```

#### 2. Validation Errors
```typescript
interface ValidationError {
  type: 'validation_error';
  field: string;
  message: string;
  suggestedValue?: string;
}
```

#### 3. API Errors
```typescript
interface ApiError {
  type: 'api_error';
  status: number;
  message: string;
  retryable: boolean;
  retryAfter?: number;
}
```

#### 4. Network Errors
```typescript
interface NetworkError {
  type: 'network_error';
  message: string;
  offline: boolean;
}
```

### Error Handling Strategy

1. **Global Error Handler**: Centralized error handling with user-friendly messages
2. **Retry Logic**: Automatic retry for transient network errors
3. **Fallback UI**: Graceful degradation when services are unavailable
4. **Error Logging**: Client-side error logging for debugging
5. **User Feedback**: Clear error messages with actionable suggestions

## Testing Strategy

### Unit Testing
- **Framework**: Vitest for fast unit testing
- **Coverage**: All services, utilities, and complex components
- **Mocking**: API calls and external dependencies

### Component Testing
- **Framework**: Vue Test Utils with Vitest
- **Focus**: Component behavior, props, events, and rendering
- **Accessibility**: ARIA compliance and keyboard navigation

### Integration Testing
- **API Integration**: Mock API responses for different scenarios
- **Authentication Flow**: JWT token handling and refresh
- **Error Scenarios**: Network failures and invalid responses

### End-to-End Testing
- **Framework**: Playwright for cross-browser testing
- **User Flows**: Complete MBTI input to itinerary display
- **Responsive Design**: Testing across different screen sizes
- **MBTI Customizations**: Verify personality-specific UI changes

## MBTI Personality Customizations

### Customization Matrix

| MBTI Type | Time Inputs | Important Checkboxes | Point Form | Descriptions | Group Notes | Share Link | Images | Flashy Style | Warm Tones |
|-----------|-------------|---------------------|------------|--------------|-------------|------------|--------|--------------|------------|
| INTJ      | ✓           | -                   | -          | -            | -           | -          | -      | -            | -          |
| INTP      | -           | -                   | ✓          | -            | -           | -          | -      | -            | -          |
| ENTJ      | ✓           | ✓                   | -          | -            | -           | -          | -      | -            | -          |
| ENTP      | -           | -                   | -          | -            | -           | -          | ✓      | -            | -          |
| INFJ      | -           | -                   | -          | ✓            | -           | -          | -      | -            | -          |
| INFP      | -           | -                   | -          | -            | -           | -          | ✓      | -            | -          |
| ENFJ      | -           | -                   | -          | -            | ✓           | ✓          | -      | -            | -          |
| ENFP      | -           | -                   | -          | -            | -           | -          | ✓      | -            | -          |
| ISTJ      | ✓           | -                   | -          | -            | -           | -          | -      | -            | -          |
| ISFJ      | -           | -                   | -          | ✓            | -           | -          | -      | -            | ✓          |
| ESTJ      | ✓           | -                   | -          | -            | -           | -          | -      | -            | -          |
| ESFJ      | -           | -                   | -          | -            | ✓           | ✓          | -      | -            | -          |
| ISTP      | -           | -                   | ✓          | -            | -           | -          | -      | -            | -          |
| ISFP      | -           | -                   | -          | -            | -           | -          | ✓      | -            | -          |
| ESTP      | -           | -                   | ✓          | -            | -           | -          | ✓      | ✓            | -          |
| ESFP      | -           | -                   | -          | -            | -           | -          | -      | -            | -          |

### Implementation Strategy

#### 1. Dynamic Component Rendering
```typescript
// Conditional rendering based on MBTI type
const showTimeInputs = computed(() => 
  ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(mbtiPersonality.value)
);

const showPointForm = computed(() => 
  ['INTP', 'ISTP', 'ESTP'].includes(mbtiPersonality.value)
);
```

#### 2. CSS Variable Theming
```css
/* Dynamic CSS variables based on MBTI personality */
:root {
  --primary-color: var(--mbti-primary);
  --secondary-color: var(--mbti-secondary);
  --accent-color: var(--mbti-accent);
  --background-color: var(--mbti-background);
  --text-color: var(--mbti-text);
}

/* Warm tones for ISFJ */
.mbti-isfj {
  --mbti-primary: #d4a574;
  --mbti-secondary: #f4e4bc;
  --mbti-accent: #b8860b;
  --mbti-background: #fdf5e6;
  --mbti-text: #8b4513;
}
```

#### 3. Component Composition
```vue
<template>
  <div class="itinerary-container" :class="personalityClass">
    <!-- Standard table for most personalities -->
    <ItineraryTable 
      v-if="!showPointForm"
      :main-itinerary="mainItinerary"
      :candidate-spots="candidateSpots"
      :candidate-restaurants="candidateRestaurants"
      :mbti-personality="mbtiPersonality"
    />
    
    <!-- Point form for flexible personalities -->
    <ItineraryPointForm 
      v-else
      :main-itinerary="mainItinerary"
      :candidate-spots="candidateSpots"
      :candidate-restaurants="candidateRestaurants"
      :mbti-personality="mbtiPersonality"
    />
    
    <!-- Personality-specific customizations -->
    <PersonalityCustomizations
      :mbti-personality="mbtiPersonality"
      :show-time-inputs="showTimeInputs"
      :show-important-checkboxes="showImportantCheckboxes"
      :show-descriptions="showDescriptions"
      :show-group-notes="showGroupNotes"
      :show-share-link="showShareLink"
      :show-images="showImages"
    />
  </div>
</template>
```

## Performance Optimization

### Loading Strategy
1. **Code Splitting**: Route-based code splitting for faster initial load
2. **Lazy Loading**: Lazy load personality-specific components
3. **Image Optimization**: Placeholder images with lazy loading
4. **API Caching**: Cache API responses for repeated requests

### Bundle Optimization
1. **Tree Shaking**: Remove unused code from final bundle
2. **Minification**: Compress JavaScript and CSS
3. **Gzip Compression**: Server-side compression for assets
4. **CDN Integration**: Serve static assets from CDN

### Runtime Performance
1. **Virtual Scrolling**: For large lists of candidates
2. **Debounced Input**: Prevent excessive API calls during typing
3. **Memoization**: Cache computed values and expensive operations
4. **Efficient Reactivity**: Use `shallowRef` for large objects

## Security Considerations

### Authentication Security
1. **JWT Validation**: Verify token signature and expiration
2. **Token Storage**: Secure storage in httpOnly cookies
3. **CSRF Protection**: Include CSRF tokens in API requests
4. **Token Refresh**: Automatic token refresh before expiration

### API Security
1. **HTTPS Only**: All API communication over HTTPS
2. **Request Validation**: Validate all user inputs
3. **Rate Limiting**: Client-side rate limiting for API calls
4. **Error Sanitization**: Sanitize error messages to prevent information leakage

### Content Security
1. **XSS Prevention**: Sanitize all user-generated content
2. **Content Security Policy**: Strict CSP headers
3. **Input Validation**: Validate and sanitize all inputs
4. **Safe HTML Rendering**: Use Vue's built-in XSS protection

## Deployment Architecture

### Build Process
```bash
# Development build
npm run dev

# Production build
npm run build

# Type checking
npm run type-check

# Linting
npm run lint

# Testing
npm run test
```

### Environment Configuration
```typescript
// Environment-specific configuration
interface EnvironmentConfig {
  API_BASE_URL: string;
  COGNITO_USER_POOL_ID: string;
  COGNITO_CLIENT_ID: string;
  MBTI_TEST_URL: string;
  ENABLE_ANALYTICS: boolean;
}
```

### Hosting Options
1. **Static Hosting**: AWS S3 + CloudFront for global distribution
2. **CDN Integration**: CloudFront for asset caching and compression
3. **Domain Configuration**: Custom domain with SSL certificate
4. **Environment Separation**: Separate deployments for dev/staging/prod

## Accessibility and Internationalization

### Accessibility Features
1. **ARIA Labels**: Proper ARIA labels for all interactive elements
2. **Keyboard Navigation**: Full keyboard accessibility
3. **Screen Reader Support**: Semantic HTML and proper headings
4. **Color Contrast**: WCAG 2.1 AA compliant color contrast ratios
5. **Focus Management**: Proper focus management for SPA navigation

### Responsive Design
1. **Mobile First**: Mobile-first responsive design approach
2. **Breakpoints**: Standard breakpoints for tablet and desktop
3. **Touch Targets**: Minimum 44px touch targets for mobile
4. **Flexible Layouts**: CSS Grid and Flexbox for flexible layouts

### Future Internationalization
1. **Vue I18n**: Prepared for future multi-language support
2. **Text Externalization**: All text strings externalized to language files
3. **RTL Support**: CSS prepared for right-to-left languages
4. **Date/Time Formatting**: Locale-aware date and time formatting
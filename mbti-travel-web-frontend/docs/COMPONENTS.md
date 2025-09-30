# Component Documentation

This document provides comprehensive documentation for all Vue components in the MBTI Travel Web Frontend application.

## 📋 Table of Contents

- [Common Components](#common-components)
- [Input Components](#input-components)
- [Itinerary Components](#itinerary-components)
- [View Components](#view-components)
- [Component Guidelines](#component-guidelines)

## Common Components

### LoadingSpinner.vue

A reusable loading spinner component with personality-themed styling.

#### Props

```typescript
interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large'
  /** MBTI personality for themed styling */
  mbtiPersonality?: MBTIPersonality
  /** Loading message to display */
  message?: string
  /** Show estimated time */
  showEstimatedTime?: boolean
  /** Estimated time in seconds */
  estimatedTime?: number
}
```

#### Usage

```vue
<template>
  <LoadingSpinner
    size="large"
    mbti-personality="ENFP"
    message="Generating your personalized itinerary..."
    :show-estimated-time="true"
    :estimated-time="100"
  />
</template>

<script setup lang="ts">
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
</script>
```

#### Styling

The component automatically applies personality-specific colors:

```css
/* ENFP example */
.loading-spinner--enfp {
  --spinner-primary: #ff6b6b;
  --spinner-secondary: #4ecdc4;
}

/* INTJ example */
.loading-spinner--intj {
  --spinner-primary: #2c3e50;
  --spinner-secondary: #34495e;
}
```

### ErrorMessage.vue

Displays user-friendly error messages with actionable suggestions.

#### Props

```typescript
interface ErrorMessageProps {
  /** Error object or message */
  error: Error | string | null
  /** Error type for styling */
  type?: 'validation' | 'network' | 'api' | 'auth'
  /** Show retry button */
  showRetry?: boolean
  /** Show dismiss button */
  dismissible?: boolean
  /** Custom retry action */
  retryAction?: () => void
}
```

#### Emits

```typescript
interface ErrorMessageEmits {
  /** Emitted when retry button is clicked */
  (e: 'retry'): void
  /** Emitted when error is dismissed */
  (e: 'dismiss'): void
}
```

#### Usage

```vue
<template>
  <ErrorMessage
    :error="apiError"
    type="api"
    :show-retry="true"
    :dismissible="true"
    @retry="handleRetry"
    @dismiss="clearError"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ErrorMessage from '@/components/common/ErrorMessage.vue'

const apiError = ref<Error | null>(null)

const handleRetry = () => {
  // Retry logic
}

const clearError = () => {
  apiError.value = null
}
</script>
```

### VirtualScrollList.vue

High-performance virtual scrolling for large lists of candidates.

#### Props

```typescript
interface VirtualScrollListProps {
  /** Array of items to display */
  items: any[]
  /** Height of each item in pixels */
  itemHeight: number
  /** Height of the container */
  containerHeight: number
  /** Number of items to render outside visible area */
  overscan?: number
}
```

#### Slots

```typescript
interface VirtualScrollListSlots {
  /** Item template */
  item: {
    item: any
    index: number
  }
}
```

#### Usage

```vue
<template>
  <VirtualScrollList
    :items="restaurantCandidates"
    :item-height="80"
    :container-height="400"
    :overscan="5"
  >
    <template #item="{ item, index }">
      <div class="restaurant-item">
        <h3>{{ item.name }}</h3>
        <p>{{ item.address }}</p>
      </div>
    </template>
  </VirtualScrollList>
</template>
```

## Input Components

### MBTIInputForm.vue

Main form component for MBTI personality input with validation.

#### Props

```typescript
interface MBTIInputFormProps {
  /** Current MBTI value */
  modelValue: string
  /** Loading state */
  isLoading?: boolean
  /** Error message */
  errorMessage?: string
  /** Disable input */
  disabled?: boolean
  /** Show external test link */
  showTestLink?: boolean
}
```

#### Emits

```typescript
interface MBTIInputFormEmits {
  /** Emitted when input value changes */
  (e: 'update:modelValue', value: string): void
  /** Emitted when form is submitted */
  (e: 'submit', mbtiCode: string): void
  /** Emitted when validation state changes */
  (e: 'validation-change', isValid: boolean): void
}
```

#### Usage

```vue
<template>
  <MBTIInputForm
    v-model="mbtiInput"
    :is-loading="isGenerating"
    :error-message="validationError"
    :show-test-link="true"
    @submit="handleSubmit"
    @validation-change="handleValidationChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MBTIInputForm from '@/components/input/MBTIInputForm.vue'

const mbtiInput = ref('')
const isGenerating = ref(false)
const validationError = ref('')

const handleSubmit = (mbtiCode: string) => {
  // Handle form submission
}

const handleValidationChange = (isValid: boolean) => {
  // Handle validation state change
}
</script>
```

#### Validation Rules

The component validates input against these rules:

1. **Length**: Exactly 4 characters
2. **Format**: Only alphabetic characters (A-Z)
3. **Valid Types**: Must be one of 16 valid MBTI types
4. **Case**: Automatically converts to uppercase

### DebouncedMBTIInput.vue

Optimized input component with debounced validation to prevent excessive API calls.

#### Props

```typescript
interface DebouncedMBTIInputProps {
  /** Current value */
  modelValue: string
  /** Debounce delay in milliseconds */
  debounceDelay?: number
  /** Enable real-time validation */
  validateOnInput?: boolean
  /** Placeholder text */
  placeholder?: string
}
```

#### Usage

```vue
<template>
  <DebouncedMBTIInput
    v-model="mbtiCode"
    :debounce-delay="300"
    :validate-on-input="true"
    placeholder="Enter your MBTI type (e.g., ENFP)"
  />
</template>
```

## Itinerary Components

### ItineraryHeader.vue

Header component for the itinerary page with personality highlighting.

#### Props

```typescript
interface ItineraryHeaderProps {
  /** MBTI personality type */
  mbtiPersonality: MBTIPersonality
  /** Show back button */
  showBackButton?: boolean
  /** Custom title */
  customTitle?: string
}
```

#### Emits

```typescript
interface ItineraryHeaderEmits {
  /** Emitted when back button is clicked */
  (e: 'back'): void
}
```

#### Usage

```vue
<template>
  <ItineraryHeader
    :mbti-personality="userPersonality"
    :show-back-button="true"
    @back="navigateToInput"
  />
</template>

<script setup lang="ts">
import ItineraryHeader from '@/components/itinerary/ItineraryHeader.vue'

const userPersonality = ref<MBTIPersonality>('ENFP')

const navigateToInput = () => {
  router.push('/')
}
</script>
```

### ItineraryTable.vue

Main table component displaying the 3-day × 6-session itinerary.

#### Props

```typescript
interface ItineraryTableProps {
  /** Main itinerary data */
  mainItinerary: MainItinerary
  /** Candidate tourist spots */
  candidateSpots: CandidateTouristSpots
  /** Candidate restaurants */
  candidateRestaurants: CandidateRestaurants
  /** MBTI personality for styling */
  mbtiPersonality: MBTIPersonality
  /** Enable combo box selections */
  enableSelections?: boolean
}
```

#### Emits

```typescript
interface ItineraryTableEmits {
  /** Emitted when a selection changes */
  (e: 'selection-change', data: {
    day: number
    session: string
    type: 'tourist-spot' | 'restaurant'
    selection: TouristSpot | Restaurant
  }): void
}
```

#### Usage

```vue
<template>
  <ItineraryTable
    :main-itinerary="itinerary.main_itinerary"
    :candidate-spots="itinerary.candidate_tourist_spots"
    :candidate-restaurants="itinerary.candidate_restaurants"
    :mbti-personality="personality"
    :enable-selections="true"
    @selection-change="handleSelectionChange"
  />
</template>

<script setup lang="ts">
import ItineraryTable from '@/components/itinerary/ItineraryTable.vue'

const handleSelectionChange = (data) => {
  console.log('Selection changed:', data)
  // Update itinerary data
}
</script>
```

### ItineraryPointForm.vue

Alternative point-form layout for flexible personality types (INTP, ISTP, ESTP).

#### Props

```typescript
interface ItineraryPointFormProps {
  /** Main itinerary data */
  mainItinerary: MainItinerary
  /** Candidate data */
  candidateSpots: CandidateTouristSpots
  candidateRestaurants: CandidateRestaurants
  /** MBTI personality */
  mbtiPersonality: MBTIPersonality
  /** Enable flashy styling (for ESTP) */
  flashyStyle?: boolean
  /** Show image placeholders */
  showImages?: boolean
}
```

#### Usage

```vue
<template>
  <ItineraryPointForm
    :main-itinerary="itinerary.main_itinerary"
    :candidate-spots="itinerary.candidate_tourist_spots"
    :candidate-restaurants="itinerary.candidate_restaurants"
    :mbti-personality="personality"
    :flashy-style="personality === 'ESTP'"
    :show-images="personality === 'ESTP'"
  />
</template>
```

### RecommendationComboBox.vue

Dropdown component for selecting alternative recommendations.

#### Props

```typescript
interface RecommendationComboBoxProps {
  /** Current selection */
  modelValue: TouristSpot | Restaurant
  /** Available options */
  options: (TouristSpot | Restaurant)[]
  /** Type of recommendations */
  type: 'tourist-spot' | 'restaurant'
  /** MBTI personality for styling */
  mbtiPersonality: MBTIPersonality
  /** Disable selection */
  disabled?: boolean
  /** Show loading state */
  loading?: boolean
}
```

#### Emits

```typescript
interface RecommendationComboBoxEmits {
  /** Emitted when selection changes */
  (e: 'update:modelValue', value: TouristSpot | Restaurant): void
  /** Emitted when dropdown opens */
  (e: 'open'): void
  /** Emitted when dropdown closes */
  (e: 'close'): void
}
```

#### Usage

```vue
<template>
  <RecommendationComboBox
    v-model="selectedRestaurant"
    :options="restaurantOptions"
    type="restaurant"
    :mbti-personality="personality"
    @update:modelValue="handleSelectionChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import RecommendationComboBox from '@/components/itinerary/RecommendationComboBox.vue'

const selectedRestaurant = ref<Restaurant>()
const restaurantOptions = ref<Restaurant[]>([])

const handleSelectionChange = (restaurant: Restaurant) => {
  console.log('Selected restaurant:', restaurant)
}
</script>
```

### PersonalityCustomizations.vue

Container component for MBTI personality-specific customizations.

#### Props

```typescript
interface PersonalityCustomizationsProps {
  /** MBTI personality type */
  mbtiPersonality: MBTIPersonality
  /** Itinerary data */
  itineraryData: MainItinerary
  /** Show time inputs (structured types) */
  showTimeInputs?: boolean
  /** Show important checkboxes (ENTJ) */
  showImportantCheckboxes?: boolean
  /** Show descriptions (feeling types) */
  showDescriptions?: boolean
  /** Show group notes (ENFJ, ESFJ) */
  showGroupNotes?: boolean
  /** Show share link (social types) */
  showShareLink?: boolean
  /** Show image placeholders */
  showImages?: boolean
}
```

#### Usage

```vue
<template>
  <PersonalityCustomizations
    :mbti-personality="personality"
    :itinerary-data="itinerary.main_itinerary"
    :show-time-inputs="isStructuredType"
    :show-important-checkboxes="personality === 'ENTJ'"
    :show-descriptions="isFeelingType"
    :show-group-notes="isSocialType"
    :show-share-link="isSocialType"
    :show-images="isCreativeType"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PersonalityCustomizations from '@/components/itinerary/PersonalityCustomizations.vue'

const isStructuredType = computed(() => 
  ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(personality.value)
)

const isFeelingType = computed(() => 
  ['INFJ', 'ISFJ'].includes(personality.value)
)

const isSocialType = computed(() => 
  ['ENFJ', 'ESFJ'].includes(personality.value)
)

const isCreativeType = computed(() => 
  ['ENTP', 'INFP', 'ENFP', 'ISFP'].includes(personality.value)
)
</script>
```

## View Components

### InputPage.vue

Main landing page for MBTI personality input.

#### Props

```typescript
interface InputPageProps {
  /** Initial MBTI value */
  initialValue?: string
  /** Show welcome message */
  showWelcome?: boolean
}
```

#### Usage

```vue
<template>
  <InputPage
    :initial-value="savedMBTI"
    :show-welcome="isFirstVisit"
  />
</template>
```

### ItineraryPage.vue

Main itinerary display page with personality customizations.

#### Props

```typescript
interface ItineraryPageProps {
  /** MBTI personality type */
  mbtiPersonality: MBTIPersonality
  /** Itinerary data */
  itineraryData: ItineraryResponse
  /** Enable editing */
  enableEditing?: boolean
}
```

#### Usage

```vue
<template>
  <ItineraryPage
    :mbti-personality="personality"
    :itinerary-data="itinerary"
    :enable-editing="true"
  />
</template>
```

## Component Guidelines

### Naming Conventions

- **Components**: PascalCase (e.g., `MBTIInputForm.vue`)
- **Props**: camelCase (e.g., `mbtiPersonality`)
- **Events**: kebab-case (e.g., `selection-change`)
- **CSS Classes**: kebab-case with BEM (e.g., `mbti-input__field--error`)

### Props Best Practices

1. **Always define TypeScript interfaces** for props
2. **Use `withDefaults()`** for default values
3. **Mark optional props** with `?`
4. **Provide JSDoc comments** for complex props

```typescript
interface ComponentProps {
  /** Required prop with description */
  requiredProp: string
  /** Optional prop with default */
  optionalProp?: boolean
  /** Complex prop with detailed description */
  complexProp?: {
    id: string
    name: string
    config: Record<string, any>
  }
}

const props = withDefaults(defineProps<ComponentProps>(), {
  optionalProp: false,
  complexProp: () => ({ id: '', name: '', config: {} })
})
```

### Event Handling

1. **Use typed emits** with interfaces
2. **Follow Vue naming conventions** (kebab-case)
3. **Provide meaningful event data**

```typescript
interface ComponentEmits {
  /** Emitted when value changes */
  (e: 'update:modelValue', value: string): void
  /** Emitted when action is performed */
  (e: 'action-performed', data: { action: string, result: any }): void
}

const emit = defineEmits<ComponentEmits>()

// Emit with proper data
emit('action-performed', {
  action: 'submit',
  result: { success: true, data: formData }
})
```

### Styling Guidelines

1. **Use scoped styles** for component-specific CSS
2. **Leverage CSS custom properties** for theming
3. **Follow BEM methodology** for class naming
4. **Ensure responsive design**

```vue
<style scoped>
.component-name {
  /* Base styles */
  background-color: var(--background-color);
  color: var(--text-color);
}

.component-name__element {
  /* Element styles */
}

.component-name__element--modifier {
  /* Modifier styles */
}

.component-name--variant {
  /* Variant styles */
}

/* Responsive design */
@media (min-width: 768px) {
  .component-name {
    /* Tablet and up styles */
  }
}
</style>
```

### Accessibility

1. **Use semantic HTML** elements
2. **Provide ARIA labels** and descriptions
3. **Ensure keyboard navigation**
4. **Maintain proper focus management**

```vue
<template>
  <div
    class="interactive-component"
    role="button"
    :aria-label="accessibleLabel"
    :aria-describedby="descriptionId"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space="handleClick"
  >
    <span :id="descriptionId" class="sr-only">
      {{ accessibleDescription }}
    </span>
    <!-- Component content -->
  </div>
</template>
```

### Performance Optimization

1. **Use `v-memo`** for expensive renders
2. **Implement virtual scrolling** for large lists
3. **Lazy load components** when appropriate
4. **Debounce user inputs**

```vue
<template>
  <!-- Memoize expensive renders -->
  <div v-memo="[expensiveData, mbtiPersonality]">
    <ExpensiveComponent :data="expensiveData" />
  </div>

  <!-- Lazy load components -->
  <LazyComponent>
    <HeavyComponent />
  </LazyComponent>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

// Lazy load heavy components
const HeavyComponent = defineAsyncComponent(
  () => import('@/components/HeavyComponent.vue')
)
</script>
```

### Testing Components

1. **Test component behavior**, not implementation
2. **Mock external dependencies**
3. **Test accessibility features**
4. **Verify responsive behavior**

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import ComponentName from '@/components/ComponentName.vue'

describe('ComponentName', () => {
  const createWrapper = (props = {}) => {
    return mount(ComponentName, {
      props: {
        modelValue: 'test',
        ...props
      },
      global: {
        plugins: [createTestingPinia({ createSpy: vi.fn })]
      }
    })
  }

  it('renders correctly', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('[data-testid="component"]').exists()).toBe(true)
  })

  it('emits events correctly', async () => {
    const wrapper = createWrapper()
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('action-performed')).toBeTruthy()
  })

  it('handles keyboard navigation', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[role="button"]').trigger('keydown.enter')
    expect(wrapper.emitted('action-performed')).toBeTruthy()
  })
})
```

---

This component documentation provides comprehensive guidance for using and developing components in the MBTI Travel Web Frontend application. Each component is designed to be reusable, accessible, and performant while maintaining consistency with the overall design system.
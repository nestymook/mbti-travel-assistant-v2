# RecommendationComboBox Component

A fully accessible, customizable dropdown component for selecting tourist spots and restaurants in the MBTI Travel Web Frontend application.

## Features

- **Accessibility First**: Full WCAG 2.1 AA compliance with proper ARIA attributes
- **Keyboard Navigation**: Complete keyboard support including arrow keys, Enter, Space, Escape, Home, End, and character navigation
- **MBTI Personality Theming**: Dynamic styling based on 16 MBTI personality types
- **Type-Safe**: Full TypeScript support with proper type guards
- **Responsive Design**: Mobile-first design with touch-friendly interactions
- **Loading States**: Built-in loading and empty state handling
- **Real-time Updates**: Dynamic option loading and selection changes

## Usage

```vue
<template>
  <RecommendationComboBox
    v-model="selectedRestaurant"
    :options="restaurantOptions"
    type="restaurant"
    :mbti-personality="userPersonality"
    label="Select Restaurant"
    description="Choose your preferred dining option"
    placeholder="Pick a restaurant..."
    :is-loading="isLoading"
    @selection-changed="handleSelectionChange"
  />
</template>

<script setup lang="ts">
import RecommendationComboBox from '@/components/itinerary/RecommendationComboBox.vue'
import type { Restaurant } from '@/types/restaurant'
import type { MBTIPersonality } from '@/types/mbti'

const selectedRestaurant = ref<Restaurant | null>(null)
const restaurantOptions = ref<Restaurant[]>([])
const userPersonality = ref<MBTIPersonality>('ENFP')
const isLoading = ref(false)

const handleSelectionChange = (selection: Restaurant | null) => {
  console.log('Selection changed:', selection)
}
</script>
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `modelValue` | `TouristSpot \| Restaurant \| null` | Yes | - | The currently selected option |
| `options` | `(TouristSpot \| Restaurant)[]` | Yes | - | Array of available options |
| `type` | `'tourist-spot' \| 'restaurant'` | Yes | - | Type of options being displayed |
| `mbtiPersonality` | `MBTIPersonality` | Yes | - | MBTI personality type for theming |
| `label` | `string` | No | `''` | Label text for the combo box |
| `showLabel` | `boolean` | No | `true` | Whether to show the label visually |
| `description` | `string` | No | `''` | Additional description text |
| `placeholder` | `string` | No | `'Select an option...'` | Placeholder text when no selection |
| `isLoading` | `boolean` | No | `false` | Whether to show loading state |
| `errorMessage` | `string` | No | `''` | Error message to display |
| `disabled` | `boolean` | No | `false` | Whether the combo box is disabled |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `update:modelValue` | `TouristSpot \| Restaurant \| null` | Emitted when selection changes (v-model) |
| `selection-changed` | `TouristSpot \| Restaurant \| null` | Emitted when user makes a selection |
| `focus` | - | Emitted when dropdown opens |
| `blur` | - | Emitted when dropdown closes |

## Accessibility Features

### ARIA Support
- `role="listbox"` on dropdown list
- `role="option"` on each option
- `aria-expanded` indicates dropdown state
- `aria-selected` marks selected options
- `aria-labelledby` connects labels
- `aria-describedby` connects descriptions
- `aria-activedescendant` tracks focused option

### Keyboard Navigation
- **Arrow Down/Up**: Open dropdown or navigate options
- **Enter/Space**: Select option or toggle dropdown
- **Escape**: Close dropdown
- **Home/End**: Jump to first/last option
- **Character Keys**: Jump to options starting with typed character
- **Tab**: Standard focus management

### Screen Reader Support
- Semantic HTML structure
- Proper heading hierarchy
- Descriptive labels and instructions
- Status announcements for state changes

## MBTI Personality Theming

The component automatically applies personality-specific styling:

### Structured Types (INTJ, ENTJ, ISTJ, ESTJ)
- Professional, clean styling
- Neutral color palette
- Emphasis on functionality

### Flexible Types (INTP, ISTP, ESTP)
- Relaxed, approachable styling
- Green color accents
- ESTP gets flashy, bold styling

### Colorful Types (ENTP, INFP, ENFP, ISFP)
- Vibrant, creative styling
- Purple/colorful themes
- Enhanced visual appeal

### Feeling Types (INFJ, ISFJ, ENFJ, ESFJ)
- Warm, empathetic styling
- Red color accents
- ISFJ gets warm orange tones

## Data Display

### Restaurant Options
- Restaurant name as primary text
- Meal types as subtext
- District, price range, and sentiment data
- Operating hours information

### Tourist Spot Options
- Spot name as primary text
- Area as subtext
- District, MBTI match, and duration info
- Full day indicator when applicable

## Responsive Design

- Mobile-first approach
- Touch-friendly 44px minimum touch targets
- Responsive table layouts
- Optimized for various screen sizes
- High contrast mode support
- Reduced motion support

## Testing

The component includes comprehensive tests covering:
- Component rendering and props
- Accessibility compliance
- Keyboard navigation
- Option selection and events
- MBTI personality styling
- Error handling and edge cases

Run tests with:
```bash
npm test -- src/components/itinerary/__tests__/RecommendationComboBox.test.ts
```

## Demo

See `RecommendationComboBoxDemo.vue` for a complete interactive demo showcasing all features and MBTI personality variations.
---


# TouristSpotComboBoxItem Component

A specialized component for displaying tourist spot information within combo box options, designed for the MBTI Travel Web Frontend application.

## Features

- **Tourist Spot Information Display**: Name, MBTI match, location details
- **Operating Hours**: Mon-Fri, Sat-Sun, and Public Holiday schedules
- **MBTI Personality Integration**: Conditional content based on personality type
- **Category and Features**: Visual badges for spot categories and amenities
- **Responsive Design**: Mobile-optimized layout with proper touch targets
- **Personality-Specific Styling**: Dynamic theming for all 16 MBTI types

## Usage

```vue
<template>
  <TouristSpotComboBoxItem
    :tourist-spot="spotData"
    :mbti-personality="userPersonality"
    :show-detailed-info="true"
  />
</template>

<script setup lang="ts">
import TouristSpotComboBoxItem from '@/components/itinerary/TouristSpotComboBoxItem.vue'
import type { TouristSpot } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'

const spotData = ref<TouristSpot>({ /* tourist spot data */ })
const userPersonality = ref<MBTIPersonality>('ENFP')
</script>
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `touristSpot` | `TouristSpot` | Yes | - | Tourist spot data to display |
| `mbtiPersonality` | `MBTIPersonality` | Yes | - | MBTI personality type for theming |
| `showDetailedInfo` | `boolean` | No | `false` | Whether to show detailed information |

## Conditional Content

### Description Display (Feeling Types)
- **INFJ, ISFJ**: Shows description field when available
- **Other types**: Description is hidden

### Personality-Specific Styling
- **ESTP**: Flashy gradient background with bold styling
- **ISFJ**: Warm orange tones
- **Creative types (ENTP, INFP, ENFP, ISFP)**: Colorful purple gradients
- **Structured types**: Professional, clean styling

---

# TouristSpotDetails Component

A comprehensive detailed view component for displaying complete tourist spot information with MBTI personality-specific customizations.

## Features

- **Complete Information Display**: All tourist spot data with proper organization
- **MBTI Personality Matching**: Detailed explanations of why spots match personalities
- **Conditional Content**: Description for feeling types, images for creative types
- **Operating Hours**: Detailed schedules for different day types
- **Admission Information**: Free or paid admission with detailed pricing
- **Accessibility Information**: Wheelchair access and accommodation details
- **Features & Amenities**: Visual badges for available facilities
- **Responsive Design**: Mobile-first layout with collapsible sections

## Usage

```vue
<template>
  <TouristSpotDetails
    :tourist-spot="selectedSpot"
    :mbti-personality="userPersonality"
  />
</template>

<script setup lang="ts">
import TouristSpotDetails from '@/components/itinerary/TouristSpotDetails.vue'
import type { TouristSpot } from '@/types/touristSpot'
import type { MBTIPersonality } from '@/types/mbti'

const selectedSpot = ref<TouristSpot>({ /* tourist spot data */ })
const userPersonality = ref<MBTIPersonality>('ENFP')
</script>
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `touristSpot` | `TouristSpot` | Yes | - | Tourist spot data to display |
| `mbtiPersonality` | `MBTIPersonality` | Yes | - | MBTI personality type for theming |

## Content Sections

### Always Displayed
- **Header**: Spot name, MBTI match, category, and duration badges
- **Location Information**: District, area, and full address
- **Operating Hours**: Mon-Fri, Sat-Sun, and Public Holiday schedules
- **MBTI Match**: Personality match with detailed explanation

### Conditionally Displayed
- **Image Placeholder**: For creative personalities (ENTP, INFP, ENFP, ISFP, ESTP)
- **Description**: For feeling personalities (INFJ, ISFJ)
- **Additional Information**: When remarks are available
- **Features & Amenities**: When features are specified
- **Admission Information**: When admission data is available
- **Accessibility**: When accessibility information is provided

## MBTI Personality Customizations

### Image Placeholders
- **Creative Types (ENTP, INFP, ENFP, ISFP, ESTP)**: Shows placeholder image
- **ESTP**: Flashy animated placeholder with pulse effect
- **Other types**: No image placeholder

### Description Display
- **Feeling Types (INFJ, ISFJ)**: Shows full description section
- **Other types**: Description is hidden

### Styling Themes
- **ESTP**: Flashy gradient background with white text and animations
- **ISFJ**: Warm orange gradient with white text
- **Creative Types**: Purple gradient backgrounds
- **Structured Types**: Professional dark themes
- **Other Feeling Types**: Red accent themes

## MBTI Match Explanations

The component provides personality-specific explanations for why each spot matches:

- **INTJ**: Strategic thinkers appreciate well-planned, intellectually stimulating experiences
- **ENFP**: Enthusiastic explorers love vibrant, dynamic environments full of possibilities
- **ISFJ**: Caring individuals enjoy peaceful, harmonious environments with cultural depth
- **ESTP**: Action-oriented individuals love exciting, dynamic experiences with immediate engagement

## Responsive Design

- **Mobile-first**: Optimized for mobile devices with collapsible sections
- **Touch-friendly**: Minimum 44px touch targets
- **Flexible layouts**: CSS Grid and Flexbox for adaptive layouts
- **Image handling**: Responsive image placeholders
- **Typography**: Scalable text with proper hierarchy

## Accessibility

- **Semantic HTML**: Proper heading structure and landmarks
- **High contrast**: Support for high contrast mode
- **Reduced motion**: Respects user motion preferences
- **Screen readers**: Descriptive labels and ARIA attributes
- **Keyboard navigation**: Full keyboard accessibility

## Testing

Both components include comprehensive test suites covering:
- Component rendering and props
- Conditional content display
- MBTI personality-specific features
- Responsive behavior
- Accessibility compliance
- Error handling and edge cases

Run tests with:
```bash
npm test -- src/components/itinerary/__tests__/TouristSpotComboBoxItem.test.ts
npm test -- src/components/itinerary/__tests__/TouristSpotDetails.test.ts
```
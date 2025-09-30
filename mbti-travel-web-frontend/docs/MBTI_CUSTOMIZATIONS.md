# MBTI Personality Customization System

This document provides comprehensive documentation for the MBTI personality customization system, including theme configuration, UI adaptations, and implementation details.

## 📋 Table of Contents

- [Overview](#overview)
- [Personality Categories](#personality-categories)
- [Theme System](#theme-system)
- [UI Customizations](#ui-customizations)
- [Implementation Guide](#implementation-guide)
- [Configuration Reference](#configuration-reference)

## Overview

The MBTI Travel Web Frontend provides unique user interface customizations for each of the 16 Myers-Briggs personality types. These customizations enhance user experience by adapting the interface to match personality preferences and cognitive styles.

### Design Philosophy

- **Personality-Driven**: Each MBTI type receives tailored UI elements
- **Cognitive Alignment**: Interface matches thinking and decision-making patterns
- **Visual Harmony**: Color schemes and layouts reflect personality traits
- **Functional Adaptation**: Features align with personality preferences

## Personality Categories

The 16 MBTI types are organized into four main categories for customization purposes:

### Structured Types
**Types**: INTJ, ENTJ, ISTJ, ESTJ  
**Characteristics**: Organized, planning-oriented, systematic  
**UI Focus**: Time management, structure, control

### Flexible Types
**Types**: INTP, ISTP, ESTP  
**Characteristics**: Adaptable, spontaneous, casual  
**UI Focus**: Simplified layouts, point-form information

### Colorful Types
**Types**: ENTP, INFP, ENFP, ISFP  
**Characteristics**: Creative, expressive, visually-oriented  
**UI Focus**: Vibrant colors, visual elements, imagery

### Feeling Types
**Types**: INFJ, ISFJ, ENFJ, ESFJ  
**Characteristics**: Relationship-focused, empathetic, social  
**UI Focus**: Descriptions, sharing features, warm tones

## Theme System

### Color Palette Configuration

Each MBTI personality has a unique color palette that reflects their characteristics:

```typescript
interface PersonalityTheme {
  primary: string      // Main brand color
  secondary: string    // Supporting color
  accent: string       // Highlight color
  background: string   // Background color
  text: string         // Text color
  warm?: boolean       // Use warm color tones
  colorful?: boolean   // Use vibrant colors
  structured?: boolean // Use structured layouts
}
```

### Theme Definitions

#### Analyst Types (NT)

**INTJ - The Architect**
```typescript
INTJ: {
  primary: '#2c3e50',     // Deep blue-gray
  secondary: '#34495e',   // Slate gray
  accent: '#3498db',      // Professional blue
  background: '#ecf0f1',  // Light gray
  text: '#2c3e50',        // Dark gray
  structured: true
}
```

**INTP - The Thinker**
```typescript
INTP: {
  primary: '#8e44ad',     // Purple
  secondary: '#9b59b6',   // Light purple
  accent: '#e74c3c',      // Red accent
  background: '#f8f9fa',  // Off-white
  text: '#2c3e50',        // Dark gray
}
```

**ENTJ - The Commander**
```typescript
ENTJ: {
  primary: '#c0392b',     // Strong red
  secondary: '#e74c3c',   // Bright red
  accent: '#f39c12',      // Orange accent
  background: '#fdfefe',  // Pure white
  text: '#2c3e50',        // Dark text
  structured: true
}
```

**ENTP - The Debater**
```typescript
ENTP: {
  primary: '#e67e22',     // Orange
  secondary: '#f39c12',   // Bright orange
  accent: '#3498db',      // Blue accent
  background: '#fef9e7',  // Warm white
  text: '#2c3e50',        // Dark text
  colorful: true
}
```

#### Diplomat Types (NF)

**INFJ - The Advocate**
```typescript
INFJ: {
  primary: '#27ae60',     // Green
  secondary: '#2ecc71',   // Light green
  accent: '#8e44ad',      // Purple accent
  background: '#f8fffe',  // Soft white
  text: '#2c3e50',        // Dark text
}
```

**INFP - The Mediator**
```typescript
INFP: {
  primary: '#9b59b6',     // Purple
  secondary: '#bb8fce',   // Light purple
  accent: '#f1c40f',      // Yellow accent
  background: '#fdf2e9',  // Warm background
  text: '#2c3e50',        // Dark text
  colorful: true
}
```

**ENFJ - The Protagonist**
```typescript
ENFJ: {
  primary: '#e74c3c',     // Red
  secondary: '#ec7063',   // Light red
  accent: '#f39c12',      // Orange accent
  background: '#fef9e7',  // Warm white
  text: '#2c3e50',        // Dark text
}
```

**ENFP - The Campaigner**
```typescript
ENFP: {
  primary: '#ff6b6b',     // Coral red
  secondary: '#4ecdc4',   // Teal
  accent: '#45b7d1',      // Sky blue
  background: '#f8f9fa',  // Light background
  text: '#2c3e50',        // Dark text
  colorful: true
}
```

#### Sentinel Types (SJ)

**ISTJ - The Logistician**
```typescript
ISTJ: {
  primary: '#34495e',     // Dark gray
  secondary: '#5d6d7e',   // Medium gray
  accent: '#3498db',      // Blue accent
  background: '#f8f9fa',  // Light gray
  text: '#2c3e50',        // Dark text
  structured: true
}
```

**ISFJ - The Protector**
```typescript
ISFJ: {
  primary: '#d4a574',     // Warm brown
  secondary: '#f4e4bc',   // Light beige
  accent: '#b8860b',      // Gold accent
  background: '#fdf5e6',  // Warm background
  text: '#8b4513',        // Brown text
  warm: true
}
```

**ESTJ - The Executive**
```typescript
ESTJ: {
  primary: '#2c3e50',     // Navy blue
  secondary: '#34495e',   // Gray blue
  accent: '#e74c3c',      // Red accent
  background: '#f8f9fa',  // Clean white
  text: '#2c3e50',        // Dark text
  structured: true
}
```

**ESFJ - The Consul**
```typescript
ESFJ: {
  primary: '#e91e63',     // Pink
  secondary: '#f8bbd9',   // Light pink
  accent: '#ff9800',      // Orange accent
  background: '#fef7f0',  // Warm background
  text: '#2c3e50',        // Dark text
}
```

#### Explorer Types (SP)

**ISTP - The Virtuoso**
```typescript
ISTP: {
  primary: '#607d8b',     // Blue gray
  secondary: '#90a4ae',   // Light blue gray
  accent: '#ff5722',      // Orange accent
  background: '#f5f5f5',  // Neutral gray
  text: '#37474f',        // Dark gray
}
```

**ISFP - The Adventurer**
```typescript
ISFP: {
  primary: '#795548',     // Brown
  secondary: '#a1887f',   // Light brown
  accent: '#4caf50',      // Green accent
  background: '#f3e5f5',  // Soft purple
  text: '#3e2723',        // Dark brown
  colorful: true
}
```

**ESTP - The Entrepreneur**
```typescript
ESTP: {
  primary: '#ff5722',     // Orange red
  secondary: '#ff8a65',   // Light orange
  accent: '#ffc107',      // Yellow accent
  background: '#fff3e0',  // Orange background
  text: '#bf360c',        // Dark orange
  colorful: true
}
```

**ESFP - The Entertainer**
```typescript
ESFP: {
  primary: '#e91e63',     // Magenta
  secondary: '#f48fb1',   // Light pink
  accent: '#ffeb3b',      // Yellow accent
  background: '#fce4ec',  // Pink background
  text: '#880e4f',        // Dark pink
}
```

## UI Customizations

### Structured Types (INTJ, ENTJ, ISTJ, ESTJ)

These personalities prefer organized, systematic interfaces with clear structure and time management features.

#### Features
- **Time Input Fields**: Target start/end time for each session
- **Structured Layout**: Traditional table format
- **Planning Tools**: Schedule management features
- **ENTJ Special**: "Important!" checkboxes for priority marking

#### Implementation
```vue
<template>
  <div v-if="isStructuredType" class="structured-customizations">
    <!-- Time input fields for each session -->
    <div class="time-inputs">
      <label for="breakfast-time">Breakfast Time:</label>
      <input
        id="breakfast-time"
        v-model="sessionTimes.breakfast"
        type="time"
        class="time-input"
      />
    </div>
    
    <!-- ENTJ: Important checkboxes -->
    <div v-if="mbtiPersonality === 'ENTJ'" class="importance-markers">
      <label>
        <input type="checkbox" v-model="importantSpots.morning" />
        Mark as Important!
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
const isStructuredType = computed(() => 
  ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(props.mbtiPersonality)
)

const sessionTimes = ref({
  breakfast: '',
  morning: '',
  lunch: '',
  afternoon: '',
  dinner: '',
  night: ''
})

const importantSpots = ref({
  morning: false,
  afternoon: false,
  night: false
})
</script>
```

### Flexible Types (INTP, ISTP, ESTP)

These personalities prefer casual, adaptable interfaces with simplified information presentation.

#### Features
- **Point Form Layout**: Bullet points instead of tables
- **Casual Styling**: Relaxed, informal presentation
- **ESTP Special**: Flashy styling with emojis and images

#### Implementation
```vue
<template>
  <div v-if="isFlexibleType" class="flexible-layout">
    <div class="day-section" v-for="(day, index) in itineraryDays" :key="index">
      <h3 class="day-title">Day {{ index + 1 }} 🌟</h3>
      
      <ul class="activity-list">
        <li v-for="activity in day.activities" :key="activity.id">
          <span class="activity-emoji">{{ activity.emoji }}</span>
          <span class="activity-name">{{ activity.name }}</span>
          
          <!-- ESTP: Image placeholders -->
          <div v-if="mbtiPersonality === 'ESTP'" class="image-placeholder">
            <img :src="activity.imagePlaceholder" :alt="activity.name" />
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
const isFlexibleType = computed(() => 
  ['INTP', 'ISTP', 'ESTP'].includes(props.mbtiPersonality)
)
</script>

<style scoped>
.flexible-layout {
  padding: 1rem;
  font-family: 'Comic Sans MS', cursive; /* Casual font for ESTP */
}

.day-title {
  color: var(--primary-color);
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.activity-list {
  list-style: none;
  padding: 0;
}

.activity-list li {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: var(--background-color);
  border-radius: 8px;
}

/* ESTP: Flashy styling */
.mbti-estp .activity-list li {
  background: linear-gradient(45deg, #ff5722, #ff8a65);
  color: white;
  font-weight: bold;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>
```

### Colorful Types (ENTP, INFP, ENFP, ISFP)

These personalities appreciate vibrant, visually appealing interfaces with creative elements.

#### Features
- **Vibrant Colors**: Bright, engaging color schemes
- **Image Placeholders**: Visual elements for tourist spots
- **Creative Styling**: Artistic, expressive design elements

#### Implementation
```vue
<template>
  <div v-if="isColorfulType" class="colorful-customizations">
    <div class="tourist-spot-card" v-for="spot in touristSpots" :key="spot.id">
      <div class="spot-image-placeholder">
        <div class="placeholder-icon">🖼️</div>
        <span class="placeholder-text">Image would appear here</span>
      </div>
      
      <div class="spot-details">
        <h4 class="spot-name">{{ spot.name }}</h4>
        <p class="spot-description">{{ spot.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const isColorfulType = computed(() => 
  ['ENTP', 'INFP', 'ENFP', 'ISFP'].includes(props.mbtiPersonality)
)
</script>

<style scoped>
.colorful-customizations {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  padding: 2rem;
  border-radius: 16px;
}

.tourist-spot-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.tourist-spot-card:hover {
  transform: translateY(-4px);
}

.spot-image-placeholder {
  width: 100%;
  height: 200px;
  background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.placeholder-text {
  color: #666;
  font-style: italic;
}

.spot-name {
  color: var(--primary-color);
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}
</style>
```

### Feeling Types (INFJ, ISFJ, ENFJ, ESFJ)

These personalities value emotional connection, descriptions, and social features.

#### Features
- **Description Fields**: Detailed emotional context (INFJ, ISFJ)
- **Group Notes**: Social planning features (ENFJ, ESFJ)
- **Share Links**: Social sharing capabilities
- **Warm Tones**: Comfortable, inviting color schemes (ISFJ)

#### Implementation
```vue
<template>
  <div v-if="isFeelingType" class="feeling-customizations">
    <!-- Description fields for INFJ and ISFJ -->
    <div v-if="showDescriptions" class="description-section">
      <h4>Why This Place Matters</h4>
      <p class="spot-description">{{ spot.description }}</p>
      <div class="emotional-context">
        <span class="context-label">Emotional Appeal:</span>
        <span class="context-text">{{ spot.emotionalContext }}</span>
      </div>
    </div>
    
    <!-- Group notes for ENFJ and ESFJ -->
    <div v-if="showGroupNotes" class="group-notes-section">
      <label for="group-notes">Group Notes:</label>
      <textarea
        id="group-notes"
        v-model="groupNotes"
        placeholder="Add notes to share with your travel group..."
        class="group-notes-input"
      ></textarea>
    </div>
    
    <!-- Share link for social types -->
    <div v-if="showShareLink" class="share-section">
      <button class="share-button" @click="shareWithFriends">
        📤 Share with Friends
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const isFeelingType = computed(() => 
  ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const showDescriptions = computed(() => 
  ['INFJ', 'ISFJ'].includes(props.mbtiPersonality)
)

const showGroupNotes = computed(() => 
  ['ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const showShareLink = computed(() => 
  ['ENFJ', 'ESFJ'].includes(props.mbtiPersonality)
)

const groupNotes = ref('')

const shareWithFriends = () => {
  // Implement sharing functionality
  console.log('Sharing itinerary with friends')
}
</script>

<style scoped>
.feeling-customizations {
  padding: 1.5rem;
  background: var(--background-color);
  border-radius: 12px;
  border: 2px solid var(--primary-color);
}

/* ISFJ: Warm tones */
.mbti-isfj .feeling-customizations {
  background: linear-gradient(135deg, #fdf5e6, #f4e4bc);
  border-color: #d4a574;
}

.description-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
}

.spot-description {
  font-style: italic;
  color: var(--text-color);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.emotional-context {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.context-label {
  font-weight: bold;
  color: var(--primary-color);
}

.group-notes-section {
  margin-bottom: 1.5rem;
}

.group-notes-input {
  width: 100%;
  min-height: 100px;
  padding: 0.75rem;
  border: 2px solid var(--secondary-color);
  border-radius: 8px;
  font-family: inherit;
  resize: vertical;
}

.share-button {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.share-button:hover {
  background: var(--accent-color);
}
</style>
```

## Implementation Guide

### Theme Service

Create a centralized theme service to manage personality-based styling:

```typescript
// services/themeService.ts
import { MBTIPersonality, PersonalityTheme } from '@/types/mbti'

export class ThemeService {
  private themes: Record<MBTIPersonality, PersonalityTheme> = {
    // Theme definitions (see above)
  }

  /**
   * Apply MBTI personality theme to the document
   */
  applyMBTITheme(personality: MBTIPersonality): void {
    const theme = this.themes[personality]
    const root = document.documentElement

    // Set CSS custom properties
    root.style.setProperty('--mbti-primary', theme.primary)
    root.style.setProperty('--mbti-secondary', theme.secondary)
    root.style.setProperty('--mbti-accent', theme.accent)
    root.style.setProperty('--mbti-background', theme.background)
    root.style.setProperty('--mbti-text', theme.text)

    // Add personality class to body
    document.body.className = document.body.className
      .replace(/mbti-\w+/g, '')
    document.body.classList.add(`mbti-${personality.toLowerCase()}`)
  }

  /**
   * Get theme configuration for a personality
   */
  getPersonalityTheme(personality: MBTIPersonality): PersonalityTheme {
    return this.themes[personality]
  }

  /**
   * Check if personality is in a specific category
   */
  isStructuredPersonality(personality: MBTIPersonality): boolean {
    return ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(personality)
  }

  isFlexiblePersonality(personality: MBTIPersonality): boolean {
    return ['INTP', 'ISTP', 'ESTP'].includes(personality)
  }

  isColorfulPersonality(personality: MBTIPersonality): boolean {
    return ['ENTP', 'INFP', 'ENFP', 'ISFP'].includes(personality)
  }

  isFeelingPersonality(personality: MBTIPersonality): boolean {
    return ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'].includes(personality)
  }

  /**
   * Reset theme to default
   */
  resetTheme(): void {
    const root = document.documentElement
    const properties = [
      '--mbti-primary',
      '--mbti-secondary', 
      '--mbti-accent',
      '--mbti-background',
      '--mbti-text'
    ]

    properties.forEach(prop => {
      root.style.removeProperty(prop)
    })

    document.body.className = document.body.className
      .replace(/mbti-\w+/g, '')
  }
}

export const themeService = new ThemeService()
```

### Vue Composable

Create a Vue composable for easy theme management:

```typescript
// composables/useTheme.ts
import { ref, computed, watch } from 'vue'
import { themeService } from '@/services/themeService'
import type { MBTIPersonality } from '@/types/mbti'

export function useTheme(personality?: Ref<MBTIPersonality>) {
  const currentPersonality = ref<MBTIPersonality | null>(null)

  const currentTheme = computed(() => {
    if (!currentPersonality.value) return null
    return themeService.getPersonalityTheme(currentPersonality.value)
  })

  const isStructured = computed(() => {
    if (!currentPersonality.value) return false
    return themeService.isStructuredPersonality(currentPersonality.value)
  })

  const isFlexible = computed(() => {
    if (!currentPersonality.value) return false
    return themeService.isFlexiblePersonality(currentPersonality.value)
  })

  const isColorful = computed(() => {
    if (!currentPersonality.value) return false
    return themeService.isColorfulPersonality(currentPersonality.value)
  })

  const isFeeling = computed(() => {
    if (!currentPersonality.value) return false
    return themeService.isFeelingPersonality(currentPersonality.value)
  })

  const applyTheme = (personality: MBTIPersonality) => {
    currentPersonality.value = personality
    themeService.applyMBTITheme(personality)
  }

  const resetTheme = () => {
    currentPersonality.value = null
    themeService.resetTheme()
  }

  // Watch for personality changes
  if (personality) {
    watch(personality, (newPersonality) => {
      if (newPersonality) {
        applyTheme(newPersonality)
      }
    }, { immediate: true })
  }

  return {
    currentPersonality: readonly(currentPersonality),
    currentTheme,
    isStructured,
    isFlexible,
    isColorful,
    isFeeling,
    applyTheme,
    resetTheme
  }
}
```

### Component Integration

Use the theme system in components:

```vue
<template>
  <div class="personality-aware-component" :class="personalityClasses">
    <!-- Conditional rendering based on personality -->
    <StructuredLayout v-if="isStructured" />
    <FlexibleLayout v-else-if="isFlexible" />
    <ColorfulLayout v-else-if="isColorful" />
    <FeelingLayout v-else-if="isFeeling" />
    <DefaultLayout v-else />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const props = defineProps<{
  mbtiPersonality: MBTIPersonality
}>()

const { isStructured, isFlexible, isColorful, isFeeling } = useTheme()

const personalityClasses = computed(() => ({
  [`mbti-${props.mbtiPersonality.toLowerCase()}`]: true,
  'personality-structured': isStructured.value,
  'personality-flexible': isFlexible.value,
  'personality-colorful': isColorful.value,
  'personality-feeling': isFeeling.value
}))
</script>
```

## Configuration Reference

### Customization Matrix

| MBTI | Time Inputs | Important Checkboxes | Point Form | Descriptions | Group Notes | Share Link | Images | Flashy Style | Warm Tones |
|------|-------------|---------------------|------------|--------------|-------------|------------|--------|--------------|------------|
| INTJ | ✓ | - | - | - | - | - | - | - | - |
| INTP | - | - | ✓ | - | - | - | - | - | - |
| ENTJ | ✓ | ✓ | - | - | - | - | - | - | - |
| ENTP | - | - | - | - | - | - | ✓ | - | - |
| INFJ | - | - | - | ✓ | - | - | - | - | - |
| INFP | - | - | - | - | - | - | ✓ | - | - |
| ENFJ | - | - | - | - | ✓ | ✓ | - | - | - |
| ENFP | - | - | - | - | - | - | ✓ | - | - |
| ISTJ | ✓ | - | - | - | - | - | - | - | - |
| ISFJ | - | - | - | ✓ | - | - | - | - | ✓ |
| ESTJ | ✓ | - | - | - | - | - | - | - | - |
| ESFJ | - | - | - | - | ✓ | ✓ | - | - | - |
| ISTP | - | - | ✓ | - | - | - | - | - | - |
| ISFP | - | - | - | - | - | - | ✓ | - | - |
| ESTP | - | - | ✓ | - | - | - | ✓ | ✓ | - |
| ESFP | - | - | - | - | - | - | - | - | - |

### CSS Custom Properties

The theme system uses CSS custom properties for dynamic styling:

```css
:root {
  /* Primary theme colors */
  --mbti-primary: #3498db;
  --mbti-secondary: #2ecc71;
  --mbti-accent: #e74c3c;
  --mbti-background: #f8f9fa;
  --mbti-text: #2c3e50;
  
  /* Semantic colors */
  --color-success: #27ae60;
  --color-warning: #f39c12;
  --color-error: #e74c3c;
  --color-info: #3498db;
  
  /* Layout properties */
  --border-radius: 8px;
  --box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
}

/* Personality-specific overrides */
.mbti-enfp {
  --mbti-primary: #ff6b6b;
  --mbti-secondary: #4ecdc4;
  --mbti-accent: #45b7d1;
}

.mbti-intj {
  --mbti-primary: #2c3e50;
  --mbti-secondary: #34495e;
  --mbti-accent: #3498db;
}
```

### TypeScript Types

```typescript
// types/mbti.ts
export type MBTIPersonality = 
  | 'INTJ' | 'INTP' | 'ENTJ' | 'ENTP'
  | 'INFJ' | 'INFP' | 'ENFJ' | 'ENFP'
  | 'ISTJ' | 'ISFJ' | 'ESTJ' | 'ESFJ'
  | 'ISTP' | 'ISFP' | 'ESTP' | 'ESFP'

export interface PersonalityTheme {
  primary: string
  secondary: string
  accent: string
  background: string
  text: string
  warm?: boolean
  colorful?: boolean
  structured?: boolean
}

export interface PersonalityCustomizations {
  showTimeInputs: boolean
  showImportantCheckboxes: boolean
  showPointForm: boolean
  showDescriptions: boolean
  showGroupNotes: boolean
  showShareLink: boolean
  showImages: boolean
  useFlashyStyle: boolean
  useWarmTones: boolean
}

export interface MBTIConfiguration {
  personality: MBTIPersonality
  theme: PersonalityTheme
  customizations: PersonalityCustomizations
}
```

---

This comprehensive MBTI customization system ensures that each personality type receives a tailored user experience that aligns with their cognitive preferences and visual aesthetics, creating a more engaging and personalized travel planning interface.
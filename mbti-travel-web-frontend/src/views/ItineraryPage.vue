<template>
  <div class="itinerary-page" :class="personalityClass">
    <div class="itinerary-container">
      <!-- Header Component -->
      <ItineraryHeader 
        :mbti-personality="mbtiPersonality" 
        @back="handleBackNavigation"
      />

      <!-- Main Content -->
      <div class="itinerary-content">
        <div class="content-header">
          <h3 class="content-title">Your Personalized 3-Day Hong Kong Itinerary</h3>
        </div>

        <!-- Placeholder for future itinerary content -->
        <div class="itinerary-placeholder">
          <div class="placeholder-card">
            <h4>Itinerary Content Coming Soon</h4>
            <p>
              Your personalized {{ mbtiPersonality }} itinerary will be displayed here with:
            </p>
            <ul class="feature-list">
              <li>3-day × 6-session table structure</li>
              <li>Restaurant recommendations with combo boxes</li>
              <li>Tourist spot recommendations with combo boxes</li>
              <li>Personality-specific customizations for {{ mbtiPersonality }}</li>
              <li v-if="isStructuredPersonality">Time input fields for structured planning</li>
              <li v-if="isFlexiblePersonality">Point form layout for flexible approach</li>
              <li v-if="isColorfulPersonality">Vibrant colors and image placeholders</li>
              <li v-if="isFeelingPersonality">Detailed descriptions and social features</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useNavigation } from '@/composables/useNavigation'
import { useRoutePreloader } from '@/utils/routePreloader'
import ItineraryHeader from '@/components/itinerary/ItineraryHeader.vue'
import { ThemeService } from '@/services'
import type { MBTIPersonality } from '@/types'

const route = useRoute()
const { goBack, goHome, restoreState, getCurrentState } = useNavigation()
const { preloadRoute } = useRoutePreloader()
const themeService = ThemeService.getInstance()

// Component state
const isLoading = ref(false)
const itineraryData = ref(null)

// Get MBTI personality from route params
const mbtiPersonality = computed(() => {
  const mbti = route.params.mbti as string
  return mbti?.toUpperCase() as MBTIPersonality
})

// Personality class for styling
const personalityClass = computed(() => {
  return `mbti-${mbtiPersonality.value.toLowerCase()}`
})

// Personality categorization for conditional features
const isStructuredPersonality = computed(() => {
  return ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ'].includes(mbtiPersonality.value)
})

const isFlexiblePersonality = computed(() => {
  return ['INTP', 'ISTP', 'ESTP'].includes(mbtiPersonality.value)
})

const isColorfulPersonality = computed(() => {
  return ['ENTP', 'INFP', 'ENFP', 'ISFP', 'ESFP'].includes(mbtiPersonality.value)
})

const isFeelingPersonality = computed(() => {
  return ['INFJ', 'ISFJ', 'ENFJ', 'ESFJ'].includes(mbtiPersonality.value)
})

// Navigation handlers
async function handleBackNavigation(): Promise<void> {
  try {
    // Save current state before navigating back
    const currentState = getCurrentState()
    
    // Go back to previous page or home
    goBack()
  } catch (error) {
    console.error('Back navigation failed:', error)
    // Fallback to home
    await goHome({ replace: true })
  }
}

// Load itinerary data
function loadItineraryData(): void {
  try {
    const storedData = sessionStorage.getItem('itineraryData')
    if (storedData) {
      itineraryData.value = JSON.parse(storedData)
    }
  } catch (error) {
    console.error('Failed to load itinerary data:', error)
  }
}

// Lifecycle hooks
onMounted(async () => {
  isLoading.value = true
  
  try {
    // Apply MBTI theme when component mounts
    if (mbtiPersonality.value) {
      themeService.applyMBTITheme(mbtiPersonality.value)
    }
    
    // Load itinerary data
    loadItineraryData()
    
    // Restore any preserved state
    restoreState()
    
    // Set dynamic page title
    document.title = `${mbtiPersonality.value} Itinerary - MBTI Travel Planner`
    
    // Preload home page for potential back navigation
    setTimeout(() => {
      preloadRoute('home')
    }, 3000)
  } catch (error) {
    console.error('Failed to initialize itinerary page:', error)
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  // Optional: Reset theme when leaving the page
  // themeService.resetTheme()
  
  // Clean up session storage if needed
  // sessionStorage.removeItem('itineraryData')
})
</script>

<style scoped>
.itinerary-page {
  min-height: 100vh;
  background: var(--mbti-background, #ffffff);
  color: var(--mbti-text, #212529);
  transition: all 0.3s ease;
}

.itinerary-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.itinerary-content {
  padding: 2rem 0;
}

.content-header {
  text-align: center;
  margin-bottom: 3rem;
}

.content-title {
  color: var(--mbti-primary, #007bff);
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.01em;
}

.itinerary-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.placeholder-card {
  background: var(--mbti-surface, #ffffff);
  border: 2px solid var(--mbti-border, #dee2e6);
  border-radius: 16px;
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 8px 24px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  text-align: center;
  transition: all 0.3s ease;
}

.placeholder-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px var(--mbti-shadow, rgba(0, 0, 0, 0.15));
}

.placeholder-card h4 {
  color: var(--mbti-primary, #007bff);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.placeholder-card p {
  color: var(--mbti-text, #212529);
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.feature-list {
  text-align: left;
  color: var(--mbti-text, #212529);
  line-height: 1.8;
  font-size: 1rem;
  margin: 0;
  padding-left: 1.5rem;
}

.feature-list li {
  margin-bottom: 0.75rem;
  position: relative;
}

.feature-list li::marker {
  color: var(--mbti-accent, #28a745);
}

/* Personality-specific styling enhancements */
.mbti-intj .placeholder-card,
.mbti-entj .placeholder-card,
.mbti-istj .placeholder-card,
.mbti-estj .placeholder-card {
  border-left: 4px solid var(--mbti-primary, #007bff);
}

.mbti-intp .placeholder-card,
.mbti-istp .placeholder-card,
.mbti-estp .placeholder-card {
  border-radius: 8px;
  border-style: dashed;
}

.mbti-entp .placeholder-card,
.mbti-infp .placeholder-card,
.mbti-enfp .placeholder-card,
.mbti-isfp .placeholder-card,
.mbti-esfp .placeholder-card {
  background: linear-gradient(135deg, var(--mbti-surface, #ffffff) 0%, rgba(255, 255, 255, 0.8) 100%);
  border: 2px solid transparent;
  background-clip: padding-box;
  position: relative;
}

.mbti-entp .placeholder-card::before,
.mbti-infp .placeholder-card::before,
.mbti-enfp .placeholder-card::before,
.mbti-isfp .placeholder-card::before,
.mbti-esfp .placeholder-card::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, var(--mbti-primary, #007bff), var(--mbti-accent, #28a745));
  border-radius: 16px;
  z-index: -1;
}

.mbti-infj .placeholder-card,
.mbti-isfj .placeholder-card,
.mbti-enfj .placeholder-card,
.mbti-esfj .placeholder-card {
  box-shadow: 0 8px 24px var(--mbti-shadow, rgba(0, 0, 0, 0.1)), 
              0 0 20px var(--mbti-warm-glow, rgba(255, 193, 7, 0.1));
}

/* Special styling for ISFJ warm tones */
.mbti-isfj .placeholder-card {
  background: linear-gradient(135deg, var(--mbti-surface, #ffffff) 0%, #fdf5e6 100%);
}

/* ESTP flashy styling */
.mbti-estp .placeholder-card {
  animation: estp-pulse 3s ease-in-out infinite;
}

@keyframes estp-pulse {
  0%, 100% {
    box-shadow: 0 8px 24px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  }
  50% {
    box-shadow: 0 12px 32px var(--mbti-accent, #28a745), 
                0 0 30px var(--mbti-primary, #007bff);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .itinerary-container {
    padding: 0 1rem;
  }

  .content-title {
    font-size: 1.5rem;
  }

  .placeholder-card {
    padding: 2rem;
    margin: 1rem;
  }

  .placeholder-card h4 {
    font-size: 1.25rem;
  }

  .placeholder-card p {
    font-size: 1rem;
  }

  .feature-list {
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .content-title {
    font-size: 1.25rem;
  }

  .placeholder-card {
    padding: 1.5rem;
    margin: 0.5rem;
  }

  .feature-list {
    padding-left: 1rem;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .placeholder-card {
    transition: none;
  }

  .placeholder-card:hover {
    transform: none;
  }

  .mbti-estp .placeholder-card {
    animation: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .placeholder-card {
    border-width: 3px;
  }

  .feature-list li::marker {
    font-weight: bold;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .placeholder-card {
    background: var(--mbti-surface, #2d2d2d);
    border-color: var(--mbti-border, #404040);
  }
}
</style>
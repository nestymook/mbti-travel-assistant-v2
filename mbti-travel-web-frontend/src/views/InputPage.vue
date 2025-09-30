<template>
  <div class="input-page">
    <div class="input-form-container">
      <MBTIInputForm
        v-model="mbtiInput"
        :is-loading="isLoading"
        :error-message="errorMessage"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthGuard } from '@/composables/useAuth'
import { useNavigation, useRouteGuard } from '@/composables/useNavigation'
import { useRoutePreloader } from '@/utils/routePreloader'
import MBTIInputForm from '@/components/input/MBTIInputForm.vue'
import { ValidationService, ApiService } from '@/services'
import type { ItineraryRequest, MBTIPersonality } from '@/types'

const route = useRoute()
const { guardComponent } = useAuthGuard()
const { goToItinerary, getCurrentState, restoreState, clearNavigationError } = useNavigation()
const { confirmNavigation } = useRouteGuard()
const { preloadLikelyRoutes } = useRoutePreloader()

const validationService = ValidationService.getInstance()
const apiService = ApiService.getInstance()

const mbtiInput = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const hasUnsavedChanges = ref(false)

// Handle query parameters for error states
const queryError = route.query.error as string
if (queryError === 'invalid-mbti') {
  errorMessage.value = 'Invalid MBTI personality type. Please enter a valid 4-letter code.'
}

async function handleSubmit(mbtiCode: string) {
  errorMessage.value = ''
  clearNavigationError()

  // Validate MBTI code
  const validation = validationService.validateMBTICode(mbtiCode)
  if (!validation.isValid) {
    errorMessage.value = validation.message || 'Invalid MBTI code'
    return
  }

  isLoading.value = true

  try {
    // Create itinerary request
    const request: ItineraryRequest = {
      mbtiPersonality: mbtiCode.toUpperCase() as MBTIPersonality,
      preferences: {
        includeRestaurants: true,
        includeTouristSpots: true,
        days: 3
      }
    }

    // Call API to generate itinerary
    const response = await apiService.generateItinerary(request)

    // Store the response in sessionStorage for the itinerary page to access
    sessionStorage.setItem('itineraryData', JSON.stringify(response))
    
    // Clear unsaved changes flag
    hasUnsavedChanges.value = false
    
    // Navigate to itinerary page with state preservation
    await goToItinerary(mbtiCode, { preserveState: false })
  } catch (error) {
    console.error('Error generating itinerary:', error)
    
    if (error instanceof Error) {
      errorMessage.value = error.message
    } else {
      errorMessage.value = 'Failed to generate itinerary. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

// Watch for input changes to track unsaved changes
watch(mbtiInput, (newValue) => {
  hasUnsavedChanges.value = newValue.trim().length > 0
})

// Set up navigation guard for unsaved changes
let removeNavigationGuard: (() => void) | null = null

onMounted(async () => {
  // Guard this component
  await guardComponent()
  
  // Restore any preserved state
  const preservedState = restoreState()
  if (preservedState?.formData?.mbtiInput) {
    mbtiInput.value = preservedState.formData.mbtiInput
  }
  
  // Set up navigation guard for unsaved changes
  removeNavigationGuard = confirmNavigation(
    'You have unsaved changes. Are you sure you want to leave?'
  )
  
  // Preload likely next routes
  setTimeout(() => {
    preloadLikelyRoutes()
  }, 2000)
  
  // Set page title
  document.title = 'MBTI Travel Planner - Plan Your Hong Kong Adventure'
})

onUnmounted(() => {
  // Remove navigation guard
  if (removeNavigationGuard) {
    removeNavigationGuard()
  }
  
  // Preserve form state if there are unsaved changes
  if (hasUnsavedChanges.value) {
    const state = {
      ...getCurrentState(),
      formData: {
        mbtiInput: mbtiInput.value
      }
    }
    // This would be handled by the navigation composable
  }
})
</script>

<style scoped>
.input-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mbti-background, #f8f9fa);
  padding: 1rem;
}

.input-form-container {
  width: 100%;
  max-width: 500px;
  display: flex;
  justify-content: center;
}

/* Responsive design */
@media (max-width: 768px) {
  .input-page {
    padding: 0.5rem;
  }
  
  .input-form-container {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .input-page {
    align-items: flex-start;
    padding-top: 2rem;
  }
}
</style>
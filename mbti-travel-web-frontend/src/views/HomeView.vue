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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthGuard } from '@/composables/useAuth'
import MBTIInputForm from '@/components/input/MBTIInputForm.vue'
import { ValidationService } from '@/services'

const router = useRouter()
const { guardComponent } = useAuthGuard()
const validationService = ValidationService.getInstance()

const mbtiInput = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleSubmit(mbtiCode: string) {
  errorMessage.value = ''

  // Validate MBTI code
  const validation = validationService.validateMBTICode(mbtiCode)
  if (!validation.isValid) {
    errorMessage.value = validation.message || 'Invalid MBTI code'
    return
  }

  isLoading.value = true

  try {
    // TODO: Implement API call to generate itinerary
    // const response = await apiService.generateItinerary({ mbtiPersonality: mbtiCode })

    // Simulate API call for now
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Navigate to itinerary page with MBTI code
    router.push({
      name: 'itinerary',
      params: { mbti: mbtiCode },
    })
  } catch (error) {
    errorMessage.value = 'Failed to generate itinerary. Please try again.'
    console.error('Error generating itinerary:', error)
  } finally {
    isLoading.value = false
  }
}

// Guard this component on mount
onMounted(async () => {
  await guardComponent()
})
</script>

<style scoped>
.input-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mbti-background, #f8f9fa);
}
</style>

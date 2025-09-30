<template>
  <div class="itinerary-page" :class="`mbti-${mbtiPersonality.toLowerCase()}`">
    <div class="itinerary-container">
      <button @click="goBack" class="back-button">← Back</button>

      <div class="itinerary-header">
        <h1>Hong Kong MBTI Travel Planner</h1>
        <h2>
          3-Day Itinerary for
          <span class="personality-highlight">{{ mbtiPersonality }}</span>
          Personality
        </h2>
      </div>

      <div class="itinerary-content">
        <h3>Your Personalized 3-Day Hong Kong Itinerary</h3>

        <!-- Placeholder for itinerary content -->
        <div class="placeholder-content">
          <p>
            Itinerary content will be displayed here based on the MBTI personality type:
            {{ mbtiPersonality }}
          </p>
          <p>This will include:</p>
          <ul>
            <li>3-day × 6-session table structure</li>
            <li>Restaurant recommendations with combo boxes</li>
            <li>Tourist spot recommendations with combo boxes</li>
            <li>Personality-specific customizations</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ThemeService } from '@/services'
import type { MBTIPersonality } from '@/types'

const route = useRoute()
const router = useRouter()
const themeService = ThemeService.getInstance()

const mbtiPersonality = computed(() => {
  return (route.params.mbti as string)?.toUpperCase() as MBTIPersonality
})

function goBack() {
  router.push({ name: 'home' })
}

onMounted(() => {
  if (mbtiPersonality.value) {
    themeService.applyMBTITheme(mbtiPersonality.value)
  }
})
</script>

<style scoped>
.itinerary-page {
  min-height: 100vh;
  background: var(--mbti-background, #ffffff);
}

.placeholder-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-top: 2rem;
}

.placeholder-content h3 {
  color: var(--mbti-primary, #007bff);
  margin-bottom: 1rem;
}

.placeholder-content ul {
  color: var(--mbti-text, #212529);
  line-height: 1.6;
}

.placeholder-content li {
  margin-bottom: 0.5rem;
}
</style>

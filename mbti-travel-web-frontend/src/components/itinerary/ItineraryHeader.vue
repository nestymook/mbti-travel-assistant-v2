<template>
  <div class="itinerary-header">
    <button @click="handleBackClick" class="back-button" aria-label="Go back to input page">
      ← Back
    </button>

    <div class="header-content">
      <h1 class="main-title">Hong Kong MBTI Travel Planner</h1>
      <h2 class="subtitle">
        3-Day Itinerary for
        <span class="personality-highlight" :class="`personality-${mbtiPersonality.toLowerCase()}`">
          {{ mbtiPersonality }}
        </span>
        Personality
      </h2>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { MBTIPersonality } from '@/types'

interface Props {
  mbtiPersonality: MBTIPersonality
}

interface Emits {
  (e: 'back'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()

function handleBackClick(): void {
  emit('back')
  router.push({ name: 'home' })
}
</script>

<style scoped>
.itinerary-header {
  padding: 2rem 0;
  background: var(--mbti-background, #ffffff);
  border-bottom: 1px solid var(--mbti-border, #dee2e6);
}

.back-button {
  background: var(--mbti-secondary, #6c757d);
  color: var(--mbti-surface, #ffffff);
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 2rem;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.back-button:hover {
  background: var(--mbti-primary, #007bff);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.back-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
}

.back-button:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--mbti-focus, rgba(0, 123, 255, 0.25));
}

.header-content {
  text-align: center;
}

.main-title {
  color: var(--mbti-primary, #007bff);
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.subtitle {
  color: var(--mbti-text, #212529);
  font-size: 1.75rem;
  font-weight: 500;
  line-height: 1.3;
  margin: 0;
}

.personality-highlight {
  background: var(--mbti-accent, #28a745);
  color: var(--mbti-surface, #ffffff);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 700;
  display: inline-block;
  margin: 0 0.25rem;
  box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
}

/* Personality-specific highlighting styles */
.personality-highlight.personality-intj,
.personality-highlight.personality-entj,
.personality-highlight.personality-istj,
.personality-highlight.personality-estj {
  background: var(--mbti-primary, #007bff);
  border: 2px solid var(--mbti-accent, #28a745);
}

.personality-highlight.personality-intp,
.personality-highlight.personality-istp,
.personality-highlight.personality-estp {
  background: var(--mbti-secondary, #6c757d);
  color: var(--mbti-surface, #ffffff);
}

.personality-highlight.personality-entp,
.personality-highlight.personality-infp,
.personality-highlight.personality-enfp,
.personality-highlight.personality-isfp,
.personality-highlight.personality-esfp {
  background: linear-gradient(135deg, var(--mbti-primary, #007bff), var(--mbti-accent, #28a745));
  animation: colorful-glow 3s ease-in-out infinite;
}

.personality-highlight.personality-infj,
.personality-highlight.personality-isfj,
.personality-highlight.personality-enfj,
.personality-highlight.personality-esfj {
  background: var(--mbti-primary, #007bff);
  box-shadow: 0 0 15px var(--mbti-warm-glow, rgba(255, 193, 7, 0.3));
}

/* Special styling for ISFJ warm tones */
.personality-highlight.personality-isfj {
  background: var(--mbti-primary, #d4a574);
  color: var(--mbti-text, #8b4513);
  box-shadow: 0 0 20px rgba(212, 165, 116, 0.4);
}

/* Animation for colorful personalities */
@keyframes colorful-glow {
  0%, 100% {
    box-shadow: 0 2px 4px var(--mbti-shadow, rgba(0, 0, 0, 0.1));
  }
  50% {
    box-shadow: 0 4px 12px var(--mbti-accent, #28a745), 0 0 20px var(--mbti-primary, #007bff);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .itinerary-header {
    padding: 1.5rem 0;
  }

  .main-title {
    font-size: 2.25rem;
  }

  .subtitle {
    font-size: 1.25rem;
  }

  .personality-highlight {
    padding: 0.375rem 0.75rem;
    font-size: 0.9em;
  }

  .back-button {
    padding: 0.625rem 1.25rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.875rem;
  }

  .subtitle {
    font-size: 1.125rem;
  }

  .personality-highlight {
    display: block;
    margin: 0.5rem auto;
    width: fit-content;
  }
}

/* Accessibility enhancements */
@media (prefers-reduced-motion: reduce) {
  .personality-highlight.personality-entp,
  .personality-highlight.personality-infp,
  .personality-highlight.personality-enfp,
  .personality-highlight.personality-isfp,
  .personality-highlight.personality-esfp {
    animation: none;
  }

  .back-button:hover {
    transform: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .personality-highlight {
    border: 2px solid currentColor;
    font-weight: 800;
  }

  .back-button {
    border: 2px solid var(--mbti-primary, #007bff);
  }
}
</style>
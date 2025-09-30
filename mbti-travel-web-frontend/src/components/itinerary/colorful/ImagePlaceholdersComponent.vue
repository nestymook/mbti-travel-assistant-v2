<template>
  <div class="image-placeholders">
    <div class="placeholder-grid">
      <div
        v-for="(placeholder, index) in placeholders"
        :key="index"
        class="placeholder-item"
        :style="{ background: placeholder.color }"
      >
        <div class="placeholder-content">
          <span class="placeholder-icon">{{ placeholder.icon }}</span>
          <span class="placeholder-text">{{ placeholder.text }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Placeholder {
  icon: string
  text: string
  color: string
}

const placeholders = ref<Placeholder[]>([
  { icon: '🏖️', text: 'Beach Photo', color: 'linear-gradient(135deg, #74b9ff, #0984e3)' },
  { icon: '🏛️', text: 'Architecture', color: 'linear-gradient(135deg, #fd79a8, #e84393)' },
  { icon: '🍜', text: 'Food Shot', color: 'linear-gradient(135deg, #fdcb6e, #e17055)' },
  { icon: '🌅', text: 'Sunrise View', color: 'linear-gradient(135deg, #a29bfe, #6c5ce7)' }
])
</script>

<style scoped>
.image-placeholders {
  padding: 1rem;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.placeholder-item {
  aspect-ratio: 4/3;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s ease;
}

.placeholder-item:hover {
  transform: translateY(-2px);
}

.placeholder-content {
  text-align: center;
}

.placeholder-icon {
  display: block;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.placeholder-text {
  font-size: 0.9rem;
  font-weight: 500;
}
</style>
</template>
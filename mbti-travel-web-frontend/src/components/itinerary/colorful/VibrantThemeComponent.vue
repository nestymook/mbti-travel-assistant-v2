<template>
  <div class="vibrant-theme">
    <div class="theme-wrapper" :style="{ background: currentGradient }">
      <div class="theme-content">
        <slot>
          <h3 class="vibrant-title">🌈 Vibrant Experience</h3>
          <p class="vibrant-text">Colorful and engaging content!</p>
        </slot>
      </div>
      <div class="theme-controls">
        <button
          v-for="(gradient, index) in gradients"
          :key="index"
          @click="changeTheme(index)"
          class="theme-btn"
          :style="{ background: gradient }"
          :class="{ active: currentIndex === index }"
        ></button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
]

const currentIndex = ref(0)

const currentGradient = computed(() => gradients[currentIndex.value])

function changeTheme(index: number) {
  currentIndex.value = index
}
</script>

<style scoped>
.vibrant-theme {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}

.theme-wrapper {
  padding: 1.5rem;
  color: white;
  transition: background 0.3s ease;
}

.theme-content {
  margin-bottom: 1rem;
}

.vibrant-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.4rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.vibrant-text {
  margin: 0;
  opacity: 0.9;
}

.theme-controls {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.theme-btn {
  width: 30px;
  height: 30px;
  border: 2px solid white;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.theme-btn:hover,
.theme-btn.active {
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style>
</template>
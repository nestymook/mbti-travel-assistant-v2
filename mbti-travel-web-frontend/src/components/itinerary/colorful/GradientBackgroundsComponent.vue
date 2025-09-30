<template>
  <div class="gradient-backgrounds">
    <div class="gradient-container" :style="{ background: activeGradient }">
      <div class="gradient-content">
        <slot>
          <h3 class="gradient-title">Dynamic Backgrounds</h3>
          <p class="gradient-description">Beautiful gradient themes</p>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const gradients = [
  'linear-gradient(45deg, #ff6b6b, #feca57)',
  'linear-gradient(45deg, #48cae4, #023e8a)',
  'linear-gradient(45deg, #f72585, #b5179e)',
  'linear-gradient(45deg, #06ffa5, #00d4aa)',
  'linear-gradient(45deg, #ffd60a, #003566)'
]

const activeGradient = ref(gradients[0])

onMounted(() => {
  // Cycle through gradients
  let index = 0
  setInterval(() => {
    index = (index + 1) % gradients.length
    activeGradient.value = gradients[index]
  }, 3000)
})
</script>

<style scoped>
.gradient-backgrounds {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}

.gradient-container {
  padding: 2rem;
  color: white;
  transition: background 1s ease-in-out;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gradient-content {
  text-align: center;
}

.gradient-title {
  margin: 0 0 1rem 0;
  font-size: 1.8rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.gradient-description {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.9;
}
</style>
</template>
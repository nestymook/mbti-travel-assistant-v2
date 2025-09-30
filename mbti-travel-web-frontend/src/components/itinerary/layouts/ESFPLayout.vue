<template>
  <div class="esfp-layout">
    <div class="layout-header">
      <h1 class="layout-title">🎉 Fun Adventure! 🎉</h1>
      <p class="layout-subtitle">Energetic and social travel experience</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ESFP-specific energetic layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// ESFP personality layout - energetic and social
defineComponent({
  name: 'ESFPLayout'
})
</script>

<style scoped>
.esfp-layout {
  background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
  border-radius: 20px;
  padding: 2rem;
  color: white;
  box-shadow: 0 12px 30px rgba(255, 107, 107, 0.4);
  animation: bounce 2s infinite;
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
}

.layout-title {
  margin: 0 0 0.5rem 0;
  font-size: 2.2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.layout-subtitle {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.9;
}

.layout-content {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1.5rem;
  line-height: 1.6;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
  60% { transform: translateY(-3px); }
}
</style>
</template>
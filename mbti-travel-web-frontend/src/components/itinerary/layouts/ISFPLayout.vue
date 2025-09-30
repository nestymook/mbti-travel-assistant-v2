<template>
  <div class="isfp-layout">
    <div class="layout-header">
      <h1 class="layout-title">🎨 Artistic Journey</h1>
      <p class="layout-subtitle">Creative and personal travel experience</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ISFP-specific artistic layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// ISFP personality layout - artistic and sensitive
defineComponent({
  name: 'ISFPLayout'
})
</script>

<style scoped>
.isfp-layout {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border-radius: 16px;
  padding: 2rem;
  color: #5d4037;
  box-shadow: 0 8px 24px rgba(252, 182, 159, 0.3);
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
}

.layout-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  color: #8b4513;
}

.layout-subtitle {
  margin: 0;
  font-style: italic;
  opacity: 0.8;
}

.layout-content {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
  line-height: 1.6;
}
</style>
</template>
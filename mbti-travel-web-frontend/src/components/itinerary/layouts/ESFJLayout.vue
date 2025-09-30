<template>
  <div class="esfj-layout">
    <div class="layout-header">
      <h1 class="layout-title">👥 Social Journey</h1>
      <p class="layout-subtitle">Community-focused and organized travel</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ESFJ-specific social layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// ESFJ personality layout - social and organized
defineComponent({
  name: 'ESFJLayout'
})
</script>

<style scoped>
.esfj-layout {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  border-radius: 16px;
  padding: 2rem;
  color: #2d3748;
  box-shadow: 0 8px 24px rgba(250, 112, 154, 0.3);
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
  border-bottom: 2px solid rgba(45, 55, 72, 0.2);
  padding-bottom: 1rem;
}

.layout-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  color: #2d3748;
  text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}

.layout-subtitle {
  margin: 0;
  font-size: 1rem;
  opacity: 0.8;
}

.layout-content {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
  line-height: 1.6;
  border: 1px solid rgba(255,255,255,0.3);
}
</style>
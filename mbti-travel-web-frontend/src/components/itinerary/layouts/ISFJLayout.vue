<template>
  <div class="isfj-layout">
    <div class="layout-header">
      <h1 class="layout-title">🌸 Caring Journey</h1>
      <p class="layout-subtitle">Thoughtful and nurturing travel experience</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ISFJ-specific caring layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// ISFJ personality layout - caring and detailed
defineComponent({
  name: 'ISFJLayout'
})
</script>

<style scoped>
.isfj-layout {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border-radius: 16px;
  padding: 2rem;
  color: #5d4037;
  box-shadow: 0 8px 24px rgba(252, 182, 159, 0.3);
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
  border-bottom: 2px solid rgba(139, 69, 19, 0.3);
  padding-bottom: 1rem;
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
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
  line-height: 1.6;
  border: 1px solid rgba(139, 69, 19, 0.2);
}
</style>
</template>
<template>
  <div class="infj-layout">
    <div class="layout-header">
      <h1 class="layout-title">🌙 Thoughtful Journey</h1>
      <p class="layout-subtitle">Meaningful and introspective travel</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>INFJ-specific contemplative layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// INFJ personality layout - thoughtful and meaningful
defineComponent({
  name: 'INFJLayout'
})
</script>

<style scoped>
.infj-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 2rem;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  position: relative;
}

.infj-layout::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
  border-radius: 16px;
  pointer-events: none;
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
  position: relative;
  z-index: 1;
}

.layout-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.layout-subtitle {
  margin: 0;
  font-style: italic;
  opacity: 0.9;
}

.layout-content {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 1.5rem;
  line-height: 1.6;
  position: relative;
  z-index: 1;
}
</style>
</template>
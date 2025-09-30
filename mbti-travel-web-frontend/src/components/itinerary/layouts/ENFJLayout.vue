<template>
  <div class="enfj-layout">
    <div class="layout-header">
      <h1 class="layout-title">🌟 Inspiring Journey</h1>
      <p class="layout-subtitle">Motivational and people-focused travel</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ENFJ-specific inspiring layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// ENFJ personality layout - inspiring and people-focused
defineComponent({
  name: 'ENFJLayout'
})
</script>

<style scoped>
.enfj-layout {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 18px;
  padding: 2rem;
  color: #2d3748;
  box-shadow: 0 10px 30px rgba(67, 233, 123, 0.3);
}

.layout-header {
  text-align: center;
  margin-bottom: 2rem;
}

.layout-title {
  margin: 0 0 0.5rem 0;
  font-size: 2.2rem;
  color: #2d3748;
  text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
}

.layout-subtitle {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.8;
}

.layout-content {
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1.5rem;
  line-height: 1.6;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}
</style>
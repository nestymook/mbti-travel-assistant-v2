<template>
  <div class="enfp-layout">
    <div class="layout-header">
      <h1 class="layout-title">🌟 Adventure Awaits! 🌟</h1>
      <p class="layout-subtitle">Colorful and inspiring journey</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ENFP-specific vibrant layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
// ENFP personality layout - colorful and enthusiastic
</script>

<style scoped>
.enfp-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1.5rem;
  line-height: 1.6;
}
</style>
</template>
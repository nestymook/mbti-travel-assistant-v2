<template>
  <div class="warm-theme-component">
    <div class="warm-container">
      <div class="warm-header">
        <h3 class="warm-title">🌸 Warm & Cozy</h3>
      </div>
      <div class="warm-content">
        <slot>
          <p class="warm-text">A gentle, nurturing space for your thoughts and plans.</p>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Warm theme for ISFJ personalities
</script>

<style scoped>
.warm-theme-component {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 24px rgba(252, 182, 159, 0.3);
}

.warm-container {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
}

.warm-header {
  text-align: center;
  margin-bottom: 1rem;
}

.warm-title {
  color: #8b4513;
  margin: 0;
  font-size: 1.4rem;
  text-shadow: 1px 1px 2px rgba(139, 69, 19, 0.1);
}

.warm-content {
  color: #5d4037;
  line-height: 1.6;
}

.warm-text {
  margin: 0;
  font-size: 1rem;
  text-align: center;
  font-style: italic;
}
</style>
</template>
<template>
  <div class="flashy-styling">
    <div class="flashy-header">
      <h3 class="flashy-title">✨ Dynamic Style ✨</h3>
    </div>
    <div class="flashy-content">
      <slot>
        <p class="flashy-text">Eye-catching, energetic content!</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
// Flashy styling for ESTP personalities
</script>

<style scoped>
.flashy-styling {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
  animation: pulse 2s infinite;
}

.flashy-header {
  text-align: center;
  margin-bottom: 1rem;
}

.flashy-title {
  margin: 0;
  font-size: 1.5rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.flashy-content {
  text-align: center;
}

.flashy-text {
  font-size: 1.1rem;
  margin: 0;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}
</style>
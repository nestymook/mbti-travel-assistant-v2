<template>
  <div class="casual-layout">
    <div class="casual-header">
      <h2 class="casual-title">Flexible Itinerary</h2>
    </div>
    <div class="casual-content">
      <slot>
        <p>Casual, flexible content layout</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
// Casual layout for flexible personalities
</script>

<style scoped>
.casual-layout {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.casual-header {
  margin-bottom: 1rem;
}

.casual-title {
  color: #495057;
  font-weight: 500;
  margin: 0;
}

.casual-content {
  line-height: 1.6;
}
</style>
</template>
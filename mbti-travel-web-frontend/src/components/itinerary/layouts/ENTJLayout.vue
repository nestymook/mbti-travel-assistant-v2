<template>
  <div class="entj-layout">
    <div class="layout-header">
      <h1 class="layout-title">Executive Travel Plan</h1>
      <p class="layout-subtitle">Leadership-focused itinerary</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>ENTJ-specific executive layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
// ENTJ personality layout - executive and commanding
</script>

<style scoped>
.entj-layout {
  background: #fff;
  border: 3px solid #dc3545;
  border-radius: 10px;
  padding: 2rem;
}

.layout-header {
  border-bottom: 3px solid #dc3545;
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.layout-title {
  color: #dc3545;
  margin: 0 0 0.5rem 0;
  font-weight: 700;
  font-size: 1.8rem;
}

.layout-subtitle {
  color: #6c757d;
  margin: 0;
  font-weight: 500;
}
</style>
</template>
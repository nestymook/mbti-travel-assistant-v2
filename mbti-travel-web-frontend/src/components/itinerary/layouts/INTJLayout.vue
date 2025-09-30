<template>
  <div class="intj-layout">
    <div class="layout-header">
      <h1 class="layout-title">Strategic Travel Plan</h1>
      <p class="layout-subtitle">Organized and efficient itinerary</p>
    </div>
    <div class="layout-content">
      <slot>
        <p>INTJ-specific layout content</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
// INTJ personality layout - structured and strategic
</script>

<style scoped>
.intj-layout {
  background: #f8f9fa;
  border: 2px solid #495057;
  border-radius: 8px;
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.layout-header {
  border-bottom: 2px solid #007bff;
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.layout-title {
  color: #212529;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.layout-subtitle {
  color: #6c757d;
  margin: 0;
  font-style: italic;
}

.layout-content {
  line-height: 1.6;
}
</style>
</template>
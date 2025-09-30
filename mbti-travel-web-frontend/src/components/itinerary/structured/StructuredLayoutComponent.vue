<template>
  <div class="structured-layout">
    <div class="layout-header">
      <h2 class="layout-title">Structured Itinerary Layout</h2>
    </div>
    <div class="layout-content">
      <div class="layout-grid">
        <div class="main-content">
          <slot name="main-content">
            <p>Main itinerary content goes here</p>
          </slot>
        </div>
        <div class="sidebar">
          <slot name="sidebar">
            <div class="sidebar-section">
              <h3>Quick Actions</h3>
              <ul>
                <li>Add new item</li>
                <li>Reorder items</li>
                <li>Set priorities</li>
              </ul>
            </div>
          </slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'

// Structured layout for organized personalities
defineComponent({
  name: 'StructuredLayoutComponent'
})
</script>

<style scoped>
.structured-layout {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.layout-header {
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.layout-title {
  color: #495057;
  margin: 0;
}

.layout-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
}

.main-content {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.sidebar {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}
</style>
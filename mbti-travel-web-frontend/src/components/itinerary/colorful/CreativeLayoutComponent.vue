<template>
  <div class="creative-layout">
    <div class="creative-header">
      <h2 class="creative-title">🎨 Creative Journey</h2>
    </div>
    <div class="creative-content">
      <div class="content-sections">
        <div class="section-card">
          <slot name="main">
            <p>Main creative content</p>
          </slot>
        </div>
        <div class="section-card accent">
          <slot name="accent">
            <p>Accent section</p>
          </slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Creative layout for artistic personalities
</script>

<style scoped>
.creative-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 2rem;
  color: white;
  position: relative;
  overflow: hidden;
}

.creative-layout::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  pointer-events: none;
}

.creative-header {
  text-align: center;
  margin-bottom: 2rem;
  position: relative;
  z-index: 1;
}

.creative-title {
  margin: 0;
  font-size: 2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.creative-content {
  position: relative;
  z-index: 1;
}

.content-sections {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.section-card {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1.5rem;
  border: 1px solid rgba(255,255,255,0.2);
}

.section-card.accent {
  background: rgba(255,255,255,0.2);
}

@media (max-width: 768px) {
  .content-sections {
    grid-template-columns: 1fr;
  }
}
</style>
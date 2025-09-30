<template>
  <div class="social-sharing-component">
    <div class="sharing-header">
      <h3 class="sharing-title">📱 Share Your Journey</h3>
    </div>
    <div class="sharing-options">
      <div class="share-buttons">
        <button
          v-for="platform in socialPlatforms"
          :key="platform.name"
          @click="shareOn(platform)"
          class="share-btn"
          :style="{ background: platform.color }"
        >
          <span class="share-icon">{{ platform.icon }}</span>
          <span class="share-text">{{ platform.name }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SocialPlatform {
  name: string
  icon: string
  color: string
}

const socialPlatforms: SocialPlatform[] = [
  { name: 'Facebook', icon: '📘', color: '#1877f2' },
  { name: 'Twitter', icon: '🐦', color: '#1da1f2' },
  { name: 'Instagram', icon: '📷', color: '#e4405f' },
  { name: 'WhatsApp', icon: '💬', color: '#25d366' }
]

function shareOn(platform: SocialPlatform) {
  alert(`Sharing to ${platform.name}`)
}
</script>

<style scoped>
.social-sharing-component {
  background: #e8f5e8;
  border: 1px solid #c3e6cb;
  border-radius: 12px;
  padding: 1.5rem;
}

.sharing-title {
  color: #155724;
  margin: 0 0 1rem 0;
}

.share-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.share-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}
</style>
</template>
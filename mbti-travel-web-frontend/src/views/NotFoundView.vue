<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="not-found-icon">
        <span class="icon">🧭</span>
      </div>
      
      <h1 class="not-found-title">Page Not Found</h1>
      
      <p class="not-found-message">
        Oops! The page you're looking for doesn't exist or has been moved.
      </p>
      
      <div class="not-found-suggestions">
        <h3>Here are some suggestions:</h3>
        <ul>
          <li>Check the URL for typos</li>
          <li>Go back to the previous page</li>
          <li>Start fresh with your MBTI travel planning</li>
        </ul>
      </div>
      
      <div class="not-found-actions">
        <button 
          @click="goBack" 
          class="action-button secondary"
          :disabled="!canGoBack"
        >
          <span class="button-icon">←</span>
          Go Back
        </button>
        
        <router-link 
          to="/" 
          class="action-button primary"
        >
          <span class="button-icon">🏠</span>
          Go Home
        </router-link>
      </div>
      
      <div class="not-found-help">
        <p>
          Need help? Visit our 
          <router-link to="/about" class="help-link">About page</router-link>
          for more information.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Check if we can go back in history
const canGoBack = computed(() => {
  return window.history.length > 1
})

// Methods
function goBack(): void {
  if (canGoBack.value) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

// Set page title
onMounted(() => {
  document.title = 'Page Not Found - MBTI Travel Planner'
})
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 2rem;
}

.not-found-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.not-found-icon {
  margin-bottom: 2rem;
}

.not-found-icon .icon {
  font-size: 4rem;
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

.not-found-title {
  color: #2d3748;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  letter-spacing: -0.02em;
}

.not-found-message {
  color: #4a5568;
  font-size: 1.125rem;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.not-found-suggestions {
  text-align: left;
  background: #f7fafc;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.not-found-suggestions h3 {
  color: #2d3748;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.not-found-suggestions ul {
  color: #4a5568;
  line-height: 1.6;
  margin: 0;
  padding-left: 1.5rem;
}

.not-found-suggestions li {
  margin-bottom: 0.5rem;
}

.not-found-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  min-width: 120px;
  justify-content: center;
}

.action-button.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-button.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.action-button.secondary {
  background: white;
  color: #4a5568;
  border: 2px solid #e2e8f0;
}

.action-button.secondary:hover:not(:disabled) {
  background: #f7fafc;
  border-color: #cbd5e0;
  transform: translateY(-1px);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.button-icon {
  font-size: 1.125rem;
}

.not-found-help {
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.not-found-help p {
  color: #718096;
  font-size: 0.9rem;
  margin: 0;
}

.help-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.help-link:hover {
  text-decoration: underline;
}

/* Responsive design */
@media (max-width: 768px) {
  .not-found-container {
    padding: 1rem;
  }
  
  .not-found-content {
    padding: 2rem;
  }
  
  .not-found-title {
    font-size: 2rem;
  }
  
  .not-found-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .action-button {
    width: 100%;
    max-width: 200px;
  }
}

@media (max-width: 480px) {
  .not-found-content {
    padding: 1.5rem;
  }
  
  .not-found-title {
    font-size: 1.75rem;
  }
  
  .not-found-icon .icon {
    font-size: 3rem;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .not-found-icon .icon {
    animation: none;
  }
  
  .action-button {
    transition: none;
  }
  
  .action-button:hover {
    transform: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .not-found-content {
    border: 2px solid #000;
  }
  
  .action-button.secondary {
    border-width: 3px;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .not-found-container {
    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  }
  
  .not-found-content {
    background: #2d3748;
    color: #e2e8f0;
  }
  
  .not-found-title {
    color: #f7fafc;
  }
  
  .not-found-message {
    color: #cbd5e0;
  }
  
  .not-found-suggestions {
    background: #4a5568;
  }
  
  .not-found-suggestions h3 {
    color: #f7fafc;
  }
  
  .not-found-suggestions ul {
    color: #e2e8f0;
  }
  
  .action-button.secondary {
    background: #4a5568;
    color: #e2e8f0;
    border-color: #718096;
  }
  
  .action-button.secondary:hover:not(:disabled) {
    background: #718096;
  }
  
  .not-found-help {
    border-color: #4a5568;
  }
  
  .not-found-help p {
    color: #a0aec0;
  }
}
</style>
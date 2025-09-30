<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>Hong Kong MBTI Travel Planner</h1>
        <p>Please sign in to access your personalized travel itineraries</p>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <div class="login-content">
        <div class="login-icon">
          🔐
        </div>
        <p class="login-description">
          Secure authentication powered by AWS Cognito
        </p>
        
        <button
          type="button"
          @click="handleHostedUILogin"
          :disabled="isLoading"
          class="login-button"
        >
          <span v-if="isLoading">Redirecting to login...</span>
          <span v-else>Sign In</span>
        </button>
      </div>

      <div class="login-footer">
        <p>Don't have an account? Contact your administrator.</p>
        <p class="security-note">Your login is secured with AWS Cognito</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

// Computed
const isLoading = computed(() => authStore.isLoading)
const error = computed(() => authStore.error)

// Methods
async function handleHostedUILogin(): Promise<void> {
  try {
    authStore.redirectToHostedUI()
  } catch (err) {
    console.error('Hosted UI login failed:', err)
  }
}

// Check authentication status when component mounts
onMounted(() => {
  authStore.clearError()
  
  // Check if user is already authenticated
  if (authStore.isAuthenticated) {
    // User is already logged in, redirect to home
    window.location.href = '/'
    return
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-header {
  margin-bottom: 2rem;
}

.login-header h1 {
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.login-header p {
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.error-message {
  background-color: #fee;
  color: #c53030;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.9rem;
  border: 1px solid #fed7d7;
  margin-bottom: 1.5rem;
}

.login-content {
  margin: 2rem 0;
}

.login-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.8;
}

.login-description {
  color: #666;
  font-size: 0.95rem;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.login-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  width: 100%;
  max-width: 250px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e1e5e9;
}

.login-footer p {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.security-note {
  color: #888;
  font-size: 0.8rem;
  font-style: italic;
}

/* Responsive design */
@media (max-width: 480px) {
  .login-container {
    padding: 0.5rem;
  }
  
  .login-card {
    padding: 1.5rem;
  }
  
  .login-header h1 {
    font-size: 1.25rem;
  }
  
  .login-button {
    font-size: 1rem;
    padding: 0.875rem 1.5rem;
  }
}
</style>
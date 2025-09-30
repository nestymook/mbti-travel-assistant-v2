<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>Hong Kong MBTI Travel Planner</h1>
        <p>Please sign in to access your personalized travel itineraries</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            :disabled="isLoading"
            placeholder="Enter your email"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            :disabled="isLoading"
            placeholder="Enter your password"
            class="form-input"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="isLoading || !isFormValid"
          class="login-button"
        >
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign In</span>
        </button>
      </form>

      <div class="login-footer">
        <p>Don't have an account? Contact your administrator.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form state
const email = ref('')
const password = ref('')

// Computed
const isLoading = computed(() => authStore.isLoading)
const error = computed(() => authStore.error)
const isFormValid = computed(() => {
  return email.value.trim() !== '' && password.value.trim() !== ''
})

// Methods
async function handleLogin(): Promise<void> {
  if (!isFormValid.value) return

  try {
    await authStore.login(email.value.trim(), password.value)
    
    // Redirect to return URL or home page
    const returnUrl = route.query.returnUrl as string
    if (returnUrl) {
      await router.push(decodeURIComponent(returnUrl))
    } else {
      await router.push({ name: 'home' })
    }
  } catch (err) {
    // Error is handled by the store
    console.error('Login failed:', err)
  }
}

// Clear any existing errors when component mounts
onMounted(() => {
  authStore.clearError()
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
}

.login-header {
  text-align: center;
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.form-input {
  padding: 0.75rem;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.error-message {
  background-color: #fee;
  color: #c53030;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.9rem;
  border: 1px solid #fed7d7;
}

.login-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.875rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
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
  text-align: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e1e5e9;
}

.login-footer p {
  color: #666;
  font-size: 0.9rem;
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
}
</style>
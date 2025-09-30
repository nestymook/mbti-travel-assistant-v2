<template>
  <div class="callback-container">
    <div class="callback-card">
      <div class="loading-spinner">
        <div class="spinner"></div>
      </div>
      <h2>Authenticating...</h2>
      <p>Please wait while we complete your sign-in process.</p>
      
      <div v-if="error" class="error-message">
        <p>{{ error }}</p>
        <button @click="redirectToLogin" class="retry-button">
          Try Again
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { cognitoAuth } from '@/services/cognitoAuthService'

const router = useRouter()
const authStore = useAuthStore()
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    console.log('=== OAuth Callback Processing Started ===')
    console.log('Current URL:', window.location.href)
    console.log('User Agent:', navigator.userAgent)
    console.log('Referrer:', document.referrer)
    
    // Check if we have the required OAuth parameters
    const urlParams = new URLSearchParams(window.location.search)
    const authCode = urlParams.get('code')
    const state = urlParams.get('state')
    const errorParam = urlParams.get('error')
    const errorDescription = urlParams.get('error_description')
    
    console.log('OAuth parameters:', { 
      hasCode: !!authCode, 
      hasState: !!state, 
      error: errorParam,
      errorDescription: errorDescription,
      allParams: Object.fromEntries(urlParams.entries())
    })
    
    // Handle OAuth errors
    if (errorParam) {
      console.error('OAuth error parameter found:', errorParam, errorDescription)
      error.value = `Authentication error: ${errorParam}${errorDescription ? ` - ${errorDescription}` : ''}`
      setTimeout(() => redirectToLogin(), 5000)
      return
    }
    
    if (!authCode) {
      console.error('No authorization code found in callback URL')
      
      // Check if this might be a hash-based callback (some OAuth flows use hash)
      const hashParams = new URLSearchParams(window.location.hash.substring(1))
      const hashCode = hashParams.get('code')
      const hashAccessToken = hashParams.get('access_token')
      
      console.log('Checking hash parameters:', {
        hasHashCode: !!hashCode,
        hasHashAccessToken: !!hashAccessToken,
        hash: window.location.hash
      })
      
      if (!hashCode && !hashAccessToken) {
        error.value = 'Invalid authentication callback. Missing authorization code.'
        setTimeout(() => redirectToLogin(), 5000)
        return
      }
    }
    
    // Give Amplify more time to process the callback
    console.log('Waiting for Amplify to process OAuth callback...')
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Try multiple authentication approaches
    let authenticationSuccessful = false
    
    // Approach 1: Use Amplify's built-in OAuth callback processing
    try {
      console.log('Approach 1: Using Amplify OAuth callback processing...')
      const isAuthenticated = await cognitoAuth.processOAuthCallback()
      
      if (isAuthenticated) {
        console.log('Amplify OAuth callback successful!')
        authenticationSuccessful = true
      }
    } catch (amplifyError) {
      console.error('Amplify OAuth callback failed:', amplifyError)
    }
    
    // Approach 2: Manual token exchange if Amplify failed
    if (!authenticationSuccessful && authCode) {
      try {
        console.log('Approach 2: Manual token exchange...')
        const tokens = await cognitoAuth.exchangeCodeForTokens(authCode)
        console.log('Manual token exchange completed:', {
          hasAccessToken: !!tokens.access_token,
          hasIdToken: !!tokens.id_token,
          hasRefreshToken: !!tokens.refresh_token
        })
        
        // Wait for tokens to be processed
        await new Promise(resolve => setTimeout(resolve, 2000))
        authenticationSuccessful = true
      } catch (tokenError) {
        console.error('Manual token exchange failed:', tokenError)
      }
    }
    
    // Approach 3: Force refresh auth store and check multiple times
    if (authenticationSuccessful || authCode) {
      console.log('Approach 3: Updating auth store and checking authentication...')
      
      for (let attempt = 1; attempt <= 5; attempt++) {
        console.log(`Auth check attempt ${attempt}/5`)
        
        try {
          // Force refresh the auth store
          await authStore.initialize()
          
          if (authStore.isAuthenticated) {
            console.log(`Authentication confirmed on attempt ${attempt}!`)
            
            // Clean up URL parameters before redirecting
            window.history.replaceState({}, document.title, '/')
            
            // Success! Redirect to home page
            await router.push({ name: 'home' })
            return
          }
        } catch (storeError) {
          console.error(`Auth store update attempt ${attempt} failed:`, storeError)
        }
        
        // Wait before next attempt
        if (attempt < 5) {
          await new Promise(resolve => setTimeout(resolve, 1500))
        }
      }
    }
    
    // If we get here, all authentication attempts failed
    console.error('All authentication attempts failed')
    console.log('Final auth store state:', {
      isAuthenticated: authStore.isAuthenticated,
      isLoading: authStore.isLoading,
      error: authStore.error,
      user: authStore.user
    })
    
    error.value = 'Authentication failed after multiple attempts. Please try again.'
    
    // Redirect to login after a longer delay to allow user to read the error
    setTimeout(() => {
      redirectToLogin()
    }, 7000)
    
  } catch (err) {
    console.error('Auth callback error:', err)
    console.error('Error stack:', err.stack)
    error.value = 'An unexpected error occurred during authentication.'
    
    // Redirect to login after a delay
    setTimeout(() => {
      redirectToLogin()
    }, 5000)
  }
})

function redirectToLogin(): void {
  router.push({ name: 'login' })
}
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.callback-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 3rem 2rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.loading-spinner {
  margin-bottom: 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e1e5e9;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

h2 {
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

p {
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.error-message {
  background-color: #fee;
  color: #c53030;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #fed7d7;
  margin-top: 2rem;
}

.retry-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 1rem;
  transition: background-color 0.2s ease;
}

.retry-button:hover {
  background: #5a67d8;
}

/* Responsive design */
@media (max-width: 480px) {
  .callback-container {
    padding: 0.5rem;
  }
  
  .callback-card {
    padding: 2rem 1.5rem;
  }
  
  h2 {
    font-size: 1.25rem;
  }
}
</style>
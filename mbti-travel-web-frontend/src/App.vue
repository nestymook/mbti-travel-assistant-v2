<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { CognitoAuthService } from '@/services/cognitoAuthService'
import ErrorNotificationSystem from '@/components/common/ErrorNotificationSystem.vue'
import { usePerformanceMonitoring, useBundleOptimization, useMemoryManagement } from '@/composables/usePerformanceOptimizations'

const route = useRoute()
const authStore = useAuthStore()

// Performance optimizations
const { recordMetric, timeOperation } = usePerformanceMonitoring('App')
const { preloadChunk, preloadResource } = useBundleOptimization()
const { registerCleanup } = useMemoryManagement()

// Reactive state
const isMobileMenuOpen = ref(false)

// Computed
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isLoginPage = computed(() => route.name === 'login')
const userDisplayName = computed(() => authStore.userDisplayName)

// Methods
function handleLogout(): void {
  closeMobileMenu()
  
  // Use Cognito Hosted UI for logout
  try {
    const cognitoAuth = CognitoAuthService.getInstance()
    const hostedUILogoutUrl = cognitoAuth.getHostedUILogoutUrl()
    window.location.href = hostedUILogoutUrl
  } catch (error) {
    console.error('Failed to redirect to Cognito Hosted UI logout:', error)
    // Fallback to regular logout
    authStore.logout()
  }
}

function toggleMobileMenu(): void {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
  
  // Update aria-expanded attribute
  const toggleButton = document.querySelector('.nav-toggle')
  if (toggleButton) {
    toggleButton.setAttribute('aria-expanded', String(isMobileMenuOpen.value))
  }
  
  // Prevent body scroll when menu is open
  if (isMobileMenuOpen.value) {
    document.body.classList.add('nav-menu-open')
  } else {
    document.body.classList.remove('nav-menu-open')
  }
}

function closeMobileMenu(): void {
  isMobileMenuOpen.value = false
  document.body.classList.remove('nav-menu-open')
  
  // Update aria-expanded attribute
  const toggleButton = document.querySelector('.nav-toggle')
  if (toggleButton) {
    toggleButton.setAttribute('aria-expanded', 'false')
  }
}

// Close mobile menu when route changes
watch(() => route.path, () => {
  closeMobileMenu()
})

// Close mobile menu on escape key
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && isMobileMenuOpen.value) {
    closeMobileMenu()
  }
}

// Initialize auth on app mount
onMounted(async () => {
  const endTiming = timeOperation('app-initialization')
  
  try {
    await authStore.initialize()
    
    // Preload critical resources (main.css is already imported in main.ts)
    // preloadResource('/assets/styles/main.css', 'style')
    
    // Preload common chunks
    await preloadChunk('vue-vendor', () => import('vue'))
    
    // Add keyboard event listener
    document.addEventListener('keydown', handleKeydown)
    
    recordMetric('app-initialization-success', 1)
  } catch (error) {
    recordMetric('app-initialization-error', 1)
    console.error('App initialization failed:', error)
  } finally {
    endTiming()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.classList.remove('nav-menu-open')
  
  // Register cleanup for memory management
  registerCleanup(() => {
    // Clean up any remaining event listeners or timers
    console.debug('App cleanup completed')
  })
})
</script>

<template>
  <div id="app">

    
    <!-- Responsive navigation header - only show when authenticated and not on login page -->
    <header v-if="isAuthenticated && !isLoginPage" class="responsive-nav" role="banner">
      <div class="nav-container">
        <div class="nav-logo">
          <RouterLink to="/" class="nav-logo-link">
            <span class="nav-logo-icon">🧭</span>
            <span>Hong Kong MBTI Travel Planner</span>
          </RouterLink>
        </div>

        <!-- Mobile menu toggle -->
        <button
          class="nav-toggle"
          :class="{ active: isMobileMenuOpen }"
          @click="toggleMobileMenu"
          aria-label="Toggle navigation menu"
          aria-expanded="false"
          aria-controls="nav-menu"
        >
          <span class="nav-toggle-bar"></span>
          <span class="nav-toggle-bar"></span>
          <span class="nav-toggle-bar"></span>
        </button>

        <!-- Navigation menu -->
        <nav
          id="nav-menu"
          class="nav-menu"
          :class="{ active: isMobileMenuOpen }"
          role="navigation"
          aria-label="Main navigation"
        >
          <div class="nav-menu-item">
            <RouterLink 
              to="/" 
              class="nav-link" 
              @click="closeMobileMenu"
              v-preload-route="'home'"
            >
              <span>🏠</span>
              <span>Home</span>
            </RouterLink>
          </div>
          <div class="nav-menu-item">
            <RouterLink 
              to="/about" 
              class="nav-link" 
              @click="closeMobileMenu"
              v-preload-route="'about'"
            >
              <span>ℹ️</span>
              <span>About</span>
            </RouterLink>
          </div>
          
          <!-- User section in mobile menu - Hidden to avoid duplicate -->
          <!-- <div class="nav-user-section nav-menu-item">
            <button @click="handleLogout" class="nav-logout-btn">
              <span>👋</span>
              <span>Sign Out</span>
            </button>
          </div> -->
        </nav>

        <!-- Desktop user section -->
        <div class="nav-user-section d-none d-md-flex">
          <button @click="handleLogout" class="nav-logout-btn">
            Sign Out
          </button>
        </div>
      </div>
    </header>

    <!-- Mobile menu overlay -->
    <div
      v-if="isMobileMenuOpen"
      class="nav-overlay"
      :class="{ active: isMobileMenuOpen }"
      @click="closeMobileMenu"
      aria-hidden="true"
    ></div>

    <!-- Main content -->
    <main
      id="main-content"
      class="main-content"
      :class="{ 'with-header': isAuthenticated && !isLoginPage }"
      role="main"
    >
      <RouterView />
    </main>

    <!-- Global error notification system -->
    <ErrorNotificationSystem />
  </div>
</template>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.main-content.with-header {
  padding-top: 0;
}



/* Responsive navigation styles are imported from responsive-navigation.css */

/* Ensure proper stacking context */
.responsive-nav {
  position: relative;
  z-index: 100;
}

.nav-overlay {
  z-index: 99;
}

/* Main content spacing */
@media (min-width: 768px) {
  .main-content.with-header {
    margin-top: 0;
  }
}

/* Focus management */
.nav-logo-link:focus-visible,
.nav-link:focus-visible,
.nav-toggle:focus-visible,
.nav-logout-btn:focus-visible {
  outline: 2px solid var(--mbti-surface, #ffffff);
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .responsive-nav {
    border-bottom: 2px solid var(--mbti-surface, #ffffff);
  }
  
  .nav-link,
  .nav-logout-btn {
    border: 1px solid transparent;
  }
  
  .nav-link:hover,
  .nav-link.router-link-active,
  .nav-logout-btn:hover {
    border-color: var(--mbti-surface, #ffffff);
  }
}

/* Print styles */
@media print {
  .responsive-nav {
    display: none;
  }
  

  
  .main-content {
    padding: 0;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .nav-toggle-bar,
  .nav-menu,
  .nav-menu-item,
  .nav-link,
  .nav-logout-btn {
    transition: none;
  }
  
  .nav-menu.active .nav-menu-item {
    transition-delay: 0s;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .responsive-nav {
    background: var(--mbti-primary, #0056b3);
  }
}

/* Ensure mobile menu doesn't interfere with main content */
.main-content {
  position: relative;
  z-index: 1;
}

/* Body scroll lock styles are handled in responsive-navigation.css */
</style>

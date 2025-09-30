<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <header class="app-header">
      <h1>🧭 MBTI Travel Planner</h1>
      <p>Discover your perfect Hong Kong itinerary based on your personality type</p>
    </header>
    
    <main class="main-content">
      <RouterView />
    </main>
    
    <footer class="app-footer">
      <p>&copy; 2025 MBTI Travel Planner</p>
    </footer>
  </div>
</template>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.app-header {
  text-align: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.app-header h1 {
  font-size: 2.5rem;
  margin: 0 0 1rem 0;
  font-weight: 700;
}

.app-header p {
  font-size: 1.2rem;
  margin: 0;
  opacity: 0.9;
}

.main-content {
  flex: 1;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.app-footer {
  text-align: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .app-header h1 {
    font-size: 2rem;
  }
  
  .app-header p {
    font-size: 1rem;
  }
  
  .main-content {
    padding: 1rem;
  }
}
</style>
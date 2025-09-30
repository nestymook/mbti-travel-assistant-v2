import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setupGlobalErrorHandling } from './utils/globalErrorHandler'
import { vPreloadRoute, vPreloadOnVisible } from './utils/routePreloader'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Register route preloading directives
app.directive('preload-route', vPreloadRoute)
app.directive('preload-on-visible', vPreloadOnVisible)

// Set up global error handling
setupGlobalErrorHandling(app)

app.mount('#app')

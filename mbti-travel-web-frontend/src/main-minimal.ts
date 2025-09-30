import { createApp } from 'vue'
import App from './App-minimal.vue'
import router from './router/index-minimal'

const app = createApp(App)

app.use(router)

app.mount('#app')

console.log('MBTI Travel App initialized successfully!')
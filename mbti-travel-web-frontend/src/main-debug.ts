import './assets/main.css'

// Global error handler to catch and display errors
window.addEventListener('error', (event) => {
  console.error('Global Error:', event.error)
  console.error('Error details:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error
  })
  
  // Display error on page for debugging
  const errorDiv = document.createElement('div')
  errorDiv.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    background: #ff4444;
    color: white;
    padding: 10px;
    border-radius: 5px;
    z-index: 9999;
    font-family: monospace;
    font-size: 12px;
    max-height: 200px;
    overflow-y: auto;
  `
  errorDiv.innerHTML = `
    <strong>JavaScript Error:</strong><br>
    ${event.message}<br>
    <small>File: ${event.filename}:${event.lineno}:${event.colno}</small><br>
    <small>Stack: ${event.error?.stack || 'No stack trace'}</small>
  `
  document.body.appendChild(errorDiv)
})

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason)
  
  const errorDiv = document.createElement('div')
  errorDiv.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    background: #ff8800;
    color: white;
    padding: 10px;
    border-radius: 5px;
    z-index: 9999;
    font-family: monospace;
    font-size: 12px;
    max-height: 200px;
    overflow-y: auto;
  `
  errorDiv.innerHTML = `
    <strong>Promise Rejection:</strong><br>
    ${event.reason}<br>
    <small>Stack: ${event.reason?.stack || 'No stack trace'}</small>
  `
  document.body.appendChild(errorDiv)
})

console.log('🚀 Starting MBTI Travel App...')
console.log('Environment:', import.meta.env.MODE)
console.log('Base URL:', import.meta.env.BASE_URL)

try {
  console.log('📦 Importing Vue...')
  const { createApp } = await import('vue')
  console.log('✅ Vue imported successfully')
  
  console.log('📦 Importing Pinia...')
  const { createPinia } = await import('pinia')
  console.log('✅ Pinia imported successfully')

  console.log('📦 Importing App component...')
  const App = await import('./App.vue')
  console.log('✅ App component imported successfully')

  console.log('📦 Importing router...')
  const router = await import('./router')
  console.log('✅ Router imported successfully')

  console.log('🏗️ Creating Vue app...')
  const app = createApp(App.default)

  console.log('🔌 Installing Pinia...')
  app.use(createPinia())

  console.log('🔌 Installing Router...')
  app.use(router.default)

  console.log('🎯 Mounting app to #app...')
  app.mount('#app')

  console.log('✨ MBTI Travel App mounted successfully!')
  
  // Add success indicator
  const successDiv = document.createElement('div')
  successDiv.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: #44ff44;
    color: black;
    padding: 10px;
    border-radius: 5px;
    z-index: 9999;
    font-family: monospace;
    font-size: 12px;
  `
  successDiv.innerHTML = '✅ App loaded successfully!'
  document.body.appendChild(successDiv)
  
  // Remove success indicator after 3 seconds
  setTimeout(() => {
    successDiv.remove()
  }, 3000)

} catch (error) {
  console.error('❌ Failed to initialize app:', error)
  
  // Display initialization error
  const errorDiv = document.createElement('div')
  errorDiv.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #ff0000;
    color: white;
    padding: 20px;
    border-radius: 10px;
    z-index: 9999;
    font-family: monospace;
    max-width: 80%;
    text-align: center;
  `
  errorDiv.innerHTML = `
    <h2>❌ App Initialization Failed</h2>
    <p><strong>Error:</strong> ${error.message}</p>
    <p><strong>Stack:</strong></p>
    <pre style="text-align: left; font-size: 10px; overflow-x: auto;">${error.stack}</pre>
    <p><small>Check browser console for more details</small></p>
  `
  document.body.appendChild(errorDiv)
}
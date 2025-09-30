import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue({
        // Enable script setup and other optimizations
        script: {
          defineModel: true,
          propsDestructure: true
        }
      }),
      // Only include dev tools in development
      ...(mode === 'development' ? [vueDevTools()] : []),
      // Bundle analyzer (only when --analyze flag is used)
      ...(process.argv.includes('--analyze') ? [
        visualizer({
          filename: 'dist/stats.html',
          open: true,
          gzipSize: true,
          brotliSize: true
        })
      ] : []),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      // Performance optimizations
      target: 'esnext',
      minify: mode === 'production' ? 'terser' : false,
      ...(mode === 'production' && {
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
            pure_funcs: ['console.log', 'console.debug']
          }
        }
      }),
      // Code splitting configuration
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            // Vendor chunks
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'utils': ['axios'],

            // Personality-specific chunks
            'personality-structured': [
              './src/components/itinerary/layouts/INTJLayout.vue',
              './src/components/itinerary/layouts/ENTJLayout.vue',
              './src/components/itinerary/layouts/ISTJLayout.vue',
              './src/components/itinerary/layouts/ESTJLayout.vue'
            ],
            'personality-flexible': [
              './src/components/itinerary/layouts/INTPLayout.vue',
              './src/components/itinerary/layouts/ISTPLayout.vue',
              './src/components/itinerary/layouts/ESTPLayout.vue'
            ],
            'personality-colorful': [
              './src/components/itinerary/layouts/ENTPLayout.vue',
              './src/components/itinerary/layouts/INFPLayout.vue',
              './src/components/itinerary/layouts/ENFPLayout.vue',
              './src/components/itinerary/layouts/ISFPLayout.vue',
              './src/components/itinerary/layouts/ESFPLayout.vue'
            ],
            'personality-feeling': [
              './src/components/itinerary/layouts/INFJLayout.vue',
              './src/components/itinerary/layouts/ISFJLayout.vue',
              './src/components/itinerary/layouts/ENFJLayout.vue',
              './src/components/itinerary/layouts/ESFJLayout.vue'
            ]
          },
          // Optimize chunk file names
          chunkFileNames: (chunkInfo) => {
            const facadeModuleId = chunkInfo.facadeModuleId
            if (facadeModuleId) {
              if (facadeModuleId.includes('personality')) {
                return 'assets/personality-[name]-[hash].js'
              }
              if (facadeModuleId.includes('components')) {
                return 'assets/components-[name]-[hash].js'
              }
            }
            return 'assets/[name]-[hash].js'
          },
          // Optimize asset file names
          assetFileNames: (assetInfo) => {
            if (/\.(css)$/.test(assetInfo.name || '')) {
              return 'assets/styles/[name]-[hash].[ext]'
            }
            if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name || '')) {
              return 'assets/images/[name]-[hash].[ext]'
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
              return 'assets/fonts/[name]-[hash].[ext]'
            }
            return 'assets/[name]-[hash].[ext]'
          }
        }
      },
      // Optimize chunk size warnings
      chunkSizeWarningLimit: 1000,
      // Enable source maps for production debugging (optional)
      sourcemap: mode === 'production' ? false : true,
      // Report compressed size
      reportCompressedSize: mode === 'production',
      // Optimize CSS code splitting
      cssCodeSplit: true,
      // Optimize asset inlining threshold
      assetsInlineLimit: 4096
    },
    // Development server optimizations
    server: {
      // Optimize HMR
      hmr: {
        overlay: true
      },
      // Configure proxy for API calls in development
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    // Dependency optimization
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios'
      ],
      exclude: [
        // Exclude personality components from pre-bundling to enable lazy loading
        '@/components/itinerary/layouts/*'
      ]
    },
    // CSS optimization
    css: {
      devSourcemap: true,
      preprocessorOptions: {
        scss: {
          // Add global SCSS variables if needed
          additionalData: `
          @import "@/styles/variables.scss";
        `
        }
      }
    },
    // Performance monitoring in development
    define: {
      __PERFORMANCE_MONITORING__: JSON.stringify(mode === 'development'),
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString())
    },

    // Environment-specific configuration
    base: env.VITE_BASE_URL || '/',

    // Preview server configuration for production testing
    preview: {
      port: 4173,
      host: true,
      strictPort: true
    }
  }
})

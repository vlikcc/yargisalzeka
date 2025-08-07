import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      react(),
      tailwindcss(),
      // Bundle analizi için (sadece build sırasında)
      isProduction && visualizer({
        filename: './dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      })
    ].filter(Boolean),
    
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    
    server: {
      proxy: {
        '/api': {
          target: process.env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    },
    
    build: {
      // Production optimizasyonları
      target: 'es2015',
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: isProduction,
          drop_debugger: isProduction,
        },
      },
      rollupOptions: {
        output: {
          // Chunk splitting
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-label'],
            'utils': ['clsx', 'tailwind-merge', 'date-fns'],
          },
          // Asset naming
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const extType = info[info.length - 1]
            if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
              return `assets/images/[name]-[hash][extname]`
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
              return `assets/fonts/[name]-[hash][extname]`
            }
            if (extType === 'css') {
              return `assets/css/[name]-[hash][extname]`
            }
            return `assets/[name]-[hash][extname]`
          },
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },
      // Chunk size warnings
      chunkSizeWarningLimit: 1000,
      // Source maps for production debugging
      sourcemap: isProduction ? 'hidden' : true,
      // CSS code splitting
      cssCodeSplit: true,
      // Asset inlining threshold
      assetsInlineLimit: 4096,
    },
    
    // Environment variable prefix
    envPrefix: 'VITE_',
    
    // Optimizations
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom'],
    },
  }
})

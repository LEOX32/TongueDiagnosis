import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      vue(),
      vueJsx(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_URL || 'http://localhost:5000',
          changeOrigin: true,
          rewrite: (path) => path
        }
      }
    },
    base: './',
    build: {
      outDir: 'dist'
    },
    preview: {
      host: '0.0.0.0',
      port: 4173,
      allowedHosts: [
        'localhost',
        '.cpolar.top',
        '.cpolar.cn',
        '.ngrok.io',
        '.ngrok-free.app'
      ]
    }
  }
})

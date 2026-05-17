import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@core': fileURLToPath(new URL('./src/core', import.meta.url)),
      '@features': fileURLToPath(new URL('./src/features', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // BACKEND_URL puede apuntar al backend nativo en el host:
      //   - docker compose (frontend en docker, backend nativo): http://host.docker.internal:8000
      //   - todo nativo:                                           http://localhost:8000
      //   - todo en docker:                                        http://backend:8000
      '/api': {
        target: process.env.BACKEND_URL ?? 'http://host.docker.internal:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.BACKEND_URL ?? 'http://host.docker.internal:8000').replace(
          /^http/,
          'ws',
        ),
        ws: true,
      },
    },
  },
})

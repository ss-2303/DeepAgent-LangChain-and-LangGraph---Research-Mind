import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /research to FastAPI so we avoid CORS in production
    proxy: {
      '/research': 'http://localhost:8000',
      '/health':   'http://localhost:8000',
    }
  }
})

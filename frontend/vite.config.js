import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',   // bind to all interfaces so Docker can expose the port
    port: 5173,
    proxy: {
      // Proxy all API, WebSocket and health calls to the FastAPI backend
      '/api':          { target: 'http://app:8001', changeOrigin: true },
      '/ws':           { target: 'ws://app:8001',   changeOrigin: true, ws: true },
      '/media-stream': { target: 'ws://app:8001',   changeOrigin: true, ws: true },
      '/ping':         { target: 'http://app:8001', changeOrigin: true },
      '/token':        { target: 'http://app:8001', changeOrigin: true },
      '/recordings':   { target: 'http://app:8001', changeOrigin: true },
    },
  },
})

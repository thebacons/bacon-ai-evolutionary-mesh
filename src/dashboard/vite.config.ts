import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://srv906866.hstgr.cloud:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: '../control_plane/static',
    emptyOutDir: true
  }
})

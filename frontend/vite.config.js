import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    host: true,
    // Accept Host headers from Cloudflare Quick Tunnels and any LAN IP
    allowedHosts: ['.trycloudflare.com', '.ngrok-free.app', '.ngrok.io', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': 'http://localhost:8000',
      '/images': 'http://localhost:8000',
    }
  }
})

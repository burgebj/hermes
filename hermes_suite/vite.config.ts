import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

const proxyTarget = process.env.VITE_HERMES_GATEWAY_URL ?? 'http://localhost:8642'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: 'HermesSuite',
        short_name: 'HermesSuite',
        description: 'Command centre for the Hermes AI agent',
        theme_color: '#0a0a0f',
        background_color: '#0a0a0f',
        display: 'standalone',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/gateway': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/gateway/, ''),
      },
      '/api/chat': {
        target: proxyTarget,
        changeOrigin: true,
      },
      '/api/mcp': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/mcp/, '/mcp'),
      },
    },
  },
})

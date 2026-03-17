import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

const isDesktop = process.env.BUILD_MODE === 'desktop';

export default defineConfig({
  plugins: [react()],
  base: isDesktop ? './' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8420',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8420',
        ws: true,
      },
    },
  },
  build: {
    outDir: '../foundrai/frontend/dist',
    emptyOutDir: true,
    // Performance optimizations
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    // Code splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@dnd-kit/core', '@dnd-kit/sortable', 'react-window'],
          'chart-vendor': ['recharts'],
          'flow-vendor': ['reactflow'],
        },
      },
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});

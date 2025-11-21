import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Base path for Electron renderer process
  base: './',

  // Configure the root directory for the renderer
  root: path.resolve(__dirname, 'src/ui/desktop/renderer'),

  // Public directory for static assets
  publicDir: path.resolve(__dirname, 'public'),

  // Build configuration
  build: {
    // Output directory relative to project root
    outDir: path.resolve(__dirname, 'dist/renderer'),

    // Clear output directory before build
    emptyOutDir: true,

    // Generate sourcemaps for debugging
    sourcemap: true,

    // Rollup options for Electron
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/ui/desktop/renderer/index.html'),
      },
    },

    // Target ES2020 for modern Electron versions
    target: 'es2020',

    // Optimize dependencies
    minify: 'esbuild',

    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
  },

  // Development server configuration
  server: {
    port: 5173,
    strictPort: true,

    // Configure CORS for Electron
    cors: true,

    // Hot module replacement
    hmr: true,
  },

  // Resolve configuration
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@renderer': path.resolve(__dirname, 'src/ui/desktop/renderer'),
      '@components': path.resolve(__dirname, 'src/ui/desktop/renderer/components'),
      '@hooks': path.resolve(__dirname, 'src/ui/desktop/renderer/hooks'),
      '@utils': path.resolve(__dirname, 'src/ui/desktop/renderer/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
    },
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
  },

  // Optimizations
  optimizeDeps: {
    exclude: ['electron'],
    include: ['react', 'react-dom'],
  },

  // Clear console on dev server start
  clearScreen: false,
});

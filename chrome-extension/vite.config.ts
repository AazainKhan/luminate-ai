import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { copyFileSync } from 'fs'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-extension-files',
      writeBundle() {
        // Copy manifest.json to dist
        copyFileSync('manifest.json', 'dist/manifest.json')
        console.log('✓ Copied manifest.json to dist/')
        
        // Note: sidepanel.html is processed by Vite, no need to copy
        
        // Copy icon if it exists
        try {
          copyFileSync('icon.svg', 'dist/icon.svg')
          console.log('✓ Copied icon.svg to dist/')
        } catch (e) {
          console.log('⚠️  No icon.svg found (optional)')
        }
      }
    }
  ],
  // Use relative paths for Chrome extension
  base: './',
  build: {
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'popup.html'),
        sidepanel: resolve(__dirname, 'sidepanel.html'),
        background: resolve(__dirname, 'src/background/index.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
        // Use ES format - we'll configure manifest to load as modules
        format: 'es',
      }
    },
    outDir: 'dist',
    sourcemap: false,
    minify: false,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// import { crx } from '@crxjs/vite-plugin' // Disabled - causing background.js resolution issues
import { resolve } from 'path'
import { copyFileSync } from 'fs'
import manifest from './manifest.json'

export default defineConfig({
  plugins: [
    react(),
    // crx({ manifest }), // Disabled - manual bundling instead
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
        // popup: resolve(__dirname, 'popup.html'), // Disabled - uses Grok UI with type issues
        sidepanel: resolve(__dirname, 'sidepanel.html'),
        background: resolve(__dirname, 'src/background/index.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: (chunkInfo) => {
          // Remove underscore prefix from chunk names for Chrome extension compatibility
          const name = chunkInfo.name.startsWith('_') 
            ? chunkInfo.name.substring(1) 
            : chunkInfo.name;
          return `${name}.js`;
        },
        assetFileNames: (assetInfo) => {
          // Remove underscore prefix from asset names
          const name = assetInfo.name?.startsWith('_') 
            ? assetInfo.name.substring(1) 
            : assetInfo.name;
          return `${name}`;
        },
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

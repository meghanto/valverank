import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// relative base so the build works under a GitHub Pages sub-path
export default defineConfig({
  base: './',
  plugins: [react()],
})

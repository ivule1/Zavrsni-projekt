import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // fiksni port - razlicit od frontend-terminal (5173) da oba mogu raditi
  // istovremeno, i da backend CORS whitelist moze biti tocno odredjena
  server: {
    port: 5174,
    strictPort: true,
  },
})

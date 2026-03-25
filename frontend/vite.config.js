import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [tailwindcss(), vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    origin: 'http://127.0.0.1', 
    hmr: {
      path: '/proxy/5173/',
      clientPort: 8080
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
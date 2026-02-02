import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [tailwindcss(), vue()],
  server: {
    host: '0.0.0.0', // 允许从容器/宿主机外部访问
    port: 5173,      // 固定端口
    // 关键配置：解决静态资源路径问题
    origin: 'http://127.0.0.1', 
    // 关键配置：解决热更新 (HMR) 失败导致的白屏或不刷新
    hmr: {
      path: '/proxy/5173/',
      clientPort: 8080 // 让 WebSocket 也能走 code-server 的转发端口
    }
  }
});
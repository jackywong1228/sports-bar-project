import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    // PWA 已移除：根作用域 Service Worker 会劫持整域名（含 /staff/、/coach/），
    // 旧缓存导致员工端白屏/按钮失灵。public/sw.js 内置自毁脚本用于清理存量客户端。
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

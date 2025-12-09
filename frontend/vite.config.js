import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 后端服务器地址配置 - 修改这里即可切换环境
const BACKEND_HOST = '192.168.95.32'
const BACKEND_PORT = '5000'
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  define: {
    // 为 simple-peer 提供 global 变量 polyfill
    global: 'globalThis',
    // 注入后端地址到全局变量，供运行时使用
    __API_BASE_URL__: JSON.stringify(BACKEND_URL)
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // 允许局域网访问
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true
      }
    }
  }
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import basicSsl from '@vitejs/plugin-basic-ssl'

// 后端服务器地址配置 - 修改这里即可切换环境
const BACKEND_HOST = '192.168.95.21'
const BACKEND_PORT = '5000'
// 使用 HTTPS 连接后端
const BACKEND_URL = `https://${BACKEND_HOST}:${BACKEND_PORT}`

export default defineConfig({
  plugins: [
    vue(),
    // 为 simple-peer 提供 Node.js polyfills
    nodePolyfills({
      include: ['buffer', 'process', 'stream', 'util', 'events'],
      globals: {
        Buffer: true,
        global: true,
        process: true
      }
    }),
    // 启用 HTTPS - 允许局域网设备访问摄像头/麦克风
    basicSsl()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  define: {
    // 注入后端地址到全局变量，供运行时使用
    __API_BASE_URL__: JSON.stringify(BACKEND_URL)
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // 允许局域网访问
    https: true,     // 启用 HTTPS
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false  // 允许自签名证书
      }
    }
  }
})

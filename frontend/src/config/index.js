/**
 * 前端配置文件
 * 统一管理后端 API 地址等配置
 * 
 * 注意：主要配置在 vite.config.js 中修改
 * 这里通过 __API_BASE_URL__ 获取编译时注入的值
 */

// 从 Vite 编译时注入的全局变量获取后端地址
// 如果没有注入，则使用默认值
const API_BASE = typeof __API_BASE_URL__ !== 'undefined' 
  ? __API_BASE_URL__ 
  : 'http://192.168.95.32:5000'

// 导出配置
export const config = {
  // 后端 API 基础地址
  apiBaseUrl: API_BASE,
  
  // WebSocket 地址
  wsUrl: API_BASE,
  
  // 静态资源地址（图片、文件等）
  staticUrl: API_BASE,
}

export default config

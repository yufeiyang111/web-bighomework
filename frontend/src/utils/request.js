import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 如果配置了skipAuth，则不添加token
    if (config.skipAuth) {
      delete config.skipAuth
      return config
    }
    
    // 从 localStorage 获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
      console.log('发送请求:', config.url, '\nToken:', token.substring(0, 50) + '...')
    } else {
      console.warn('请求时未找到token:', config.url)
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          console.error('401错误详情:', data)
          ElMessage.error(data.message || '未授权，请重新登录')
          // 暂时注释掉自动跳转，以便调试
          // localStorage.removeItem('token')
          // window.location.href = '/login'
          break
        case 403:
          ElMessage.error(data.message || '权限不足')
          break
        case 404:
          ElMessage.error(data.message || '请求的资源不存在')
          break
        case 422:
          // 422 通常是验证错误或JWT错误
          console.error('422 错误详情:', data)
          ElMessage.error(data.msg || data.message || 'Token验证失败，请重新登录')
          // 清除token并跳转到登录页
          localStorage.removeItem('token')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1500)
          break
        case 500:
          ElMessage.error(data.message || '服务器错误')
          break
        default:
          ElMessage.error(data.message || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default request

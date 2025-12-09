import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, verifyToken, register as registerApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

/**
 * 用户状态管理Store
 * 
 * 功能：
 * - 用户认证：登录、注册、退出
 * - Token管理：存储和验证JWT令牌
 * - 用户信息：获取和存储用户数据
 * - 状态持久化：将token存储到localStorage
 */
export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const userRole = computed(() => userInfo.value?.role || '')
  const permissions = computed(() => userInfo.value?.permissions || [])
  const systemAccount = computed(() => userInfo.value?.systemAccount || '')
  
  /**
   * 登录方法
   */
  const loginAction = async (email, password) => {
    try {
      const response = await loginApi(email, password)
      
      if (response.success) {
        // 存储token到localStorage
        token.value = response.token
        localStorage.setItem('token', response.token)
        
        // 存储用户信息到内存
        userInfo.value = response.userInfo
        
        ElMessage.success(response.message || '登录成功')
        return { success: true }
      } else {
        ElMessage.error(response.message || '登录失败')
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('登录失败详情:', error)
      let errorMessage = '登录失败，请稍后重试'
      
      // 更详细的错误处理
      if (error.response) {
        // 服务器返回了错误响应
        errorMessage = error.response.data?.message || `服务器错误 (${error.response.status})`
      } else if (error.request) {
        // 请求已发送但没有收到响应
        errorMessage = '网络错误，无法连接到服务器'
      }
      
      ElMessage.error(errorMessage)
      return { success: false, message: errorMessage }
    }
  }
  
  /**
   * 注册方法
   */
  const registerAction = async (registerData) => {
    try {
      const response = await registerApi(registerData)
      
      if (response.success) {
        ElMessage.success(response.message || '注册成功')
        return { success: true, data: response }
      } else {
        ElMessage.error(response.message || '注册失败')
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('注册失败:', error)
      ElMessage.error('注册失败，请稍后重试')
      return { success: false, message: '注册失败' }
    }
  }
  
  /**
   * 退出登录方法
   */
  const logoutAction = async () => {
    try {
      await logoutApi()
    } catch (error) {
      console.error('退出登录API调用失败:', error)
    } finally {
      // 无论API调用是否成功，都清除本地状态
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
      ElMessage.success('已退出登录')
    }
  }
  
  /**
   * 验证Token方法
   * 用于页面刷新或应用启动时验证token有效性
   */
  const verifyTokenAction = async () => {
    if (!token.value) {
      return false
    }
    
    try {
      const response = await verifyToken()
      
      if (response.success) {
        userInfo.value = response.userInfo
        return true
      } else {
        // Token无效，清除状态
        token.value = ''
        userInfo.value = null
        localStorage.removeItem('token')
        return false
      }
    } catch (error) {
      console.error('Token验证失败:', error)
      // 验证失败，清除状态
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
      return false
    }
  }
  
  /**
   * 获取用户数据库的方法
   * 返回存储在userInfo中的用户数据
   */
  const getUserData = () => {
    return userInfo.value
  }
  
  /**
   * 检查用户是否拥有特定权限
   */
  const hasPermission = (permission) => {
    return permissions.value.includes(permission)
  }
  
  /**
   * 检查用户是否拥有特定角色
   */
  const hasRole = (role) => {
    return userRole.value === role
  }
  
  /**
   * 更新用户信息
   */
  const updateUserInfo = (newUserInfo) => {
    userInfo.value = { ...userInfo.value, ...newUserInfo }
  }
  
  // 导出接口
  return {
    // 状态
    token,
    userInfo,
    
    // 计算属性
    isLoggedIn,
    userRole,
    permissions,
    systemAccount,
    
    // 方法
    loginAction,
    registerAction,
    logoutAction,
    verifyTokenAction,
    getUserData,
    hasPermission,
    hasRole,
    updateUserInfo
  }
})

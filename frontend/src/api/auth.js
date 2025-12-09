import request from '@/utils/request'

/**
 * 认证相关API
 */

// 发送邮箱验证码
export const sendVerificationCode = (email) => {
  return request({
    url: '/auth/send-code',
    method: 'post',
    data: { email }
  })
}

// 用户注册
export const register = (data) => {
  const formData = new FormData()
  formData.append('email', data.email)
  formData.append('password', data.password)
  formData.append('verificationCode', data.verificationCode)
  formData.append('role', data.role)
  
  if (data.realName) formData.append('realName', data.realName)
  if (data.studentNumber) formData.append('studentNumber', data.studentNumber)
  if (data.photo) formData.append('photo', data.photo)
  if (data.rosterId) formData.append('rosterId', data.rosterId)  // 添加 rosterId
  
  console.log('注册请求数据:', {
    email: data.email,
    role: data.role,
    realName: data.realName,
    studentNumber: data.studentNumber,
    rosterId: data.rosterId,
    hasPhoto: !!data.photo
  })
  
  return request({
    url: '/auth/register',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 用户登录
export const login = (email, password) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data: { email, password }
  })
}

// 用户登出
export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

// 验证Token
export const verifyToken = () => {
  return request({
    url: '/auth/verify-token',
    method: 'get'
  })
}

// 获取用户信息
export const getUserProfile = () => {
  return request({
    url: '/users/profile',
    method: 'get'
  })
}

// 通过系统账号查找用户
export const searchUser = (account) => {
  return request({
    url: '/users/search',
    method: 'get',
    params: { account }
  })
}

// 修改密码
export const changePassword = (oldPassword, newPassword) => {
  return request({
    url: '/users/change-password',
    method: 'post',
    data: { oldPassword, newPassword }
  })
}

// 获取待审核教师列表
export const getPendingTeachers = () => {
  return request({
    url: '/admin/pending-teachers',
    method: 'get'
  })
}

// 审核教师
export const approveTeacher = (approvalId, approved, note = '') => {
  return request({
    url: '/admin/approve-teacher',
    method: 'post',
    data: { approvalId, approved, note }
  })
}

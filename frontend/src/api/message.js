import request from '@/utils/request'

// 获取会话列表
export const getConversations = () => {
  return request({
    url: '/messages/conversations',
    method: 'get'
  })
}

// 获取聊天记录
export const getMessages = (otherUserId, page = 1) => {
  return request({
    url: `/messages/conversation/${otherUserId}`,
    method: 'get',
    params: { page }
  })
}

// 发送文本消息
export const sendTextMessage = (receiverId, content) => {
  return request({
    url: '/messages/send',
    method: 'post',
    data: { receiver_id: receiverId, message_type: 'text', content }
  })
}

// 发送文件消息
export const sendFileMessage = (receiverId, messageType, file) => {
  const formData = new FormData()
  formData.append('receiver_id', receiverId)
  formData.append('message_type', messageType)
  formData.append('file', file)
  
  return request({
    url: '/messages/send',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000  // 文件上传超时设为2分钟
  })
}

// 获取未读消息数
export const getUnreadCount = () => {
  return request({
    url: '/messages/unread-count',
    method: 'get'
  })
}

// 搜索用户
export const searchUsers = (keyword) => {
  return request({
    url: '/messages/search-users',
    method: 'get',
    params: { keyword }
  })
}

// 获取在线状态
export const getOnlineStatus = (userIds) => {
  return request({
    url: '/messages/online-status',
    method: 'post',
    data: { user_ids: userIds }
  })
}

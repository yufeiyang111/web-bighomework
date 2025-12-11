import { io } from 'socket.io-client'
import { ref } from 'vue'
import config from '@/config'

class SocketService {
  constructor() {
    this.socket = null
    this.connected = ref(false)
    this.listeners = new Map()
    this.userId = null
  }

  connect() {
    if (this.socket?.connected) {
      console.log('[Socket] 已连接，跳过重复连接')
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      console.log('[Socket] 无 token，跳过连接')
      return
    }

    console.log('[Socket] ========== 开始连接 ==========')
    console.log('[Socket] 目标地址:', config.wsUrl)
    console.log('[Socket] Token 前50字符:', token.substring(0, 50))
    
    // 如果已有 socket 实例但未连接，先断开
    if (this.socket) {
      console.log('[Socket] 清理旧的 socket 实例')
      this.socket.disconnect()
      this.socket = null
    }
    
    this.socket = io(config.wsUrl, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    })
    
    console.log('[Socket] Socket.IO 实例已创建')

    this.socket.on('connect', () => {
      console.log('[Socket] 已连接, socket.id:', this.socket.id)
      // 发送认证
      this.socket.emit('authenticate', { token })
    })

    this.socket.on('authenticated', (data) => {
      console.log('[Socket] 认证成功, user_id:', data.user_id)
      this.connected.value = true
      this.userId = data.user_id
    })

    this.socket.on('auth_error', (data) => {
      console.error('[Socket] 认证失败:', data)
      this.connected.value = false
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[Socket] 已断开, 原因:', reason)
      this.connected.value = false
    })

    this.socket.on('connect_error', (error) => {
      console.error('[Socket] 连接错误:', error.message)
    })

    this.socket.on('error', (data) => {
      console.error('[Socket] 错误:', data)
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected.value = false
    }
  }

  // 发送消息
  sendMessage(receiverId, messageType, content) {
    if (!this.socket?.connected) return false
    this.socket.emit('send_message', {
      receiver_id: receiverId,
      message_type: messageType,
      content: content
    })
    return true
  }

  // 发送正在输入状态
  sendTyping(receiverId, isTyping) {
    if (!this.socket?.connected) return
    this.socket.emit('typing', { receiver_id: receiverId, is_typing: isTyping })
  }

  // 标记消息已读
  markRead(conversationId, senderId) {
    if (!this.socket?.connected) return
    this.socket.emit('mark_read', { conversation_id: conversationId, sender_id: senderId })
  }

  // 监听事件
  on(event, callback) {
    if (!this.socket) return
    
    // 先移除该事件的所有旧监听器，防止重复注册
    if (this.listeners.has(event)) {
      const oldCallbacks = this.listeners.get(event)
      oldCallbacks.forEach(cb => this.socket.off(event, cb))
      this.listeners.delete(event)
    }
    
    this.socket.on(event, callback)
    
    // 保存监听器以便清理
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  // 移除监听
  off(event, callback) {
    if (!this.socket) return
    if (callback) {
      this.socket.off(event, callback)
    } else {
      this.socket.off(event)
    }
  }

  // WebRTC 相关
  callUser(receiverId, signal, isVideo = true) {
    if (!this.socket?.connected) {
      console.error('[Socket] 无法发起通话: 未连接')
      return false
    }
    console.log('[Socket] 发起通话:', { receiver_id: receiverId, is_video: isVideo })
    this.socket.emit('call_user', { receiver_id: receiverId, signal, is_video: isVideo })
    return true
  }

  answerCall(callerId, signal) {
    if (!this.socket?.connected) {
      console.error('[Socket] 无法接听: 未连接')
      return false
    }
    console.log('[Socket] 接听通话:', { caller_id: callerId })
    this.socket.emit('answer_call', { caller_id: callerId, signal })
    return true
  }

  rejectCall(callerId) {
    if (!this.socket?.connected) {
      console.error('[Socket] 无法拒绝: 未连接')
      return false
    }
    console.log('[Socket] 拒绝通话:', { caller_id: callerId })
    this.socket.emit('reject_call', { caller_id: callerId })
    return true
  }

  endCall(otherUserId) {
    if (!this.socket?.connected) {
      console.error('[Socket] 无法结束通话: 未连接')
      return false
    }
    console.log('[Socket] 结束通话:', { other_user_id: otherUserId })
    this.socket.emit('end_call', { other_user_id: otherUserId })
    return true
  }

  sendIceCandidate(otherUserId, candidate) {
    if (!this.socket?.connected) return false
    this.socket.emit('ice_candidate', { other_user_id: otherUserId, candidate })
    return true
  }
  
  // 获取连接状态
  isConnected() {
    return this.socket?.connected || false
  }
  
  // 获取当前用户ID
  getUserId() {
    return this.userId
  }

  // 通用 emit 方法
  emit(event, data) {
    if (!this.socket?.connected) {
      console.error('[Socket] 无法发送事件: 未连接')
      return false
    }
    this.socket.emit(event, data)
    return true
  }

  // 加入群聊房间
  joinGroup(groupId) {
    return this.emit('join_group', { group_id: groupId })
  }

  // 离开群聊房间
  leaveGroupRoom(groupId) {
    return this.emit('leave_group_room', { group_id: groupId })
  }

  // 发送群消息
  sendGroupMessage(groupId, messageType, content) {
    return this.emit('send_group_message', {
      group_id: groupId,
      message_type: messageType,
      content: content
    })
  }
}

export const socketService = new SocketService()
export default socketService

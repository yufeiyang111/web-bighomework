/**
 * AI聊天机器人相关API
 */

import request from '../utils/request'

/**
 * 获取用户的聊天会话列表
 */
export function getSessions() {
  return request({
    url: '/chatbot/sessions',
    method: 'get'
  })
}

/**
 * 创建新的聊天会话
 */
export function createSession(sessionName = '新对话') {
  return request({
    url: '/chatbot/sessions',
    method: 'post',
    data: { sessionName }
  })
}

/**
 * 删除聊天会话
 */
export function deleteSession(sessionId) {
  return request({
    url: `/chatbot/sessions/${sessionId}`,
    method: 'delete'
  })
}

/**
 * 获取会话的历史消息
 */
export function getMessages(sessionId) {
  return request({
    url: `/chatbot/sessions/${sessionId}/messages`,
    method: 'get'
  })
}

/**
 * 发送消息给AI
 */
export function sendMessage(sessionId, message, useKnowledgeBase = true) {
  return request({
    url: '/chatbot/chat',
    method: 'post',
    data: {
      sessionId,
      message,
      useKnowledgeBase
    }
  })
}

/**
 * 搜索学习资料
 */
export function searchMaterials(query, limit = 10) {
  return request({
    url: '/chatbot/materials',
    method: 'get',
    params: { q: query, limit }
  })
}

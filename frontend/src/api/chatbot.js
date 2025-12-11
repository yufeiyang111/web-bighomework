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

/**
 * 获取知识库列表（分页）
 */
export function getKnowledgeBase(params) {
  return request({
    url: '/chatbot/knowledge-base',
    method: 'get',
    params
  })
}

/**
 * 添加知识库条目
 */
export function addKnowledge(data) {
  return request({
    url: '/chatbot/knowledge-base',
    method: 'post',
    data
  })
}

/**
 * 获取知识库条目详情
 */
export function getKnowledgeDetail(materialId) {
  return request({
    url: `/chatbot/knowledge-base/${materialId}`,
    method: 'get'
  })
}

/**
 * 更新知识库条目
 */
export function updateKnowledge(materialId, data) {
  return request({
    url: `/chatbot/knowledge-base/${materialId}`,
    method: 'put',
    data
  })
}

/**
 * 删除知识库条目
 */
export function deleteKnowledge(materialId) {
  return request({
    url: `/chatbot/knowledge-base/${materialId}`,
    method: 'delete'
  })
}

/**
 * 获取所有分类
 */
export function getCategories() {
  return request({
    url: '/chatbot/categories',
    method: 'get'
  })
}

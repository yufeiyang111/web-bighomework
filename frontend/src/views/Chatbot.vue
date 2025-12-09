<template>
  <div class="chatbot-container">
    <!-- 左侧会话列表 -->
    <div class="session-sidebar">
      <div class="sidebar-header">
        <h3>对话列表</h3>
        <el-button type="primary" size="small" @click="handleCreateSession">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
      
      <div class="session-list">
        <div 
          v-for="session in sessions" 
          :key="session.session_id"
          :class="['session-item', { active: currentSessionId === session.session_id }]"
          @click="handleSelectSession(session.session_id)"
        >
          <div class="session-info">
            <div class="session-name">{{ session.session_name }}</div>
            <div class="session-time">{{ formatTime(session.updated_at) }}</div>
          </div>
          <el-icon 
            class="delete-icon" 
            @click.stop="handleDeleteSession(session.session_id)"
          >
            <Delete />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-area">
      <div class="chat-header">
        <h3>AI助教</h3>
        <el-switch
          v-model="useKnowledgeBase"
          active-text="使用知识库"
          inactive-text="纯聊天"
        />
      </div>

      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-messages">
          <el-empty description="开始新的对话吧！">
            <el-text type="info">
              你可以问我关于学习资料的问题，我会基于知识库为你解答
            </el-text>
          </el-empty>
        </div>

        <div 
          v-for="msg in messages" 
          :key="msg.message_id"
          :class="['message-item', msg.role]"
        >
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="40">
              {{ userStore.userInfo?.realName?.[0] || 'U' }}
            </el-avatar>
            <el-avatar v-else :size="40" style="background-color: #409EFF">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div class="message-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="message-item assistant">
          <div class="message-avatar">
            <el-avatar :size="40" style="background-color: #409EFF">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              AI正在思考中...
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入你的问题..."
          @keydown.enter.ctrl="handleSendMessage"
        />
        <div class="input-actions">
          <el-text type="info" size="small">Ctrl + Enter 发送</el-text>
          <el-button 
            type="primary" 
            @click="handleSendMessage"
            :loading="isLoading"
            :disabled="!inputMessage.trim() || !currentSessionId"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ChatDotRound, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { 
  getSessions, 
  createSession, 
  deleteSession, 
  getMessages, 
  sendMessage 
} from '../api/chatbot'

const userStore = useUserStore()

// 状态
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const useKnowledgeBase = ref(true)
const messagesContainer = ref(null)

// 加载会话列表
const loadSessions = async () => {
  try {
    const res = await getSessions()
    if (res.success) {
      sessions.value = res.sessions
      
      // 如果没有当前会话且有会话列表，选择第一个
      if (!currentSessionId.value && sessions.value.length > 0) {
        currentSessionId.value = sessions.value[0].session_id
        await loadMessages()
      }
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 创建新会话
const handleCreateSession = async () => {
  try {
    const res = await createSession('新对话')
    if (res.success) {
      ElMessage.success('创建成功')
      await loadSessions()
      currentSessionId.value = res.sessionId
      messages.value = []
    }
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 选择会话
const handleSelectSession = async (sessionId) => {
  currentSessionId.value = sessionId
  await loadMessages()
}

// 删除会话
const handleDeleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm('确定删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await deleteSession(sessionId)
    if (res.success) {
      ElMessage.success('删除成功')
      
      // 如果删除的是当前会话，清空消息
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
        messages.value = []
      }
      
      await loadSessions()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 加载消息历史
const loadMessages = async () => {
  if (!currentSessionId.value) return
  
  try {
    const res = await getMessages(currentSessionId.value)
    if (res.success) {
      messages.value = res.messages
      await scrollToBottom()
    }
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

// 发送消息
const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || !currentSessionId.value || isLoading.value) {
    return
  }
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息到界面
  messages.value.push({
    message_id: Date.now(),
    role: 'user',
    content: userMessage,
    created_at: new Date().toISOString()
  })
  
  await scrollToBottom()
  
  isLoading.value = true
  
  try {
    const res = await sendMessage(currentSessionId.value, userMessage, useKnowledgeBase.value)
    
    if (res.success) {
      // 添加AI回复到界面
      messages.value.push({
        message_id: Date.now() + 1,
        role: 'assistant',
        content: res.message,
        created_at: new Date().toISOString()
      })
      
      await scrollToBottom()
      await loadSessions() // 刷新会话列表（更新时间）
      
      if (res.is_demo) {
        ElMessage.warning('当前为演示模式，请配置通义千问API Key使用真实AI功能')
      }
    } else {
      ElMessage.error(res.message || 'AI回复失败')
    }
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  } finally {
    isLoading.value = false
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化消息（支持简单的换行）
const formatMessage = (text) => {
  return text.replace(/\n/g, '<br>')
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  // MySQL返回的时间格式: "2025-12-04 17:47:45"
  // 需要转换为标准格式以便正确解析
  let dateStr = timestamp
  if (typeof timestamp === 'string' && !timestamp.includes('T')) {
    // 如果是MySQL格式(本地时间),直接转换
    dateStr = timestamp.replace(' ', 'T')
  }
  
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  // Debug: 输出时间信息
  console.log('formatTime Debug:', {
    original: timestamp,
    converted: dateStr,
    parsedDate: date.toISOString(),
    now: now.toISOString(),
    diff: diff,
    diffMinutes: Math.floor(diff / 60000)
  })
  
  // 小于1分钟
  if (diff < 60000) return '刚刚'
  // 小于1小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 小于1天
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  // 小于7天
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  // 超过7天,显示具体日期时间
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.chatbot-container {
  display: flex;
  height: calc(100vh - 120px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

/* 左侧会话列表 */
.session-sidebar {
  width: 280px;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  padding: 15px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.3s;
}

.session-item:hover {
  background: #f5f5f5;
}

.session-item.active {
  background: #e6f7ff;
  border-left: 3px solid #409EFF;
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 12px;
  color: #999;
}

.delete-icon {
  color: #999;
  cursor: pointer;
  padding: 5px;
}

.delete-icon:hover {
  color: #f56c6c;
}

/* 右侧聊天区域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-messages {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 12px;
}

.message-content {
  max-width: 60%;
  position: relative;
}

.message-text {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-item.user .message-text {
  background: #409EFF;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  text-align: right;
}

.message-item.user .message-time {
  text-align: left;
}

.message-loading {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 8px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-area {
  border-top: 1px solid #eee;
  padding: 20px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}
</style>

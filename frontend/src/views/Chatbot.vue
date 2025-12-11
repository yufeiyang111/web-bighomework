<template>
  <Layout pageTitle="AI助教">
    <div class="chatbot-page">
      <!-- 头部切换按钮 -->
      <div class="header-tabs">
        <el-button 
          :type="activeTab === 'chat' ? 'primary' : ''"
          @click="activeTab = 'chat'"
          size="default"
        >
          💬 对话聊天
        </el-button>
        <el-button 
          v-if="userStore.userInfo?.role === 'teacher' || userStore.userInfo?.role === 'admin'"
          :type="activeTab === 'knowledge' ? 'primary' : ''"
          @click="activeTab = 'knowledge'"
          size="default"
        >
          📚 知识库管理
        </el-button>
      </div>

      <!-- 对话模式 -->
      <div v-show="activeTab === 'chat'" class="chat-container">
      <!-- 左侧会话列表 -->
      <div class="sidebar" :class="{ 'mobile-show': mobileShowSidebar }">
        <div class="sidebar-header">
          <span>对话列表</span>
          <div class="sidebar-actions">
            <el-button type="primary" size="small" @click="handleCreateSession">
              新建
            </el-button>
            <el-button class="mobile-close-btn" size="small" @click="mobileShowSidebar = false">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="session-list">
          <div 
            v-for="session in sessions" 
            :key="session.session_id"
            :class="['session-item', { active: currentSessionId === session.session_id }]"
            @click="handleSelectSession(session.session_id); mobileShowSidebar = false"
          >
            <div class="session-info">
              <span class="session-name">{{ session.session_name }}</span>
              <span class="session-time">{{ formatTime(session.updated_at) }}</span>
            </div>
            <button class="delete-btn" @click.stop="handleDeleteSession(session.session_id)">×</button>
          </div>
          <div v-if="sessions.length === 0" class="empty-sessions">
            暂无对话
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area">
        <div class="chat-header">
          <div class="chat-header-left">
            <el-button class="mobile-menu-btn" size="small" @click="mobileShowSidebar = true">
              <el-icon><Menu /></el-icon>
            </el-button>
            <span>🤖 AI智能助教</span>
          </div>
          <el-switch v-model="useKnowledgeBase" active-text="知识库" inactive-text="纯聊天" size="small" />
        </div>

        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-messages">
            <div class="empty-icon">💬</div>
            <h3>开始新的对话</h3>
            <p>你可以问我关于学习资料的问题</p>
          </div>

          <div v-for="msg in messages" :key="msg.message_id" :class="['message', msg.role]">
            <div class="avatar">{{ msg.role === 'user' ? (userStore.userInfo?.realName?.[0] || '我') : '🤖' }}</div>
            <div class="content">
              <div class="text" v-html="formatMessage(msg.content)"></div>
              <div class="time">{{ formatTime(msg.created_at) }}</div>
            </div>
          </div>

          <div v-if="isLoading" class="message assistant">
            <div class="avatar">🤖</div>
            <div class="content">
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入消息... (Ctrl+Enter 发送)"
            @keydown.enter.ctrl="handleSendMessage"
            resize="none"
          />
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

    <!-- 知识库管理模式 -->
    <div v-show="activeTab === 'knowledge'" class="knowledge-container">
      <div class="knowledge-header">
        <div class="knowledge-filters">
          <el-select v-model="selectedCategory" placeholder="全部分类" clearable @change="loadKnowledgeList">
            <el-option label="全部" value="" />
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </div>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon> 添加知识
        </el-button>
      </div>

      <el-table :data="knowledgeList" stripe style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="tags" label="标签" width="150" />
        <el-table-column prop="creator_name" label="创建者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetailDialog(row)">查看</el-button>
            <el-button size="small" type="primary" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteKnowledge(row.material_id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadKnowledgeList"
        @size-change="loadKnowledgeList"
        style="margin-top: 20px; justify-content: center;"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogMode === 'add' ? '添加知识' : '编辑知识'" 
      width="600px"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="formData.category" placeholder="例如：Python基础" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="formData.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input 
            v-model="formData.content" 
            type="textarea" 
            :rows="8" 
            placeholder="请输入知识内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKnowledge">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailVisible" title="知识详情" width="600px">
      <div v-if="currentDetail">
        <p><strong>标题：</strong>{{ currentDetail.title }}</p>
        <p><strong>分类：</strong>{{ currentDetail.category || '无' }}</p>
        <p><strong>标签：</strong>{{ currentDetail.tags || '无' }}</p>
        <p><strong>内容：</strong></p>
        <div class="detail-content">{{ currentDetail.content }}</div>
        <p><strong>创建者：</strong>{{ currentDetail.creator_name || '未知' }}</p>
        <p><strong>创建时间：</strong>{{ currentDetail.created_at }}</p>
      </div>
    </el-dialog>
  </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Menu, Close } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { 
  getSessions, createSession, deleteSession, getMessages, sendMessage,
  getKnowledgeBase, addKnowledge, updateKnowledge, deleteKnowledge, getCategories
} from '@/api/chatbot'
import Layout from '@/components/Layout.vue'

const userStore = useUserStore()

// 标签页切换
const activeTab = ref('chat')

// 移动端侧边栏显示
const mobileShowSidebar = ref(false)

// 对话相关
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const useKnowledgeBase = ref(true)
const messagesContainer = ref(null)

// 知识库相关
const knowledgeList = ref([])
const categories = ref([])
const selectedCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogMode = ref('add') // 'add' or 'edit'
const currentDetail = ref(null)
const formData = ref({
  title: '',
  content: '',
  category: '',
  tags: ''
})
const editingId = ref(null)

const loadSessions = async () => {
  try {
    const res = await getSessions()
    if (res.success) {
      sessions.value = res.sessions
      if (!currentSessionId.value && sessions.value.length > 0) {
        currentSessionId.value = sessions.value[0].session_id
        await loadMessages()
      }
    }
  } catch (error) { console.error('加载会话失败:', error) }
}

const handleCreateSession = async () => {
  try {
    const res = await createSession('新对话')
    if (res.success) {
      ElMessage.success('创建成功')
      await loadSessions()
      currentSessionId.value = res.sessionId
      messages.value = []
    }
  } catch (error) { ElMessage.error('创建失败') }
}

const handleSelectSession = async (sessionId) => {
  currentSessionId.value = sessionId
  await loadMessages()
}

const handleDeleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm('确定删除这个对话吗？', '提示', { type: 'warning' })
    const res = await deleteSession(sessionId)
    if (res.success) {
      ElMessage.success('删除成功')
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
        messages.value = []
      }
      await loadSessions()
    }
  } catch (error) { if (error !== 'cancel') ElMessage.error('删除失败') }
}

const loadMessages = async () => {
  if (!currentSessionId.value) return
  try {
    const res = await getMessages(currentSessionId.value)
    if (res.success) {
      messages.value = res.messages
      await scrollToBottom()
    }
  } catch (error) { console.error('加载消息失败:', error) }
}

const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || !currentSessionId.value || isLoading.value) return
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  messages.value.push({ message_id: Date.now(), role: 'user', content: userMessage, created_at: new Date().toISOString() })
  await scrollToBottom()
  isLoading.value = true
  try {
    const res = await sendMessage(currentSessionId.value, userMessage, useKnowledgeBase.value)
    if (res.success) {
      messages.value.push({ message_id: Date.now() + 1, role: 'assistant', content: res.message, created_at: new Date().toISOString() })
      await scrollToBottom()
      await loadSessions()
    } else ElMessage.error(res.message || 'AI回复失败')
  } catch (error) { ElMessage.error('发送失败') }
  finally { isLoading.value = false }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

const formatMessage = (text) => text.replace(/\n/g, '<br>')

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  let dateStr = timestamp
  if (typeof timestamp === 'string' && !timestamp.includes('T')) dateStr = timestamp.replace(' ', 'T')
  const date = new Date(dateStr)
  const diff = Date.now() - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// 知识库管理函数
const loadKnowledgeList = async () => {
  try {
    const res = await getKnowledgeBase({
      category: selectedCategory.value || undefined,
      page: currentPage.value,
      pageSize: pageSize.value
    })
    if (res.success) {
      knowledgeList.value = res.materials
      total.value = res.total
    }
  } catch (error) {
    ElMessage.error('加载知识库失败')
  }
}

const loadCategories = async () => {
  try {
    const res = await getCategories()
    if (res.success) {
      categories.value = res.categories
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const showAddDialog = () => {
  dialogMode.value = 'add'
  formData.value = { title: '', content: '', category: '', tags: '' }
  editingId.value = null
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  dialogMode.value = 'edit'
  formData.value = {
    title: row.title,
    content: row.content,
    category: row.category || '',
    tags: row.tags || ''
  }
  editingId.value = row.material_id
  dialogVisible.value = true
}

const showDetailDialog = (row) => {
  currentDetail.value = row
  detailVisible.value = true
}

const handleSaveKnowledge = async () => {
  if (!formData.value.title || !formData.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  
  try {
    let res
    if (dialogMode.value === 'add') {
      res = await addKnowledge(formData.value)
    } else {
      res = await updateKnowledge(editingId.value, formData.value)
    }
    
    if (res.success) {
      ElMessage.success(dialogMode.value === 'add' ? '添加成功' : '更新成功')
      dialogVisible.value = false
      await loadKnowledgeList()
      await loadCategories()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDeleteKnowledge = async (materialId) => {
  try {
    await ElMessageBox.confirm('确定删除这条知识吗？', '提示', { type: 'warning' })
    const res = await deleteKnowledge(materialId)
    if (res.success) {
      ElMessage.success('删除成功')
      await loadKnowledgeList()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadSessions()
  loadCategories()
  if (userStore.userInfo?.role === 'teacher' || userStore.userInfo?.role === 'admin') {
    loadKnowledgeList()
  }
})
</script>

<style scoped>
.chatbot-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
}

.header-tabs {
  padding: 16px;
  border-bottom: 1px solid #d0d7de;
  display: flex;
  gap: 12px;
  background: #f6f8fa;
}

.chat-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  border-right: 1px solid #d0d7de;
  display: flex;
  flex-direction: column;
  background: #f6f8fa;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid #d0d7de;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  color: #1f2328;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  transition: background 0.15s;
}

.session-item:hover {
  background: #ffffff;
}

.session-item.active {
  background: #ffffff;
  border: 1px solid #d0d7de;
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-name {
  display: block;
  font-size: 14px;
  color: #1f2328;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #656d76;
}

.delete-btn {
  opacity: 0;
  background: none;
  border: none;
  font-size: 18px;
  color: #656d76;
  cursor: pointer;
  padding: 0 4px;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #cf222e;
}

.empty-sessions {
  text-align: center;
  padding: 20px;
  color: #656d76;
  font-size: 14px;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid #d0d7de;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  color: #1f2328;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-messages {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #656d76;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-messages h3 {
  font-size: 16px;
  color: #1f2328;
  margin: 0 0 8px;
}

.empty-messages p {
  font-size: 14px;
  margin: 0;
}

.message {
  display: flex;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  margin: 0 10px;
  flex-shrink: 0;
  background: #f6f8fa;
  border: 1px solid #d0d7de;
}

.message.user .avatar {
  background: #ddf4ff;
  border-color: #54aeff;
  color: #0969da;
}

.content {
  max-width: 70%;
}

.text {
  padding: 10px 14px;
  border-radius: 6px;
  line-height: 1.5;
  font-size: 14px;
  background: #f6f8fa;
  border: 1px solid #d0d7de;
  color: #1f2328;
}

.message.user .text {
  background: #ddf4ff;
  border-color: #54aeff;
}

.time {
  font-size: 11px;
  color: #656d76;
  margin-top: 4px;
  text-align: right;
}

.message.user .time {
  text-align: left;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  background: #f6f8fa;
  border: 1px solid #d0d7de;
  border-radius: 6px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #656d76;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 16px;
  border-top: 1px solid #d0d7de;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area :deep(.el-textarea__inner) {
  background: #f6f8fa;
  border-radius: 6px;
}

.input-area .el-button {
  background: #2da44e;
  border-color: #2da44e;
}

.input-area .el-button:hover {
  background: #2c974b;
}

/* 知识库管理样式 */
.knowledge-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.knowledge-filters {
  display: flex;
  gap: 12px;
}

.detail-content {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  line-height: 1.6;
  margin: 8px 0;
  max-height: 400px;
  overflow-y: auto;
}

/* 移动端隐藏的元素 */
.mobile-menu-btn,
.mobile-close-btn {
  display: none;
}

.sidebar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ==================== 移动端响应式样式 ==================== */
@media screen and (max-width: 768px) {
  .chatbot-page {
    height: calc(100vh - 120px);
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .header-tabs {
    padding: 12px;
    gap: 8px;
    overflow-x: auto;
    flex-wrap: nowrap;
  }

  .header-tabs .el-button {
    flex-shrink: 0;
    font-size: 13px;
    padding: 8px 12px;
  }

  /* 侧边栏移动端样式 */
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 85%;
    max-width: 320px;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: none;
  }

  .sidebar.mobile-show {
    transform: translateX(0);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
  }

  /* 侧边栏遮罩层 */
  .sidebar.mobile-show::after {
    content: '';
    position: fixed;
    top: 0;
    left: 100%;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.4);
  }

  .mobile-menu-btn {
    display: flex;
  }

  .mobile-close-btn {
    display: flex;
  }

  .sidebar-header {
    padding: 16px;
  }

  .session-item {
    padding: 12px;
  }

  .delete-btn {
    opacity: 1;
  }

  /* 聊天区域移动端样式 */
  .chat-area {
    width: 100%;
  }

  .chat-header {
    padding: 12px;
  }

  .messages {
    padding: 12px;
  }

  .message {
    margin-bottom: 12px;
  }

  .avatar {
    width: 32px;
    height: 32px;
    font-size: 12px;
    margin: 0 8px;
  }

  .content {
    max-width: 80%;
  }

  .text {
    padding: 8px 12px;
    font-size: 14px;
  }

  .input-area {
    padding: 12px;
    gap: 8px;
    flex-direction: column;
  }

  .input-area :deep(.el-textarea) {
    width: 100%;
  }

  .input-area .el-button {
    width: 100%;
    margin: 0;
  }

  /* 知识库管理移动端样式 */
  .knowledge-container {
    padding: 12px;
  }

  .knowledge-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .knowledge-filters {
    width: 100%;
  }

  .knowledge-filters .el-select {
    width: 100%;
  }

  .knowledge-header .el-button {
    width: 100%;
  }

  /* 表格移动端优化 */
  :deep(.el-table) {
    font-size: 13px;
  }

  :deep(.el-table .el-button) {
    padding: 4px 8px;
    font-size: 12px;
  }

  /* 分页移动端优化 */
  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }

  :deep(.el-pagination .el-pagination__sizes) {
    display: none;
  }

  /* 对话框移动端优化 */
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto;
  }

  :deep(.el-dialog__body) {
    padding: 16px;
  }

  .empty-icon {
    font-size: 36px;
  }

  .empty-messages h3 {
    font-size: 15px;
  }

  .empty-messages p {
    font-size: 13px;
  }
}

/* 超小屏幕优化 */
@media screen and (max-width: 375px) {
  .header-tabs .el-button {
    font-size: 12px;
    padding: 6px 10px;
  }

  .content {
    max-width: 85%;
  }

  .text {
    font-size: 13px;
  }
}
</style>

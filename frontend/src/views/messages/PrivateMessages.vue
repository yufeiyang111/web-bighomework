<template>
  <Layout pageTitle="私信">
    <div class="chat-container">
      <!-- 左侧会话列表 -->
      <div class="conversation-list" :class="{ show: !mobileShowChat }">
        <div class="search-box">
          <el-input v-model="searchKeyword" placeholder="搜索用户" prefix-icon="Search" @input="handleSearch" clearable />
        </div>
        
        <!-- 搜索结果 -->
        <div class="search-results" v-if="searchResults.length > 0">
          <div class="result-item" v-for="user in searchResults" :key="user.user_id" @click="startChat(user)">
            <el-avatar :src="getAvatarUrl(user.photo_url)" :size="40">{{ user.real_name?.[0] }}</el-avatar>
            <div class="user-info">
              <span class="name">{{ user.real_name }}</span>
              <span class="account">{{ user.system_account }}</span>
            </div>
          </div>
        </div>
        
        <!-- 会话列表 -->
        <div class="conversations" v-else>
          <div 
            class="conv-item" 
            v-for="conv in conversations" 
            :key="conv.conversation_id"
            :class="{ active: currentChat?.other_user_id === conv.other_user_id }"
            @click="selectConversation(conv)"
          >
            <div class="avatar-wrapper">
              <el-avatar :src="getAvatarUrl(conv.other_user_avatar)" :size="48">{{ conv.other_user_name?.[0] }}</el-avatar>
              <span class="online-dot" v-if="onlineStatus[conv.other_user_id]?.is_online"></span>
            </div>
            <div class="conv-info">
              <div class="conv-header">
                <span class="name">{{ conv.other_user_name }}</span>
                <span class="time">{{ formatTime(conv.last_message_time) }}</span>
              </div>
              <div class="last-msg">
                <span v-if="conv.last_message_type === 'image'">[图片]</span>
                <span v-else-if="conv.last_message_type === 'file'">[文件]</span>
                <span v-else-if="conv.last_message_type === 'video'">[视频]</span>
                <span v-else-if="conv.last_message_type === 'voice'">[语音]</span>
                <span v-else-if="conv.last_message_type === 'video_call'">[视频通话]</span>
                <span v-else-if="conv.last_message_type === 'voice_call'">[语音通话]</span>
                <span v-else-if="conv.last_message_type === 'emoji'">{{ conv.last_message }}</span>
                <span v-else>{{ conv.last_message || '暂无消息' }}</span>
              </div>
            </div>
            <el-badge :value="conv.unread_count" v-if="conv.unread_count > 0" class="unread-badge" />
          </div>
          <div class="empty-tip" v-if="conversations.length === 0">暂无会话，搜索用户开始聊天</div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area" :class="{ show: mobileShowChat }" v-if="currentChat">
        <div class="chat-header">
          <div class="user-info">
            <button class="mobile-back-btn" @click="mobileShowChat = false">
              <el-icon :size="20"><ArrowLeft /></el-icon>
            </button>
            <el-avatar :src="getAvatarUrl(currentChat.other_user_avatar)" :size="40">{{ currentChat.other_user_name?.[0] }}</el-avatar>
            <div class="info">
              <span class="name">{{ currentChat.other_user_name }}</span>
              <span class="status" :class="{ online: onlineStatus[currentChat.other_user_id]?.is_online }">
                {{ onlineStatus[currentChat.other_user_id]?.is_online ? '在线' : '离线' }}
              </span>
            </div>
          </div>
          <div class="actions">
            <el-button :icon="Phone" circle @click="startVoiceCall" title="语音通话" />
            <el-button :icon="VideoCamera" circle @click="startVideoCall" title="视频通话" />
          </div>
        </div>
        
        <div class="messages-container" ref="messagesContainer" @scroll="handleScroll">
          <div class="load-more" v-if="hasMoreMessages">
            <el-button link @click="loadMoreMessages" :loading="loadingMore">加载更多</el-button>
          </div>
          
          <template v-for="(msg, index) in messages" :key="msg.message_id">
            <!-- 时间分隔线 -->
            <div class="time-divider" v-if="shouldShowTimeDivider(msg, index)">
              {{ formatTimeDivider(msg.created_at) }}
            </div>
            
            <div class="message-item" :class="{ mine: msg.sender_id === userId }">
              <!-- 对方消息：头像在左 -->
              <div class="avatar-box" v-if="msg.sender_id !== userId">
                <el-avatar :src="getAvatarUrl(msg.sender_avatar)" :size="40">{{ msg.sender_name?.[0] }}</el-avatar>
              </div>
              
              <div class="message-body">
                <!-- 对方消息显示名字 -->
                <div class="sender-name" v-if="msg.sender_id !== userId">{{ msg.sender_name }}</div>
                
                <div class="bubble-wrapper">
                  <div class="bubble" :class="[msg.message_type, { sending: msg.sending }]">
                    <!-- 文本消息 -->
                    <template v-if="msg.message_type === 'text'">
                      <span class="text-content">{{ msg.content }}</span>
                    </template>
                    <!-- 图片消息 -->
                    <template v-else-if="msg.message_type === 'image'">
                      <el-image :src="getFileUrl(msg.file_url)" fit="cover" :preview-src-list="[getFileUrl(msg.file_url)]" class="msg-image" />
                    </template>
                    <!-- 文件消息 -->
                    <template v-else-if="msg.message_type === 'file'">
                      <div class="file-msg" @click="downloadFile(msg)">
                        <div class="file-info">
                          <span class="file-name">{{ msg.file_name }}</span>
                          <span class="file-size">{{ formatFileSize(msg.file_size) }}</span>
                        </div>
                        <div class="file-icon-box">
                          <el-icon class="file-icon"><Document /></el-icon>
                        </div>
                      </div>
                    </template>
                    <!-- 视频消息 -->
                    <template v-else-if="msg.message_type === 'video'">
                      <video :src="getFileUrl(msg.file_url)" controls class="msg-video"></video>
                    </template>
                    <!-- 语音消息 -->
                    <template v-else-if="msg.message_type === 'voice'">
                      <div class="voice-msg" @click="playVoice(msg)">
                        <el-icon><Microphone /></el-icon>
                        <span>{{ msg.duration || '0' }}''</span>
                      </div>
                    </template>
                    <!-- 表情消息 -->
                    <template v-else-if="msg.message_type === 'emoji'">
                      <span class="emoji-content">{{ msg.content }}</span>
                    </template>
                    <!-- 视频通话记录 -->
                    <template v-else-if="msg.message_type === 'video_call'">
                      <div class="call-msg">
                        <el-icon class="call-icon video"><VideoCamera /></el-icon>
                        <span>视频通话 · {{ msg.content }}</span>
                      </div>
                    </template>
                    <!-- 语音通话记录 -->
                    <template v-else-if="msg.message_type === 'voice_call'">
                      <div class="call-msg">
                        <el-icon class="call-icon voice"><Phone /></el-icon>
                        <span>语音通话 · {{ msg.content }}</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
              
              <!-- 自己消息：头像在右 -->
              <div class="avatar-box" v-if="msg.sender_id === userId">
                <el-avatar :src="getAvatarUrl(userStore.userInfo?.photoUrl)" :size="40">{{ userStore.userInfo?.realName?.[0] }}</el-avatar>
              </div>
            </div>
          </template>
          
          <div class="typing-indicator" v-if="isTyping">
            <span>对方正在输入</span>
            <span class="dots"><span>.</span><span>.</span><span>.</span></span>
          </div>
        </div>

        <!-- 输入区域 - 微信风格 -->
        <div class="input-area">
          <div class="toolbar-row">
            <div class="toolbar-left">
              <el-popover trigger="click" width="320" :teleported="false">
                <template #reference>
                  <svg class="tool-icon emoji-icon" viewBox="0 0 24 24" title="表情">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/>
                    <circle cx="8" cy="10" r="1.2" fill="currentColor"/>
                    <circle cx="16" cy="10" r="1.2" fill="currentColor"/>
                    <path d="M8 14.5c0 0 1.5 2.5 4 2.5s4-2.5 4-2.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </template>
                <div class="emoji-picker">
                  <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
                </div>
              </el-popover>
              <el-upload :show-file-list="false" :before-upload="handleImageUpload" accept="image/*">
                <el-icon class="tool-icon" title="图片"><Picture /></el-icon>
              </el-upload>
              <el-upload :show-file-list="false" :before-upload="handleFileUpload">
                <el-icon class="tool-icon" title="文件"><Folder /></el-icon>
              </el-upload>
              <el-upload :show-file-list="false" :before-upload="handleVideoUpload" accept="video/*">
                <el-icon class="tool-icon" title="视频"><Film /></el-icon>
              </el-upload>
            </div>
            <div class="toolbar-right">
              <el-icon class="tool-icon" @click="startVoiceCall" title="语音通话"><Microphone /></el-icon>
              <el-icon class="tool-icon" @click="startVideoCall" title="视频通话"><VideoCamera /></el-icon>
            </div>
          </div>
          <div class="input-wrapper">
            <el-input 
              v-model="inputMessage" 
              type="textarea" 
              :rows="4" 
              placeholder="" 
              @keydown="handleKeydown"
              @input="handleTyping"
              resize="none"
            />
          </div>
          <div class="send-row">
            <el-button @click="sendMessage" :disabled="!inputMessage.trim()" :loading="sending">
              发送(S)
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="no-chat" v-else>
        <el-empty description="选择一个会话开始聊天">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><ChatDotRound /></el-icon>
          </template>
        </el-empty>
      </div>
    </div>

    <!-- 视频/语音通话弹窗 -->
    <el-dialog 
      v-model="showVideoCall" 
      :show-close="false"
      width="900px" 
      :close-on-click-modal="false" 
      :close-on-press-escape="false"
      class="video-call-dialog"
    >
      <div class="video-call-wrapper">
        <!-- 通话头部信息 -->
        <div class="call-header">
          <div class="call-user-info">
            <el-avatar :src="getAvatarUrl(currentChat?.other_user_avatar)" :size="36">{{ currentChat?.other_user_name?.[0] }}</el-avatar>
            <div class="call-user-detail">
              <span class="call-user-name">{{ currentChat?.other_user_name }}</span>
              <span class="call-status-text">{{ callStatusText }}</span>
            </div>
          </div>
          <div class="call-timer" v-if="callConnected">{{ callDuration }}</div>
        </div>

        <!-- 视频区域 -->
        <div class="video-call-container" :class="{ 'voice-only': !isVideoCall }">
          <!-- 语音通话时显示头像 -->
          <div class="voice-call-display" v-if="!isVideoCall">
            <div class="voice-avatar-wrapper">
              <el-avatar :src="getAvatarUrl(currentChat?.other_user_avatar)" :size="120">{{ currentChat?.other_user_name?.[0] }}</el-avatar>
              <div class="voice-wave" v-if="callConnected">
                <span></span><span></span><span></span>
              </div>
            </div>
            <p class="voice-user-name">{{ currentChat?.other_user_name }}</p>
          </div>

          <!-- 视频通话 -->
          <template v-else>
            <!-- 主视频（可切换） -->
            <video 
              ref="remoteVideo" 
              autoplay 
              playsinline 
              :class="['main-video', { hidden: isLocalMain }]"
            ></video>
            <video 
              ref="localVideoMain" 
              autoplay 
              playsinline 
              muted 
              :class="['main-video', { hidden: !isLocalMain }]"
            ></video>

            <!-- 小窗视频（可点击切换） -->
            <div class="pip-video-wrapper" @click="toggleVideoPosition">
              <video 
                ref="localVideo" 
                autoplay 
                playsinline 
                muted 
                :class="['pip-video', { hidden: isLocalMain }]"
              ></video>
              <video 
                ref="remoteVideoPip" 
                autoplay 
                playsinline 
                :class="['pip-video', { hidden: !isLocalMain }]"
              ></video>
              <div class="pip-switch-hint">
                <el-icon><Switch /></el-icon>
              </div>
            </div>

            <!-- 等待连接时的提示 -->
            <div class="call-waiting" v-if="!callConnected">
              <div class="waiting-avatar">
                <el-avatar :src="getAvatarUrl(currentChat?.other_user_avatar)" :size="100">{{ currentChat?.other_user_name?.[0] }}</el-avatar>
                <div class="waiting-pulse"></div>
              </div>
              <p class="waiting-text">{{ callStatus }}</p>
            </div>
          </template>
        </div>

        <!-- 控制栏 -->
        <div class="call-controls-bar">
          <div class="control-btn" :class="{ active: isMuted }" @click="toggleMute">
            <el-icon :size="24"><MuteNotification v-if="isMuted" /><Microphone v-else /></el-icon>
            <span>{{ isMuted ? '取消静音' : '静音' }}</span>
          </div>
          <div class="control-btn" :class="{ active: isVideoOff }" @click="toggleVideo" v-if="isVideoCall">
            <el-icon :size="24"><VideoPause v-if="isVideoOff" /><VideoCamera v-else /></el-icon>
            <span>{{ isVideoOff ? '开启视频' : '关闭视频' }}</span>
          </div>
          <div class="control-btn" @click="toggleVideoPosition" v-if="isVideoCall && callConnected">
            <el-icon :size="24"><Switch /></el-icon>
            <span>切换画面</span>
          </div>
          <div class="control-btn hangup" @click="endCall">
            <el-icon :size="24"><PhoneFilled /></el-icon>
            <span>挂断</span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 来电弹窗 -->
    <el-dialog v-model="showIncomingCall" :show-close="false" width="380px" :close-on-click-modal="false" :close-on-press-escape="false" class="incoming-call-dialog">
      <div class="incoming-call">
        <div class="incoming-avatar-wrapper">
          <el-avatar :src="getAvatarUrl(incomingCaller?.avatar)" :size="100">{{ incomingCaller?.name?.[0] }}</el-avatar>
          <div class="incoming-pulse"></div>
        </div>
        <p class="caller-name">{{ incomingCaller?.name }}</p>
        <p class="call-type">
          <el-icon v-if="incomingCaller?.isVideo"><VideoCamera /></el-icon>
          <el-icon v-else><Phone /></el-icon>
          {{ incomingCaller?.isVideo ? '视频通话' : '语音通话' }}
        </p>
      </div>
      <div class="incoming-call-actions">
        <div class="action-btn reject" @click="rejectCall">
          <el-icon :size="28"><PhoneFilled /></el-icon>
          <span>拒绝</span>
        </div>
        <div class="action-btn accept" @click="acceptCall">
          <el-icon :size="28"><Phone /></el-icon>
          <span>接听</span>
        </div>
      </div>
    </el-dialog>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { getConversations, getMessages, sendFileMessage, searchUsers, getOnlineStatus } from '@/api/message'
import socketService from '@/utils/socket'
import Layout from '@/components/Layout.vue'
import { ElMessage } from 'element-plus'
import { 
  Search, VideoCamera, Picture, Folder, Document, Download, Microphone, 
  Check, ChatDotRound, Phone, PhoneFilled, Film, Bell, MuteNotification, VideoPause, ArrowLeft, Switch
} from '@element-plus/icons-vue'
import SimplePeer from 'simple-peer'
import config from '@/config'

const userStore = useUserStore()
const userId = computed(() => userStore.userInfo?.userId)
const API_BASE = config.staticUrl

// 移动端视图切换
const mobileShowChat = ref(false)

// 会话相关
const conversations = ref([])
const currentChat = ref(null)
const messages = ref([])
const onlineStatus = ref({})
const searchKeyword = ref('')
const searchResults = ref([])
const currentPage = ref(1)
const hasMoreMessages = ref(false)
const loadingMore = ref(false)

// 消息输入
const inputMessage = ref('')
const isTyping = ref(false)
const messagesContainer = ref(null)
const sending = ref(false)
let typingTimer = null

// 表情列表
const emojis = [
  '😀','😃','😄','😁','😆','😅','🤣','😂','🙂','😊',
  '😇','🥰','😍','🤩','😘','😗','😚','😋','😛','😜',
  '🤪','😝','🤑','🤗','🤭','🤫','🤔','🤐','🤨','😐',
  '😑','😶','😏','😒','🙄','😬','🤥','😌','😔','😪',
  '🤤','😴','😷','🤒','🤕','🤢','🤮','🤧','🥵','🥶',
  '🥴','😵','🤯','🤠','🥳','😎','🤓','🧐','😕','😟',
  '🙁','☹️','😮','😯','😲','😳','🥺','😦','😧','😨',
  '😰','😥','😢','😭','😱','😖','😣','😞','😓','😩',
  '😫','🥱','😤','😡','😠','🤬','👍','👎','👏','🙌',
  '👐','🤲','🤝','🙏','✌️','🤞','🤟','🤘','👌','🤏',
  '❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔',
  '❣️','💕','💞','💓','💗','💖','💘','💝','💟','🔥'
]

// 视频通话相关
const showVideoCall = ref(false)
const showIncomingCall = ref(false)
const callStatus = ref('')
const callConnected = ref(false)
const incomingCaller = ref(null)
const localVideo = ref(null)
const localVideoMain = ref(null)
const remoteVideo = ref(null)
const remoteVideoPip = ref(null)
const isVideoCall = ref(true)
const isMuted = ref(false)
const isVideoOff = ref(false)
const isLocalMain = ref(false) // 是否本地视频为主画面
const callStartTime = ref(null)
const callDuration = ref('00:00')
let callDurationTimer = null
let peer = null
let localStream = null
let incomingSignal = null

// 通话状态文本
const callStatusText = computed(() => {
  if (callConnected.value) return '通话中'
  return callStatus.value
})

// 工具函数
const getAvatarUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}

const getFileUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString()
}

const formatMsgTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  
  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// 判断是否显示时间分隔线（间隔超过5分钟）
const shouldShowTimeDivider = (msg, index) => {
  if (index === 0) return true
  const prevMsg = messages.value[index - 1]
  if (!prevMsg) return true
  const currTime = new Date(msg.created_at).getTime()
  const prevTime = new Date(prevMsg.created_at).getTime()
  return currTime - prevTime > 5 * 60 * 1000 // 5分钟
}

// 格式化时间分隔线显示
const formatTimeDivider = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isYesterday = new Date(now - 86400000).toDateString() === date.toDateString()
  
  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  if (isYesterday) {
    return `昨天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  }
  return date.toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 加载会话列表
const loadConversations = async () => {
  try {
    const res = await getConversations()
    if (res.success) {
      conversations.value = res.conversations
      const userIds = res.conversations.map(c => c.other_user_id)
      if (userIds.length > 0) {
        const statusRes = await getOnlineStatus(userIds)
        if (statusRes.success) {
          onlineStatus.value = statusRes.status
        }
      }
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  }
}

// 搜索用户
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  try {
    const res = await searchUsers(searchKeyword.value)
    if (res.success) {
      searchResults.value = res.users
    }
  } catch (e) {
    console.error('搜索失败:', e)
  }
}

// 开始新聊天
const startChat = (user) => {
  currentChat.value = {
    other_user_id: user.user_id,
    other_user_name: user.real_name,
    other_user_avatar: user.photo_url,
    other_user_account: user.system_account
  }
  searchKeyword.value = ''
  searchResults.value = []
  mobileShowChat.value = true // 移动端切换到聊天视图
  loadMessages()
}

// 选择会话
const selectConversation = async (conv) => {
  currentChat.value = conv
  currentPage.value = 1
  mobileShowChat.value = true // 移动端切换到聊天视图
  await loadMessages()
}

// 加载消息
const loadMessages = async () => {
  if (!currentChat.value) return
  try {
    const res = await getMessages(currentChat.value.other_user_id, currentPage.value)
    if (res.success) {
      messages.value = res.messages
      hasMoreMessages.value = res.messages.length >= 50
      scrollToBottom()
      socketService.markRead(res.conversation_id, currentChat.value.other_user_id)
      // 更新会话列表中的未读数
      const conv = conversations.value.find(c => c.other_user_id === currentChat.value.other_user_id)
      if (conv) conv.unread_count = 0
    }
  } catch (e) {
    console.error('加载消息失败:', e)
  }
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (loadingMore.value || !hasMoreMessages.value) return
  loadingMore.value = true
  currentPage.value++
  try {
    const res = await getMessages(currentChat.value.other_user_id, currentPage.value)
    if (res.success) {
      messages.value = [...res.messages, ...messages.value]
      hasMoreMessages.value = res.messages.length >= 50
    }
  } catch (e) {
    console.error('加载更多消息失败:', e)
  } finally {
    loadingMore.value = false
  }
}

const handleScroll = () => {
  if (messagesContainer.value?.scrollTop === 0 && hasMoreMessages.value) {
    loadMoreMessages()
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !currentChat.value || sending.value) return
  
  const content = inputMessage.value.trim()
  inputMessage.value = ''
  sending.value = true
  
  // 先添加到本地消息列表（乐观更新）
  const tempMsg = {
    message_id: Date.now(),
    sender_id: userId.value,
    receiver_id: currentChat.value.other_user_id,
    message_type: 'text',
    content,
    created_at: new Date().toISOString(),
    sending: true
  }
  messages.value.push(tempMsg)
  scrollToBottom()
  
  // 通过 WebSocket 发送
  const success = socketService.sendMessage(currentChat.value.other_user_id, 'text', content)
  
  if (!success) {
    ElMessage.error('发送失败，请检查网络连接')
    messages.value = messages.value.filter(m => m.message_id !== tempMsg.message_id)
  }
  sending.value = false
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 正在输入状态
const handleTyping = () => {
  if (!currentChat.value) return
  socketService.sendTyping(currentChat.value.other_user_id, true)
  
  clearTimeout(typingTimer)
  typingTimer = setTimeout(() => {
    socketService.sendTyping(currentChat.value.other_user_id, false)
  }, 2000)
}

// 插入表情
const insertEmoji = (emoji) => {
  inputMessage.value += emoji
}

// 上传图片
const handleImageUpload = async (file) => {
  if (!currentChat.value) return false
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过10MB')
    return false
  }
  
  try {
    const res = await sendFileMessage(currentChat.value.other_user_id, 'image', file)
    if (res.success) {
      messages.value.push(res)
      scrollToBottom()
      loadConversations()
    }
  } catch (e) {
    ElMessage.error('图片发送失败')
  }
  return false
}

// 上传视频
const handleVideoUpload = async (file) => {
  if (!currentChat.value) return false
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('视频大小不能超过100MB')
    return false
  }
  
  try {
    ElMessage.info('视频上传中...')
    const res = await sendFileMessage(currentChat.value.other_user_id, 'video', file)
    if (res.success) {
      messages.value.push(res)
      scrollToBottom()
      loadConversations()
      ElMessage.success('视频发送成功')
    }
  } catch (e) {
    ElMessage.error('视频发送失败')
  }
  return false
}

// 上传文件
const handleFileUpload = async (file) => {
  if (!currentChat.value) return false
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  
  try {
    const res = await sendFileMessage(currentChat.value.other_user_id, 'file', file)
    if (res.success) {
      messages.value.push(res)
      scrollToBottom()
      loadConversations()
    }
  } catch (e) {
    ElMessage.error('文件发送失败')
  }
  return false
}

// 下载文件
const downloadFile = (msg) => {
  const link = document.createElement('a')
  link.href = getFileUrl(msg.file_url)
  link.download = msg.file_name
  link.target = '_blank'
  link.click()
}

// 播放语音
const playVoice = (msg) => {
  const audio = new Audio(getFileUrl(msg.file_url))
  audio.play()
}

// ==================== 视频/语音通话功能 ====================

// 获取媒体流
const getMediaStream = async (video = true) => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: video ? { width: 640, height: 480 } : false,
      audio: true
    })
    return stream
  } catch (e) {
    console.error('获取媒体流失败:', e)
    ElMessage.error('无法访问摄像头或麦克风')
    return null
  }
}

// 发起视频通话
const startVideoCall = async () => {
  if (!currentChat.value) return
  isVideoCall.value = true
  await initiateCall(true)
}

// 发起语音通话
const startVoiceCall = async () => {
  if (!currentChat.value) return
  isVideoCall.value = false
  await initiateCall(false)
}

// 发起通话
const initiateCall = async (video) => {
  console.log('[通话] ========== 发起通话 ==========')
  console.log('[通话] 目标用户:', currentChat.value?.other_user_id)
  console.log('[通话] WebSocket 连接状态:', socketService.isConnected())
  
  // 检查 WebSocket 连接
  if (!socketService.isConnected()) {
    ElMessage.error('WebSocket 未连接，无法发起通话')
    console.error('[通话] WebSocket 未连接!')
    return
  }
  
  localStream = await getMediaStream(video)
  if (!localStream) {
    console.error('[通话] 获取媒体流失败')
    return
  }
  
  console.log('[通话] 媒体流获取成功')
  
  showVideoCall.value = true
  callStatus.value = '正在呼叫...'
  callConnected.value = false
  
  // 等待 DOM 更新后设置视频流
  await nextTick()
  if (localVideo.value) {
    localVideo.value.srcObject = localStream
  }
  if (localVideoMain.value) {
    localVideoMain.value.srcObject = localStream
  }
  
  // 创建 Peer 连接（作为发起方）
  // 使用 trickle: false 确保一次性发送完整的 offer
  console.log('[通话] 创建 SimplePeer 连接...')
  peer = new SimplePeer({
    initiator: true,
    trickle: false,
    stream: localStream,
    config: {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
      ]
    }
  })
  
  peer.on('signal', (signal) => {
    console.log('[通话] SimplePeer 生成信号:', signal.type)
    console.log('[通话] 发送 call_user 到服务器, receiver_id:', currentChat.value.other_user_id)
    const result = socketService.callUser(currentChat.value.other_user_id, signal, video)
    console.log('[通话] callUser 返回:', result)
  })
  
  peer.on('stream', (stream) => {
    console.log('收到远程视频流')
    callConnected.value = true
    callStatus.value = '通话中'
    startCallTimer() // 开始计时
    if (remoteVideo.value) {
      remoteVideo.value.srcObject = stream
    }
    // 同步到小窗视频
    if (remoteVideoPip.value) {
      remoteVideoPip.value.srcObject = stream
    }
  })
  
  peer.on('error', (err) => {
    console.error('Peer 错误:', err)
    ElMessage.error('通话连接失败')
    endCall(true) // 通知对方连接失败
  })
  
  peer.on('close', () => {
    console.log('Peer 连接关闭')
    // 不在这里调用 endCall，因为可能是正常结束
  })
}

// 接听来电
const acceptCall = async () => {
  showIncomingCall.value = false
  isVideoCall.value = incomingCaller.value?.isVideo ?? true
  
  // 设置当前聊天对象为来电者（如果还没设置）
  if (!currentChat.value || currentChat.value.other_user_id !== incomingCaller.value.caller_id) {
    currentChat.value = {
      other_user_id: incomingCaller.value.caller_id,
      other_user_name: incomingCaller.value.name,
      other_user_avatar: incomingCaller.value.avatar
    }
  }
  
  localStream = await getMediaStream(isVideoCall.value)
  if (!localStream) {
    socketService.rejectCall(incomingCaller.value.caller_id)
    return
  }
  
  showVideoCall.value = true
  callStatus.value = '连接中...'
  
  // 等待 DOM 更新后设置视频流
  await nextTick()
  if (localVideo.value) {
    localVideo.value.srcObject = localStream
  }
  if (localVideoMain.value) {
    localVideoMain.value.srcObject = localStream
  }
  
  // 创建 Peer 连接（作为接收方）
  peer = new SimplePeer({
    initiator: false,
    trickle: false,
    stream: localStream,
    config: {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
      ]
    }
  })
  
  peer.on('signal', (signal) => {
    console.log('发送应答信号:', signal.type)
    socketService.answerCall(incomingCaller.value.caller_id, signal)
  })
  
  peer.on('stream', (stream) => {
    console.log('收到远程视频流')
    callConnected.value = true
    callStatus.value = '通话中'
    startCallTimer() // 开始计时
    if (remoteVideo.value) {
      remoteVideo.value.srcObject = stream
    }
    // 同步到小窗视频
    if (remoteVideoPip.value) {
      remoteVideoPip.value.srcObject = stream
    }
  })
  
  peer.on('error', (err) => {
    console.error('Peer 错误:', err)
    endCall(true) // 通知对方连接失败
  })
  
  peer.on('close', () => {
    console.log('Peer 连接关闭')
    // 不在这里调用 endCall，因为可能是正常结束
  })
  
  // 处理来电信号
  if (incomingSignal) {
    console.log('处理来电信号')
    peer.signal(incomingSignal)
  }
}

// 拒绝来电
const rejectCall = () => {
  socketService.rejectCall(incomingCaller.value?.caller_id)
  showIncomingCall.value = false
  incomingCaller.value = null
  incomingSignal = null
}

// 结束通话 - sendNotification 参数控制是否通知对方
const endCall = (sendNotification = true) => {
  // 保存需要通知的用户ID
  const otherUserId = currentChat.value?.other_user_id
  
  // 停止计时
  stopCallTimer()
  
  if (peer) {
    peer.destroy()
    peer = null
  }
  
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop())
    localStream = null
  }
  
  // 只有主动挂断时才通知对方
  if (sendNotification && otherUserId && showVideoCall.value) {
    socketService.endCall(otherUserId)
  }
  
  showVideoCall.value = false
  callConnected.value = false
  callStatus.value = ''
  isMuted.value = false
  isVideoOff.value = false
  isLocalMain.value = false
  incomingCaller.value = null
  incomingSignal = null
}

// 静音切换
const toggleMute = () => {
  if (localStream) {
    const audioTrack = localStream.getAudioTracks()[0]
    if (audioTrack) {
      audioTrack.enabled = !audioTrack.enabled
      isMuted.value = !audioTrack.enabled
    }
  }
}

// 视频开关
const toggleVideo = () => {
  if (localStream) {
    const videoTrack = localStream.getVideoTracks()[0]
    if (videoTrack) {
      videoTrack.enabled = !videoTrack.enabled
      isVideoOff.value = !videoTrack.enabled
    }
  }
}

// 切换主画面/小窗位置
const toggleVideoPosition = () => {
  isLocalMain.value = !isLocalMain.value
}

// 开始通话计时
const startCallTimer = () => {
  callStartTime.value = Date.now()
  callDurationTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - callStartTime.value) / 1000)
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0')
    const seconds = (elapsed % 60).toString().padStart(2, '0')
    callDuration.value = `${minutes}:${seconds}`
  }, 1000)
}

// 停止通话计时
const stopCallTimer = () => {
  if (callDurationTimer) {
    clearInterval(callDurationTimer)
    callDurationTimer = null
  }
  callDuration.value = '00:00'
  callStartTime.value = null
}

// ==================== WebSocket 事件监听 ====================

const setupSocketListeners = () => {
  // 收到新消息
  socketService.on('new_message', (msg) => {
    // 如果是当前聊天对象的消息，添加到消息列表
    if (currentChat.value && msg.sender_id === currentChat.value.other_user_id) {
      messages.value.push(msg)
      scrollToBottom()
      socketService.markRead(msg.conversation_id, msg.sender_id)
    }
    // 更新会话列表
    loadConversations()
  })
  
  // 消息发送成功
  socketService.on('message_sent', (msg) => {
    // 替换临时消息
    const idx = messages.value.findIndex(m => m.sending && m.content === msg.content)
    if (idx !== -1) {
      messages.value[idx] = { ...msg, sending: false }
    } else {
      messages.value.push(msg)
    }
    scrollToBottom()
    loadConversations()
  })
  
  // 对方正在输入
  socketService.on('user_typing', (data) => {
    if (currentChat.value && data.user_id === currentChat.value.other_user_id) {
      isTyping.value = data.is_typing
    }
  })
  
  // 消息已读
  socketService.on('messages_read', (data) => {
    if (currentChat.value && data.reader_id === currentChat.value.other_user_id) {
      messages.value.forEach(msg => {
        if (msg.sender_id === userId.value) {
          msg.is_read = true
        }
      })
    }
  })
  
  // 用户在线状态变化
  socketService.on('user_status_changed', (data) => {
    onlineStatus.value[data.user_id] = { is_online: data.is_online }
  })
  
  // 来电 - 在私聊页面直接显示来电弹窗
  socketService.on('incoming_call', (data) => {
    console.log('【私聊页面】收到来电:', data)
    
    // 忽略自己发起的通话（防止发起者也收到来电通知）
    if (data.caller_id === userId.value) {
      console.log('【私聊页面】忽略自己发起的通话')
      return
    }
    
    // 如果已经在通话中，拒绝新来电
    if (showVideoCall.value || peer) {
      console.log('【私聊页面】已在通话中，自动拒绝新来电')
      socketService.rejectCall(data.caller_id)
      return
    }
    
    // 标记已在私聊页面处理，防止 App.vue 重复处理
    window.__incomingCallHandled = true
    
    incomingCaller.value = {
      caller_id: data.caller_id,
      name: data.caller_name,
      avatar: data.caller_avatar,
      isVideo: data.is_video !== false
    }
    incomingSignal = data.signal
    showIncomingCall.value = true
  })
  
  // 通话被接听
  socketService.on('call_answered', (data) => {
    console.log('通话被接听:', data)
    if (peer) {
      peer.signal(data.signal)
    }
  })
  
  // 通话被拒绝
  socketService.on('call_rejected', (data) => {
    console.log('通话被拒绝:', data)
    ElMessage.warning(data?.reason || '对方拒绝了通话')
    endCall(false) // 不再通知对方，因为是对方拒绝的
  })
  
  // 通话结束 - 收到对方的结束通知
  socketService.on('call_ended', () => {
    console.log('收到通话结束通知')
    ElMessage.info('通话已结束')
    endCall(false) // 不再通知对方，避免循环
  })
  
  // ICE candidate
  socketService.on('ice_candidate', (data) => {
    if (peer && data.candidate) {
      peer.signal(data.candidate)
    }
  })
}

// 检查是否有待处理的来电（从 App.vue 跳转过来）
const checkPendingIncomingCall = () => {
  const pendingCall = sessionStorage.getItem('incomingCall')
  if (pendingCall) {
    try {
      const { caller, signal } = JSON.parse(pendingCall)
      sessionStorage.removeItem('incomingCall')
      
      console.log('处理待接来电:', caller)
      incomingCaller.value = caller
      incomingSignal = signal
      
      // 自动接听
      acceptCall()
    } catch (e) {
      console.error('解析来电信息失败:', e)
      sessionStorage.removeItem('incomingCall')
    }
  }
}

// 生命周期
onMounted(() => {
  socketService.connect()
  loadConversations()
  setupSocketListeners()
  
  // 检查是否有待处理的来电
  checkPendingIncomingCall()
})

onUnmounted(() => {
  clearTimeout(typingTimer)
  endCall()
  // 清理 socket 监听器
  socketService.off('new_message')
  socketService.off('message_sent')
  socketService.off('user_typing')
  socketService.off('messages_read')
  socketService.off('user_status_changed')
  socketService.off('incoming_call')
  socketService.off('call_answered')
  socketService.off('call_rejected')
  socketService.off('call_ended')
  socketService.off('ice_candidate')
})

// 监听当前聊天变化
watch(currentChat, () => {
  isTyping.value = false
})
</script>

<style scoped>
/* ==================== 微信风格聊天界面 ==================== */
.chat-container {
  display: flex;
  height: calc(100vh - 180px);
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  max-height: calc(100vh - 180px);
}

/* 左侧会话列表 - 微信风格 */
.conversation-list {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-box {
  padding: 10px;
  background: #f7f7f7;
  flex-shrink: 0;
}

.search-box :deep(.el-input__wrapper) {
  background: #e7e7e7;
  border-radius: 4px;
  box-shadow: none;
}

.search-results, .conversations {
  flex: 1;
  overflow-y: auto;
}

.result-item, .conv-item {
  display: flex;
  align-items: center;
  padding: 12px 10px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.result-item:hover, .conv-item:hover {
  background: #f3f3f3;
}

.conv-item.active {
  background: #c9c9c9;
}

.avatar-wrapper {
  position: relative;
  margin-right: 10px;
  flex-shrink: 0;
}

.avatar-wrapper :deep(.el-avatar) {
  border-radius: 4px;
}

.online-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 8px;
  height: 8px;
  background: #07c160;
  border-radius: 50%;
  border: 1.5px solid #fff;
}

.conv-info, .user-info {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.conv-info .name, .user-info .name {
  font-size: 14px;
  color: #191919;
  font-weight: 400;
}

.conv-info .time {
  font-size: 11px;
  color: #b2b2b2;
}

.last-msg {
  font-size: 12px;
  color: #b2b2b2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-info .account {
  display: block;
  font-size: 12px;
  color: #b2b2b2;
}

.unread-badge :deep(.el-badge__content) {
  background: #f43530;
  border: none;
}

.empty-tip {
  text-align: center;
  padding: 40px 20px;
  color: #b2b2b2;
  font-size: 13px;
}

/* 右侧聊天区域 - 微信风格 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow: hidden;
  min-height: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #ededed;
  border-bottom: 1px solid #ddd;
  flex-shrink: 0;
}

.chat-header .user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-header .user-info :deep(.el-avatar) {
  display: none;
}

.chat-header .info {
  display: flex;
  flex-direction: column;
}

.chat-header .name {
  font-size: 16px;
  color: #191919;
  font-weight: 500;
}

.chat-header .status {
  font-size: 12px;
  color: #b2b2b2;
}

.chat-header .status.online {
  color: #07c160;
}

.chat-header .actions {
  display: flex;
  gap: 15px;
}

.chat-header .actions .el-button {
  border: none;
  background: transparent;
  color: #5f5f5f;
  font-size: 18px;
}

.chat-header .actions .el-button:hover {
  color: #07c160;
}

/* 消息容器 - 微信风格 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #ededed;
  min-height: 0;
}

.load-more {
  text-align: center;
  padding: 10px;
}

.load-more .el-button {
  color: #576b95;
  font-size: 12px;
}

/* 时间分隔 - 微信风格 */
.time-divider {
  text-align: center;
  margin: 20px 0;
  font-size: 12px;
  color: #b2b2b2;
}

/* 消息项布局 */
.message-item {
  display: flex;
  margin-bottom: 16px;
  gap: 10px;
  align-items: flex-start;
}

.message-item.mine {
  justify-content: flex-end;
}

/* 头像容器 */
.avatar-box {
  flex-shrink: 0;
}

.avatar-box :deep(.el-avatar) {
  border-radius: 4px;
}

/* 消息主体 */
.message-body {
  max-width: 60%;
  display: flex;
  flex-direction: column;
}

.message-item.mine .message-body {
  align-items: flex-end;
}

/* 发送者名字 */
.sender-name {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  padding-left: 4px;
}

/* 气泡容器 */
.bubble-wrapper {
  display: flex;
  align-items: flex-start;
}

/* 消息气泡 - 微信风格 */
.bubble {
  padding: 10px 12px;
  border-radius: 4px;
  background: #fff;
  word-break: break-word;
  position: relative;
  font-size: 14px;
  line-height: 1.5;
  color: #191919;
  max-width: 100%;
}

/* 气泡小三角 */
.bubble::before {
  content: '';
  position: absolute;
  top: 12px;
  width: 0;
  height: 0;
  border: 6px solid transparent;
}

.message-item:not(.mine) .bubble::before {
  left: -10px;
  border-right-color: #fff;
}

.message-item.mine .bubble {
  background: #95ec69;
  color: #000;
}

.message-item.mine .bubble::before {
  right: -10px;
  border-left-color: #95ec69;
}

.bubble.sending {
  opacity: 0.6;
}

.bubble.image, .bubble.video {
  padding: 0;
  background: transparent;
}

.bubble.image::before, .bubble.video::before {
  display: none;
}

.msg-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  cursor: pointer;
  display: block;
}

.msg-video {
  max-width: 260px;
  border-radius: 4px;
}

/* 文件消息 - 微信风格 */
.file-msg {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  min-width: 220px;
  max-width: 280px;
  border: 1px solid #e5e5e5;
}

.message-item.mine .file-msg {
  background: #95ec69;
  border-color: #7ed956;
}

.file-icon {
  font-size: 40px;
  color: #1989fa;
  flex-shrink: 0;
}

/* Word 文档图标颜色 */
.file-msg.docx .file-icon,
.file-msg.doc .file-icon {
  color: #2b5797;
}

.message-item.mine .file-icon {
  color: #1a6b1a;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  display: block;
  font-size: 14px;
  color: #191919;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.file-size {
  font-size: 12px;
  color: #999;
}

.message-item.mine .file-size {
  color: #1a6b1a;
}

.download-icon {
  display: none;
}

.voice-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  min-width: 80px;
  padding: 8px 12px;
}

.emoji-content {
  font-size: 28px;
  line-height: 1;
}

/* 通话记录 - 微信风格 */
.call-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: 14px;
  color: #191919;
}

.call-icon {
  font-size: 20px;
  color: #07c160;
}

.call-icon.video {
  color: #07c160;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  padding: 0 4px;
}

.msg-meta .time {
  font-size: 11px;
  color: #b2b2b2;
}

.read-icon {
  font-size: 12px;
  color: #07c160;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px;
  color: #b2b2b2;
  font-size: 12px;
}

.typing-indicator .dots span {
  animation: blink 1.4s infinite both;
}

.typing-indicator .dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator .dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}

/* 输入区域 - 微信风格 */
.input-area {
  background: #f5f5f5;
  border-top: 1px solid #ddd;
  padding: 10px 15px 15px;
  flex-shrink: 0;
  overflow: hidden;
}

/* 工具栏行 */
.toolbar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.tool-icon {
  font-size: 22px;
  color: #5f5f5f;
  cursor: pointer;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-icon:hover {
  color: #07c160;
}

/* 微信风格表情图标 */
.emoji-icon {
  width: 24px;
  height: 24px;
}

/* 输入框容器 */
.input-wrapper {
  margin-bottom: 10px;
}

.input-wrapper :deep(.el-textarea__inner) {
  resize: none;
  border: none;
  border-radius: 0;
  background: #f5f5f5;
  padding: 10px 0;
  font-size: 14px;
  min-height: 80px !important;
  box-shadow: none;
}

.input-wrapper :deep(.el-textarea__inner):focus {
  box-shadow: none;
}

/* 发送按钮行 */
.send-row {
  display: flex;
  justify-content: flex-end;
}

.send-row .el-button {
  background: #07c160;
  border-color: #07c160;
  color: #fff;
  padding: 8px 20px;
  font-size: 14px;
  border-radius: 4px;
}

.send-row .el-button:hover {
  background: #06ad56;
  border-color: #06ad56;
}

.send-row .el-button:disabled {
  background: #a0cfb4;
  border-color: #a0cfb4;
}

.emoji-picker {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 5px;
  max-height: 200px;
  overflow-y: auto;
  padding: 5px;
}

.emoji-item {
  font-size: 24px;
  padding: 5px;
  cursor: pointer;
  text-align: center;
  border-radius: 4px;
  transition: background 0.15s;
}

.emoji-item:hover {
  background: #f0f0f0;
}

/* 无聊天选中 */
.no-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ededed;
}

.no-chat :deep(.el-empty__description) {
  color: #b2b2b2;
}

/* ==================== 视频/语音通话界面 ==================== */
.video-call-wrapper {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  overflow: hidden;
}

/* 通话头部 */
.call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.3);
}

.call-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.call-user-detail {
  display: flex;
  flex-direction: column;
}

.call-user-name {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.call-status-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.call-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-variant-numeric: tabular-nums;
  background: linear-gradient(135deg, rgba(7, 193, 96, 0.2) 0%, rgba(7, 193, 96, 0.1) 100%);
  padding: 8px 16px;
  border-radius: 24px;
  border: 1px solid rgba(7, 193, 96, 0.3);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.call-timer::before {
  content: '';
  width: 8px;
  height: 8px;
  background: #07c160;
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(7, 193, 96, 0.6);
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(0.85);
  }
}

/* 视频容器 */
.video-call-container {
  position: relative;
  width: 100%;
  height: 450px;
  background: #0a0a0a;
  overflow: hidden;
}

.video-call-container.voice-only {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
}

/* 语音通话显示 */
.voice-call-display {
  text-align: center;
}

.voice-avatar-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 20px;
}

.voice-avatar-wrapper :deep(.el-avatar) {
  border: 4px solid rgba(255, 255, 255, 0.2);
}

.voice-wave {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
}

.voice-wave span {
  width: 4px;
  height: 20px;
  background: #07c160;
  border-radius: 2px;
  animation: voiceWave 1s ease-in-out infinite;
}

.voice-wave span:nth-child(2) {
  animation-delay: 0.2s;
}

.voice-wave span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes voiceWave {
  0%, 100% { height: 8px; }
  50% { height: 24px; }
}

.voice-user-name {
  color: #fff;
  font-size: 20px;
  font-weight: 500;
  margin: 0;
}

/* 主视频 */
.main-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.main-video.hidden {
  display: none;
}

/* 小窗视频 (画中画) */
.pip-video-wrapper {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 180px;
  height: 135px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.pip-video-wrapper:hover {
  transform: scale(1.05);
  border-color: #07c160;
}

.pip-video-wrapper:hover .pip-switch-hint {
  opacity: 1;
}

.pip-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pip-video.hidden {
  display: none;
}

.pip-switch-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
}

/* 等待连接 */
.call-waiting {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.waiting-avatar {
  position: relative;
  display: inline-block;
}

.waiting-pulse {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border: 3px solid #07c160;
  border-radius: 50%;
  animation: waitingPulse 1.5s ease-out infinite;
}

@keyframes waitingPulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}

.waiting-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin-top: 24px;
}

/* 控制栏 */
.call-controls-bar {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 24px;
  background: rgba(0, 0, 0, 0.4);
}

.control-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn .el-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.2s;
}

.control-btn:hover .el-icon {
  background: rgba(255, 255, 255, 0.25);
}

.control-btn.active .el-icon {
  background: #f56c6c;
}

.control-btn span {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.control-btn.hangup .el-icon {
  background: #f56c6c;
}

.control-btn.hangup:hover .el-icon {
  background: #e04848;
}

/* ==================== 来电弹窗 ==================== */
.incoming-call {
  text-align: center;
  padding: 30px 20px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
}

.incoming-avatar-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 20px;
}

.incoming-avatar-wrapper :deep(.el-avatar) {
  border: 4px solid rgba(255, 255, 255, 0.2);
}

.incoming-pulse {
  position: absolute;
  top: -15px;
  left: -15px;
  right: -15px;
  bottom: -15px;
  border: 3px solid #07c160;
  border-radius: 50%;
  animation: incomingPulse 1.2s ease-out infinite;
}

@keyframes incomingPulse {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.caller-name {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}

.call-type {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.incoming-call-actions {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding: 20px;
  background: linear-gradient(180deg, #16213e 0%, #1a1a2e 100%);
  border-radius: 0 0 12px 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}

.action-btn:hover {
  transform: scale(1.1);
}

.action-btn .el-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.action-btn.reject .el-icon {
  background: linear-gradient(135deg, #f56c6c 0%, #e04848 100%);
  transform: rotate(135deg);
}

.action-btn.accept .el-icon {
  background: linear-gradient(135deg, #07c160 0%, #06ad56 100%);
}

.action-btn span {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

/* 对话框样式覆盖 */
:deep(.video-call-dialog .el-dialog) {
  background: transparent;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border-radius: 16px;
}

:deep(.video-call-dialog .el-dialog__header) {
  display: none;
}

:deep(.video-call-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.video-call-dialog .el-dialog__footer) {
  display: none;
}

:deep(.incoming-call-dialog .el-dialog) {
  background: transparent;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border-radius: 16px;
}

:deep(.incoming-call-dialog .el-dialog__header) {
  display: none;
}

:deep(.incoming-call-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.incoming-call-dialog .el-dialog__footer) {
  display: none;
}

.incoming-call-actions .el-button--success {
  background: #07c160;
  border-color: #07c160;
}

.incoming-call-actions .el-button--danger {
  background: #fa5151;
  border-color: #fa5151;
}

/* 对话框样式 */
:deep(.video-call-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.incoming-call-dialog .el-dialog__header) {
  text-align: center;
}

/* 滚动条样式 */
.conversations::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.conversations::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.conversations::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 移动端响应式 ==================== */
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
    height: calc(100vh - 130px);
    max-height: calc(100vh - 130px);
  }
  
  /* 移动端会话列表 */
  .conversation-list {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
    max-height: 100%;
    display: none;
  }
  
  .conversation-list.show {
    display: flex;
  }
  
  /* 移动端聊天区域 */
  .chat-area {
    display: none;
    height: 100%;
  }
  
  .chat-area.show {
    display: flex;
  }
  
  /* 移动端聊天头部 */
  .chat-header {
    padding: 10px 12px;
  }
  
  .chat-header .name {
    font-size: 15px;
  }
  
  .chat-header .actions {
    gap: 8px;
  }
  
  .chat-header .actions .el-button {
    font-size: 16px;
    padding: 6px;
  }
  
  /* 移动端消息区域 */
  .messages-container {
    padding: 12px;
  }
  
  .message-body {
    max-width: 75%;
  }
  
  .bubble {
    padding: 8px 10px;
    font-size: 14px;
  }
  
  .msg-image {
    max-width: 160px;
    max-height: 160px;
  }
  
  .msg-video {
    max-width: 200px;
  }
  
  .file-msg {
    min-width: 180px;
    max-width: 220px;
    padding: 10px;
  }
  
  /* 移动端输入区域 */
  .input-area {
    padding: 8px 10px 12px;
  }
  
  .toolbar-row {
    padding-bottom: 8px;
  }
  
  .toolbar-left, .toolbar-right {
    gap: 12px;
  }
  
  .tool-icon {
    font-size: 20px;
  }
  
  .input-wrapper :deep(.el-textarea__inner) {
    min-height: 60px !important;
    font-size: 14px;
  }
  
  .send-row .el-button {
    padding: 6px 16px;
    font-size: 13px;
  }
  
  /* 移动端表情选择器 */
  .emoji-picker {
    grid-template-columns: repeat(6, 1fr);
  }
  
  .emoji-item {
    font-size: 20px;
    padding: 4px;
  }
  
  /* 移动端无聊天选中 */
  .no-chat {
    display: none;
  }
  
  /* 移动端视频通话 */
  .video-call-container {
    height: 280px;
  }
  
  .video-call-container.voice-only {
    height: 220px;
  }
  
  .pip-video-wrapper {
    width: 120px;
    height: 90px;
    bottom: 12px;
    right: 12px;
  }
  
  .call-controls-bar {
    gap: 16px;
    padding: 16px;
  }
  
  .control-btn .el-icon {
    width: 48px;
    height: 48px;
  }
  
  .control-btn span {
    font-size: 11px;
  }
  
  .incoming-call-actions {
    gap: 50px;
    padding: 16px;
  }
  
  .action-btn .el-icon {
    width: 56px;
    height: 56px;
  }
  
  :deep(.video-call-dialog .el-dialog) {
    width: 95% !important;
    margin: 10px auto;
  }
  
  :deep(.incoming-call-dialog .el-dialog) {
    width: 90% !important;
  }
}

/* 移动端返回按钮 */
.mobile-back-btn {
  display: none;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #1f2328;
  margin-right: 8px;
}

@media (max-width: 768px) {
  .mobile-back-btn {
    display: flex;
    align-items: center;
  }
}
</style>

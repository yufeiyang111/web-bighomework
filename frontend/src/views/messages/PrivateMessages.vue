<template>
  <Layout pageTitle="私信">
    <div class="chat-container">
      <!-- 左侧会话列表 -->
      <div class="conversation-list">
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
      <div class="chat-area" v-if="currentChat">
        <div class="chat-header">
          <div class="user-info">
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
          <div class="message-item" v-for="msg in messages" :key="msg.message_id" :class="{ mine: msg.sender_id === userId }">
            <el-avatar v-if="msg.sender_id !== userId" :src="getAvatarUrl(msg.sender_avatar)" :size="36">{{ msg.sender_name?.[0] }}</el-avatar>
            <div class="message-content">
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
                    <el-icon class="file-icon"><Document /></el-icon>
                    <div class="file-info">
                      <span class="file-name">{{ msg.file_name }}</span>
                      <span class="file-size">{{ formatFileSize(msg.file_size) }}</span>
                    </div>
                    <el-icon class="download-icon"><Download /></el-icon>
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
              <div class="msg-meta">
                <span class="time">{{ formatMsgTime(msg.created_at) }}</span>
                <el-icon v-if="msg.sender_id === userId && msg.is_read" class="read-icon"><Check /></el-icon>
              </div>
            </div>
            <el-avatar v-if="msg.sender_id === userId" :src="getAvatarUrl(userStore.userInfo?.photoUrl)" :size="36">{{ userStore.userInfo?.realName?.[0] }}</el-avatar>
          </div>
          <div class="typing-indicator" v-if="isTyping">
            <span>对方正在输入</span>
            <span class="dots"><span>.</span><span>.</span><span>.</span></span>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="toolbar">
            <el-upload :show-file-list="false" :before-upload="handleImageUpload" accept="image/*">
              <el-button :icon="Picture" title="发送图片" />
            </el-upload>
            <el-upload :show-file-list="false" :before-upload="handleVideoUpload" accept="video/*">
              <el-button :icon="Film" title="发送视频" />
            </el-upload>
            <el-upload :show-file-list="false" :before-upload="handleFileUpload">
              <el-button :icon="Folder" title="发送文件" />
            </el-upload>
            <el-popover trigger="click" width="320" :teleported="false">
              <template #reference>
                <el-button title="表情">😊</el-button>
              </template>
              <div class="emoji-picker">
                <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
              </div>
            </el-popover>
          </div>
          <div class="input-box">
            <el-input 
              v-model="inputMessage" 
              type="textarea" 
              :rows="3" 
              placeholder="输入消息，Enter发送，Shift+Enter换行" 
              @keydown="handleKeydown"
              @input="handleTyping"
              resize="none"
            />
            <el-button type="primary" @click="sendMessage" :disabled="!inputMessage.trim()" :loading="sending">
              发送
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
      :title="callStatus" 
      width="800px" 
      :close-on-click-modal="false" 
      :close-on-press-escape="false"
      @close="endCall"
      class="video-call-dialog"
    >
      <div class="video-call-container">
        <video ref="remoteVideo" autoplay playsinline class="remote-video"></video>
        <video ref="localVideo" autoplay playsinline muted class="local-video"></video>
        <div class="call-info" v-if="!callConnected">
          <el-avatar :src="getAvatarUrl(currentChat?.other_user_avatar)" :size="100">{{ currentChat?.other_user_name?.[0] }}</el-avatar>
          <p>{{ callStatus }}</p>
        </div>
      </div>
      <template #footer>
        <div class="call-controls">
          <el-button :icon="isMuted ? MuteNotification : Bell" circle @click="toggleMute" :title="isMuted ? '取消静音' : '静音'" />
          <el-button :icon="isVideoOff ? VideoPause : VideoCamera" circle @click="toggleVideo" :title="isVideoOff ? '开启视频' : '关闭视频'" v-if="isVideoCall" />
          <el-button type="danger" :icon="PhoneFilled" circle @click="endCall" title="挂断" />
        </div>
      </template>
    </el-dialog>

    <!-- 来电弹窗 -->
    <el-dialog v-model="showIncomingCall" title="来电" width="400px" :close-on-click-modal="false" :close-on-press-escape="false" class="incoming-call-dialog">
      <div class="incoming-call">
        <el-avatar :src="getAvatarUrl(incomingCaller?.avatar)" :size="100">{{ incomingCaller?.name?.[0] }}</el-avatar>
        <p class="caller-name">{{ incomingCaller?.name }}</p>
        <p class="call-type">{{ incomingCaller?.isVideo ? '视频通话' : '语音通话' }}</p>
      </div>
      <template #footer>
        <div class="incoming-call-actions">
          <el-button type="danger" :icon="PhoneFilled" circle size="large" @click="rejectCall" />
          <el-button type="success" :icon="Phone" circle size="large" @click="acceptCall" />
        </div>
      </template>
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
  Check, ChatDotRound, Phone, PhoneFilled, Film, Bell, MuteNotification, VideoPause
} from '@element-plus/icons-vue'
import SimplePeer from 'simple-peer'
import config from '@/config'

const userStore = useUserStore()
const userId = computed(() => userStore.userInfo?.userId)
const API_BASE = config.staticUrl

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
const remoteVideo = ref(null)
const isVideoCall = ref(true)
const isMuted = ref(false)
const isVideoOff = ref(false)
let peer = null
let localStream = null
let incomingSignal = null

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
  loadMessages()
}

// 选择会话
const selectConversation = async (conv) => {
  currentChat.value = conv
  currentPage.value = 1
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
  localStream = await getMediaStream(video)
  if (!localStream) return
  
  showVideoCall.value = true
  callStatus.value = '正在呼叫...'
  callConnected.value = false
  
  // 等待 DOM 更新后设置视频流
  await nextTick()
  if (localVideo.value) {
    localVideo.value.srcObject = localStream
  }
  
  // 创建 Peer 连接（作为发起方）
  // 使用 trickle: false 确保一次性发送完整的 offer
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
    console.log('发送呼叫信号:', signal.type)
    socketService.callUser(currentChat.value.other_user_id, signal, video)
  })
  
  peer.on('stream', (stream) => {
    console.log('收到远程视频流')
    callConnected.value = true
    callStatus.value = '通话中'
    if (remoteVideo.value) {
      remoteVideo.value.srcObject = stream
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
    if (remoteVideo.value) {
      remoteVideo.value.srcObject = stream
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
.chat-container {
  display: flex;
  height: calc(100vh - 120px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 左侧会话列表 */
.conversation-list {
  width: 300px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.search-box {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.search-results, .conversations {
  flex: 1;
  overflow-y: auto;
}

.result-item, .conv-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover, .conv-item:hover {
  background: #f5f7fa;
}

.conv-item.active {
  background: #ecf5ff;
}

.avatar-wrapper {
  position: relative;
  margin-right: 12px;
}

.online-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 10px;
  height: 10px;
  background: #67c23a;
  border-radius: 50%;
  border: 2px solid #fff;
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
  font-weight: 500;
  color: #303133;
}

.conv-info .time {
  font-size: 12px;
  color: #909399;
}

.last-msg {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-info .account {
  display: block;
  font-size: 12px;
  color: #909399;
}

.unread-badge {
  margin-left: 8px;
}

.empty-tip {
  text-align: center;
  padding: 40px;
  color: #909399;
}

/* 右侧聊天区域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.chat-header .user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header .info {
  display: flex;
  flex-direction: column;
}

.chat-header .name {
  font-weight: 600;
  font-size: 15px;
}

.chat-header .status {
  font-size: 12px;
  color: #909399;
}

.chat-header .status.online {
  color: #67c23a;
}

.chat-header .actions {
  display: flex;
  gap: 8px;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
}

.load-more {
  text-align: center;
  padding: 8px;
}

.message-item {
  display: flex;
  margin-bottom: 16px;
  gap: 8px;
}

.message-item.mine {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 60%;
  display: flex;
  flex-direction: column;
}

.message-item.mine .message-content {
  align-items: flex-end;
}

.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  word-break: break-word;
}

.message-item.mine .bubble {
  background: #409eff;
  color: #fff;
}

.bubble.sending {
  opacity: 0.7;
}

.bubble.image, .bubble.video {
  padding: 4px;
  background: transparent;
  box-shadow: none;
}

.msg-image {
  max-width: 250px;
  max-height: 250px;
  border-radius: 8px;
  cursor: pointer;
}

.msg-video {
  max-width: 300px;
  border-radius: 8px;
}

.file-msg {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  min-width: 200px;
}

.message-item.mine .file-msg {
  background: rgba(255, 255, 255, 0.2);
}

.file-icon {
  font-size: 32px;
  color: #409eff;
}

.message-item.mine .file-icon {
  color: #fff;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  display: block;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.message-item.mine .file-size {
  color: rgba(255, 255, 255, 0.8);
}

.download-icon {
  font-size: 20px;
}

.voice-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  min-width: 80px;
}

.emoji-content {
  font-size: 32px;
}

.call-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 8px;
  color: #67c23a;
  font-size: 13px;
}

.message-item.mine .call-msg {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.call-icon {
  font-size: 18px;
}

.call-icon.video {
  color: #409eff;
}

.call-icon.voice {
  color: #67c23a;
}

.message-item.mine .call-icon {
  color: #fff;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.msg-meta .time {
  font-size: 11px;
  color: #909399;
}

.read-icon {
  font-size: 12px;
  color: #67c23a;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  color: #909399;
  font-size: 13px;
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

/* 输入区域 */
.input-area {
  border-top: 1px solid #e4e7ed;
  background: #fff;
}

.toolbar {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.toolbar .el-button {
  padding: 8px;
}

.input-box {
  display: flex;
  gap: 12px;
  padding: 12px;
  align-items: flex-end;
}

.input-box .el-textarea {
  flex: 1;
}

.input-box :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 8px;
}

.emoji-picker {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.emoji-item {
  font-size: 22px;
  padding: 4px;
  cursor: pointer;
  text-align: center;
  border-radius: 4px;
  transition: background 0.2s;
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
  background: #fafafa;
}

/* 视频通话 */
.video-call-container {
  position: relative;
  width: 100%;
  height: 450px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.remote-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.local-video {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 150px;
  height: 112px;
  border-radius: 8px;
  object-fit: cover;
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.call-info {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #fff;
}

.call-info p {
  margin-top: 16px;
  font-size: 16px;
}

.call-controls {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.call-controls .el-button {
  width: 50px;
  height: 50px;
}

/* 来电弹窗 */
.incoming-call {
  text-align: center;
  padding: 20px;
}

.caller-name {
  font-size: 20px;
  font-weight: 600;
  margin: 16px 0 8px;
}

.call-type {
  color: #909399;
}

.incoming-call-actions {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.incoming-call-actions .el-button {
  width: 60px;
  height: 60px;
}

/* 对话框样式 */
:deep(.video-call-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.incoming-call-dialog .el-dialog__header) {
  text-align: center;
}
</style>

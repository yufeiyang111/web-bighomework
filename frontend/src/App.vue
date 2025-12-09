<template>
  <div id="app">
    <router-view />
    
    <!-- 全局来电弹窗 -->
    <el-dialog 
      v-model="showIncomingCall" 
      title="来电" 
      width="400px" 
      :close-on-click-modal="false" 
      :close-on-press-escape="false"
      class="global-incoming-call-dialog"
    >
      <div class="incoming-call">
        <el-avatar :src="getAvatarUrl(incomingCaller?.avatar)" :size="100">
          {{ incomingCaller?.name?.[0] }}
        </el-avatar>
        <p class="caller-name">{{ incomingCaller?.name }}</p>
        <p class="call-type">{{ incomingCaller?.isVideo ? '视频通话' : '语音通话' }}</p>
      </div>
      <template #footer>
        <div class="incoming-call-actions">
          <el-button type="danger" circle size="large" @click="rejectCall">
            <el-icon><Close /></el-icon>
          </el-button>
          <el-button type="success" circle size="large" @click="acceptCall">
            <el-icon><Phone /></el-icon>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import socketService from '@/utils/socket'
import config from '@/config'
import { ElMessage } from 'element-plus'
import { Phone, Close } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 来电相关状态
const showIncomingCall = ref(false)
const incomingCaller = ref(null)
let incomingSignal = null

// 获取头像URL
const getAvatarUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${config.staticUrl}${url}`
}

// 接听来电 - 跳转到私聊页面处理
const acceptCall = () => {
  // 保存来电信息到 sessionStorage，供私聊页面使用
  sessionStorage.setItem('incomingCall', JSON.stringify({
    caller: incomingCaller.value,
    signal: incomingSignal
  }))
  showIncomingCall.value = false
  
  // 跳转到私聊页面
  router.push('/messages/private')
}

// 拒绝来电
const rejectCall = () => {
  if (incomingCaller.value?.caller_id) {
    socketService.rejectCall(incomingCaller.value.caller_id)
  }
  showIncomingCall.value = false
  incomingCaller.value = null
  incomingSignal = null
}

// 设置全局 WebSocket 监听
const setupGlobalSocketListeners = () => {
  // 来电通知 - 作为后备，当用户不在私聊页面时显示
  socketService.on('incoming_call', (data) => {
    console.log('【全局 App.vue】收到 incoming_call 事件')
    console.log('【全局 App.vue】来电数据:', JSON.stringify(data))
    
    // 检查是否已被私聊页面处理
    if (window.__incomingCallHandled) {
      window.__incomingCallHandled = false
      console.log('【全局 App.vue】来电已被私聊页面处理，跳过')
      return
    }
    
    console.log('【全局 App.vue】显示来电弹窗')
    incomingCaller.value = {
      caller_id: data.caller_id,
      name: data.caller_name,
      avatar: data.caller_avatar,
      isVideo: data.is_video !== false
    }
    incomingSignal = data.signal
    showIncomingCall.value = true
  })
}

// 监听用户登录状态，登录后连接 WebSocket
watch(() => userStore.isLoggedIn, (isLoggedIn) => {
  console.log('[App.vue] isLoggedIn 变化:', isLoggedIn)
  if (isLoggedIn) {
    console.log('[App.vue] 用户已登录，连接 WebSocket')
    socketService.connect()
    setupGlobalSocketListeners()
  } else {
    console.log('[App.vue] 用户已登出，断开 WebSocket')
    socketService.disconnect()
  }
}, { immediate: true })

// 也监听 token 变化，确保 token 存在时尝试连接
watch(() => userStore.token, (token) => {
  console.log('[App.vue] token 变化:', token ? '有token' : '无token')
  if (token && !socketService.isConnected()) {
    console.log('[App.vue] 有 token 但未连接，尝试连接 WebSocket')
    socketService.connect()
    setupGlobalSocketListeners()
  }
}, { immediate: true })

onMounted(() => {
  console.log('[App.vue] onMounted, isLoggedIn:', userStore.isLoggedIn, 'token:', !!userStore.token)
  // 如果有 token，连接 WebSocket（即使 userInfo 还没加载完）
  if (userStore.token) {
    socketService.connect()
    setupGlobalSocketListeners()
  }
})

onUnmounted(() => {
  socketService.off('incoming_call')
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: #f6f8fa;
  color: #1f2328;
  font-size: 14px;
  line-height: 1.5;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d0d7de;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #afb8c1;
}

/* Element Plus 覆盖 - GitHub风格 */
.el-card {
  border-radius: 6px;
  border: 1px solid #d0d7de;
  box-shadow: none;
}

.el-button {
  border-radius: 6px;
  font-weight: 500;
  font-size: 14px;
}

.el-button--primary {
  background-color: #2da44e;
  border-color: #2da44e;
}

.el-button--primary:hover {
  background-color: #2c974b;
  border-color: #2c974b;
}

.el-input__wrapper {
  border-radius: 6px;
  box-shadow: inset 0 0 0 1px #d0d7de;
}

.el-input__wrapper:hover {
  box-shadow: inset 0 0 0 1px #0969da;
}

.el-input__wrapper.is-focus {
  box-shadow: inset 0 0 0 1px #0969da, 0 0 0 3px rgba(9, 105, 218, 0.3);
}

.el-tag {
  border-radius: 20px;
}

.el-table {
  border-radius: 6px;
  border: 1px solid #d0d7de;
}

.el-dialog {
  border-radius: 12px;
}

/* 链接 */
a {
  color: #0969da;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* 全局来电弹窗样式 */
.global-incoming-call-dialog .incoming-call {
  text-align: center;
  padding: 20px;
}

.global-incoming-call-dialog .caller-name {
  font-size: 20px;
  font-weight: 600;
  margin: 16px 0 8px;
  color: #303133;
}

.global-incoming-call-dialog .call-type {
  color: #909399;
  font-size: 14px;
}

.global-incoming-call-dialog .incoming-call-actions {
  display: flex;
  justify-content: center;
  gap: 60px;
}

.global-incoming-call-dialog .incoming-call-actions .el-button {
  width: 60px;
  height: 60px;
}

.global-incoming-call-dialog .incoming-call-actions .el-button .el-icon {
  font-size: 24px;
}
</style>

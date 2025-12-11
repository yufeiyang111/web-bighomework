<template>
  <Layout pageTitle="群聊">
    <div class="chat-container">
      <!-- 左侧群组列表 -->
      <div class="conversation-list" :class="{ show: !mobileShowChat }">
        <div class="search-box">
          <div v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" 
               class="create-group-btn" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
          </div>
        </div>
        
        <div class="conversations">
          <div 
            v-for="group in groups" 
            :key="group.id"
            :class="['conv-item', { active: currentGroup?.id === group.id }]"
            @click="selectGroup(group)"
          >
            <div class="avatar-wrapper">
              <div class="group-avatar">{{ group.name?.[0] || 'G' }}</div>
            </div>
            <div class="conv-info">
              <div class="conv-header">
                <span class="name">{{ group.name }}</span>
                <span class="time">{{ group.member_count }}人</span>
              </div>
              <div class="last-msg">
                <span v-if="group.course_name">{{ group.course_name }}</span>
                <span v-else>普通群组</span>
              </div>
            </div>
          </div>
          <div class="empty-tip" v-if="groups.length === 0">暂无群组</div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area" :class="{ show: mobileShowChat }" v-if="currentGroup">
        <div class="chat-header">
          <div class="user-info">
            <button class="mobile-back-btn" @click="mobileShowChat = false">
              <el-icon :size="20"><ArrowLeft /></el-icon>
            </button>
            <div class="info">
              <span class="name">{{ currentGroup.name }}</span>
              <span class="status">{{ memberList.length || currentGroup.member_count }}人</span>
            </div>
          </div>
          <div class="actions">
            <el-button size="small" @click="showMembersDialog = true">成员</el-button>
            <el-button v-if="isGroupAdmin" size="small" @click="showAddMemberDialog = true">拉人</el-button>
          </div>
        </div>
        
        <div class="messages-container" ref="messagesContainer">
          <template v-for="(msg, index) in messages" :key="msg.id">
            <div class="time-divider" v-if="shouldShowTimeDivider(msg, index)">
              {{ formatTimeDivider(msg.created_at) }}
            </div>
            
            <!-- 系统消息 -->
            <div v-if="msg.message_type === 'system'" class="system-message">
              {{ msg.content }}
            </div>
            
            <!-- 公告消息 -->
            <div v-else-if="msg.message_type === 'notice'" class="notice-message">
              <div class="notice-icon">📢</div>
              <div class="notice-body">
                <div class="notice-title">群公告</div>
                <div class="notice-content">{{ msg.content }}</div>
                <div class="notice-footer">{{ msg.sender_name }} · {{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
            
            <!-- 签到通知 -->
            <div v-else-if="msg.message_type === 'checkin'" class="special-card checkin-card">
              <div class="card-icon">✅</div>
              <div class="card-body">
                <div class="card-title">签到</div>
                <div class="card-content">{{ msg.content }}</div>
                <el-button size="small" type="success" @click="goToCheckin(msg)">去签到</el-button>
              </div>
            </div>
            
            <!-- 普通消息 -->
            <div v-else class="message-item" :class="{ mine: msg.sender_id === userId }">
              <div class="avatar-box" v-if="msg.sender_id !== userId">
                <el-avatar :src="getAvatarUrl(msg.sender_avatar)" :size="40">{{ msg.sender_name?.[0] }}</el-avatar>
              </div>
              
              <div class="message-body">
                <div class="sender-name" v-if="msg.sender_id !== userId">{{ msg.sender_name }}</div>
                <div class="bubble-wrapper">
                  <div class="bubble" :class="msg.message_type">
                    <template v-if="msg.message_type === 'text'">
                      <span class="text-content">{{ msg.content }}</span>
                    </template>
                    <template v-else-if="msg.message_type === 'image'">
                      <el-image :src="getFileUrl(msg.file_url)" fit="cover" :preview-src-list="[getFileUrl(msg.file_url)]" class="msg-image" />
                    </template>
                    <template v-else-if="msg.message_type === 'file'">
                      <div class="file-msg" @click="downloadFile(msg)">
                        <div class="file-info">
                          <span class="file-name">{{ msg.file_name }}</span>
                          <span class="file-size">{{ formatFileSize(msg.file_size) }}</span>
                        </div>
                        <el-icon class="file-icon"><Document /></el-icon>
                      </div>
                    </template>
                    <template v-else>
                      <span class="text-content">{{ msg.content }}</span>
                    </template>
                  </div>
                </div>
              </div>
              
              <div class="avatar-box" v-if="msg.sender_id === userId">
                <el-avatar :src="getAvatarUrl(userStore.userInfo?.photoUrl)" :size="40">{{ userStore.userInfo?.realName?.[0] }}</el-avatar>
              </div>
            </div>
          </template>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="toolbar-row">
            <div class="toolbar-left">
              <svg class="tool-icon emoji-icon" viewBox="0 0 24 24" @click="showEmojiPicker = !showEmojiPicker">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="8" cy="10" r="1.2" fill="currentColor"/>
                <circle cx="16" cy="10" r="1.2" fill="currentColor"/>
                <path d="M8 14.5c0 0 1.5 2.5 4 2.5s4-2.5 4-2.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <el-upload :show-file-list="false" :before-upload="handleImageUpload" accept="image/*">
                <el-icon class="tool-icon"><Picture /></el-icon>
              </el-upload>
              <el-upload :show-file-list="false" :before-upload="handleFileUpload">
                <el-icon class="tool-icon"><Folder /></el-icon>
              </el-upload>
              <!-- 教师功能按钮 -->
              <el-popover v-if="isGroupAdmin" trigger="click" width="160" placement="top">
                <template #reference>
                  <el-icon class="tool-icon plus-icon"><Plus /></el-icon>
                </template>
                <div class="teacher-menu">
                  <div class="menu-item" @click="showNoticeDialog = true">📢 发布公告</div>
                  <div class="menu-item" @click="showCheckinDialog = true">✅ 发起签到</div>
                  <div class="menu-item" @click="showQuestionDialog = true">❓ 随机提问</div>
                </div>
              </el-popover>
            </div>
          </div>
          <!-- 表情选择器 -->
          <div class="emoji-picker" v-if="showEmojiPicker">
            <span v-for="emoji in emojis" :key="emoji" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</span>
          </div>
          <div class="input-wrapper">
            <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="" @keydown="handleKeydown" resize="none" />
          </div>
          <div class="send-row">
            <el-button @click="sendMessage" :disabled="!inputMessage.trim()">发送(S)</el-button>
          </div>
        </div>
      </div>
      
      <div class="no-chat" v-else>
        <el-empty description="选择一个群组开始聊天">
          <template #image><span style="font-size: 60px">👥</span></template>
        </el-empty>
      </div>
    </div>

    <!-- 创建群组对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建群组" width="500px">
      <el-form label-position="top">
        <el-form-item label="群组名称" required>
          <el-input v-model="newGroup.name" placeholder="输入群组名称" />
        </el-form-item>
        <el-form-item label="关联课程">
          <el-select v-model="newGroup.course_id" placeholder="选择课程（可选）" clearable style="width: 100%" @change="onCourseChange">
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择成员" v-if="availableStudents.length > 0">
          <el-checkbox-group v-model="newGroup.member_ids">
            <el-checkbox v-for="s in availableStudents" :key="s.user_id" :value="s.user_id">{{ s.real_name }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createGroup" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 群成员对话框 -->
    <el-dialog v-model="showMembersDialog" title="群成员" width="400px">
      <div class="members-list">
        <div v-for="member in memberList" :key="member.user_id" class="member-item">
          <el-avatar :src="getAvatarUrl(member.photo_url)" :size="36">{{ member.real_name?.[0] }}</el-avatar>
          <div class="member-info">
            <span class="member-name">{{ member.real_name }}</span>
            <el-tag v-if="member.role === 'owner'" size="small" type="danger">群主</el-tag>
            <el-tag v-else-if="member.role === 'admin'" size="small" type="warning">管理员</el-tag>
          </div>
          <el-button v-if="isGroupAdmin && member.role !== 'owner' && member.user_id !== userId" type="danger" size="small" text @click="removeMember(member)">移除</el-button>
        </div>
      </div>
      <template #footer>
        <el-button v-if="currentGroup?.my_role === 'owner'" type="danger" @click="dissolveGroup">解散群聊</el-button>
        <el-button v-else-if="currentGroup?.my_role !== 'owner'" type="danger" @click="leaveCurrentGroup">退出群组</el-button>
        <el-button @click="showMembersDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog v-model="showAddMemberDialog" title="添加成员" width="400px">
      <el-input v-model="searchKeyword" placeholder="搜索用户（至少2个字符）" @input="searchUsers" clearable />
      <div class="search-results">
        <div v-for="user in searchUserResults" :key="user.user_id" class="member-item" @click="toggleSelectUser(user)">
          <el-avatar :src="getAvatarUrl(user.photo_url)" :size="36">{{ user.real_name?.[0] }}</el-avatar>
          <div class="member-info">
            <span class="member-name">{{ user.real_name }}</span>
            <span class="member-account">{{ user.system_account }}</span>
          </div>
          <el-checkbox :model-value="selectedUserIds.includes(user.user_id)" />
        </div>
      </div>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="addMembers" :disabled="selectedUserIds.length === 0">添加({{ selectedUserIds.length }})</el-button>
      </template>
    </el-dialog>

    <!-- 发布公告对话框 -->
    <el-dialog v-model="showNoticeDialog" title="发布公告" width="400px">
      <el-input v-model="noticeContent" type="textarea" :rows="4" placeholder="输入公告内容" />
      <template #footer>
        <el-button @click="showNoticeDialog = false">取消</el-button>
        <el-button type="primary" @click="sendNotice" :disabled="!noticeContent.trim()">发布</el-button>
      </template>
    </el-dialog>

    <!-- 发起签到对话框 -->
    <el-dialog v-model="showCheckinDialog" title="发起签到" width="450px">
      <el-form label-position="top">
        <el-form-item label="签到说明">
          <el-input v-model="checkinContent" placeholder="如：第3周课堂签到" />
        </el-form-item>
        <el-form-item label="签到方式">
          <div class="checkin-types">
            <div 
              v-for="type in checkinTypes" 
              :key="type.value"
              :class="['checkin-type-item', { active: selectedCheckinType === type.value }]"
              @click="selectedCheckinType = type.value"
            >
              <span class="type-icon">{{ type.icon }}</span>
              <span class="type-name">{{ type.label }}</span>
            </div>
          </div>
        </el-form-item>
        <!-- 手势签到：选择数字 -->
        <el-form-item v-if="selectedCheckinType === 'gesture'" label="指定手势数字">
          <div class="gesture-numbers">
            <div 
              v-for="n in 5" 
              :key="n"
              :class="['gesture-num', { active: gestureNumber === n }]"
              @click="gestureNumber = n"
            >
              {{ ['☝️', '✌️', '🤟', '🖖', '🖐️'][n-1] }} {{ n }}
            </div>
          </div>
        </el-form-item>
        <!-- 位置签到：获取当前位置 -->
        <el-form-item v-if="selectedCheckinType === 'location'" label="签到位置">
          <div class="location-setting">
            <el-button @click="getCurrentLocation" :loading="gettingLocation">
              {{ checkinLocation.lat ? '重新定位' : '获取当前位置' }}
            </el-button>
            <span v-if="checkinLocation.lat" class="location-info">
              ✅ 已定位 ({{ checkinLocation.lat.toFixed(6) }}, {{ checkinLocation.lng.toFixed(6) }})
            </span>
          </div>
          <div class="location-range" v-if="checkinLocation.lat">
            <span>允许范围：</span>
            <el-input-number v-model="checkinLocationRange" :min="10" :max="500" :step="10" /> 米
          </div>
        </el-form-item>
        <el-form-item label="签到时长（分钟）">
          <el-input-number v-model="checkinDuration" :min="1" :max="60" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCheckinDialog = false">取消</el-button>
        <el-button type="primary" @click="sendCheckin" :disabled="!canSendCheckin">发起签到</el-button>
      </template>
    </el-dialog>

    <!-- 随机提问对话框 -->
    <el-dialog v-model="showQuestionDialog" title="随机提问" width="450px">
      <div v-if="pickedStudents.length === 0" class="random-pick">
        <div class="pick-hint">选择要随机抽取的学生人数</div>
        <div class="pick-count">
          <el-input-number v-model="pickCount" :min="1" :max="maxPickCount" />
          <span class="count-hint">/ {{ maxPickCount }} 人</span>
        </div>
        <el-button type="primary" size="large" @click="pickRandomStudents">🎲 随机选人</el-button>
      </div>
      <div v-else class="picked-students">
        <div class="picked-list">
          <div v-for="student in pickedStudents" :key="student.user_id" class="picked-item">
            <el-avatar :size="50">{{ student.real_name?.[0] }}</el-avatar>
            <span class="student-name">{{ student.real_name }}</span>
          </div>
        </div>
        <div class="pick-actions">
          <el-button @click="resetPick">重新选择</el-button>
          <el-button type="primary" @click="confirmPick">确认并发送</el-button>
        </div>
      </div>
    </el-dialog>
  </Layout>
</template>


<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getMyGroups, createGroup as createGroupApi, getGroupInfo, getGroupMessages, addGroupMembers, removeGroupMember, leaveGroup, dissolveGroup as dissolveGroupApi, getMyCourses, getCourseStudents, searchUsersForGroup, sendGroupNotice } from '@/api/groupChat'
import socketService from '@/utils/socket'
import Layout from '@/components/Layout.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Folder, Document, Plus, ArrowLeft } from '@element-plus/icons-vue'
import config from '@/config'

const router = useRouter()
const userStore = useUserStore()
const userId = computed(() => userStore.userInfo?.userId)
const API_BASE = config.staticUrl

// 移动端视图切换
const mobileShowChat = ref(false)

// 群组相关
const groups = ref([])
const currentGroup = ref(null)
const messages = ref([])
const memberList = ref([])
const inputMessage = ref('')
const messagesContainer = ref(null)

// 对话框
const showCreateDialog = ref(false)
const showMembersDialog = ref(false)
const showAddMemberDialog = ref(false)
const showNoticeDialog = ref(false)
const showCheckinDialog = ref(false)
const showQuestionDialog = ref(false)
const showEmojiPicker = ref(false)

// 创建群组
const newGroup = reactive({ name: '', course_id: null, member_ids: [] })
const courses = ref([])
const availableStudents = ref([])
const creating = ref(false)

// 添加成员
const searchKeyword = ref('')
const searchUserResults = ref([])
const selectedUserIds = ref([])

// 功能
const noticeContent = ref('')
const checkinContent = ref('')
const selectedCheckinType = ref('qrcode')
const checkinDuration = ref(5)
const gestureNumber = ref(1)
const checkinLocation = ref({ lat: null, lng: null })
const checkinLocationRange = ref(50)
const gettingLocation = ref(false)

// 随机选人
const pickCount = ref(1)
const pickedStudents = ref([])
const maxPickCount = computed(() => {
  const students = memberList.value.filter(m => m.role === 'member')
  return Math.max(1, students.length)
})

// 签到类型
const checkinTypes = [
  { value: 'qrcode', label: '扫码签到', icon: '📱' },
  { value: 'face', label: '人脸签到', icon: '😊' },
  { value: 'gesture', label: '手势签到', icon: '✋' },
  { value: 'location', label: '位置签到', icon: '📍' }
]

// 表情
const emojis = ['😀','😃','😄','😁','😆','😅','🤣','😂','🙂','😊','😇','🥰','😍','🤩','😘','😗','👍','👎','👏','🙌','❤️','🔥','🎉','💯']

const isGroupAdmin = computed(() => currentGroup.value?.my_role === 'owner' || currentGroup.value?.my_role === 'admin')

// 检查是否可以发起签到
const canSendCheckin = computed(() => {
  if (selectedCheckinType.value === 'gesture' && !gestureNumber.value) return false
  if (selectedCheckinType.value === 'location' && !checkinLocation.value.lat) return false
  return true
})

const getAvatarUrl = (url) => {
  if (!url) return ''
  return url.startsWith('http') ? url : `${API_BASE}${url}`
}

const getFileUrl = (url) => {
  if (!url) return ''
  return url.startsWith('http') ? url : `${API_BASE}${url}`
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const shouldShowTimeDivider = (msg, index) => {
  if (index === 0) return true
  const prev = messages.value[index - 1]
  return new Date(msg.created_at).getTime() - new Date(prev.created_at).getTime() > 5 * 60 * 1000
}

const formatTimeDivider = (time) => {
  const date = new Date(time)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++ }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

// 加载群组
const loadGroups = async () => {
  try {
    const res = await getMyGroups()
    if (res.success) groups.value = res.groups
  } catch (e) {
    console.error('加载群组失败:', e)
  }
}

// 选择群组
const selectGroup = async (group) => {
  currentGroup.value = group
  messages.value = []
  mobileShowChat.value = true // 移动端切换到聊天视图
  socketService.emit('join_group', { group_id: group.id })
  await loadGroupDetail(group.id)
  await loadMessages()
}

const loadGroupDetail = async (groupId) => {
  try {
    const res = await getGroupInfo(groupId)
    if (res.success) {
      currentGroup.value = { ...currentGroup.value, ...res.group }
      memberList.value = res.group.members || []
    }
  } catch (e) {
    console.error('加载群详情失败:', e)
  }
}

const loadMessages = async () => {
  if (!currentGroup.value) return
  try {
    const res = await getGroupMessages(currentGroup.value.id, 1)
    if (res.success) {
      messages.value = res.messages
      scrollToBottom()
    }
  } catch (e) {
    console.error('加载消息失败:', e)
  }
}

// 发送消息
const sendMessage = () => {
  if (!inputMessage.value.trim() || !currentGroup.value) return
  socketService.emit('send_group_message', {
    group_id: currentGroup.value.id,
    message_type: 'text',
    content: inputMessage.value.trim()
  })
  inputMessage.value = ''
  showEmojiPicker.value = false
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const insertEmoji = (emoji) => {
  inputMessage.value += emoji
}

// 上传图片
const handleImageUpload = async (file) => {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片不能超过10MB')
    return false
  }
  // TODO: 实现图片上传
  ElMessage.info('图片上传功能开发中')
  return false
}

// 上传文件
const handleFileUpload = async (file) => {
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件不能超过50MB')
    return false
  }
  // TODO: 实现文件上传
  ElMessage.info('文件上传功能开发中')
  return false
}

const downloadFile = (msg) => {
  window.open(getFileUrl(msg.file_url), '_blank')
}

// 创建群组
const createGroup = async () => {
  if (!newGroup.name.trim()) {
    ElMessage.warning('请输入群组名称')
    return
  }
  creating.value = true
  try {
    const res = await createGroupApi({
      name: newGroup.name,
      course_id: newGroup.course_id,
      member_ids: newGroup.member_ids
    })
    if (res.success) {
      ElMessage.success('群组创建成功')
      showCreateDialog.value = false
      newGroup.name = ''
      newGroup.course_id = null
      newGroup.member_ids = []
      loadGroups()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const onCourseChange = async (courseId) => {
  if (!courseId) {
    availableStudents.value = []
    return
  }
  try {
    const res = await getCourseStudents(courseId)
    if (res.success) availableStudents.value = res.students
  } catch (e) {
    console.error(e)
  }
}

// 搜索用户
let searchTimer = null
const searchUsers = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (searchKeyword.value.length < 2) {
      searchUserResults.value = []
      return
    }
    try {
      const res = await searchUsersForGroup(searchKeyword.value)
      if (res.success) {
        const memberIds = memberList.value.map(m => m.user_id)
        searchUserResults.value = res.users.filter(u => !memberIds.includes(u.user_id))
      }
    } catch (e) {
      console.error(e)
    }
  }, 300)
}

const toggleSelectUser = (user) => {
  const idx = selectedUserIds.value.indexOf(user.user_id)
  if (idx === -1) selectedUserIds.value.push(user.user_id)
  else selectedUserIds.value.splice(idx, 1)
}

const addMembers = async () => {
  try {
    const res = await addGroupMembers(currentGroup.value.id, selectedUserIds.value)
    if (res.success) {
      ElMessage.success(res.message)
      showAddMemberDialog.value = false
      selectedUserIds.value = []
      searchKeyword.value = ''
      loadGroupDetail(currentGroup.value.id)
    }
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const removeMember = async (member) => {
  try {
    await ElMessageBox.confirm(`确定移除 ${member.real_name}？`, '提示')
    const res = await removeGroupMember(currentGroup.value.id, member.user_id)
    if (res.success) {
      ElMessage.success('已移除')
      loadGroupDetail(currentGroup.value.id)
    }
  } catch (e) {}
}

const leaveCurrentGroup = async () => {
  try {
    await ElMessageBox.confirm('确定退出群组？', '提示')
    const res = await leaveGroup(currentGroup.value.id)
    if (res.success) {
      ElMessage.success('已退出')
      showMembersDialog.value = false
      currentGroup.value = null
      loadGroups()
    }
  } catch (e) {}
}

// 解散群聊
const dissolveGroup = async () => {
  try {
    await ElMessageBox.confirm('确定解散群聊？解散后所有消息将被删除，此操作不可恢复！', '警告', {
      confirmButtonText: '确定解散',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await dissolveGroupApi(currentGroup.value.id)
    if (res.success) {
      ElMessage.success('群聊已解散')
      showMembersDialog.value = false
      currentGroup.value = null
      loadGroups()
    } else {
      ElMessage.error(res.message || '解散失败')
    }
  } catch (e) {}
}

// 发布公告
const sendNotice = async () => {
  if (!noticeContent.value.trim()) return
  try {
    const res = await sendGroupNotice(currentGroup.value.id, noticeContent.value)
    if (res.success) {
      ElMessage.success('公告已发布')
      showNoticeDialog.value = false
      noticeContent.value = ''
      loadMessages()
    }
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

// 发起签到
// 获取当前位置
const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    ElMessage.error('浏览器不支持定位功能')
    return
  }
  gettingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      checkinLocation.value = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude
      }
      gettingLocation.value = false
      ElMessage.success('定位成功')
    },
    (err) => {
      gettingLocation.value = false
      ElMessage.error('定位失败：' + err.message)
    },
    { enableHighAccuracy: false, timeout: 10000 }
  )
}

const sendCheckin = () => {
  const typeInfo = checkinTypes.find(t => t.value === selectedCheckinType.value)
  const typeLabel = typeInfo ? typeInfo.label : '签到'
  const content = checkinContent.value 
    ? `${checkinContent.value}（${typeLabel}，${checkinDuration.value}分钟）`
    : `老师发起了${typeLabel}，限时${checkinDuration.value}分钟`
  
  const messageData = {
    group_id: currentGroup.value.id,
    message_type: 'checkin',
    content: content,
    checkin_type: selectedCheckinType.value,
    duration: checkinDuration.value
  }
  
  // 手势签到添加数字
  if (selectedCheckinType.value === 'gesture') {
    messageData.gesture_number = gestureNumber.value
  }
  
  // 位置签到添加位置信息
  if (selectedCheckinType.value === 'location') {
    messageData.location_lat = checkinLocation.value.lat
    messageData.location_lng = checkinLocation.value.lng
    messageData.location_range = checkinLocationRange.value
  }
  
  socketService.emit('send_group_message', messageData)
  showCheckinDialog.value = false
  checkinContent.value = ''
  selectedCheckinType.value = 'qrcode'
  checkinDuration.value = 5
  gestureNumber.value = 1
  checkinLocation.value = { lat: null, lng: null }
  checkinLocationRange.value = 50
  ElMessage.success('签到已发起')
}

// 随机选人
const pickRandomStudents = () => {
  const students = memberList.value.filter(m => m.role === 'member')
  if (students.length === 0) {
    ElMessage.warning('没有可选的学生')
    return
  }
  const count = Math.min(pickCount.value, students.length)
  const shuffled = [...students].sort(() => Math.random() - 0.5)
  pickedStudents.value = shuffled.slice(0, count)
}

const resetPick = () => {
  pickedStudents.value = []
  pickCount.value = 1
}

const confirmPick = () => {
  const names = pickedStudents.value.map(s => s.real_name).join('、')
  const content = pickedStudents.value.length === 1
    ? `🎯 随机点名：${names}，请回答问题！`
    : `🎯 随机点名 ${pickedStudents.value.length} 人：${names}，请回答问题！`
  
  socketService.emit('send_group_message', {
    group_id: currentGroup.value.id,
    message_type: 'text',
    content: content
  })
  showQuestionDialog.value = false
  resetPick()
}

const goToCheckin = (msg) => {
  // 如果消息中有签到ID或签到码，带上参数跳转
  if (msg?.reference_id) {
    router.push(`/checkin/student?id=${msg.reference_id}`)
  } else if (msg?.checkin_code) {
    router.push(`/checkin/scan?code=${msg.checkin_code}`)
  } else {
    router.push('/checkin/student')
  }
}

// WebSocket
const setupSocketListeners = () => {
  socketService.on('new_group_message', (msg) => {
    if (currentGroup.value && msg.group_id === currentGroup.value.id) {
      messages.value.push(msg)
      scrollToBottom()
    }
  })
}

onMounted(async () => {
  socketService.connect()
  await loadGroups()
  if (userStore.hasRole('teacher') || userStore.hasRole('admin')) {
    try {
      const res = await getMyCourses()
      if (res.success) courses.value = res.courses
    } catch (e) {}
  }
  setupSocketListeners()
})

onUnmounted(() => {
  if (currentGroup.value) socketService.emit('leave_group_room', { group_id: currentGroup.value.id })
  socketService.off('new_group_message')
})

watch(currentGroup, (newVal, oldVal) => {
  if (oldVal && oldVal.id !== newVal?.id) {
    socketService.emit('leave_group_room', { group_id: oldVal.id })
  }
})
</script>


<style scoped>
/* ==================== 微信风格群聊界面 ==================== */
.chat-container {
  display: flex;
  height: calc(100vh - 180px);
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  max-height: calc(100vh - 180px);
}

/* 左侧群组列表 - 微信风格 */
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
  display: flex;
  justify-content: center;
}

/* 创建群组按钮 - 圆形加号 */
.create-group-btn {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  background: linear-gradient(135deg, #07c160 0%, #06ad56 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 20px;
}

.create-group-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(7, 193, 96, 0.4);
}

.conversations {
  flex: 1;
  overflow-y: auto;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 12px 10px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.conv-item:hover {
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

/* 群头像 - 绿色渐变 */
.group-avatar {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  background: linear-gradient(135deg, #07c160 0%, #06ad56 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 500;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.conv-info .name {
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

.chat-header .actions {
  display: flex;
  gap: 10px;
}

/* 消息容器 - 微信风格 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #ededed;
  min-height: 0;
}

/* 时间分隔 - 微信风格 */
.time-divider {
  text-align: center;
  margin: 20px 0;
  font-size: 12px;
  color: #b2b2b2;
}

/* 系统消息 */
.system-message {
  text-align: center;
  margin: 15px 0;
  font-size: 12px;
  color: #b2b2b2;
}

/* 公告消息 - 微信风格 */
.notice-message {
  display: flex;
  background: #fff;
  border-radius: 8px;
  padding: 12px 15px;
  margin: 15px 40px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.notice-icon {
  font-size: 24px;
  margin-right: 12px;
  flex-shrink: 0;
}

.notice-body {
  flex: 1;
}

.notice-title {
  font-size: 14px;
  font-weight: 500;
  color: #191919;
  margin-bottom: 6px;
}

.notice-content {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 8px;
}

.notice-footer {
  font-size: 11px;
  color: #b2b2b2;
}

/* 特殊卡片（签到等） */
.special-card {
  display: flex;
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 40px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card-icon {
  font-size: 28px;
  margin-right: 12px;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
  color: #191919;
  margin-bottom: 6px;
}

.card-content {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
}

.checkin-card .el-button {
  background: #07c160;
  border-color: #07c160;
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

.bubble.image {
  padding: 0;
  background: transparent;
}

.bubble.image::before {
  display: none;
}

.msg-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  cursor: pointer;
  display: block;
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

.toolbar-left {
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

/* 加号图标 */
.plus-icon {
  font-size: 24px;
  font-weight: bold;
}

/* 表情选择器 */
.emoji-picker {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 5px;
  max-height: 150px;
  overflow-y: auto;
  padding: 10px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 10px;
  border: 1px solid #e5e5e5;
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
  min-height: 60px !important;
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

/* 教师功能菜单 */
.teacher-menu {
  padding: 5px 0;
}

.menu-item {
  padding: 10px 15px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.15s;
}

.menu-item:hover {
  background: #f5f5f5;
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

/* 成员列表 */
.members-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  gap: 10px;
}

.member-item:last-child {
  border-bottom: none;
}

.member-item :deep(.el-avatar) {
  border-radius: 4px;
  flex-shrink: 0;
}

.member-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-name {
  font-size: 14px;
  color: #191919;
}

.member-account {
  font-size: 12px;
  color: #b2b2b2;
}

/* 搜索结果 */
.search-results {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 10px;
}

/* 随机选人 */
.random-pick {
  text-align: center;
  padding: 30px 20px;
}

.pick-hint {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.pick-count {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 25px;
}

.count-hint {
  font-size: 14px;
  color: #999;
}

.picked-students {
  padding: 20px;
}

.picked-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
  margin-bottom: 25px;
}

.picked-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.picked-item .student-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 0;
}

.pick-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
}

/* 签到类型选择 */
.checkin-types {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.checkin-type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px 10px;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checkin-type-item:hover {
  border-color: #07c160;
  background: #f0fff5;
}

.checkin-type-item.active {
  border-color: #07c160;
  background: #e8f8ef;
}

.checkin-type-item .type-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.checkin-type-item .type-name {
  font-size: 12px;
  color: #333;
}

.checkin-type-item.active .type-name {
  color: #07c160;
  font-weight: 500;
}

/* 手势数字选择 */
.gesture-numbers {
  display: flex;
  gap: 10px;
}

.gesture-num {
  padding: 10px 16px;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.gesture-num:hover {
  border-color: #07c160;
  background: #f0fff5;
}

.gesture-num.active {
  border-color: #07c160;
  background: #e8f8ef;
  color: #07c160;
  font-weight: 500;
}

/* 位置签到设置 */
.location-setting {
  display: flex;
  align-items: center;
  gap: 12px;
}

.location-info {
  color: #07c160;
  font-size: 13px;
}

.location-range {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

/* 对话框样式 */
:deep(.el-dialog__body) {
  padding: 20px;
}

/* 滚动条样式 */
.conversations::-webkit-scrollbar,
.messages-container::-webkit-scrollbar,
.members-list::-webkit-scrollbar,
.search-results::-webkit-scrollbar {
  width: 6px;
}

.conversations::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb,
.members-list::-webkit-scrollbar-thumb,
.search-results::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.conversations::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover,
.members-list::-webkit-scrollbar-thumb:hover,
.search-results::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 移动端响应式 ==================== */
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
    height: calc(100vh - 130px);
    max-height: calc(100vh - 130px);
  }
  
  /* 移动端群组列表 */
  .conversation-list {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
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
    gap: 6px;
  }
  
  .chat-header .actions .el-button {
    padding: 6px 10px;
    font-size: 12px;
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
  
  .file-msg {
    min-width: 180px;
    max-width: 220px;
    padding: 10px;
  }
  
  /* 移动端公告和特殊卡片 */
  .notice-message,
  .special-card {
    margin: 15px 10px;
  }
  
  /* 移动端输入区域 */
  .input-area {
    padding: 8px 10px 12px;
  }
  
  .toolbar-row {
    padding-bottom: 8px;
  }
  
  .toolbar-left {
    gap: 12px;
  }
  
  .tool-icon {
    font-size: 20px;
  }
  
  .input-wrapper :deep(.el-textarea__inner) {
    min-height: 50px !important;
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
  
  /* 移动端签到类型选择 */
  .checkin-types {
    grid-template-columns: repeat(2, 1fr);
  }
  
  /* 移动端对话框 */
  :deep(.el-dialog) {
    width: 90% !important;
    max-width: 400px;
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

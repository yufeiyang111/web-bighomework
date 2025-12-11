<template>
  <Layout pageTitle="签到">
    <div class="student-checkin">
      <!-- 签到方式入口 -->
      <div class="checkin-methods">
        <div class="method-card" @click="showScanDialog = true">
          <div class="method-icon">📱</div>
          <div class="method-info">
            <span class="method-title">扫码签到</span>
            <span class="method-desc">扫描二维码快速签到</span>
          </div>
        </div>
        <div class="method-card" @click="openFaceCheckinPicker">
          <div class="method-icon">👤</div>
          <div class="method-info">
            <span class="method-title">人脸签到</span>
            <span class="method-desc">人脸识别验证签到</span>
          </div>
        </div>
        <div class="method-card" @click="openGestureCheckinPicker">
          <div class="method-icon">✋</div>
          <div class="method-info">
            <span class="method-title">手势签到</span>
            <span class="method-desc">手势+人脸验证签到</span>
          </div>
        </div>
        <div class="method-card" @click="openLocationCheckinPicker">
          <div class="method-icon">📍</div>
          <div class="method-info">
            <span class="method-title">位置签到</span>
            <span class="method-desc">定位验证签到</span>
          </div>
        </div>
        <div class="method-card code-method">
          <div class="method-icon">🔢</div>
          <div class="method-info">
            <span class="method-title">签到码</span>
            <div class="code-input-inline">
              <el-input v-model="manualCode" placeholder="输入签到码" maxlength="8" size="small" />
              <el-button type="primary" size="small" @click="submitByCode" :disabled="!manualCode">签到</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 当前签到任务 -->
      <div v-if="activeCheckins.length > 0" class="active-section">
        <h3>📢 进行中的签到</h3>
        <div class="checkin-cards">
          <div v-for="item in activeCheckins" :key="item.id" class="checkin-card" :class="{ done: item.my_status }">
            <div class="card-header">
              <span class="card-title">{{ item.title }}</span>
              <span class="card-type" :class="item.type">{{ getTypeName(item.type) }}</span>
            </div>
            <div class="card-info">
              <div class="info-item">
                <span class="info-label">群组</span>
                <span class="info-value">{{ item.group_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">剩余时间</span>
                <span class="info-value countdown">{{ formatRemaining(item.end_time) }}</span>
              </div>
            </div>
            <div class="card-action">
              <el-button v-if="!item.my_status" type="primary" @click="doCheckin(item)">
                {{ item.type === 'face' ? '👤 人脸签到' : item.type === 'gesture' ? '✋ 手势签到' : item.type === 'location' ? '📍 位置签到' : '立即签到' }}
              </el-button>
              <span v-else class="checked-tag">✓ {{ item.my_status === 'late' ? '已签到(迟到)' : '已签到' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-active">
        <div class="empty-icon">✅</div>
        <p>暂无进行中的签到</p>
      </div>

      <!-- 签到历史 -->
      <div class="history-section">
        <h3>签到历史</h3>
        <div class="history-card">
          <el-table :data="checkinHistory" border v-if="checkinHistory.length > 0">
            <el-table-column prop="title" label="签到标题" min-width="120" />
            <el-table-column prop="group_name" label="群组" width="100" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <span class="type-badge" :class="row.type">{{ getTypeName(row.type) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="人脸截图" width="80" v-if="hasFaceRecords">
              <template #default="{ row }">
                <el-image 
                  v-if="row.face_image_url" 
                  :src="getImageUrl(row.face_image_url)" 
                  :preview-src-list="[getImageUrl(row.face_image_url)]"
                  fit="cover"
                  class="face-thumb"
                />
                <span v-else class="no-face">-</span>
              </template>
            </el-table-column>
            <el-table-column label="相似度" width="80" v-if="hasFaceRecords">
              <template #default="{ row }">
                <span v-if="row.face_similarity" class="similarity">{{ row.face_similarity }}%</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="checkin_time" label="签到时间" width="150">
              <template #default="{ row }">{{ formatTime(row.checkin_time) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <span :class="['status-tag', row.status]">{{ getStatusName(row.status) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无签到记录" />
        </div>
      </div>
    </div>

    <!-- 扫码对话框 -->
    <el-dialog v-model="showScanDialog" title="扫码签到" width="400px" class="scan-dialog-wrapper">
      <div class="scan-dialog">
        <div v-if="!scanning" class="scan-start">
          <p>点击下方按钮打开摄像头扫描二维码</p>
          <el-button type="primary" @click="startScan">开始扫描</el-button>
        </div>
        <div v-else class="scan-area">
          <video ref="videoRef" autoplay playsinline></video>
          <canvas ref="canvasRef" style="display: none;"></canvas>
          <div class="scan-tip">将二维码放入框内</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="stopScan">取消</el-button>
      </template>
    </el-dialog>

    <!-- 选择人脸签到任务对话框 -->
    <el-dialog v-model="showFacePickerDialog" title="选择人脸签到任务" width="450px">
      <div class="face-picker">
        <div v-if="faceCheckins.length > 0" class="face-checkin-list">
          <div 
            v-for="item in faceCheckins" 
            :key="item.id" 
            class="face-checkin-item"
            :class="{ disabled: item.my_status }"
            @click="!item.my_status && startFaceCheckin(item)"
          >
            <div class="item-info">
              <span class="item-title">{{ item.title }}</span>
              <span class="item-group">{{ item.group_name }}</span>
            </div>
            <div class="item-status">
              <span v-if="item.my_status" class="done-tag">已签到</span>
              <span v-else class="time-tag">{{ formatRemaining(item.end_time) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无进行中的人脸签到" />
      </div>
    </el-dialog>

    <!-- 签到确认对话框 -->
    <el-dialog v-model="showConfirmDialog" title="确认签到" width="400px">
      <div class="confirm-dialog">
        <div class="confirm-icon">✅</div>
        <p class="confirm-title">{{ currentCheckin?.title }}</p>
        <p class="confirm-group">{{ currentCheckin?.group_name }}</p>
      </div>
      <template #footer>
        <el-button @click="showConfirmDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCheckin" :loading="submitting">确认签到</el-button>
      </template>
    </el-dialog>

    <!-- 人脸签到对话框 -->
    <el-dialog v-model="showFaceDialog" title="人脸签到" width="500px" :close-on-click-modal="false" class="face-dialog-wrapper">
      <div class="face-checkin-section">
        <div class="face-checkin-header">
          <span class="checkin-title">{{ currentCheckin?.title }}</span>
          <span class="checkin-group">{{ currentCheckin?.group_name }}</span>
        </div>
        
        <div class="camera-box">
          <video ref="faceVideoRef" autoplay playsinline muted></video>
          <canvas ref="faceCanvasRef" class="hidden"></canvas>
          
          <div class="face-guide" v-if="faceCameraReady && !faceModelLoading">
            <div class="guide-oval" :class="faceGuideClass"></div>
          </div>
          
          <div class="loading-overlay" v-if="faceModelLoading || !faceCameraReady">
            <div class="spinner"></div>
            <p>{{ faceLoadingText }}</p>
          </div>
        </div>
        
        <!-- 检测步骤 -->
        <div class="detect-steps">
          <div class="step-item" :class="getFaceStepClass(1)">
            <div class="step-icon">{{ faceStep >= 1 ? '✓' : '1' }}</div>
            <div class="step-info">
              <span class="step-title">眨眼</span>
              <span class="step-progress" v-if="faceStep === 0">{{ blinkCount }}/2</span>
            </div>
          </div>
          <div class="step-line" :class="{ done: faceStep >= 1 }"></div>
          <div class="step-item" :class="getFaceStepClass(2)">
            <div class="step-icon">{{ faceStep >= 2 ? '✓' : '2' }}</div>
            <div class="step-info">
              <span class="step-title">{{ turnDir === 'left' ? '左转' : '右转' }}</span>
              <span class="step-progress" v-if="faceStep === 1">{{ turnProgress }}%</span>
            </div>
          </div>
          <div class="step-line" :class="{ done: faceStep >= 2 }"></div>
          <div class="step-item" :class="getFaceStepClass(3)">
            <div class="step-icon">{{ faceStep >= 3 ? '✓' : '3' }}</div>
            <div class="step-info">
              <span class="step-title">验证</span>
            </div>
          </div>
        </div>
        
        <div class="tip-box" :class="{ success: faceStep >= 3 }">{{ faceTipText }}</div>
      </div>
      <template #footer>
        <el-button @click="closeFaceDialog">取消</el-button>
        <el-button @click="resetFaceDetection">重新检测</el-button>
        <el-button type="primary" :loading="faceVerifying" :disabled="faceStep < 3" @click="doFaceCheckin">
          {{ faceVerifying ? '验证中...' : '确认签到' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 选择手势签到任务对话框 -->
    <el-dialog v-model="showGesturePickerDialog" title="选择手势签到任务" width="450px">
      <div class="face-picker">
        <div v-if="gestureCheckins.length > 0" class="face-checkin-list">
          <div 
            v-for="item in gestureCheckins" 
            :key="item.id" 
            class="face-checkin-item"
            :class="{ disabled: item.my_status }"
            @click="!item.my_status && startGestureCheckin(item)"
          >
            <div class="item-info">
              <span class="item-title">{{ item.title }}</span>
              <span class="item-group">{{ item.group_name }} · 手势: {{ item.gesture_number }}</span>
            </div>
            <div class="item-status">
              <span v-if="item.my_status" class="done-tag">已签到</span>
              <span v-else class="time-tag">{{ formatRemaining(item.end_time) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无进行中的手势签到" />
      </div>
    </el-dialog>

    <!-- 手势签到对话框 -->
    <el-dialog v-model="showGestureDialog" title="手势签到" width="550px" :close-on-click-modal="false" class="gesture-dialog-wrapper">
      <div class="gesture-checkin-section">
        <div class="face-checkin-header">
          <span class="checkin-title">{{ currentCheckin?.title }}</span>
          <span class="checkin-group">{{ currentCheckin?.group_name }}</span>
        </div>
        
        <div class="gesture-requirement">
          <span class="gesture-label">请比出数字</span>
          <span class="gesture-number">{{ currentCheckin?.gesture_number }}</span>
          <span class="gesture-icon">{{ gestureEmoji }}</span>
        </div>
        
        <div class="camera-box gesture-camera">
          <video ref="gestureVideoRef" autoplay playsinline muted></video>
          <canvas ref="gestureCanvasRef" class="gesture-overlay"></canvas>
          <canvas ref="gestureCaptureCanvas" class="hidden"></canvas>
          
          <div class="gesture-status" v-if="gestureCameraReady && !gestureModelLoading">
            <div class="detected-gesture" :class="{ correct: gestureCorrect, detecting: detectedGesture !== null && !gestureCorrect }">
              <span v-if="detectedGesture !== null">
                检测到: {{ detectedGesture }} 
                <span v-if="gestureCorrect" class="hold-hint">保持中...</span>
              </span>
              <span v-else>请将手放入画面</span>
            </div>
          </div>
          
          <div class="loading-overlay" v-if="gestureModelLoading || !gestureCameraReady">
            <div class="spinner"></div>
            <p>{{ gestureLoadingText }}</p>
          </div>
        </div>
        
        <div class="gesture-steps">
          <div class="step-item" :class="getGestureStepClass(1)">
            <div class="step-icon">{{ gestureStep >= 1 ? '✓' : '1' }}</div>
            <span class="step-title">手势识别</span>
          </div>
          <div class="step-line" :class="{ done: gestureStep >= 1 }"></div>
          <div class="step-item" :class="getGestureStepClass(2)">
            <div class="step-icon">{{ gestureStep >= 2 ? '✓' : '2' }}</div>
            <span class="step-title">人脸验证</span>
          </div>
        </div>
        
        <div class="tip-box" :class="{ success: gestureStep >= 2 }">{{ gestureTipText }}</div>
      </div>
      <template #footer>
        <el-button @click="closeGestureDialog">取消</el-button>
        <el-button @click="resetGestureDetection">重新检测</el-button>
        <el-button type="primary" :loading="gestureVerifying" :disabled="gestureStep < 2" @click="doGestureCheckin">
          {{ gestureVerifying ? '验证中...' : '确认签到' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 选择位置签到任务对话框 -->
    <el-dialog v-model="showLocationPickerDialog" title="选择位置签到任务" width="450px">
      <div class="face-picker">
        <div v-if="locationCheckins.length > 0" class="face-checkin-list">
          <div 
            v-for="item in locationCheckins" 
            :key="item.id" 
            class="face-checkin-item"
            :class="{ disabled: item.my_status }"
            @click="!item.my_status && startLocationCheckin(item)"
          >
            <div class="item-info">
              <span class="item-title">{{ item.title }}</span>
              <span class="item-group">{{ item.group_name }} · 范围: {{ item.location_range || 50 }}米</span>
            </div>
            <div class="item-status">
              <span v-if="item.my_status" class="done-tag">已签到</span>
              <span v-else class="time-tag">{{ formatRemaining(item.end_time) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无进行中的位置签到" />
      </div>
    </el-dialog>

    <!-- 位置签到对话框 -->
    <el-dialog v-model="showLocationDialog" title="位置签到" width="500px" :close-on-click-modal="false" class="location-dialog-wrapper">
      <div class="location-checkin-section">
        <div class="face-checkin-header">
          <span class="checkin-title">{{ currentCheckin?.title }}</span>
          <span class="checkin-group">{{ currentCheckin?.group_name }}</span>
        </div>
        
        <div class="location-target">
          <span class="target-label">签到范围</span>
          <span class="target-range">{{ currentCheckin?.location_range || 50 }}米内</span>
        </div>
        
        <div class="location-map-container" ref="locationMapRef"></div>
        
        <div class="location-status">
          <div v-if="locationLoading" class="status-loading">
            <div class="spinner"></div>
            <span>{{ locationLoadingText }}</span>
          </div>
          <div v-else-if="userLocation.lat" class="status-info">
            <div class="status-row">
              <span class="status-label">您的位置:</span>
              <span class="status-value">{{ userLocation.lat?.toFixed(6) }}, {{ userLocation.lng?.toFixed(6) }}</span>
            </div>
            <div class="status-row" v-if="userLocation.accuracy">
              <span class="status-label">定位精度:</span>
              <span class="status-value" :class="{ 'low-accuracy': userLocation.accuracy > 500 }">
                约{{ Math.round(userLocation.accuracy) }}米
                <span v-if="userLocation.accuracy > 500" class="accuracy-tip">（建议用手机）</span>
              </span>
            </div>
            <div class="status-row" v-if="locationDistance !== null">
              <span class="status-label">距离签到点:</span>
              <span class="status-value" :class="{ 'in-range': locationDistance <= (currentCheckin?.location_range || 50) }">
                {{ locationDistance.toFixed(0) }}米
              </span>
            </div>
          </div>
          <div v-else class="status-empty">
            <el-button type="primary" @click="getUserLocation">📍 获取我的位置</el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeLocationDialog">取消</el-button>
        <el-button @click="getUserLocation" :loading="locationLoading">重新定位</el-button>
        <el-button 
          type="primary" 
          :loading="locationVerifying" 
          :disabled="!userLocation.lat || locationDistance > (currentCheckin?.location_range || 50)"
          @click="doLocationCheckin"
        >
          {{ locationVerifying ? '验证中...' : '确认签到' }}
        </el-button>
      </template>
    </el-dialog>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { getActiveCheckins, getMyCheckinHistory, doCheckin as doCheckinApi, faceCheckin, gestureCheckin, locationCheckin, getCheckinDetail } from '@/api/checkin'
import jsQR from 'jsqr'
import * as faceapi from 'face-api.js'
import config from '@/config'

const activeCheckins = ref([])
const checkinHistory = ref([])
const manualCode = ref('')
const showScanDialog = ref(false)
const showConfirmDialog = ref(false)
const showFacePickerDialog = ref(false)
const scanning = ref(false)
const submitting = ref(false)
const currentCheckin = ref(null)

const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null
let scanInterval = null

// 人脸签到相关
const showFaceDialog = ref(false)
const faceVideoRef = ref(null)
const faceCanvasRef = ref(null)
const faceCameraReady = ref(false)
const faceModelLoading = ref(true)
const faceLoadingText = ref('正在加载...')
const faceVerifying = ref(false)
const faceStep = ref(0)
const blinkCount = ref(0)
const turnDir = ref('left')
const turnProgress = ref(0)
const capturedImage = ref(null)
const faceDetected = ref(false)

let faceStream = null
let faceDetectInterval = null
let faceModelsLoaded = false
let earHistory = []
let lastBlinkTime = 0
const BLINK_COOLDOWN = 400
const YAW_THRESHOLD = 20

// 手势签到相关
const showGestureDialog = ref(false)
const showGesturePickerDialog = ref(false)
const gestureVideoRef = ref(null)
const gestureCanvasRef = ref(null)
const gestureCaptureCanvas = ref(null)
const gestureCameraReady = ref(false)
const gestureModelLoading = ref(true)
const gestureLoadingText = ref('正在加载...')
const gestureVerifying = ref(false)
const gestureStep = ref(0)
const detectedGesture = ref(null)
const gestureCorrect = ref(false)
const gestureCapturedImage = ref(null)

let gestureStream = null
let gestureDetectInterval = null
let handsModel = null
let gestureHoldStart = 0
const GESTURE_HOLD_TIME = 1500 // 需要保持手势1.5秒

// 位置签到相关
const showLocationDialog = ref(false)
const showLocationPickerDialog = ref(false)
const locationLoading = ref(false)
const locationLoadingText = ref('')
const userLocation = ref({ lat: null, lng: null })
const locationVerifying = ref(false)
let locationMapInstance = null

// 计算属性
const faceCheckins = computed(() => activeCheckins.value.filter(c => c.type === 'face'))
const gestureCheckins = computed(() => activeCheckins.value.filter(c => c.type === 'gesture'))
const locationCheckins = computed(() => activeCheckins.value.filter(c => c.type === 'location'))
const hasFaceRecords = computed(() => checkinHistory.value.some(r => r.face_image_url))

const gestureEmoji = computed(() => {
  const emojis = { 1: '☝️', 2: '✌️', 3: '🤟', 4: '🖖', 5: '🖐️' }
  return emojis[currentCheckin.value?.gesture_number] || '✋'
})

const getTypeName = (type) => {
  const types = { normal: '普通', qrcode: '扫码', face: '人脸', gesture: '手势', location: '位置' }
  return types[type] || type
}

const getStatusName = (status) => {
  const names = { checked: '已签到', late: '迟到', absent: '缺勤' }
  return names[status] || status
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const formatRemaining = (endTime) => {
  if (!endTime) return ''
  const diff = new Date(endTime).getTime() - Date.now()
  if (diff <= 0) return '已结束'
  const minutes = Math.floor(diff / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)
  return `${minutes}分${seconds}秒`
}

const getImageUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${config.staticUrl}${url}`
}

const faceTipText = computed(() => {
  if (faceModelLoading.value) return '正在加载人脸检测模型...'
  if (!faceCameraReady.value) return '请允许使用摄像头'
  if (!faceDetected.value) return '⚠️ 请将脸部对准摄像头'
  if (faceStep.value === 0) return '👁️ 请眨眼2次'
  if (faceStep.value === 1) return turnDir.value === 'left' ? '👈 请向左转头' : '👉 请向右转头'
  if (faceStep.value === 2) return '📸 请正对摄像头，正在拍照...'
  return '✅ 活体检测通过，点击确认签到'
})

const faceGuideClass = computed(() => {
  if (!faceDetected.value) return 'warning'
  if (faceStep.value >= 3) return 'success'
  if (faceStep.value > 0) return 'progress'
  return ''
})

const getFaceStepClass = (s) => {
  if (faceStep.value >= s) return 'done'
  if (faceStep.value === s - 1) return 'active'
  return ''
}

const loadData = async () => {
  try {
    const [activeRes, historyRes] = await Promise.all([
      getActiveCheckins(),
      getMyCheckinHistory()
    ])
    if (activeRes.success) activeCheckins.value = activeRes.checkins
    if (historyRes.success) checkinHistory.value = historyRes.records
  } catch (e) {
    console.error(e)
  }
}

const doCheckin = (item) => {
  currentCheckin.value = item
  if (item.type === 'face') {
    showFaceDialog.value = true
    initFaceCamera()
  } else if (item.type === 'gesture') {
    showGestureDialog.value = true
    initGestureCamera()
  } else if (item.type === 'location') {
    showLocationDialog.value = true
    initLocationCheckin()
  } else {
    showConfirmDialog.value = true
  }
}

const openFaceCheckinPicker = () => {
  if (faceCheckins.value.length === 0) {
    ElMessage.info('暂无进行中的人脸签到任务')
    return
  }
  if (faceCheckins.value.length === 1 && !faceCheckins.value[0].my_status) {
    startFaceCheckin(faceCheckins.value[0])
  } else {
    showFacePickerDialog.value = true
  }
}

const startFaceCheckin = (item) => {
  showFacePickerDialog.value = false
  currentCheckin.value = item
  showFaceDialog.value = true
  initFaceCamera()
}

const submitByCode = async () => {
  if (!manualCode.value) return
  submitting.value = true
  try {
    const res = await doCheckinApi({ checkin_code: manualCode.value.toUpperCase() })
    if (res.success) {
      ElMessage.success(res.message)
      manualCode.value = ''
      loadData()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('签到失败')
  } finally {
    submitting.value = false
  }
}

const confirmCheckin = async () => {
  if (!currentCheckin.value) return
  submitting.value = true
  try {
    const res = await doCheckinApi({
      checkin_id: currentCheckin.value.id,
      checkin_code: currentCheckin.value.checkin_code || ''
    })
    if (res.success) {
      ElMessage.success(res.message)
      showConfirmDialog.value = false
      loadData()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('签到失败')
  } finally {
    submitting.value = false
  }
}

// 二维码扫描
const startScan = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      scanning.value = true
      scanInterval = setInterval(scanQrCode, 200)
    }
  } catch (e) {
    ElMessage.error('无法访问摄像头')
  }
}

const scanQrCode = () => {
  if (!videoRef.value || !canvasRef.value) return
  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (video.readyState !== video.HAVE_ENOUGH_DATA) return
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const code = jsQR(imageData.data, imageData.width, imageData.height)
  if (code && code.data) {
    stopScan()
    try {
      const url = new URL(code.data)
      const checkinCode = url.searchParams.get('code')
      if (checkinCode) { manualCode.value = checkinCode; submitByCode() }
    } catch {
      if (code.data.length === 8) { manualCode.value = code.data; submitByCode() }
    }
  }
}

const stopScan = () => {
  scanning.value = false
  showScanDialog.value = false
  if (scanInterval) { clearInterval(scanInterval); scanInterval = null }
  if (stream) { stream.getTracks().forEach(track => track.stop()); stream = null }
}

// 人脸签到
const initFaceCamera = async () => {
  faceModelLoading.value = true
  faceLoadingText.value = '正在启动摄像头...'
  resetFaceDetection()
  try {
    faceStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } })
    if (faceVideoRef.value) {
      faceVideoRef.value.srcObject = faceStream
      await new Promise(r => { faceVideoRef.value.onloadedmetadata = r })
      faceCameraReady.value = true
    }
    if (!faceModelsLoaded) {
      faceLoadingText.value = '正在加载人脸检测模型...'
      await loadFaceModels()
      faceModelsLoaded = true
    }
    faceModelLoading.value = false
    startFaceDetection()
  } catch (err) {
    faceModelLoading.value = false
    ElMessage.error('摄像头初始化失败: ' + (err.message || err.name))
  }
}

const loadFaceModels = async () => {
  const LOCAL_URL = '/models'
  const CDN_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model'
  try { await faceapi.nets.tinyFaceDetector.loadFromUri(LOCAL_URL) } 
  catch { await faceapi.nets.tinyFaceDetector.loadFromUri(CDN_URL) }
  try { await faceapi.nets.faceLandmark68Net.loadFromUri(LOCAL_URL) } 
  catch { await faceapi.nets.faceLandmark68Net.loadFromUri(CDN_URL) }
}

const startFaceDetection = () => {
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 })
  faceDetectInterval = setInterval(async () => {
    if (!faceVideoRef.value || !faceCameraReady.value || faceStep.value >= 3) return
    try {
      const detection = await faceapi.detectSingleFace(faceVideoRef.value, options).withFaceLandmarks()
      if (detection) {
        faceDetected.value = true
        const positions = detection.landmarks.positions
        const ear = calculateEAR(positions)
        const yaw = calculateYaw(positions)
        if (faceStep.value === 0) detectBlink(ear)
        if (faceStep.value === 1) detectTurn(yaw)
        if (faceStep.value === 2 && Math.abs(yaw) < 8) { capturePhoto(); faceStep.value = 3 }
      } else { faceDetected.value = false }
    } catch (e) { console.error('检测错误:', e) }
  }, 100)
}

const calculateEAR = (positions) => {
  const euclidean = (p1, p2) => Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
  const leftV1 = euclidean(positions[37], positions[41])
  const leftV2 = euclidean(positions[38], positions[40])
  const leftH = euclidean(positions[36], positions[39])
  const leftEAR = (leftV1 + leftV2) / (2 * leftH)
  const rightV1 = euclidean(positions[43], positions[47])
  const rightV2 = euclidean(positions[44], positions[46])
  const rightH = euclidean(positions[42], positions[45])
  const rightEAR = (rightV1 + rightV2) / (2 * rightH)
  return (leftEAR + rightEAR) / 2
}

const calculateYaw = (positions) => {
  const nose = positions[30], leftJaw = positions[0], rightJaw = positions[16]
  const faceWidth = rightJaw.x - leftJaw.x
  const faceCenter = (leftJaw.x + rightJaw.x) / 2
  const noseOffset = nose.x - faceCenter
  const ratio = (noseOffset / (faceWidth / 2)) * 2
  return Math.asin(Math.max(-1, Math.min(1, ratio))) * (180 / Math.PI)
}

const detectBlink = (ear) => {
  const now = Date.now()
  earHistory.push({ ear, time: now })
  if (earHistory.length > 15) earHistory.shift()
  if (earHistory.length < 10) return
  const stableEars = earHistory.slice(0, -3).map(h => h.ear)
  const avgEAR = stableEars.reduce((a, b) => a + b) / stableEars.length
  const currentEAR = Math.min(...earHistory.slice(-2).map(h => h.ear))
  const dropPercent = ((avgEAR - currentEAR) / avgEAR) * 100
  if (dropPercent > 6.5 && (now - lastBlinkTime) > BLINK_COOLDOWN) {
    const lastThree = earHistory.slice(-3)
    const isRecovering = lastThree[2].ear > lastThree[1].ear && lastThree[1].ear > lastThree[0].ear * 0.95
    if (isRecovering) {
      lastBlinkTime = now
      blinkCount.value++
      if (blinkCount.value >= 2) { faceStep.value = 1; turnDir.value = Math.random() > 0.5 ? 'left' : 'right' }
    }
  }
}

const detectTurn = (yaw) => {
  const progress = Math.min(100, Math.abs(yaw) / YAW_THRESHOLD * 100)
  turnProgress.value = Math.round(progress)
  if (turnDir.value === 'left' && yaw < -YAW_THRESHOLD) faceStep.value = 2
  else if (turnDir.value === 'right' && yaw > YAW_THRESHOLD) faceStep.value = 2
}

const capturePhoto = () => {
  if (!faceVideoRef.value || !faceCanvasRef.value) return
  const canvas = faceCanvasRef.value, video = faceVideoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  capturedImage.value = canvas.toDataURL('image/jpeg', 0.9)
}

const resetFaceDetection = () => {
  faceStep.value = 0; blinkCount.value = 0
  turnDir.value = Math.random() > 0.5 ? 'left' : 'right'
  turnProgress.value = 0; capturedImage.value = null
  faceDetected.value = false; earHistory = []; lastBlinkTime = 0
}

const stopFaceCamera = () => {
  if (faceDetectInterval) { clearInterval(faceDetectInterval); faceDetectInterval = null }
  if (faceStream) { faceStream.getTracks().forEach(t => t.stop()); faceStream = null }
  faceCameraReady.value = false
}

const closeFaceDialog = () => { stopFaceCamera(); showFaceDialog.value = false; resetFaceDetection() }

const doFaceCheckin = async () => {
  console.log('[人脸签到] 开始提交')
  console.log('[人脸签到] currentCheckin:', currentCheckin.value)
  console.log('[人脸签到] capturedImage 长度:', capturedImage.value?.length)
  
  if (!capturedImage.value || !currentCheckin.value) { 
    ElMessage.warning('请完成活体检测')
    return 
  }
  
  faceVerifying.value = true
  try {
    console.log('[人脸签到] 发送请求到后端...')
    const res = await faceCheckin({
      checkin_id: currentCheckin.value.id,
      face_image: capturedImage.value,
      liveness_data: { blink_detected: true, head_turn_detected: true }
    })
    console.log('[人脸签到] 后端响应:', res)
    
    if (res.success) { 
      ElMessage.success(res.message)
      closeFaceDialog()
      loadData() 
    } else { 
      ElMessage.error(res.message || '人脸签到失败')
      resetFaceDetection() 
    }
  } catch (e) { 
    console.error('[人脸签到] 请求失败:', e)
    ElMessage.error(e.message || '签到失败')
    resetFaceDetection() 
  } finally { 
    faceVerifying.value = false 
  }
}

// 手势签到相关函数
const openGestureCheckinPicker = () => {
  if (gestureCheckins.value.length === 0) {
    ElMessage.info('暂无进行中的手势签到任务')
    return
  }
  if (gestureCheckins.value.length === 1 && !gestureCheckins.value[0].my_status) {
    startGestureCheckin(gestureCheckins.value[0])
  } else {
    showGesturePickerDialog.value = true
  }
}

const startGestureCheckin = (item) => {
  showGesturePickerDialog.value = false
  currentCheckin.value = item
  showGestureDialog.value = true
  initGestureCamera()
}

const initGestureCamera = async () => {
  gestureModelLoading.value = true
  gestureLoadingText.value = '正在启动摄像头...'
  resetGestureDetection()
  try {
    gestureStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } })
    if (gestureVideoRef.value) {
      gestureVideoRef.value.srcObject = gestureStream
      await new Promise(r => { gestureVideoRef.value.onloadedmetadata = r })
      gestureCameraReady.value = true
    }
    gestureLoadingText.value = '正在加载手势检测模型...'
    try {
      await loadHandsModel()
      gestureModelLoading.value = false
      startGestureDetection()
    } catch (err) {
      gestureModelLoading.value = false
      gestureLoadingText.value = '模型加载失败，请刷新重试'
      console.error('[手势检测] 初始化失败:', err)
      ElMessage.error('手势检测模型加载失败')
    }
  } catch (err) {
    gestureModelLoading.value = false
    ElMessage.error('摄像头初始化失败: ' + (err.message || err.name))
  }
}

const loadHandsModel = async () => {
  // 使用 MediaPipe Hands CDN
  if (!handsModel) {
    try {
      console.log('[手势检测] 开始加载 MediaPipe Hands...')
      const { Hands } = await import('@mediapipe/hands')
      handsModel = new Hands({
        locateFile: (file) => {
          console.log('[手势检测] 加载文件:', file)
          return `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`
        }
      })
      handsModel.setOptions({
        maxNumHands: 1,
        modelComplexity: 0,  // 使用轻量模型，更快
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      })
      handsModel.onResults(onHandsResults)
      // 初始化模型（发送一个空帧来预热）
      console.log('[手势检测] 初始化模型...')
      await handsModel.initialize()
      console.log('[手势检测] 模型加载完成!')
    } catch (err) {
      console.error('[手势检测] 模型加载失败:', err)
      throw err
    }
  }
}

const onHandsResults = (results) => {
  const canvas = gestureCanvasRef.value
  const video = gestureVideoRef.value
  if (!canvas || !video) return
  
  const ctx = canvas.getContext('2d')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  ctx.save()
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.scale(-1, 1)
  ctx.translate(-canvas.width, 0)
  
  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0]
    console.log('[手势检测] 检测到手部!')
    
    // 绘制手部关键点
    drawHandLandmarks(ctx, landmarks, canvas.width, canvas.height)
    
    // 识别手势数字
    const gesture = recognizeGesture(landmarks)
    console.log('[手势检测] 识别结果:', gesture)
    detectedGesture.value = gesture
    
    // 检查是否是正确的手势
    const requiredGesture = currentCheckin.value?.gesture_number
    if (gesture === requiredGesture) {
      if (!gestureCorrect.value) {
        gestureCorrect.value = true
        gestureHoldStart = Date.now()
      } else if (Date.now() - gestureHoldStart >= GESTURE_HOLD_TIME && gestureStep.value === 0) {
        // 手势保持足够时间，进入人脸验证
        gestureStep.value = 1
        captureGesturePhoto()
        // 开始人脸检测
        startGestureFaceDetection()
      }
    } else {
      gestureCorrect.value = false
      gestureHoldStart = 0
    }
  } else {
    detectedGesture.value = null
    gestureCorrect.value = false
    gestureHoldStart = 0
  }
  
  ctx.restore()
}

const drawHandLandmarks = (ctx, landmarks, width, height) => {
  // 手指连接定义
  const fingerConnections = [
    { indices: [0,1,2,3,4], color: '#ff6b6b' },      // 拇指 - 红色
    { indices: [0,5,6,7,8], color: '#4ecdc4' },      // 食指 - 青色
    { indices: [0,9,10,11,12], color: '#45b7d1' },   // 中指 - 蓝色
    { indices: [0,13,14,15,16], color: '#96ceb4' },  // 无名指 - 绿色
    { indices: [0,17,18,19,20], color: '#dda0dd' }   // 小指 - 紫色
  ]
  
  // 绘制手掌连接
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 3
  const palmConnections = [[5,9],[9,13],[13,17],[0,5],[0,17]]
  palmConnections.forEach(([i, j]) => {
    const p1 = landmarks[i], p2 = landmarks[j]
    ctx.beginPath()
    ctx.moveTo(p1.x * width, p1.y * height)
    ctx.lineTo(p2.x * width, p2.y * height)
    ctx.stroke()
  })
  
  // 绘制每根手指
  fingerConnections.forEach(({ indices, color }) => {
    ctx.strokeStyle = color
    ctx.lineWidth = 4
    for (let i = 0; i < indices.length - 1; i++) {
      const p1 = landmarks[indices[i]], p2 = landmarks[indices[i + 1]]
      ctx.beginPath()
      ctx.moveTo(p1.x * width, p1.y * height)
      ctx.lineTo(p2.x * width, p2.y * height)
      ctx.stroke()
    }
  })
  
  // 绘制关键点
  landmarks.forEach((point, i) => {
    const x = point.x * width, y = point.y * height
    // 指尖用大圆点
    const isTip = [4, 8, 12, 16, 20].includes(i)
    const radius = isTip ? 8 : 5
    
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, 2 * Math.PI)
    ctx.fillStyle = isTip ? '#ffff00' : (i === 0 ? '#ff0000' : '#00ff00')
    ctx.fill()
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 1
    ctx.stroke()
  })
}

const recognizeGesture = (landmarks) => {
  // 计算两点距离
  const distance = (p1, p2) => Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
  
  // 手腕和中指根部的距离作为参考
  const wrist = landmarks[0]
  const middleMcp = landmarks[9]
  const palmSize = distance(wrist, middleMcp)
  
  // 判断手指是否伸直（使用指尖到手腕的距离与手掌大小的比例）
  const isFingerUp = (tipIdx, mcpIdx) => {
    const tip = landmarks[tipIdx]
    const mcp = landmarks[mcpIdx]
    // 指尖到手腕的距离
    const tipToWrist = distance(tip, wrist)
    // 指根到手腕的距离
    const mcpToWrist = distance(mcp, wrist)
    // 如果指尖比指根更远离手腕，说明手指伸直
    return tipToWrist > mcpToWrist * 1.1
  }
  
  // 拇指特殊处理：检查拇指尖是否远离手掌中心
  const isThumbUp = () => {
    const thumbTip = landmarks[4]
    const thumbIp = landmarks[3]
    const thumbMcp = landmarks[2]
    const indexMcp = landmarks[5]
    
    // 拇指尖到食指根部的距离
    const thumbToIndex = distance(thumbTip, indexMcp)
    // 如果拇指尖远离食指根部，说明拇指张开
    return thumbToIndex > palmSize * 0.7
  }
  
  // 检测每个手指状态
  const fingers = [
    isThumbUp(),                    // 拇指
    isFingerUp(8, 5),               // 食指
    isFingerUp(12, 9),              // 中指
    isFingerUp(16, 13),             // 无名指
    isFingerUp(20, 17)              // 小指
  ]
  
  // 计算伸直的手指数量（不含拇指）
  const extendedCount = fingers.slice(1).filter(Boolean).length
  const thumbUp = fingers[0]
  
  // 手势判断逻辑
  // 1: 只有食指伸直
  if (extendedCount === 1 && fingers[1] && !thumbUp) return 1
  // 2: 食指和中指伸直（剪刀手）
  if (extendedCount === 2 && fingers[1] && fingers[2] && !fingers[3] && !fingers[4]) return 2
  // 3: 三根手指伸直（食指+中指+无名指 或 摇滚手势）
  if (extendedCount === 3 && fingers[1] && fingers[2] && fingers[3] && !fingers[4]) return 3
  if (thumbUp && fingers[1] && !fingers[2] && !fingers[3] && fingers[4]) return 3 // 🤟
  // 4: 四根手指伸直（除拇指外）
  if (extendedCount === 4 && !thumbUp) return 4
  // 5: 全部伸直（张开手掌）
  if (extendedCount >= 4 && thumbUp) return 5
  
  return null
}

const startGestureDetection = () => {
  console.log('[手势检测] 开始检测循环')
  let frameCount = 0
  gestureDetectInterval = setInterval(async () => {
    if (!gestureVideoRef.value || !gestureCameraReady.value || gestureStep.value >= 2) return
    if (handsModel && gestureVideoRef.value.readyState >= 2) {
      try {
        frameCount++
        if (frameCount % 50 === 0) {
          console.log('[手势检测] 已处理帧数:', frameCount)
        }
        await handsModel.send({ image: gestureVideoRef.value })
      } catch (err) {
        console.error('[手势检测] 发送帧失败:', err)
      }
    }
  }, 100)
}

const startGestureFaceDetection = async () => {
  // 加载人脸模型（如果还没加载）
  if (!faceModelsLoaded) {
    await loadFaceModels()
    faceModelsLoaded = true
  }
  
  // 检测人脸
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 })
  const checkFace = async () => {
    if (gestureStep.value >= 2 || !gestureVideoRef.value) return
    try {
      const detection = await faceapi.detectSingleFace(gestureVideoRef.value, options)
      if (detection) {
        gestureStep.value = 2
        captureGesturePhoto()
      } else {
        setTimeout(checkFace, 200)
      }
    } catch (e) {
      setTimeout(checkFace, 200)
    }
  }
  checkFace()
}

const captureGesturePhoto = () => {
  if (!gestureVideoRef.value || !gestureCaptureCanvas.value) return
  const canvas = gestureCaptureCanvas.value, video = gestureVideoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  gestureCapturedImage.value = canvas.toDataURL('image/jpeg', 0.9)
}

const resetGestureDetection = () => {
  gestureStep.value = 0
  detectedGesture.value = null
  gestureCorrect.value = false
  gestureCapturedImage.value = null
  gestureHoldStart = 0
}

const stopGestureCamera = () => {
  if (gestureDetectInterval) { clearInterval(gestureDetectInterval); gestureDetectInterval = null }
  if (gestureStream) { gestureStream.getTracks().forEach(t => t.stop()); gestureStream = null }
  gestureCameraReady.value = false
}

const closeGestureDialog = () => {
  stopGestureCamera()
  showGestureDialog.value = false
  resetGestureDetection()
}

const getGestureStepClass = (s) => {
  if (gestureStep.value >= s) return 'done'
  if (gestureStep.value === s - 1) return 'active'
  return ''
}

const gestureTipText = computed(() => {
  if (gestureModelLoading.value) return '正在加载手势检测模型...'
  if (!gestureCameraReady.value) return '请允许使用摄像头'
  if (gestureStep.value === 0) {
    if (detectedGesture.value === null) return '👋 请将手放入画面'
    if (gestureCorrect.value) return `✓ 检测到正确手势，请保持...`
    return `❌ 请比出数字 ${currentCheckin.value?.gesture_number}`
  }
  if (gestureStep.value === 1) return '👤 正在验证人脸...'
  return '✅ 验证通过，点击确认签到'
})

const doGestureCheckin = async () => {
  if (!gestureCapturedImage.value || !currentCheckin.value) {
    ElMessage.warning('请完成手势和人脸验证')
    return
  }
  
  gestureVerifying.value = true
  try {
    const res = await gestureCheckin({
      checkin_id: currentCheckin.value.id,
      face_image: gestureCapturedImage.value,
      detected_gesture: currentCheckin.value.gesture_number,
      liveness_data: { gesture_verified: true }
    })
    
    if (res.success) {
      ElMessage.success(res.message)
      closeGestureDialog()
      loadData()
    } else {
      ElMessage.error(res.message || '手势签到失败')
      resetGestureDetection()
    }
  } catch (e) {
    ElMessage.error(e.message || '签到失败')
    resetGestureDetection()
  } finally {
    gestureVerifying.value = false
  }
}

// 位置签到相关函数
const locationMapRef = ref(null)
const locationDistance = ref(null)

const openLocationCheckinPicker = () => {
  if (locationCheckins.value.length === 0) {
    ElMessage.info('暂无进行中的位置签到任务')
    return
  }
  if (locationCheckins.value.length === 1 && !locationCheckins.value[0].my_status) {
    startLocationCheckin(locationCheckins.value[0])
  } else {
    showLocationPickerDialog.value = true
  }
}

const startLocationCheckin = (item) => {
  showLocationPickerDialog.value = false
  currentCheckin.value = item
  showLocationDialog.value = true
  initLocationCheckin()
}

const initLocationCheckin = async () => {
  locationLoading.value = true
  locationLoadingText.value = '正在初始化...'
  userLocation.value = { lat: null, lng: null }
  locationDistance.value = null
  
  // 初始化地图
  setTimeout(() => {
    initLocationMap()
    getUserLocation()
  }, 100)
}

const initLocationMap = async () => {
  if (!locationMapRef.value) return
  
  // 动态加载 Leaflet
  if (!window.L) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
    
    await new Promise((resolve) => {
      const script = document.createElement('script')
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
      script.onload = resolve
      document.head.appendChild(script)
    })
  }
  
  const L = window.L
  const checkin = currentCheckin.value
  if (!checkin?.location_lat || !checkin?.location_lng) return
  
  // 销毁旧地图
  if (locationMapInstance) {
    locationMapInstance.remove()
  }
  
  // 创建地图，以签到点为中心
  locationMapInstance = L.map(locationMapRef.value).setView(
    [parseFloat(checkin.location_lat), parseFloat(checkin.location_lng)], 
    17
  )
  
  // 添加地图图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(locationMapInstance)
  
  // 添加签到点标记
  const targetMarker = L.marker([parseFloat(checkin.location_lat), parseFloat(checkin.location_lng)], {
    icon: L.divIcon({
      className: 'target-marker',
      html: '<div style="background:#07c160;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;white-space:nowrap;">📍 签到点</div>',
      iconSize: [80, 30],
      iconAnchor: [40, 30]
    })
  }).addTo(locationMapInstance)
  
  // 添加范围圆
  L.circle([parseFloat(checkin.location_lat), parseFloat(checkin.location_lng)], {
    color: '#07c160',
    fillColor: '#07c160',
    fillOpacity: 0.15,
    radius: checkin.location_range || 50
  }).addTo(locationMapInstance)
}

const getUserLocation = () => {
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持定位功能')
    return
  }
  
  locationLoading.value = true
  locationLoadingText.value = '正在获取您的位置...'
  
  const onSuccess = (position) => {
    const accuracy = position.coords.accuracy // 精度（米）
    userLocation.value = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy: accuracy
    }
    locationLoading.value = false
    
    // 根据精度给出提示
    if (accuracy > 1000) {
      ElMessage.warning(`定位精度较差（${Math.round(accuracy)}米），建议使用手机签到`)
    } else if (accuracy > 100) {
      ElMessage.info(`定位成功，精度约${Math.round(accuracy)}米`)
    } else {
      ElMessage.success(`定位成功，精度约${Math.round(accuracy)}米`)
    }
    
    // 计算距离
    calculateDistance()
    
    // 在地图上显示用户位置
    updateUserMarker()
  }
  
  const onError = (error) => {
    console.log('高精度定位失败，尝试低精度定位...', error)
    locationLoadingText.value = '正在尝试低精度定位...'
    
    // 高精度失败，尝试低精度定位
    navigator.geolocation.getCurrentPosition(
      onSuccess,
      (err) => {
        locationLoading.value = false
        let msg = '定位失败'
        switch (err.code) {
          case err.PERMISSION_DENIED:
            msg = '请允许浏览器获取位置权限（设置 > 隐私 > 位置）'
            break
          case err.POSITION_UNAVAILABLE:
            msg = '无法获取位置信息，请检查网络或GPS'
            break
          case err.TIMEOUT:
            msg = '定位超时，请检查网络后重试'
            break
        }
        ElMessage.error(msg)
      },
      { enableHighAccuracy: false, timeout: 30000, maximumAge: 60000 }
    )
  }
  
  // 先尝试高精度定位
  navigator.geolocation.getCurrentPosition(
    onSuccess,
    onError,
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
  )
}

let userMarker = null
const updateUserMarker = () => {
  if (!locationMapInstance || !userLocation.value.lat) return
  
  const L = window.L
  
  // 移除旧标记
  if (userMarker) {
    locationMapInstance.removeLayer(userMarker)
  }
  
  // 添加用户位置标记
  userMarker = L.marker([userLocation.value.lat, userLocation.value.lng], {
    icon: L.divIcon({
      className: 'user-marker',
      html: '<div style="background:#3b82f6;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;white-space:nowrap;">👤 我的位置</div>',
      iconSize: [80, 30],
      iconAnchor: [40, 30]
    })
  }).addTo(locationMapInstance)
  
  // 调整地图视野包含两个点
  const checkin = currentCheckin.value
  if (checkin?.location_lat) {
    const bounds = L.latLngBounds([
      [parseFloat(checkin.location_lat), parseFloat(checkin.location_lng)],
      [userLocation.value.lat, userLocation.value.lng]
    ])
    locationMapInstance.fitBounds(bounds, { padding: [50, 50] })
  }
}

const calculateDistance = () => {
  const checkin = currentCheckin.value
  if (!checkin?.location_lat || !userLocation.value.lat) {
    locationDistance.value = null
    return
  }
  
  const userLat = userLocation.value.lat
  const userLng = userLocation.value.lng
  const targetLat = parseFloat(checkin.location_lat)
  const targetLng = parseFloat(checkin.location_lng)
  
  console.log('[位置签到] 用户位置:', userLat, userLng)
  console.log('[位置签到] 签到点位置:', targetLat, targetLng)
  
  // Haversine 公式
  const R = 6371000 // 地球半径（米）
  const lat1Rad = userLat * Math.PI / 180
  const lat2Rad = targetLat * Math.PI / 180
  const deltaLatRad = (targetLat - userLat) * Math.PI / 180
  const deltaLngRad = (targetLng - userLng) * Math.PI / 180
  
  const a = Math.sin(deltaLatRad/2) ** 2 + Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(deltaLngRad/2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  const distance = R * c
  
  console.log('[位置签到] 计算距离:', distance, '米')
  locationDistance.value = distance
}

const closeLocationDialog = () => {
  showLocationDialog.value = false
  if (locationMapInstance) {
    locationMapInstance.remove()
    locationMapInstance = null
  }
  userMarker = null
  userLocation.value = { lat: null, lng: null }
  locationDistance.value = null
}

const doLocationCheckin = async () => {
  if (!userLocation.value.lat || !currentCheckin.value) {
    ElMessage.warning('请先获取您的位置')
    return
  }
  
  locationVerifying.value = true
  try {
    const res = await locationCheckin({
      checkin_id: currentCheckin.value.id,
      latitude: userLocation.value.lat,
      longitude: userLocation.value.lng
    })
    
    if (res.success) {
      ElMessage.success(res.message)
      closeLocationDialog()
      loadData()
    } else {
      ElMessage.error(res.message || '位置签到失败')
    }
  } catch (e) {
    ElMessage.error(e.message || '签到失败')
  } finally {
    locationVerifying.value = false
  }
}

const route = useRoute()

// 根据URL参数自动打开签到
const handleUrlParams = async () => {
  const checkinId = route.query.id
  if (checkinId) {
    try {
      const res = await getCheckinDetail(checkinId)
      if (res.success && res.checkin) {
        const checkin = res.checkin
        // 检查签到是否还在进行中
        if (checkin.status === 'active' && new Date(checkin.end_time) > new Date()) {
          currentCheckin.value = checkin
          // 根据签到类型打开对应的签到对话框
          if (checkin.type === 'face') {
            showFaceDialog.value = true
            initFaceCamera()
          } else if (checkin.type === 'gesture') {
            showGestureDialog.value = true
            initGestureCamera()
          } else if (checkin.type === 'location') {
            showLocationDialog.value = true
            initLocationCheckin()
          } else if (checkin.type === 'qrcode') {
            showConfirmDialog.value = true
          }
        } else {
          ElMessage.warning('该签到已结束')
        }
      }
    } catch (e) {
      console.error('加载签到详情失败:', e)
    }
  }
}

onMounted(async () => {
  await loadData()
  // 处理URL参数中的签到ID
  await handleUrlParams()
  
  const refreshInterval = setInterval(loadData, 30000)
  onUnmounted(() => { 
    clearInterval(refreshInterval)
    stopScan()
    stopFaceCamera()
    stopGestureCamera()
    if (locationMapInstance) locationMapInstance.remove()
  })
})
</script>

<style scoped>
.student-checkin { display: flex; flex-direction: column; gap: 24px; }

/* 签到方式入口卡片 */
.checkin-methods { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.method-card {
  background: #fff; border: 1px solid #d0d7de; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; gap: 16px; cursor: pointer; transition: all 0.2s;
}
.method-card:hover { border-color: #2da44e; box-shadow: 0 4px 12px rgba(45, 164, 78, 0.15); }
.method-card.code-method { cursor: default; }
.method-card.code-method:hover { border-color: #d0d7de; box-shadow: none; }
.method-icon { font-size: 36px; }
.method-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.method-title { font-size: 16px; font-weight: 600; color: #1f2328; }
.method-desc { font-size: 13px; color: #656d76; }
.code-input-inline { display: flex; gap: 8px; margin-top: 8px; }
.code-input-inline .el-input { width: 120px; }

/* 签到卡片 */
.active-section h3, .history-section h3 { font-size: 16px; font-weight: 600; color: #1f2328; margin: 0 0 16px; }
.checkin-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.checkin-card { background: #dafbe1; border: 1px solid #2da44e; border-radius: 8px; padding: 16px; }
.checkin-card.done { background: #f6f8fa; border-color: #d0d7de; }
.card-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
.card-title { font-weight: 600; color: #1f2328; }
.card-type { padding: 2px 8px; background: #fff; border-radius: 4px; font-size: 12px; color: #656d76; }
.card-type.face { background: #ddf4ff; color: #0969da; }
.card-info { display: flex; gap: 24px; margin-bottom: 16px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; color: #656d76; }
.info-value { font-weight: 500; color: #1f2328; }
.countdown { color: #cf222e; }
.checked-tag { color: #1a7f37; font-weight: 500; }

.empty-active { text-align: center; padding: 60px 20px; background: #fff; border: 1px solid #d0d7de; border-radius: 8px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }

/* 历史记录 */
.history-card { background: #fff; border: 1px solid #d0d7de; border-radius: 8px; padding: 16px; }
.status-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.status-tag.checked { background: #dafbe1; color: #1a7f37; }
.status-tag.late { background: #fff8c5; color: #9a6700; }
.type-badge { padding: 2px 6px; border-radius: 4px; font-size: 11px; background: #f6f8fa; color: #656d76; }
.type-badge.face { background: #ddf4ff; color: #0969da; }
.type-badge.gesture { background: #fff8c5; color: #9a6700; }
.card-type.gesture { background: #fff8c5; color: #9a6700; }
.face-thumb { width: 40px; height: 40px; border-radius: 4px; cursor: pointer; }
.no-face { color: #aaa; }
.similarity { color: #2da44e; font-weight: 500; }

/* 扫码对话框 */
.scan-dialog { text-align: center; padding: 20px 0; }
.scan-start p { margin-bottom: 20px; color: #666; }
.scan-area { position: relative; }
.scan-area video { width: 100%; max-width: 300px; border-radius: 8px; }
.scan-tip { margin-top: 10px; color: #666; font-size: 14px; }

/* 人脸签到选择器 */
.face-picker { max-height: 400px; overflow-y: auto; }
.face-checkin-list { display: flex; flex-direction: column; gap: 12px; }
.face-checkin-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 8px; cursor: pointer;
}
.face-checkin-item:hover { border-color: #2da44e; background: #dafbe1; }
.face-checkin-item.disabled { opacity: 0.6; cursor: not-allowed; }
.face-checkin-item.disabled:hover { border-color: #d0d7de; background: #f6f8fa; }
.item-info { display: flex; flex-direction: column; gap: 4px; }
.item-title { font-weight: 600; color: #1f2328; }
.item-group { font-size: 13px; color: #656d76; }
.done-tag { color: #1a7f37; font-weight: 500; }
.time-tag { color: #cf222e; font-size: 13px; }

/* 确认对话框 */
.confirm-dialog { text-align: center; padding: 20px 0; }
.confirm-icon { font-size: 48px; margin-bottom: 16px; }
.confirm-title { font-size: 18px; font-weight: 600; color: #1f2328; }
.confirm-group { color: #666; }

/* 人脸签到 */
.face-checkin-section { display: flex; flex-direction: column; gap: 16px; }
.face-checkin-header { text-align: center; padding-bottom: 12px; border-bottom: 1px solid #eee; }
.checkin-title { display: block; font-size: 16px; font-weight: 600; color: #1f2328; }
.checkin-group { font-size: 13px; color: #656d76; }
.camera-box { position: relative; width: 100%; height: 280px; background: #000; border-radius: 8px; overflow: hidden; }
.camera-box video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
.camera-box .hidden { display: none; }
.face-guide { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; }
.guide-oval { width: 140px; height: 180px; border: 3px solid rgba(255,255,255,0.5); border-radius: 50%; transition: all 0.3s; }
.guide-oval.warning { border-color: #ef4444; animation: pulse 1s infinite; }
.guide-oval.progress { border-color: #f59e0b; box-shadow: 0 0 20px rgba(245,158,11,0.4); }
.guide-oval.success { border-color: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.4); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.loading-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.85); color: #fff; gap: 12px; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 检测步骤 */
.detect-steps { display: flex; align-items: flex-start; justify-content: center; gap: 6px; }
.step-item { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: #f3f4f6; border-radius: 8px; }
.step-item.active { background: #dbeafe; }
.step-item.done { background: #dcfce7; }
.step-icon { width: 26px; height: 26px; border-radius: 50%; background: #d1d5db; color: #6b7280; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0; }
.step-item.active .step-icon { background: #3b82f6; color: #fff; }
.step-item.done .step-icon { background: #22c55e; color: #fff; }
.step-info { display: flex; flex-direction: column; }
.step-title { font-size: 13px; font-weight: 500; color: #374151; }
.step-progress { font-size: 11px; color: #6b7280; }
.step-line { width: 20px; height: 2px; background: #d1d5db; margin-top: 18px; }
.step-line.done { background: #22c55e; }
.tip-box { text-align: center; padding: 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; font-size: 14px; color: #92400e; }
.tip-box.success { background: #dcfce7; border-color: #22c55e; color: #166534; }

/* 手势签到 */
.gesture-checkin-section { display: flex; flex-direction: column; gap: 16px; }
.gesture-requirement { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 16px; background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 12px; }
.gesture-label { font-size: 16px; color: #92400e; }
.gesture-number { font-size: 48px; font-weight: 700; color: #d97706; }
.gesture-icon { font-size: 48px; }
.gesture-camera { position: relative; }
.gesture-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; transform: scaleX(-1); }
.gesture-status { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); }
.detected-gesture { padding: 8px 20px; background: rgba(0,0,0,0.7); color: #fff; border-radius: 20px; font-size: 14px; font-weight: 500; transition: all 0.3s; }
.detected-gesture.detecting { background: rgba(234, 179, 8, 0.9); }
.detected-gesture.correct { background: rgba(34, 197, 94, 0.9); animation: pulse-green 1s infinite; }
.hold-hint { margin-left: 8px; font-size: 12px; opacity: 0.9; }
@keyframes pulse-green { 0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); } 50% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); } }
.gesture-steps { display: flex; align-items: center; justify-content: center; gap: 12px; }
.gesture-steps .step-item { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: #f3f4f6; border-radius: 8px; }
.gesture-steps .step-item.active { background: #dbeafe; }
.gesture-steps .step-item.done { background: #dcfce7; }
.gesture-steps .step-icon { width: 26px; height: 26px; border-radius: 50%; background: #d1d5db; color: #6b7280; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
.gesture-steps .step-item.active .step-icon { background: #3b82f6; color: #fff; }
.gesture-steps .step-item.done .step-icon { background: #22c55e; color: #fff; }
.gesture-steps .step-title { font-size: 14px; font-weight: 500; color: #374151; }
.gesture-steps .step-line { width: 30px; height: 2px; background: #d1d5db; }
.gesture-steps .step-line.done { background: #22c55e; }

/* 位置签到 */
.location-checkin-section { display: flex; flex-direction: column; gap: 16px; }
.location-target { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 12px; background: linear-gradient(135deg, #dbeafe, #bfdbfe); border-radius: 8px; }
.target-label { font-size: 14px; color: #1e40af; }
.target-range { font-size: 24px; font-weight: 700; color: #1d4ed8; }
.location-map-container { width: 100%; height: 250px; border-radius: 8px; overflow: hidden; border: 1px solid #d0d7de; background: #f6f8fa; }
.location-status { padding: 16px; background: #f6f8fa; border-radius: 8px; }
.status-loading { display: flex; align-items: center; justify-content: center; gap: 12px; color: #666; }
.status-info { display: flex; flex-direction: column; gap: 8px; }
.status-row { display: flex; justify-content: space-between; align-items: center; }
.status-label { color: #666; font-size: 14px; }
.status-value { font-weight: 600; color: #1f2328; font-family: monospace; }
.status-value.in-range { color: #22c55e; }
.status-value.low-accuracy { color: #f59e0b; }
.accuracy-tip { font-size: 12px; color: #f59e0b; font-weight: normal; }
.status-empty { text-align: center; }
.card-type.location { background: #dbeafe; color: #1d4ed8; }
.type-badge.location { background: #dbeafe; color: #1d4ed8; }

/* 移动端响应式 */
@media screen and (max-width: 768px) {
  .checkin-methods { grid-template-columns: 1fr; }
  .method-card { padding: 16px; }
  .method-icon { font-size: 28px; }
  .code-input-inline { flex-direction: column; }
  .code-input-inline .el-input { width: 100%; }
  .checkin-cards { grid-template-columns: 1fr; }
  .card-info { flex-direction: column; gap: 12px; }
  .history-card { padding: 12px; overflow-x: auto; }
  :deep(.el-table) { font-size: 13px; }
  .camera-box { height: 240px; }
  .guide-oval { width: 120px; height: 150px; }
  .detect-steps { flex-wrap: wrap; gap: 8px; }
  .step-item { padding: 8px 10px; }
  .step-line { display: none; }
}

@media screen and (max-width: 500px) {
  :deep(.scan-dialog-wrapper .el-dialog),
  :deep(.face-dialog-wrapper .el-dialog) { width: 95% !important; margin: 10px auto; }
}
</style>

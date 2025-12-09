R<template>
  <div class="login-page">
    <div class="login-box">
      <div class="login-header">
        <svg height="48" viewBox="0 0 24 24" width="48" fill="#1f2328">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <h1>登录到教育系统</h1>
      </div>
      
      <div class="login-tabs">
        <button :class="['tab-btn', { active: loginMode === 'password' }]" @click="switchMode('password')">密码登录</button>
        <button :class="['tab-btn', { active: loginMode === 'face' }]" @click="switchMode('face')">人脸登录</button>
      </div>
      
      <div class="login-card">
        <!-- 密码登录 -->
        <template v-if="loginMode === 'password'">
          <el-form :model="loginForm" :rules="rules" ref="loginFormRef">
            <el-form-item prop="email">
              <label class="form-label">邮箱地址</label>
              <el-input v-model="loginForm.email" placeholder="you@example.com" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <label class="form-label">密码</label>
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" size="large" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">登录</el-button>
          </el-form>
        </template>
        
        <!-- 人脸登录 -->
        <template v-else>
          <div class="face-section">
            <div class="camera-box">
              <video ref="videoRef" autoplay playsinline muted></video>
              <canvas ref="overlayRef" class="overlay-canvas"></canvas>
              <canvas ref="canvasRef" class="hidden"></canvas>
              
              <div class="face-guide" v-if="cameraReady && !modelLoading">
                <div class="guide-oval" :class="guideClass"></div>
              </div>
              
              <div class="loading-overlay" v-if="modelLoading || !cameraReady">
                <div class="spinner"></div>
                <p>{{ loadingText }}</p>
              </div>
              
              <div class="error-overlay" v-if="cameraError">
                <p>{{ cameraError }}</p>
                <el-button size="small" @click="initCamera">重试</el-button>
              </div>
              
              <!-- 实时数据 -->
              <div class="debug-panel" v-if="cameraReady && !modelLoading && showDebug">
                <div>EAR: {{ earDisplay }} (阈值: {{ thresholdDisplay }})</div>
                <div>YAW: {{ yawDisplay }}°</div>
                <div>检测: {{ faceDetected ? '✓' : '✗' }}</div>
              </div>
            </div>
            
            <!-- 检测步骤 -->
            <div class="detect-steps">
              <div class="step-item" :class="getStepClass(1)">
                <div class="step-icon">{{ step >= 1 ? '✓' : '1' }}</div>
                <div class="step-info">
                  <span class="step-title">眨眼</span>
                  <span class="step-progress" v-if="step === 0">{{ blinkCount }}/2</span>
                </div>
              </div>
              <div class="step-line" :class="{ done: step >= 1 }"></div>
              <div class="step-item" :class="getStepClass(2)">
                <div class="step-icon">{{ step >= 2 ? '✓' : '2' }}</div>
                <div class="step-info">
                  <span class="step-title">{{ turnDir === 'left' ? '左转' : '右转' }}</span>
                  <span class="step-progress" v-if="step === 1">{{ turnProgress }}%</span>
                </div>
              </div>
              <div class="step-line" :class="{ done: step >= 2 }"></div>
              <div class="step-item" :class="getStepClass(3)">
                <div class="step-icon">{{ step >= 3 ? '✓' : '3' }}</div>
                <div class="step-info">
                  <span class="step-title">验证</span>
                </div>
              </div>
            </div>
            
            <div class="tip-box" :class="{ success: step >= 3 }">{{ tipText }}</div>
            
            <el-button type="primary" size="large" :loading="verifying" :disabled="step < 3" @click="doFaceLogin" class="login-btn">
              {{ verifying ? '验证中...' : '确认登录' }}
            </el-button>
            <el-button size="large" @click="resetDetection" class="reset-btn">重新检测</el-button>
          </div>
        </template>
      </div>
      
      <div class="login-footer">
        <p>还没有账号？<router-link to="/register">创建账号</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { faceLoginWithLiveness } from '@/api/auth'
import { ElMessage } from 'element-plus'
import * as faceapi from 'face-api.js'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 密码登录
const loginFormRef = ref(null)
const loading = ref(false)
const loginMode = ref('password')
const loginForm = reactive({ email: '', password: '' })

const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const result = await userStore.loginAction(loginForm.email, loginForm.password)
      if (result.success) router.push(route.query.redirect || '/dashboard')
    } finally {
      loading.value = false
    }
  })
}

// 人脸登录
const videoRef = ref(null)
const canvasRef = ref(null)
const overlayRef = ref(null)
const cameraReady = ref(false)
const cameraError = ref('')
const modelLoading = ref(true)
const loadingText = ref('正在加载...')
const verifying = ref(false)
const showDebug = ref(false)

let mediaStream = null
let detectInterval = null
let modelsLoaded = false

// 检测状态
const step = ref(0)
const blinkCount = ref(0)
const turnDir = ref('left')
const turnProgress = ref(0)
const capturedImage = ref(null)
const faceDetected = ref(false)

// 实时数据
const earDisplay = ref('--')
const yawDisplay = ref('--')
const thresholdDisplay = ref('--')

// 眨眼检测变量 - 基于变化率检测
let earHistory = []  // EAR历史记录
let lastBlinkTime = 0  // 上次眨眼时间，防止重复计数
const BLINK_COOLDOWN = 400  // 眨眼冷却时间(ms)

// 转头检测 - 需要转头超过20度
const YAW_THRESHOLD = 20

// 68点人脸关键点中的眼睛索引
const LEFT_EYE = [36, 37, 38, 39, 40, 41]
const RIGHT_EYE = [42, 43, 44, 45, 46, 47]

const tipText = computed(() => {
  if (modelLoading.value) return '正在加载人脸检测模型...'
  if (!cameraReady.value) return '请允许使用摄像头'
  if (!faceDetected.value) return '⚠️ 请将脸部对准摄像头'
  if (step.value === 0) return '👁️ 请眨眼2次'
  if (step.value === 1) return turnDir.value === 'left' ? '👈 请向左转头' : '👉 请向右转头'
  if (step.value === 2) return '📸 请正对摄像头，正在拍照...'
  return '✅ 活体检测通过'
})

const guideClass = computed(() => {
  if (!faceDetected.value) return 'warning'
  if (step.value >= 3) return 'success'
  if (step.value > 0) return 'progress'
  return ''
})

const getStepClass = (s) => {
  if (step.value >= s) return 'done'
  if (step.value === s - 1) return 'active'
  return ''
}

const switchMode = (mode) => {
  loginMode.value = mode
  if (mode === 'face') initCamera()
  else stopAll()
}

const initCamera = async () => {
  cameraError.value = ''
  modelLoading.value = true
  loadingText.value = '正在启动摄像头...'
  resetDetection()
  
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' }
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      await new Promise(r => { videoRef.value.onloadedmetadata = r })
      cameraReady.value = true
    }
    
    if (!modelsLoaded) {
      loadingText.value = '正在加载人脸检测模型...'
      await loadModels()
      modelsLoaded = true
    }
    
    modelLoading.value = false
    startDetection()
    
  } catch (err) {
    modelLoading.value = false
    console.error('初始化失败:', err)
    if (err.name === 'NotAllowedError') {
      cameraError.value = '请允许摄像头权限'
    } else if (err.message && err.message.includes('模型')) {
      cameraError.value = err.message
    } else {
      cameraError.value = '初始化失败: ' + (err.message || err.name)
    }
  }
}

const loadModels = async () => {
  try {
    // 优先从本地加载，失败则从CDN加载
    const LOCAL_URL = '/models'
    const CDN_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model'
    
    console.log('开始加载模型...')
    
    try {
      loadingText.value = '加载人脸检测模型(本地)...'
      await faceapi.nets.tinyFaceDetector.loadFromUri(LOCAL_URL)
      console.log('tinyFaceDetector 从本地加载完成')
    } catch (e) {
      console.log('本地加载失败，尝试CDN...', e)
      loadingText.value = '加载人脸检测模型(CDN)...'
      await faceapi.nets.tinyFaceDetector.loadFromUri(CDN_URL)
      console.log('tinyFaceDetector 从CDN加载完成')
    }
    
    try {
      loadingText.value = '加载关键点模型(本地)...'
      await faceapi.nets.faceLandmark68Net.loadFromUri(LOCAL_URL)
      console.log('faceLandmark68Net 从本地加载完成')
    } catch (e) {
      console.log('本地加载失败，尝试CDN...', e)
      loadingText.value = '加载关键点模型(CDN)...'
      await faceapi.nets.faceLandmark68Net.loadFromUri(CDN_URL)
      console.log('faceLandmark68Net 从CDN加载完成')
    }
    
    console.log('所有模型加载完成')
  } catch (err) {
    console.error('模型加载失败:', err)
    throw new Error('模型加载失败: ' + err.message)
  }
}

const stopAll = () => {
  if (detectInterval) {
    clearInterval(detectInterval)
    detectInterval = null
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop())
    mediaStream = null
  }
  cameraReady.value = false
}

const startDetection = () => {
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 })
  
  detectInterval = setInterval(async () => {
    if (!videoRef.value || !cameraReady.value || step.value >= 3) return
    
    try {
      const detection = await faceapi.detectSingleFace(videoRef.value, options).withFaceLandmarks()
      
      if (detection) {
        faceDetected.value = true
        const landmarks = detection.landmarks
        const positions = landmarks.positions
        
        // 计算EAR
        const ear = calculateEAR(positions)
        earDisplay.value = ear.toFixed(3)
        
        // 计算头部偏转
        const yaw = calculateYaw(positions)
        yawDisplay.value = yaw.toFixed(1)
        
        // 眨眼检测
        if (step.value === 0) {
          detectBlink(ear)
        }
        
        // 转头检测
        if (step.value === 1) {
          detectTurn(yaw)
        }
        
        // 拍照
        if (step.value === 2) {
          if (Math.abs(yaw) < 8) {
            capturePhoto()
            step.value = 3
          }
        }
        

      } else {
        faceDetected.value = false
        earDisplay.value = '--'
        yawDisplay.value = '--'
      }
    } catch (e) {
      console.error('检测错误:', e)
    }
  }, 100)  // 10fps
}

const calculateEAR = (positions) => {
  const euclidean = (p1, p2) => Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
  
  // 左眼 EAR
  const leftV1 = euclidean(positions[37], positions[41])
  const leftV2 = euclidean(positions[38], positions[40])
  const leftH = euclidean(positions[36], positions[39])
  const leftEAR = (leftV1 + leftV2) / (2 * leftH)
  
  // 右眼 EAR
  const rightV1 = euclidean(positions[43], positions[47])
  const rightV2 = euclidean(positions[44], positions[46])
  const rightH = euclidean(positions[42], positions[45])
  const rightEAR = (rightV1 + rightV2) / (2 * rightH)
  
  return (leftEAR + rightEAR) / 2
}

const calculateYaw = (positions) => {
  // 使用鼻尖(30)和脸部轮廓点计算
  const nose = positions[30]
  const leftJaw = positions[0]
  const rightJaw = positions[16]
  
  const faceWidth = rightJaw.x - leftJaw.x
  const faceCenter = (leftJaw.x + rightJaw.x) / 2
  const noseOffset = nose.x - faceCenter
  
  // 转换为角度
  const ratio = (noseOffset / (faceWidth / 2)) * 2
  return Math.asin(Math.max(-1, Math.min(1, ratio))) * (180 / Math.PI)
}

const detectBlink = (ear) => {
  const now = Date.now()
  
  // 保存最近15帧的EAR值
  earHistory.push({ ear, time: now })
  if (earHistory.length > 15) earHistory.shift()
  
  // 至少需要10帧数据建立基准
  if (earHistory.length < 10) {
    thresholdDisplay.value = '采集中...'
    return
  }
  
  // 计算稳定状态的平均EAR（排除最近3帧）
  const stableEars = earHistory.slice(0, -3).map(h => h.ear)
  const avgEAR = stableEars.reduce((a, b) => a + b) / stableEars.length
  
  // 当前EAR（最近2帧的最小值）
  const currentEAR = Math.min(...earHistory.slice(-2).map(h => h.ear))
  
  // 计算下降百分比
  const dropPercent = ((avgEAR - currentEAR) / avgEAR) * 100
  
  thresholdDisplay.value = `降${dropPercent.toFixed(1)}%`
  
  // 眨眼需要EAR下降超过12%（更严格），且冷却时间已过
  if (dropPercent > 6.5 && (now - lastBlinkTime) > BLINK_COOLDOWN) {
    // 检查是否正在恢复（眼睛正在睁开）
    const lastThree = earHistory.slice(-3)
    const isRecovering = lastThree[2].ear > lastThree[1].ear && lastThree[1].ear > lastThree[0].ear * 0.95
    
    if (isRecovering) {
      lastBlinkTime = now
      blinkCount.value++
      console.log('检测到眨眼:', blinkCount.value, '下降:', dropPercent.toFixed(1) + '%')
      
      if (blinkCount.value >= 2) {
        step.value = 1
        turnDir.value = Math.random() > 0.5 ? 'left' : 'right'
      }
    }
  }
}

const detectTurn = (yaw) => {
  const progress = Math.min(100, Math.abs(yaw) / YAW_THRESHOLD * 100)
  turnProgress.value = Math.round(progress)
  
  if (turnDir.value === 'left' && yaw < -YAW_THRESHOLD) {
    step.value = 2
  } else if (turnDir.value === 'right' && yaw > YAW_THRESHOLD) {
    step.value = 2
  }
}

const capturePhoto = () => {
  if (!videoRef.value || !canvasRef.value) return
  const canvas = canvasRef.value
  const video = videoRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  capturedImage.value = canvas.toDataURL('image/jpeg', 0.9)
  console.log('拍照完成')
}

const resetDetection = () => {
  step.value = 0
  blinkCount.value = 0
  turnDir.value = Math.random() > 0.5 ? 'left' : 'right'
  turnProgress.value = 0
  capturedImage.value = null
  faceDetected.value = false
  earHistory = []
  lastBlinkTime = 0
}

const doFaceLogin = async () => {
  if (!capturedImage.value) {
    ElMessage.warning('请完成活体检测')
    return
  }
  
  verifying.value = true
  try {
    const res = await faceLoginWithLiveness(capturedImage.value, {
      blink_detected: true,
      head_turn_detected: true
    })
    
    if (res.success) {
      localStorage.setItem('token', res.token)
      userStore.token = res.token
      userStore.userInfo = res.userInfo
      ElMessage.success(`登录成功，相似度: ${res.similarity}%`)
      stopAll()
      router.push(route.query.redirect || '/dashboard')
    } else {
      ElMessage.error(res.message || '人脸验证失败')
      resetDetection()
    }
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
    resetDetection()
  } finally {
    verifying.value = false
  }
}

watch(loginMode, m => m === 'face' ? initCamera() : stopAll())
onUnmounted(() => stopAll())
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f6f8fa; padding: 40px 20px; }
.login-box { width: 100%; max-width: 420px; }
.login-header { text-align: center; margin-bottom: 24px; }
.login-header svg { margin-bottom: 16px; }
.login-header h1 { font-size: 24px; font-weight: 300; color: #1f2328; margin: 0; }

.login-tabs { display: flex; background: #fff; border: 1px solid #d0d7de; border-bottom: none; border-radius: 6px 6px 0 0; }
.tab-btn { flex: 1; padding: 12px; border: none; background: #f6f8fa; color: #656d76; font-size: 14px; cursor: pointer; }
.tab-btn:first-child { border-right: 1px solid #d0d7de; }
.tab-btn.active { background: #fff; color: #1f2328; }

.login-card { background: #fff; border: 1px solid #d0d7de; border-radius: 0 0 6px 6px; padding: 20px; }
.form-label { display: block; font-size: 14px; font-weight: 600; color: #1f2328; margin-bottom: 8px; }
:deep(.el-form-item) { margin-bottom: 16px; }
:deep(.el-input__wrapper) { background: #f6f8fa; }

.login-btn { width: 100%; background: #2da44e; border-color: #2da44e; margin-top: 12px; }
.login-btn:hover { background: #2c974b; }
.login-btn:disabled { background: #94d3a2; border-color: #94d3a2; }
.reset-btn { width: 100%; margin-top: 8px; }

.login-footer { margin-top: 16px; padding: 16px; background: #fff; border: 1px solid #d0d7de; border-radius: 6px; text-align: center; }
.login-footer a { color: #0969da; }

/* 人脸登录 */
.face-section { display: flex; flex-direction: column; gap: 16px; }
.camera-box { position: relative; width: 100%; height: 300px; background: #000; border-radius: 8px; overflow: hidden; }
.camera-box video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
.camera-box .hidden { display: none; }
.overlay-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform: scaleX(-1); pointer-events: none; }

.face-guide { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; }
.guide-oval { width: 160px; height: 200px; border: 3px solid rgba(255,255,255,0.5); border-radius: 50%; transition: all 0.3s; }
.guide-oval.warning { border-color: #ef4444; animation: pulse 1s infinite; }
.guide-oval.progress { border-color: #f59e0b; box-shadow: 0 0 20px rgba(245,158,11,0.4); }
.guide-oval.success { border-color: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.4); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

.loading-overlay, .error-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.85); color: #fff; gap: 12px; }
.spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.debug-panel { position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); color: #0f0; padding: 6px 10px; border-radius: 4px; font-size: 11px; font-family: monospace; line-height: 1.5; }

/* 步骤 */
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
</style>

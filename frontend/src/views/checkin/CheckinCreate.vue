<template>
  <Layout pageTitle="发布签到">
    <div class="checkin-create">
      <div class="create-card">
        <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
          <el-form-item label="选择群组" prop="groupId">
            <el-select v-model="form.groupId" placeholder="请选择群组" style="width: 100%">
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="签到标题" prop="title">
            <el-input v-model="form.title" placeholder="如：第3周课堂签到" />
          </el-form-item>

          <el-form-item label="签到方式" prop="type">
            <div class="type-options">
              <div 
                v-for="t in checkinTypes" 
                :key="t.value"
                :class="['type-option', { active: form.type === t.value }]"
                @click="form.type = t.value"
              >
                <span class="type-icon">{{ t.icon }}</span>
                <span class="type-name">{{ t.label }}</span>
                <span class="type-desc">{{ t.desc }}</span>
              </div>
            </div>
          </el-form-item>

          <!-- 手势签到数字选择 -->
          <el-form-item v-if="form.type === 'gesture'" label="指定手势数字" prop="gestureNumber">
            <div class="gesture-options">
              <div 
                v-for="n in 5" 
                :key="n"
                :class="['gesture-option', { active: form.gestureNumber === n }]"
                @click="form.gestureNumber = n"
              >
                <span class="gesture-icon">{{ ['✊','☝️','✌️','🤟','🖐️'][n-1] }}</span>
                <span class="gesture-num">{{ n }}</span>
              </div>
            </div>
          </el-form-item>

          <!-- 位置签到设置 -->
          <el-form-item v-if="form.type === 'location'" label="签到位置" required>
            <div class="location-picker">
              <div class="location-info" v-if="form.locationLat && form.locationLng">
                <div class="location-coords">
                  <span>📍 {{ form.locationAddress || '已选择位置' }}</span>
                  <span class="coords-text">{{ form.locationLat.toFixed(6) }}, {{ form.locationLng.toFixed(6) }}</span>
                </div>
                <el-button size="small" @click="getCurrentLocation" :loading="gettingLocation">重新定位</el-button>
              </div>
              <div class="location-empty" v-else>
                <el-button type="primary" @click="getCurrentLocation" :loading="gettingLocation">
                  {{ gettingLocation ? '定位中...' : '📍 获取当前位置' }}
                </el-button>
              </div>
              <div class="map-container" ref="mapContainer" v-show="form.locationLat"></div>
              <div class="location-range">
                <span>签到范围：</span>
                <el-slider v-model="form.locationRange" :min="20" :max="200" :step="10" :format-tooltip="v => v + '米'" />
                <span class="range-value">{{ form.locationRange }}米</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="签到时长（分钟）" prop="duration">
            <el-input-number v-model="form.duration" :min="1" :max="120" />
          </el-form-item>

          <el-form-item label="签到说明">
            <el-input v-model="form.description" type="textarea" :rows="2" placeholder="选填" />
          </el-form-item>

          <div class="form-actions">
            <el-button @click="$router.back()">取消</el-button>
            <el-button type="primary" @click="submitCheckin" :loading="submitting">发布签到</el-button>
          </div>
        </el-form>
      </div>

      <!-- 签到发布成功弹窗 -->
      <el-dialog v-model="showQrcodeDialog" title="签到已发布" width="450px" :close-on-click-modal="false">
        <div class="qrcode-dialog">
          <div class="qrcode-box">
            <canvas ref="qrcodeCanvas"></canvas>
          </div>
          <div class="checkin-code">签到码：{{ createdCheckin?.checkin_code }}</div>
          <div class="checkin-info">
            <p>{{ createdCheckin?.title }}</p>
            <p class="countdown">剩余时间：{{ remainingTime }}</p>
          </div>
        </div>
        <template #footer>
          <el-button @click="viewRecords">查看签到情况</el-button>
          <el-button type="primary" @click="closeAndBack">完成</el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { getMyGroups } from '@/api/groupChat'
import { createCheckin, getCheckinQrcode } from '@/api/checkin'
import QRCode from 'qrcode'

const router = useRouter()
const formRef = ref(null)
const qrcodeCanvas = ref(null)

const groups = ref([])
const submitting = ref(false)
const showQrcodeDialog = ref(false)
const createdCheckin = ref(null)
const remainingTime = ref('')
let countdownTimer = null

const checkinTypes = [
  { value: 'qrcode', label: '扫码签到', icon: '📱', desc: '扫描二维码签到' },
  { value: 'face', label: '人脸签到', icon: '👤', desc: '人脸识别验证签到' },
  { value: 'gesture', label: '手势签到', icon: '✋', desc: '手势识别验证签到' },
  { value: 'location', label: '位置签到', icon: '📍', desc: '定位验证签到' },
  { value: 'photo', label: '智能点到', icon: '📸', desc: '上传合照自动识别' }
]

const form = reactive({
  groupId: '',
  title: '',
  type: 'qrcode',
  duration: 5,
  description: '',
  gestureNumber: 1,  // 手势签到的数字
  locationLat: null,  // 位置签到的纬度
  locationLng: null,  // 位置签到的经度
  locationAddress: '',  // 位置地址
  locationRange: 50  // 签到范围（米）
})

const mapContainer = ref(null)
const gettingLocation = ref(false)
let mapInstance = null
let markerInstance = null
let circleInstance = null

const rules = {
  groupId: [{ required: true, message: '请选择群组', trigger: 'change' }],
  title: [{ required: true, message: '请输入签到标题', trigger: 'blur' }],
  duration: [{ required: true, message: '请设置签到时长', trigger: 'change' }]
}

const loadGroups = async () => {
  try {
    const res = await getMyGroups()
    if (res.success) {
      groups.value = res.groups.filter(g => g.my_role === 'owner' || g.my_role === 'admin')
    }
  } catch (e) {
    console.error(e)
  }
}

const submitCheckin = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  submitting.value = true
  try {
    // 位置签到验证
    if (form.type === 'location' && (!form.locationLat || !form.locationLng)) {
      ElMessage.warning('请先获取签到位置')
      submitting.value = false
      return
    }
    
    const res = await createCheckin({
      group_id: form.groupId,
      title: form.title,
      type: form.type,
      duration: form.duration,
      description: form.description,
      gesture_number: form.type === 'gesture' ? form.gestureNumber : null,
      location_lat: form.type === 'location' ? form.locationLat : null,
      location_lng: form.type === 'location' ? form.locationLng : null,
      location_range: form.type === 'location' ? form.locationRange : null
    })
    
    if (res.success) {
      ElMessage.success('签到发布成功')
      createdCheckin.value = {
        id: res.checkin_id,
        checkin_code: res.checkin_code,
        title: form.title,
        end_time: res.end_time,
        type: form.type,
        gesture_number: form.gestureNumber
      }
      
      // 人脸签到、手势签到、位置签到、智能点到不显示二维码，直接跳转
      if (form.type === 'face' || form.type === 'gesture' || form.type === 'location' || form.type === 'photo') {
        router.push(`/checkin/records/${res.checkin_id}`)
      } else {
        // 显示二维码
        showQrcodeDialog.value = true
        setTimeout(() => generateQrcode(res.checkin_id), 100)
        startCountdown(res.end_time)
      }
    } else {
      ElMessage.error(res.message || '发布失败')
    }
  } catch (e) {
    ElMessage.error('发布失败')
  } finally {
    submitting.value = false
  }
}

const generateQrcode = async (checkinId) => {
  try {
    const res = await getCheckinQrcode(checkinId)
    if (res.success && qrcodeCanvas.value) {
      await QRCode.toCanvas(qrcodeCanvas.value, res.qr_data, {
        width: 200,
        margin: 2,
        color: { dark: '#000000', light: '#ffffff' }
      })
    }
  } catch (e) {
    console.error('生成二维码失败:', e)
  }
}

const startCountdown = (endTime) => {
  const updateCountdown = () => {
    const end = new Date(endTime).getTime()
    const now = Date.now()
    const diff = end - now
    
    if (diff <= 0) {
      remainingTime.value = '已结束'
      clearInterval(countdownTimer)
      return
    }
    
    const minutes = Math.floor(diff / 60000)
    const seconds = Math.floor((diff % 60000) / 1000)
    remainingTime.value = `${minutes}分${seconds}秒`
  }
  
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
}

const viewRecords = () => {
  if (createdCheckin.value) {
    router.push(`/checkin/records/${createdCheckin.value.id}`)
  }
}

const closeAndBack = () => {
  showQrcodeDialog.value = false
  router.push('/checkin/manage')
}

// 获取当前位置
const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    ElMessage.error('您的浏览器不支持定位功能')
    return
  }
  
  gettingLocation.value = true
  
  const onSuccess = async (position) => {
    const accuracy = position.coords.accuracy
    form.locationLat = position.coords.latitude
    form.locationLng = position.coords.longitude
    form.locationAccuracy = accuracy
    form.locationAddress = `精度约${Math.round(accuracy)}米`
    gettingLocation.value = false
    
    // 根据精度给出提示
    if (accuracy > 1000) {
      ElMessage.warning(`定位精度较差（${Math.round(accuracy)}米），建议使用手机发布位置签到`)
    } else if (accuracy > 100) {
      ElMessage.info(`定位成功，精度约${Math.round(accuracy)}米`)
    } else {
      ElMessage.success(`定位成功，精度约${Math.round(accuracy)}米`)
    }
    
    // 初始化地图
    setTimeout(() => initMap(), 100)
  }
  
  const onError = (error) => {
    console.log('高精度定位失败，尝试低精度定位...', error)
    // 高精度失败，尝试低精度定位
    navigator.geolocation.getCurrentPosition(
      onSuccess,
      (err) => {
        gettingLocation.value = false
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

// 初始化地图（使用 Leaflet + OpenStreetMap，免费无需 key）
const initMap = async () => {
  if (!mapContainer.value || !form.locationLat) return
  
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
  
  // 销毁旧地图
  if (mapInstance) {
    mapInstance.remove()
  }
  
  // 创建地图
  mapInstance = L.map(mapContainer.value).setView([form.locationLat, form.locationLng], 17)
  
  // 添加地图图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(mapInstance)
  
  // 添加标记
  markerInstance = L.marker([form.locationLat, form.locationLng]).addTo(mapInstance)
  markerInstance.bindPopup('签到位置').openPopup()
  
  // 添加范围圆
  circleInstance = L.circle([form.locationLat, form.locationLng], {
    color: '#07c160',
    fillColor: '#07c160',
    fillOpacity: 0.2,
    radius: form.locationRange
  }).addTo(mapInstance)
}

// 监听范围变化更新圆
import { watch } from 'vue'
watch(() => form.locationRange, (newRange) => {
  if (circleInstance) {
    circleInstance.setRadius(newRange)
  }
})

onMounted(() => {
  loadGroups()
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
  if (mapInstance) mapInstance.remove()
})
</script>

<style scoped>
.checkin-create {
  max-width: 700px;
}

.create-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 24px;
}

.type-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 768px) {
  .type-options {
    grid-template-columns: repeat(2, 1fr);
  }
}

.type-option {
  padding: 16px;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.type-option:hover {
  border-color: #07c160;
}

.type-option.active {
  border-color: #07c160;
  background: #e8f8ef;
}

.type-icon {
  display: block;
  font-size: 32px;
  margin-bottom: 8px;
}

.type-name {
  display: block;
  font-weight: 600;
  color: #1f2328;
  margin-bottom: 4px;
}

.type-desc {
  display: block;
  font-size: 12px;
  color: #656d76;
}

.gesture-options {
  display: flex;
  gap: 12px;
}

.gesture-option {
  width: 60px;
  height: 70px;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.gesture-option:hover {
  border-color: #07c160;
}

.gesture-option.active {
  border-color: #07c160;
  background: #e8f8ef;
}

.gesture-icon {
  font-size: 28px;
}

.gesture-num {
  font-size: 16px;
  font-weight: 600;
  color: #1f2328;
}

/* 位置选择器 */
.location-picker {
  width: 100%;
}

.location-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
  margin-bottom: 12px;
}

.location-coords {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.coords-text {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.location-empty {
  text-align: center;
  padding: 24px;
  background: #f6f8fa;
  border: 2px dashed #d0d7de;
  border-radius: 8px;
  margin-bottom: 12px;
}

.map-container {
  width: 100%;
  height: 250px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  border: 1px solid #d0d7de;
}

.location-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.location-range .el-slider {
  flex: 1;
}

.range-value {
  min-width: 50px;
  text-align: right;
  font-weight: 600;
  color: #07c160;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.qrcode-dialog {
  text-align: center;
  padding: 20px 0;
}

.qrcode-box {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.qrcode-box canvas {
  border: 4px solid #07c160;
  border-radius: 8px;
}

.checkin-code {
  font-size: 24px;
  font-weight: bold;
  color: #07c160;
  margin-bottom: 15px;
  letter-spacing: 4px;
}

.checkin-info p {
  margin: 8px 0;
  color: #666;
}

.checkin-info .countdown {
  font-size: 18px;
  color: #cf222e;
  font-weight: 500;
}

:deep(.el-form-item__label) {
  font-weight: 600;
}
</style>

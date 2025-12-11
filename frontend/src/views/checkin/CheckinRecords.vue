<template>
  <Layout pageTitle="签到详情">
    <div class="checkin-records">
      <!-- 签到信息 -->
      <div class="info-card">
        <div class="info-header">
          <h2>{{ checkin?.title }}</h2>
          <span :class="['status-badge', checkin?.status]">
            {{ checkin?.status === 'active' ? '进行中' : '已结束' }}
          </span>
        </div>
        <div class="info-row">
          <span>群组：{{ checkin?.group_name }}</span>
          <span>类型：{{ getTypeName(checkin?.type) }}</span>
          <span>创建时间：{{ formatTime(checkin?.created_at) }}</span>
        </div>
        <div class="info-actions" v-if="checkin?.status === 'active'">
          <el-button v-if="checkin?.type !== 'photo'" @click="showQrcode">显示二维码</el-button>
          <el-button v-if="checkin?.type === 'photo'" type="primary" @click="showPhotoUpload = true">
            📸 上传班级合照
          </el-button>
          <el-button type="danger" @click="endCheckinNow">结束签到</el-button>
        </div>
      </div>

      <!-- 智能点到上传区域 -->
      <div v-if="checkin?.type === 'photo' && checkin?.status === 'active'" class="photo-upload-card">
        <h3>📸 智能点到</h3>
        <p class="upload-tip">上传班级合照，系统将自动识别照片中的学生并完成签到</p>
        <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
          <input type="file" ref="fileInput" accept="image/*" @change="handleFileSelect" style="display:none" />
          <div v-if="!uploadingPhoto" class="upload-placeholder">
            <span class="upload-icon">📷</span>
            <span>点击或拖拽上传班级合照</span>
            <span class="upload-hint">支持 JPG、PNG 格式</span>
          </div>
          <div v-else class="upload-loading">
            <div class="spinner"></div>
            <span>正在识别人脸，请稍候...</span>
          </div>
        </div>
        <div v-if="photoResult" class="photo-result" :class="{ success: photoResult.success }">
          <p>{{ photoResult.message }}</p>
          <div v-if="photoResult.matched_users?.length" class="matched-list">
            <span v-for="u in photoResult.matched_users" :key="u.user_id" class="matched-tag">
              {{ u.real_name }} ({{ u.similarity }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- 统计 -->
      <div class="stats-row">
        <div class="stat-item checked">
          <span class="stat-num">{{ records.checked_count }}</span>
          <span class="stat-label">已签到</span>
        </div>
        <div class="stat-item unchecked">
          <span class="stat-num">{{ records.unchecked_count }}</span>
          <span class="stat-label">未签到</span>
        </div>
        <div class="stat-item total">
          <span class="stat-num">{{ records.total }}</span>
          <span class="stat-label">总人数</span>
        </div>
      </div>

      <!-- 签到列表 -->
      <div class="records-section">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="已签到" name="checked">
            <div class="member-list">
              <div v-for="m in records.checked" :key="m.user_id" class="member-item">
                <el-avatar :src="getAvatarUrl(m.photo_url)" :size="40">{{ m.real_name?.[0] }}</el-avatar>
                <div class="member-info">
                  <span class="member-name">{{ m.real_name }}</span>
                  <span class="member-time">{{ formatTime(m.checkin_time) }}</span>
                </div>
                <!-- 人脸签到截图 -->
                <div class="face-capture" v-if="m.face_image_url">
                  <el-image 
                    :src="getAvatarUrl(m.face_image_url)" 
                    :preview-src-list="[getAvatarUrl(m.face_image_url)]"
                    fit="cover"
                    class="face-thumb"
                  />
                  <span class="face-similarity">{{ m.face_similarity }}%</span>
                </div>
                <span :class="['member-status', m.status]">
                  {{ m.status === 'late' ? '迟到' : '正常' }}
                </span>
              </div>
              <el-empty v-if="records.checked?.length === 0" description="暂无签到记录" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="未签到" name="unchecked">
            <div class="member-list">
              <div v-for="m in records.unchecked" :key="m.user_id" class="member-item">
                <el-avatar :src="getAvatarUrl(m.photo_url)" :size="40">{{ m.real_name?.[0] }}</el-avatar>
                <div class="member-info">
                  <span class="member-name">{{ m.real_name }}</span>
                </div>
                <span class="member-status absent">未签到</span>
              </div>
              <el-empty v-if="records.unchecked?.length === 0" description="全部已签到" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 二维码弹窗 -->
      <el-dialog v-model="showQrcodeDialog" title="签到二维码" width="400px">
        <div class="qrcode-dialog">
          <canvas ref="qrcodeCanvas"></canvas>
          <div class="checkin-code">签到码：{{ qrcodeData?.checkin_code }}</div>
        </div>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Layout from '@/components/Layout.vue'
import { getCheckinDetail, getCheckinRecords, getCheckinQrcode, endCheckin, smartCheckin } from '@/api/checkin'
import QRCode from 'qrcode'
import config from '@/config'

const route = useRoute()
const router = useRouter()
const checkinId = route.params.id

const checkin = ref(null)
const records = ref({ checked: [], unchecked: [], checked_count: 0, unchecked_count: 0, total: 0 })
const activeTab = ref('checked')
const showQrcodeDialog = ref(false)
const qrcodeData = ref(null)
const qrcodeCanvas = ref(null)

const API_BASE = config.staticUrl

const getTypeName = (type) => {
  const types = { normal: '普通', qrcode: '扫码', face: '人脸', gesture: '手势', location: '位置', photo: '智能点到' }
  return types[type] || type
}

// 智能点到相关
const fileInput = ref(null)
const uploadingPhoto = ref(false)
const photoResult = ref(null)
const showPhotoUpload = ref(false)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (file) processPhoto(file)
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('image/')) processPhoto(file)
}

const processPhoto = async (file) => {
  uploadingPhoto.value = true
  photoResult.value = null
  
  try {
    // 转换为 base64
    const base64 = await new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.readAsDataURL(file)
    })
    
    const res = await smartCheckin({
      checkin_id: checkinId,
      class_photo: base64
    })
    
    photoResult.value = res
    if (res.success) {
      ElMessage.success(res.message)
      loadData()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    photoResult.value = { success: false, message: e.message || '识别失败' }
    ElMessage.error('识别失败')
  } finally {
    uploadingPhoto.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const getAvatarUrl = (url) => {
  if (!url) return ''
  return url.startsWith('http') ? url : `${API_BASE}${url}`
}

const loadData = async () => {
  try {
    const [detailRes, recordsRes] = await Promise.all([
      getCheckinDetail(checkinId),
      getCheckinRecords(checkinId)
    ])
    if (detailRes.success) checkin.value = detailRes.checkin
    if (recordsRes.success) records.value = recordsRes
  } catch (e) {
    console.error(e)
  }
}

const showQrcode = async () => {
  try {
    const res = await getCheckinQrcode(checkinId)
    if (res.success) {
      qrcodeData.value = res
      showQrcodeDialog.value = true
      setTimeout(async () => {
        if (qrcodeCanvas.value) {
          await QRCode.toCanvas(qrcodeCanvas.value, res.qr_data, { width: 200, margin: 2 })
        }
      }, 100)
    }
  } catch (e) {
    ElMessage.error('获取二维码失败')
  }
}

const endCheckinNow = async () => {
  try {
    await ElMessageBox.confirm('确定结束签到？', '提示')
    const res = await endCheckin(checkinId)
    if (res.success) {
      ElMessage.success('签到已结束')
      loadData()
    }
  } catch (e) {}
}

onMounted(() => {
  loadData()
  // 定时刷新
  const interval = setInterval(loadData, 10000)
  return () => clearInterval(interval)
})
</script>

<style scoped>
.checkin-records {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
}

.info-card {
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 20px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-header h2 {
  margin: 0;
  font-size: 20px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}

.status-badge.active {
  background: #dafbe1;
  color: #1a7f37;
}

.status-badge.ended {
  background: #f6f8fa;
  color: #656d76;
}

.info-row {
  display: flex;
  gap: 24px;
  color: #656d76;
  font-size: 14px;
  margin-bottom: 16px;
}

.info-actions {
  display: flex;
  gap: 12px;
}

.stats-row {
  display: flex;
  gap: 16px;
}

.stat-item {
  flex: 1;
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 32px;
  font-weight: 600;
}

.stat-label {
  color: #656d76;
  font-size: 14px;
}

.stat-item.checked .stat-num { color: #1a7f37; }
.stat-item.unchecked .stat-num { color: #cf222e; }

.records-section {
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 20px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.member-name {
  font-weight: 500;
}

.member-time {
  font-size: 12px;
  color: #656d76;
}

.member-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.member-status.checked { background: #dafbe1; color: #1a7f37; }
.member-status.late { background: #fff8c5; color: #9a6700; }
.member-status.absent { background: #ffebe9; color: #cf222e; }

/* 人脸签到截图 */
.face-capture {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 12px;
}

.face-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid #d0d7de;
}

.face-similarity {
  font-size: 13px;
  font-weight: 600;
  color: #2da44e;
}

.qrcode-dialog {
  text-align: center;
  padding: 20px 0;
}

.checkin-code {
  margin-top: 16px;
  font-size: 20px;
  font-weight: bold;
  color: #07c160;
  letter-spacing: 3px;
}

/* 智能点到 */
.photo-upload-card {
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 20px;
}

.photo-upload-card h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.upload-tip {
  color: #656d76;
  font-size: 14px;
  margin-bottom: 16px;
}

.upload-area {
  border: 2px dashed #d0d7de;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #07c160;
  background: #f0fdf4;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #656d76;
}

.upload-icon {
  font-size: 48px;
}

.upload-hint {
  font-size: 12px;
  color: #8b949e;
}

.upload-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #07c160;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e5e5;
  border-top-color: #07c160;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.photo-result {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #ffebe9;
  color: #cf222e;
}

.photo-result.success {
  background: #dafbe1;
  color: #1a7f37;
}

.matched-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.matched-tag {
  padding: 4px 10px;
  background: rgba(255,255,255,0.5);
  border-radius: 4px;
  font-size: 13px;
}
</style>

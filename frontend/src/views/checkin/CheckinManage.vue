<template>
  <Layout pageTitle="签到管理">
    <div class="checkin-manage">
      <!-- 顶部操作栏 -->
      <div class="page-header">
        <div class="header-left">
          <el-radio-group v-model="statusFilter" size="default">
            <el-radio-button label="all">全部 ({{ checkinList.length }})</el-radio-button>
            <el-radio-button label="active">进行中 ({{ activeCount }})</el-radio-button>
            <el-radio-button label="ended">已结束 ({{ endedCount }})</el-radio-button>
          </el-radio-group>
        </div>
        <div class="header-right">
          <el-button @click="loadCheckins" :loading="loading">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button type="primary" @click="$router.push('/checkin/create')">
            <el-icon><Plus /></el-icon> 发布签到
          </el-button>
        </div>
      </div>

      <!-- 签到卡片列表 -->
      <div class="checkin-list" v-loading="loading">
        <div v-if="filteredList.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <p>暂无签到记录</p>
          <el-button type="primary" @click="$router.push('/checkin/create')">发布第一个签到</el-button>
        </div>

        <div v-else class="checkin-cards">
          <div 
            v-for="item in filteredList" 
            :key="item.id" 
            class="checkin-card"
            :class="{ active: item.status === 'active' }"
          >
            <!-- 卡片头部 -->
            <div class="card-top">
              <span class="type-badge" :class="item.type">
                {{ getTypeIcon(item.type) }} {{ getTypeName(item.type) }}
              </span>
              <span class="status-badge" :class="item.status">
                {{ item.status === 'active' ? '● 进行中' : '已结束' }}
              </span>
            </div>

            <!-- 卡片主体 -->
            <div class="card-body">
              <h3 class="card-title">{{ item.title }}</h3>
              <div class="card-meta">
                <div class="meta-item">
                  <span class="meta-icon">👥</span>
                  <span>{{ item.group_name || '未关联群组' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">🕐</span>
                  <span>{{ formatTime(item.created_at) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">⏱️</span>
                  <span>{{ item.duration }}分钟</span>
                </div>
              </div>
            </div>

            <!-- 签到进度 -->
            <div class="card-progress">
              <div class="progress-info">
                <span class="progress-label">签到进度</span>
                <span class="progress-count">
                  <strong>{{ item.checked_count || 0 }}</strong> / {{ item.total_count || 0 }}
                </span>
              </div>
              <el-progress 
                :percentage="getProgress(item)" 
                :stroke-width="8"
                :color="item.status === 'active' ? '#07c160' : '#909399'"
              />
            </div>

            <!-- 卡片操作 -->
            <div class="card-actions">
              <el-button size="small" @click="viewRecords(item)">
                <el-icon><View /></el-icon> 查看详情
              </el-button>
              <el-button v-if="item.status === 'active'" size="small" type="success" @click="showQrcode(item)">
                <el-icon><Iphone /></el-icon> 二维码
              </el-button>
              <el-button v-if="item.status === 'active'" size="small" type="danger" plain @click="handleEndCheckin(item)">
                结束签到
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 二维码弹窗 -->
      <el-dialog v-model="qrcodeVisible" title="签到二维码" width="380px" center>
        <div class="qrcode-dialog">
          <div class="qrcode-box">
            <canvas ref="qrcodeCanvas"></canvas>
          </div>
          <div class="qrcode-info">
            <div class="checkin-code">
              签到码: <span class="code-text">{{ currentCheckin?.checkin_code }}</span>
            </div>
            <div class="checkin-title">{{ currentCheckin?.title }}</div>
            <div class="checkin-time" v-if="currentCheckin?.end_time">
              截止时间: {{ formatTime(currentCheckin.end_time) }}
            </div>
          </div>
          <div class="qrcode-tip">
            <el-icon><InfoFilled /></el-icon>
            学生扫描二维码或输入签到码即可完成签到
          </div>
        </div>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, View, Iphone, InfoFilled } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'
import { getMyCreatedCheckins, getCheckinQrcode, endCheckin } from '@/api/checkin'
import QRCode from 'qrcode'

const router = useRouter()
const statusFilter = ref('all')
const checkinList = ref([])
const loading = ref(false)
const qrcodeVisible = ref(false)
const currentCheckin = ref(null)
const qrcodeCanvas = ref(null)

const filteredList = computed(() => {
  if (statusFilter.value === 'all') return checkinList.value
  return checkinList.value.filter(c => c.status === statusFilter.value)
})

const activeCount = computed(() => checkinList.value.filter(c => c.status === 'active').length)
const endedCount = computed(() => checkinList.value.filter(c => c.status === 'ended').length)

const getTypeName = (type) => {
  const types = {
    normal: '普通',
    location: '位置',
    qrcode: '扫码',
    gesture: '手势',
    face: '人脸'
  }
  return types[type] || type
}

const getTypeIcon = (type) => {
  const icons = {
    normal: '✅',
    location: '📍',
    qrcode: '📱',
    gesture: '✋',
    face: '👤'
  }
  return icons[type] || '📋'
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getMonth()+1}月${d.getDate()}日 ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

const getProgress = (item) => {
  if (!item.total_count || item.total_count === 0) return 0
  return Math.round((item.checked_count || 0) / item.total_count * 100)
}

const loadCheckins = async () => {
  loading.value = true
  try {
    const res = await getMyCreatedCheckins()
    if (res.success) {
      checkinList.value = res.checkins || []
    }
  } catch (e) {
    console.error('加载签到列表失败:', e)
  } finally {
    loading.value = false
  }
}

const viewRecords = (row) => {
  router.push(`/checkin/records/${row.id}`)
}

const showQrcode = async (row) => {
  try {
    const res = await getCheckinQrcode(row.id)
    if (res.success) {
      currentCheckin.value = { ...row, checkin_code: res.checkin_code }
      qrcodeVisible.value = true
      await nextTick()
      QRCode.toCanvas(qrcodeCanvas.value, res.qr_data, { width: 220, margin: 2 })
    }
  } catch (e) {
    ElMessage.error('获取二维码失败')
  }
}

const handleEndCheckin = async (row) => {
  try {
    await ElMessageBox.confirm('确定要结束此签到吗？结束后学生将无法继续签到。', '结束签到', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await endCheckin(row.id)
    if (res.success) {
      ElMessage.success('签到已结束')
      loadCheckins()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  loadCheckins()
})
</script>

<style scoped>
.checkin-manage {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 顶部操作栏 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-right {
  display: flex;
  gap: 10px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 12px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  color: #909399;
  margin-bottom: 20px;
}

/* 签到卡片列表 */
.checkin-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.checkin-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.checkin-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.checkin-card.active {
  border-color: #07c160;
  background: linear-gradient(135deg, #f0fff4 0%, #fff 100%);
}

/* 卡片顶部 */
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.type-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.normal { background: #f4f4f5; color: #909399; }
.type-badge.location { background: #ecf5ff; color: #409eff; }
.type-badge.qrcode { background: #fdf6ec; color: #e6a23c; }
.type-badge.gesture { background: #fef0f0; color: #f56c6c; }
.type-badge.face { background: #f0f9eb; color: #67c23a; }

.status-badge {
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active { color: #07c160; }
.status-badge.ended { color: #909399; }

/* 卡片主体 */
.card-body {
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
  line-height: 1.4;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.meta-icon {
  font-size: 14px;
}

/* 签到进度 */
.card-progress {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 13px;
  color: #909399;
}

.progress-count {
  font-size: 14px;
  color: #606266;
}

.progress-count strong {
  font-size: 18px;
  color: #07c160;
}

/* 卡片操作 */
.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-actions .el-button {
  flex: 1;
  min-width: 80px;
}

/* 二维码弹窗 */
.qrcode-dialog {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
}

.qrcode-box {
  padding: 20px;
  background: #fff;
  border: 3px solid #07c160;
  border-radius: 16px;
  margin-bottom: 20px;
}

.qrcode-info {
  text-align: center;
  margin-bottom: 16px;
}

.checkin-code {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.code-text {
  font-size: 24px;
  font-weight: bold;
  color: #07c160;
  letter-spacing: 3px;
}

.checkin-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.checkin-time {
  font-size: 13px;
  color: #f56c6c;
}

.qrcode-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #f4f4f5;
  border-radius: 8px;
  font-size: 13px;
  color: #909399;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-left, .header-right {
    justify-content: center;
  }
  
  .checkin-cards {
    grid-template-columns: 1fr;
  }
}
</style>

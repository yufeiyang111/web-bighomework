<template>
  <div class="scan-checkin-page">
    <div class="checkin-card">
      <div class="logo">📚</div>
      <h1>课堂签到</h1>
      
      <!-- 未登录状态 -->
      <div v-if="!isLoggedIn" class="login-prompt">
        <p>请先登录后再进行签到</p>
        <el-button type="primary" size="large" @click="goLogin">登录</el-button>
      </div>
      
      <!-- 已登录状态 -->
      <div v-else class="checkin-form">
        <div class="user-info">
          <el-avatar :size="50">{{ userStore.userInfo?.realName?.[0] }}</el-avatar>
          <span class="user-name">{{ userStore.userInfo?.realName }}</span>
        </div>
        
        <div class="code-section">
          <p class="hint">请输入签到码完成签到</p>
          <el-input 
            v-model="checkinCode" 
            placeholder="输入签到码" 
            size="large"
            maxlength="8"
            class="code-input"
            @keyup.enter="submitCheckin"
          />
          <el-button 
            type="primary" 
            size="large" 
            :loading="submitting"
            :disabled="!checkinCode"
            @click="submitCheckin"
            class="submit-btn"
          >
            确认签到
          </el-button>
        </div>
        
        <!-- 签到结果 -->
        <div v-if="checkinResult" :class="['result', checkinResult.success ? 'success' : 'error']">
          <span class="result-icon">{{ checkinResult.success ? '✅' : '❌' }}</span>
          <span class="result-text">{{ checkinResult.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { doCheckin } from '@/api/checkin'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const checkinCode = ref('')
const submitting = ref(false)
const checkinResult = ref(null)

const isLoggedIn = computed(() => userStore.isLoggedIn)

// 从URL参数获取签到码
onMounted(() => {
  const code = route.query.code
  if (code) {
    checkinCode.value = code.toUpperCase()
  }
})

const goLogin = () => {
  // 保存当前页面URL，登录后跳回
  router.push({ path: '/login', query: { redirect: route.fullPath } })
}

const submitCheckin = async () => {
  if (!checkinCode.value) {
    ElMessage.warning('请输入签到码')
    return
  }
  
  submitting.value = true
  checkinResult.value = null
  
  try {
    const res = await doCheckin({ checkin_code: checkinCode.value.toUpperCase() })
    checkinResult.value = {
      success: res.success,
      message: res.success ? (res.message || '签到成功！') : (res.message || '签到失败')
    }
    if (res.success) {
      ElMessage.success(res.message || '签到成功')
    } else {
      ElMessage.error(res.message || '签到失败')
    }
  } catch (e) {
    checkinResult.value = {
      success: false,
      message: e.response?.data?.message || '签到失败，请重试'
    }
    ElMessage.error(checkinResult.value.message)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.scan-checkin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.checkin-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 30px;
  width: 100%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.logo {
  font-size: 48px;
  margin-bottom: 10px;
}

h1 {
  font-size: 24px;
  color: #333;
  margin: 0 0 30px;
}

.login-prompt {
  padding: 20px 0;
}

.login-prompt p {
  color: #666;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 30px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.user-name {
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.code-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.hint {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.code-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 24px;
  letter-spacing: 4px;
  font-weight: bold;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 18px;
}

.result {
  margin-top: 25px;
  padding: 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.result.success {
  background: #d4edda;
  color: #155724;
}

.result.error {
  background: #f8d7da;
  color: #721c24;
}

.result-icon {
  font-size: 24px;
}

.result-text {
  font-size: 16px;
  font-weight: 500;
}
</style>

<template>
  <Layout pageTitle="个人设置">
    <div class="profile-page">
      <!-- 人脸信息管理 -->
      <div class="settings-card">
        <div class="card-header">
          <h3>人脸信息管理</h3>
        </div>
        <div class="card-body">
          <div class="face-section">
            <div class="face-status">
              <div class="status-icon" :class="{ registered: hasFace }">
                <el-icon v-if="hasFace" :size="32"><CircleCheckFilled /></el-icon>
                <el-icon v-else :size="32"><User /></el-icon>
              </div>
              <div class="status-info">
                <p class="status-title">{{ hasFace ? '已录入人脸' : '未录入人脸' }}</p>
                <p class="status-desc">{{ hasFace ? '您可以使用人脸登录功能' : '录入人脸后可使用人脸登录' }}</p>
              </div>
            </div>
            
            <!-- 上传区域 -->
            <div class="face-upload">
              <div class="upload-preview" v-if="previewUrl">
                <img :src="previewUrl" alt="预览" />
                <el-button class="remove-btn" type="danger" size="small" circle @click="clearPreview">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <el-upload
                v-else
                class="face-uploader"
                :auto-upload="false"
                :show-file-list="false"
                accept="image/*"
                @change="handleFileChange"
              >
                <div class="upload-trigger">
                  <el-icon :size="40"><Camera /></el-icon>
                  <p>点击上传人脸照片</p>
                  <span>支持 JPG、PNG 格式</span>
                </div>
              </el-upload>
            </div>
            
            <div class="face-actions">
              <el-button 
                type="primary" 
                :loading="faceLoading" 
                :disabled="!selectedFile"
                @click="handleRegisterFace"
              >
                {{ hasFace ? '更新人脸' : '录入人脸' }}
              </el-button>
              <el-button 
                v-if="hasFace" 
                type="danger" 
                :loading="deleteLoading"
                @click="handleDeleteFace"
              >
                删除人脸
              </el-button>
            </div>
            
            <div class="face-tips">
              <p><strong>提示：</strong></p>
              <ul>
                <li>请上传清晰的正面人脸照片</li>
                <li>确保光线充足，避免逆光</li>
                <li>照片中只包含一张人脸</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="settings-card">
        <div class="card-header">
          <h3>修改密码</h3>
        </div>
        <div class="card-body">
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-position="top" class="password-form">
            <el-form-item label="原密码" prop="oldPassword">
              <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
            </el-form-item>
            
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码（至少6位）" show-password />
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
            </el-form-item>
            
            <div class="form-actions">
              <el-button type="primary" :loading="loading" @click="handleChangePassword">
                更新密码
              </el-button>
              <el-button @click="resetPasswordForm">
                重置
              </el-button>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { changePassword, getFaceStatus, registerFace, deleteFace } from '@/api/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled, User, Camera, Close } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'

// 密码相关
const passwordFormRef = ref(null)
const loading = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') callback(new Error('请再次输入新密码'))
  else if (value !== passwordForm.newPassword) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '密码长度至少6位', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }]
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const response = await changePassword(passwordForm.oldPassword, passwordForm.newPassword)
      if (response.success) {
        ElMessage.success(response.message || '密码修改成功')
        resetPasswordForm()
      }
    } finally {
      loading.value = false
    }
  })
}

const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  if (passwordFormRef.value) passwordFormRef.value.clearValidate()
}

// 人脸相关
const hasFace = ref(false)
const faceLoading = ref(false)
const deleteLoading = ref(false)
const selectedFile = ref(null)
const previewUrl = ref('')

// 获取人脸状态
const loadFaceStatus = async () => {
  try {
    const response = await getFaceStatus()
    if (response.success) {
      hasFace.value = response.hasFace
    }
  } catch (error) {
    console.error('获取人脸状态失败:', error)
  }
}

// 处理文件选择
const handleFileChange = (file) => {
  const rawFile = file.raw
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  if (rawFile.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }
  selectedFile.value = rawFile
  previewUrl.value = URL.createObjectURL(rawFile)
}

// 清除预览
const clearPreview = () => {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

// 注册人脸
const handleRegisterFace = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择人脸照片')
    return
  }
  
  faceLoading.value = true
  try {
    const response = await registerFace(selectedFile.value)
    if (response.success) {
      ElMessage.success(response.message || '人脸录入成功')
      hasFace.value = true
      clearPreview()
    } else {
      ElMessage.error(response.message || '人脸录入失败')
    }
  } catch (error) {
    ElMessage.error(error.message || '人脸录入失败')
  } finally {
    faceLoading.value = false
  }
}

// 删除人脸
const handleDeleteFace = async () => {
  try {
    await ElMessageBox.confirm('确定要删除已录入的人脸信息吗？删除后将无法使用人脸登录。', '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    deleteLoading.value = true
    const response = await deleteFace()
    if (response.success) {
      ElMessage.success(response.message || '人脸信息已删除')
      hasFace.value = false
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  loadFaceStatus()
})
</script>

<style scoped>
.profile-page {
  max-width: 600px;
}

.settings-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 16px;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid #d0d7de;
  background: #f6f8fa;
}

.card-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2328;
  margin: 0;
}

.card-body {
  padding: 20px;
}

/* 人脸管理样式 */
.face-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.face-status {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
}

.status-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #d0d7de;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #656d76;
}

.status-icon.registered {
  background: #dafbe1;
  color: #1a7f37;
}

.status-info .status-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2328;
  margin: 0 0 4px 0;
}

.status-info .status-desc {
  font-size: 14px;
  color: #656d76;
  margin: 0;
}

.face-upload {
  display: flex;
  justify-content: center;
}

.face-uploader {
  width: 200px;
}

.upload-trigger {
  width: 200px;
  height: 200px;
  border: 2px dashed #d0d7de;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #656d76;
}

.upload-trigger:hover {
  border-color: #0969da;
  color: #0969da;
}

.upload-trigger p {
  margin: 8px 0 4px;
  font-size: 14px;
}

.upload-trigger span {
  font-size: 12px;
  color: #8c959f;
}

.upload-preview {
  position: relative;
  width: 200px;
  height: 200px;
}

.upload-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #d0d7de;
}

.upload-preview .remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
}

.face-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.face-tips {
  padding: 12px 16px;
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  font-size: 13px;
  color: #6c5700;
}

.face-tips p {
  margin: 0 0 8px 0;
}

.face-tips ul {
  margin: 0;
  padding-left: 20px;
}

.face-tips li {
  margin-bottom: 4px;
}

/* 密码表单样式 */
.password-form {
  max-width: 400px;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #1f2328;
}

:deep(.el-input__wrapper) {
  background: #f6f8fa;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.form-actions .el-button--primary {
  background: #2da44e;
  border-color: #2da44e;
}

.form-actions .el-button--primary:hover {
  background: #2c974b;
}

.face-actions .el-button--primary {
  background: #2da44e;
  border-color: #2da44e;
}

.face-actions .el-button--primary:hover {
  background: #2c974b;
}
</style>

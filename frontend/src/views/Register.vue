<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>用户注册</h2>
          <p>Web教育系统</p>
        </div>
      </template>
      
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="80px">
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="registerForm.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入QQ邮箱"
          />
        </el-form-item>
        
        <el-form-item label="验证码" prop="verificationCode">
          <div style="display: flex; gap: 10px;">
            <el-input
              v-model="registerForm.verificationCode"
              placeholder="请输入验证码"
              style="flex: 1;"
            />
            <el-button
              @click="sendCode"
              :disabled="countdown > 0"
              :loading="sendingCode"
            >
              {{ countdown > 0 ? `${countdown}秒后重试` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="真实姓名" prop="realName">
          <el-input
            v-model="registerForm.realName"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        
        <el-form-item label="学号" prop="studentNumber" v-if="registerForm.role === 'student'">
          <el-input
            v-model="registerForm.studentNumber"
            placeholder="请输入学号"
            @blur="checkStudentInRoster"
          />
        </el-form-item>
        
        <el-form-item label="照片" prop="photo" v-if="registerForm.role === 'student'">
          <el-upload
            class="upload-demo"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept="image/*"
            list-type="picture-card"
            :file-list="fileList"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="el-upload__tip">
            请上传清晰的正面照片，用于人脸身份验证
          </div>
          <div v-if="faceVerified" class="verification-success">
            <el-tag type="success">✓ 人脸验证通过 (相似度: {{ (similarity * 100).toFixed(1) }}%)</el-tag>
          </div>
        </el-form-item>
        
        <el-form-item v-if="registerForm.role === 'student' && registerForm.photo && !faceVerified">
          <el-button
            type="warning"
            @click="handleFaceVerification"
            :loading="verifying"
            style="width: 100%"
          >
            <el-icon><Avatar /></el-icon>
            验证人脸
          </el-button>
        </el-form-item>
        
        <el-form-item label="照片" prop="photo" v-if="registerForm.role === 'teacher'">
          <el-upload
            class="upload-demo"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept="image/*"
          >
            <el-button size="small">选择照片</el-button>
            <template #tip>
              <div class="el-upload__tip">
                选填，用于人脸识别
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleRegister"
            :disabled="registerForm.role === 'student' && !faceVerified"
            style="width: 100%"
          >
            注册
          </el-button>
          <div v-if="registerForm.role === 'student' && !faceVerified" class="register-tip">
            <el-text type="warning">请先完成人脸验证后再注册</el-text>
          </div>
        </el-form-item>
        
        <div class="links">
          <router-link to="/login">已有账号？立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { sendVerificationCode } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { Plus, Avatar } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const registerFormRef = ref(null)
const loading = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)
const verifying = ref(false)
const faceVerified = ref(false)
const similarity = ref(0)
const fileList = ref([])
const rosterId = ref(null)

const registerForm = reactive({
  role: 'student',
  email: '',
  verificationCode: '',
  password: '',
  confirmPassword: '',
  realName: '',
  studentNumber: '',
  photo: null
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  studentNumber: [
    { required: true, message: '请输入学号', trigger: 'blur' }
  ]
}

const sendCode = async () => {
  if (!registerForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  
  sendingCode.value = true
  
  try {
    const response = await sendVerificationCode(registerForm.email)
    
    if (response.success) {
      ElMessage.success(response.message)
      // 开始60秒倒计时
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
  } finally {
    sendingCode.value = false
  }
}

const handleFileChange = (file) => {
  registerForm.photo = file.raw
  fileList.value = [file]
  // Reset verification when photo changes
  faceVerified.value = false
  similarity.value = 0
}

const checkStudentInRoster = async () => {
  // This could optionally check if student ID exists in roster
  // For now, we'll do the check during face verification
}

const handleFaceVerification = async () => {
  if (!registerForm.studentNumber) {
    ElMessage.warning('请先输入学号')
    return
  }
  
  if (!registerForm.photo) {
    ElMessage.warning('请先上传照片')
    return
  }
  
  verifying.value = true
  
  try {
    const formData = new FormData()
    formData.append('studentIdNumber', registerForm.studentNumber)
    formData.append('faceImage', registerForm.photo)
    
    const res = await request({
      url: '/roster/verify-face',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      // This endpoint doesn't require auth
      skipAuth: true
    })
    
    if (res.success) {
      faceVerified.value = true
      similarity.value = res.similarity
      rosterId.value = res.roster_id
      ElMessage.success(`人脸验证通过！相似度: ${(res.similarity * 100).toFixed(1)}%`)
    } else {
      ElMessage.error(res.message || '人脸验证失败')
    }
  } catch (error) {
    console.error('Face verification error:', error)
    ElMessage.error(error.response?.data?.message || '人脸验证失败，请重试')
  } finally {
    verifying.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 学生必须完成人脸验证
    if (registerForm.role === 'student') {
      if (!registerForm.photo) {
        ElMessage.warning('请上传照片用于人脸识别')
        return
      }
      if (!faceVerified.value) {
        ElMessage.warning('请先完成人脸验证')
        return
      }
    }
    
    loading.value = true
    
    try {
      // Add rosterId to form data for students
      const formDataToSubmit = { ...registerForm }
      if (registerForm.role === 'student') {
        formDataToSubmit.rosterId = rosterId.value
      }
      
      const result = await userStore.registerAction(formDataToSubmit)
      
      if (result.success) {
        setTimeout(() => {
          router.push('/login')
        }, 1500)
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 40px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 560px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 28px;
}

.card-header p {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 14px;
}

.links {
  text-align: center;
  margin-top: 16px;
}

.links a {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}

.links a:hover {
  text-decoration: underline;
}

.upload-demo {
  width: 100%;
}

.verification-success {
  margin-top: 10px;
}

.register-tip {
  margin-top: 10px;
  text-align: center;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 148px;
  height: 148px;
}

:deep(.el-upload--picture-card) {
  width: 148px;
  height: 148px;
}
</style>

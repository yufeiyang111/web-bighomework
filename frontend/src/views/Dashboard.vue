<template>
  <div class="dashboard-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>Web教育系统</h1>
          <div class="user-info">
            <span>欢迎，{{ userStore.userInfo?.realName || userStore.userInfo?.email }}</span>
            <el-dropdown @command="handleCommand">
              <el-button type="primary" size="small">
                {{ roleText }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="admin" v-if="userStore.hasRole('admin')">管理中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>用户信息</h2>
            </div>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统账号">
              {{ userStore.userInfo?.systemAccount }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ userStore.userInfo?.email }}
            </el-descriptions-item>
            <el-descriptions-item label="真实姓名">
              {{ userStore.userInfo?.realName || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag :type="roleTagType">{{ roleText }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="审核状态" v-if="userStore.userRole === 'teacher'">
              <el-tag :type="userStore.userInfo?.isApproved ? 'success' : 'warning'">
                {{ userStore.userInfo?.isApproved ? '已审核' : '待审核' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="权限列表" :span="2">
              <el-tag
                v-for="permission in userStore.permissions"
                :key="permission"
                size="small"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ permission }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
        
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <h2>快速操作</h2>
            </div>
          </template>
          
          <div class="quick-actions">
            <el-button type="primary" @click="router.push('/profile')">
              个人设置
            </el-button>
            <el-button type="info" @click="router.push('/chatbot')">
              <el-icon><ChatDotRound /></el-icon>
              AI助教
            </el-button>
            <el-button type="warning" v-if="userStore.hasRole('teacher')" @click="router.push('/student-roster')">
              <el-icon><User /></el-icon>
              学生管理
            </el-button>
            <el-button type="success" v-if="userStore.hasRole('admin')" @click="router.push('/admin')">
              管理中心
            </el-button>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ArrowDown, ChatDotRound, User } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const roleText = computed(() => {
  const roleMap = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return roleMap[userStore.userRole] || '未知'
})

const roleTagType = computed(() => {
  const typeMap = {
    admin: 'danger',
    teacher: 'warning',
    student: 'success'
  }
  return typeMap[userStore.userRole] || 'info'
})

const handleCommand = async (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      await userStore.logoutAction()
      router.push('/login')
    }).catch(() => {})
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'admin') {
    router.push('/admin')
  }
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 40px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.el-main {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
}

.quick-actions {
  display: flex;
  gap: 16px;
}
</style>

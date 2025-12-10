<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-container">
        <div class="nav-left">
          <router-link to="/dashboard" class="logo">
            <svg height="24" viewBox="0 0 24 24" width="24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <span>教育系统</span>
          </router-link>
          
          <nav class="nav-menu">
            <router-link to="/dashboard" :class="['nav-link', { active: isActive('/dashboard') }]">
              首页
            </router-link>
            
            <!-- 消息通信 -->
            <el-dropdown trigger="hover" @command="handleNav">
              <span :class="['nav-link', { active: isMessageActive }]">
                消息 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="/messages/private">私信</el-dropdown-item>
                  <el-dropdown-item command="/messages/group">群聊</el-dropdown-item>
                  <el-dropdown-item command="/messages/notifications">通知公告</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <!-- 签到系统 (教师/管理员) -->
            <el-dropdown v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" trigger="hover" @command="handleNav">
              <span :class="['nav-link', { active: isCheckinActive }]">
                签到 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="/checkin/manage">签到管理</el-dropdown-item>
                  <el-dropdown-item command="/checkin/create">发布签到</el-dropdown-item>
                  <el-dropdown-item command="/checkin/records">签到记录</el-dropdown-item>
                  <el-dropdown-item command="/checkin/smart" divided>智能点到</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <!-- 签到 (学生) -->
            <router-link v-if="userStore.hasRole('student')" to="/checkin/student" :class="['nav-link', { active: isActive('/checkin/student') }]">
              签到
            </router-link>
            
            <router-link to="/chatbot" :class="['nav-link', { active: isActive('/chatbot') }]">
              AI助教
            </router-link>
            
            <router-link v-if="userStore.hasRole('teacher')" to="/student-roster" :class="['nav-link', { active: isActive('/student-roster') }]">
              学生管理
            </router-link>

            <!-- 教师管理功能：与学生管理同级展示 -->
            <router-link 
              v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" 
              to="/teacher/class-manager" 
              :class="['nav-link', { active: isActive('/teacher/class-manager') }]">
              班级管理
            </router-link>
            <router-link 
              v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" 
              to="/teacher/exam-manager" 
              :class="['nav-link', { active: isActive('/teacher/exam-manager') }]">
              考试管理
            </router-link>
            <router-link 
              v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" 
              to="/teacher/score-manager" 
              :class="['nav-link', { active: isActive('/teacher/score-manager') }]">
              成绩管理
            </router-link>
            <router-link 
              v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')" 
              to="/teacher/course-manager" 
              :class="['nav-link', { active: isActive('/teacher/course-manager') }]">
              课程管理
            </router-link>
            
            <router-link v-if="userStore.hasRole('admin')" to="/admin" :class="['nav-link', { active: isActive('/admin') }]">
              管理中心
            </router-link>

            <router-link to="Material" :class="['nav-link', { active: isActive('/admin') }]">
              资料中心
            </router-link>

            <router-link to="Chapter" :class="['nav-link', { active: isActive('/admin') }]">
              章节学习
            </router-link>
          </nav>
        </div>
        
        <div class="nav-right">
          <!-- 消息提醒 -->
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="msg-badge">
            <router-link to="/messages/private" class="icon-btn">
              <el-icon :size="20"><Bell /></el-icon>
            </router-link>
          </el-badge>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-dropdown">
              <div class="user-avatar">
                {{ userStore.userInfo?.realName?.[0] || userStore.userInfo?.email?.[0] || 'U' }}
              </div>
              <el-icon class="dropdown-caret"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <div class="dropdown-header">
                  <span class="dropdown-name">{{ userStore.userInfo?.realName || '用户' }}</span>
                  <span class="dropdown-role">{{ roleText }}</span>
                </div>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>
    
    <!-- 页面标题栏 -->
    <div class="page-header" v-if="pageTitle">
      <div class="header-container">
        <h1>{{ pageTitle }}</h1>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <div class="content-container">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import { ArrowDown, Bell } from '@element-plus/icons-vue'

const props = defineProps({
  pageTitle: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 未读消息数（后续接入API）
const unreadCount = ref(0)

const roleText = computed(() => {
  const roleMap = { admin: '管理员', teacher: '教师', student: '学生' }
  return roleMap[userStore.userRole] || '用户'
})

const isActive = (path) => route.path === path

const isMessageActive = computed(() => route.path.startsWith('/messages'))
const isCheckinActive = computed(() => route.path.startsWith('/checkin'))

const handleNav = (path) => {
  router.push(path)
}

const handleCommand = (command) => {
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
  }
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: #f6f8fa;
}

.top-nav {
  background: #ffffff;
  border-bottom: 1px solid #d0d7de;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1f2328;
  font-weight: 600;
  font-size: 16px;
  text-decoration: none;
}

.logo:hover {
  text-decoration: none;
  color: #1f2328;
}

.nav-menu {
  display: flex;
  gap: 4px;
  align-items: center;
}

.nav-link {
  padding: 8px 12px;
  color: #1f2328;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
  text-decoration: none;
  transition: background 0.15s;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link:hover {
  background: #f6f8fa;
  text-decoration: none;
}

.nav-link.active {
  background: rgba(9, 105, 218, 0.1);
  color: #0969da;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  color: #656d76;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: #f6f8fa;
  color: #1f2328;
}

.msg-badge :deep(.el-badge__content) {
  background: #cf222e;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.user-dropdown:hover {
  background: #f6f8fa;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ddf4ff;
  color: #0969da;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.dropdown-caret {
  color: #656d76;
  font-size: 12px;
}

.dropdown-header {
  padding: 8px 16px 12px;
  border-bottom: 1px solid #d0d7de;
  margin-bottom: 4px;
}

.dropdown-name {
  display: block;
  font-weight: 600;
  color: #1f2328;
}

.dropdown-role {
  font-size: 12px;
  color: #656d76;
}

.page-header {
  background: #ffffff;
  border-bottom: 1px solid #d0d7de;
  padding: 24px 0;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2328;
  margin: 0;
}

.main-content {
  padding: 24px 0;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}
</style>

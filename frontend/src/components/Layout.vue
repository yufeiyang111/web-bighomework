<template>
  <div class="app-layout" :class="{ 'mobile': isMobile }">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-container">
        <div class="nav-left">
          <!-- 移动端菜单按钮 -->
          <button class="mobile-menu-btn" @click="showMobileMenu = true" v-if="isMobile">
            <el-icon :size="24"><Menu /></el-icon>
          </button>
          
          <router-link to="/dashboard" class="logo">
            <svg height="24" viewBox="0 0 24 24" width="24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <span class="logo-text">教育系统</span>
          </router-link>
          
          <!-- 桌面端导航菜单 -->
          <nav class="nav-menu" v-if="!isMobile">
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
              <el-icon class="dropdown-caret" v-if="!isMobile"><ArrowDown /></el-icon>
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

    <!-- 移动端侧边菜单 -->
    <el-drawer v-model="showMobileMenu" direction="ltr" size="280px" :show-close="false" class="mobile-drawer">
      <template #header>
        <div class="drawer-header">
          <div class="drawer-user">
            <div class="drawer-avatar">{{ userStore.userInfo?.realName?.[0] || 'U' }}</div>
            <div class="drawer-info">
              <span class="drawer-name">{{ userStore.userInfo?.realName || '用户' }}</span>
              <span class="drawer-role">{{ roleText }}</span>
            </div>
          </div>
        </div>
      </template>
      <div class="mobile-menu">
        <div class="menu-item" @click="mobileNav('/dashboard')">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </div>
        <div class="menu-group">
          <div class="menu-group-title">消息</div>
          <div class="menu-item" @click="mobileNav('/messages/private')">
            <el-icon><ChatDotRound /></el-icon>
            <span>私信</span>
          </div>
          <div class="menu-item" @click="mobileNav('/messages/group')">
            <el-icon><UserFilled /></el-icon>
            <span>群聊</span>
          </div>
          <div class="menu-item" @click="mobileNav('/messages/notifications')">
            <el-icon><Bell /></el-icon>
            <span>通知公告</span>
          </div>
        </div>
        <div class="menu-group" v-if="userStore.hasRole('teacher') || userStore.hasRole('admin')">
          <div class="menu-group-title">签到管理</div>
          <div class="menu-item" @click="mobileNav('/checkin/manage')">
            <el-icon><List /></el-icon>
            <span>签到管理</span>
          </div>
          <div class="menu-item" @click="mobileNav('/checkin/create')">
            <el-icon><Plus /></el-icon>
            <span>发布签到</span>
          </div>
        </div>
        <div class="menu-item" v-if="userStore.hasRole('student')" @click="mobileNav('/checkin/student')">
          <el-icon><Check /></el-icon>
          <span>签到</span>
        </div>
        <div class="menu-item" @click="mobileNav('/chatbot')">
          <el-icon><Service /></el-icon>
          <span>AI助教</span>
        </div>
        <div class="menu-item" v-if="userStore.hasRole('teacher')" @click="mobileNav('/student-roster')">
          <el-icon><User /></el-icon>
          <span>学生管理</span>
        </div>
        <div class="menu-item" v-if="userStore.hasRole('admin')" @click="mobileNav('/admin')">
          <el-icon><Setting /></el-icon>
          <span>管理中心</span>
        </div>
        <div class="menu-divider"></div>
        <div class="menu-item" @click="mobileNav('/profile')">
          <el-icon><UserFilled /></el-icon>
          <span>个人设置</span>
        </div>
        <div class="menu-item logout" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
      </div>
    </el-drawer>
    
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import { 
  ArrowDown, Bell, Menu, HomeFilled, ChatDotRound, UserFilled, 
  List, Plus, Check, Service, User, Setting, SwitchButton 
} from '@element-plus/icons-vue'

const props = defineProps({
  pageTitle: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式检测
const isMobile = ref(false)
const showMobileMenu = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

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

const mobileNav = (path) => {
  showMobileMenu.value = false
  router.push(path)
}

const handleLogout = () => {
  showMobileMenu.value = false
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await userStore.logoutAction()
    router.push('/login')
  }).catch(() => {})
}

const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
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

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #1f2328;
  border-radius: 6px;
}

.mobile-menu-btn:hover {
  background: #f6f8fa;
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

/* ========== 移动端侧边菜单样式 ========== */
.drawer-header {
  padding: 0;
}

.drawer-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drawer-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 20px;
}

.drawer-info {
  display: flex;
  flex-direction: column;
}

.drawer-name {
  font-weight: 600;
  font-size: 16px;
  color: #1f2328;
}

.drawer-role {
  font-size: 12px;
  color: #656d76;
}

.mobile-menu {
  padding: 8px 0;
}

.menu-group {
  margin-bottom: 8px;
}

.menu-group-title {
  padding: 12px 20px 8px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  color: #1f2328;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f6f8fa;
}

.menu-item:active {
  background: #e8e8e8;
}

.menu-item .el-icon {
  font-size: 20px;
  color: #656d76;
}

.menu-item.logout {
  color: #f56c6c;
}

.menu-item.logout .el-icon {
  color: #f56c6c;
}

.menu-divider {
  height: 1px;
  background: #e5e5e5;
  margin: 8px 20px;
}

/* ========== 移动端响应式 ========== */
@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
  
  .nav-container {
    padding: 0 12px;
    height: 56px;
  }
  
  .nav-left {
    gap: 8px;
  }
  
  .logo-text {
    display: none;
  }
  
  .nav-right {
    gap: 8px;
  }
  
  .page-header {
    padding: 16px 0;
  }
  
  .header-container {
    padding: 0 12px;
  }
  
  .page-header h1 {
    font-size: 18px;
  }
  
  .main-content {
    padding: 12px 0;
  }
  
  .content-container {
    padding: 0 12px;
  }
}

/* 移动端抽屉样式覆盖 */
:deep(.mobile-drawer .el-drawer__header) {
  padding: 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #e5e5e5;
}

:deep(.mobile-drawer .el-drawer__body) {
  padding: 0;
}
</style>

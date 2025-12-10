import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresRole: 'admin' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chatbot',
    name: 'Chatbot',
    component: () => import('@/views/Chatbot.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/student-roster',
    name: 'StudentRoster',
    component: () => import('@/views/StudentRoster.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  // 消息通信模块
  {
    path: '/messages/private',
    name: 'PrivateMessages',
    component: () => import('@/views/messages/PrivateMessages.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/messages/group',
    name: 'GroupChat',
    component: () => import('@/views/messages/GroupChat.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/messages/notifications',
    name: 'Notifications',
    component: () => import('@/views/messages/Notifications.vue'),
    meta: { requiresAuth: true }
  },
  // 签到模块 - 教师/管理员
  {
    path: '/checkin/manage',
    name: 'CheckinManage',
    component: () => import('@/views/checkin/CheckinManage.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/checkin/create',
    name: 'CheckinCreate',
    component: () => import('@/views/checkin/CheckinCreate.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/checkin/records',
    name: 'CheckinRecords',
    component: () => import('@/views/checkin/CheckinRecords.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/checkin/smart',
    name: 'SmartCheckin',
    component: () => import('@/views/checkin/SmartCheckin.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  // 签到模块 - 学生
  {
    path: '/checkin/student',
    name: 'StudentCheckin',
    component: () => import('@/views/checkin/StudentCheckin.vue'),
    meta: { requiresAuth: true, requiresRole: 'student' }
  },
  // 成绩/课程管理模块 - 教师/管理员
  {
    path: '/teacher/class-manager',
    name: 'ClassManager',
    component: () => import('@/views/teacher/ClassManager.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/classes/:id',
    name: 'ClassDetail',
    component: () => import('@/views/ClassDetail.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/course-manager',
    name: 'CourseManager',
    component: () => import('@/views/teacher/CourseManager.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/exam-manager',
    name: 'ExamManager',
    component: () => import('@/views/teacher/ExamManager.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/score-manager',
    name: 'ScoreManager',
    component: () => import('@/views/teacher/ScoreManager.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/importer',
    name: 'GradeImporter',
    component: () => import('@/views/teacher/GradeImporter.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/question-chat',
    name: 'QuestionChat',
    component: () => import('@/views/teacher/QuestionChat.vue'),
    meta: { requiresAuth: true, requiresRole: 'teacher' }
  },
  {
    path: '/teacher/Material',
    name: 'Material',
    component: () => import('@/views/Yves/pages/Material.vue')
  },
  {
    path: '/teacher/Chapter',
    name: 'Chapter',
    component: () => import('@/views/Yves/pages/Chapter.vue')
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  if (userStore.token && !userStore.userInfo) {
    await userStore.verifyTokenAction()
  }
  
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    
    if (to.meta.requiresRole) {
      // 管理员可以访问教师页面
      const allowedRoles = to.meta.requiresRole === 'teacher' 
        ? ['teacher', 'admin'] 
        : [to.meta.requiresRole]
      
      if (!allowedRoles.includes(userStore.userRole)) {
        next('/dashboard')
        return
      }
    }
  } else {
    if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next('/dashboard')
      return
    }
  }
  
  next()
})

export default router

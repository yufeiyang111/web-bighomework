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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 路由守卫
 * 根据登录状态和用户角色控制路由访问
 */
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 如果有token但没有用户信息，尝试验证token
  if (userStore.token && !userStore.userInfo) {
    await userStore.verifyTokenAction()
  }
  
  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      // 未登录，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 检查角色权限
    if (to.meta.requiresRole) {
      if (userStore.userRole !== to.meta.requiresRole) {
        // 角色不匹配，跳转到仪表板
        next('/dashboard')
        return
      }
    }
  } else {
    // 如果已登录，访问登录/注册页面时跳转到仪表板
    if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      next('/dashboard')
      return
    }
  }
  
  next()
})

export default router

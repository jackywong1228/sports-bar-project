import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/schedule',
    children: [
      {
        path: 'schedule',
        name: 'Schedule',
        component: () => import('@/views/Schedule.vue'),
        meta: { title: '我的排课' }
      },
      {
        path: 'courses',
        name: 'Courses',
        component: () => import('@/views/Courses.vue'),
        meta: { title: '我的课程' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '我的' }
      }
    ]
  },
  {
    path: '/sessions/:id/bookings',
    name: 'SessionBookings',
    component: () => import('@/views/SessionBookings.vue'),
    meta: { title: '报名名单' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/schedule'
  }
]

const router = createRouter({
  history: createWebHashHistory('/coach/'),
  routes
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || ''} - 教练工作台`

  const userStore = useUserStore()

  if (to.meta.requiresAuth === false) {
    next()
    return
  }

  if (!userStore.token) {
    next('/login')
    return
  }

  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (_e) {
      userStore.logout()
      next('/login')
      return
    }
  }

  next()
})

export default router

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
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '工作台' }
  },
  {
    path: '/food/orders',
    name: 'FoodOrderList',
    component: () => import('@/views/food/OrderList.vue'),
    meta: { title: '餐饮订单' }
  },
  {
    path: '/food/orders/:id',
    name: 'FoodOrderDetail',
    component: () => import('@/views/food/OrderDetail.vue'),
    meta: { title: '订单详情' }
  },
  {
    path: '/reservation/list',
    name: 'ReservationList',
    component: () => import('@/views/reservation/ReservationList.vue'),
    meta: { title: '预约管理' }
  },
  {
    path: '/reservation/:id',
    name: 'ReservationDetail',
    component: () => import('@/views/reservation/ReservationDetail.vue'),
    meta: { title: '预约详情' }
  },
  {
    path: '/scan',
    name: 'ScanVerify',
    component: () => import('@/views/scan/ScanVerify.vue'),
    meta: { title: '扫码核销' }
  },
  {
    path: '/member/search',
    name: 'MemberSearch',
    component: () => import('@/views/member/MemberSearch.vue'),
    meta: { title: '会员查询' }
  },
  {
    path: '/member/:id',
    name: 'MemberDetail',
    component: () => import('@/views/member/MemberDetail.vue'),
    meta: { title: '会员详情' }
  },
  {
    path: '/checkin/records',
    name: 'CheckinRecords',
    component: () => import('@/views/checkin/CheckinRecords.vue'),
    meta: { title: '打卡记录' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人中心' }
  }
]

const router = createRouter({
  history: createWebHashHistory('/staff/'),
  routes
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || ''} - 员工工作台`

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

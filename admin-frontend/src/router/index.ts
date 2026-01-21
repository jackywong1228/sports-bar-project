import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
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
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', icon: 'HomeFilled' }
      },
      // 系统管理
      {
        path: 'system',
        name: 'System',
        redirect: '/system/user',
        meta: { title: '系统管理', icon: 'Setting' },
        children: [
          {
            path: 'user',
            name: 'SystemUser',
            component: () => import('@/views/system/User.vue'),
            meta: { title: '用户管理' }
          },
          {
            path: 'role',
            name: 'SystemRole',
            component: () => import('@/views/system/Role.vue'),
            meta: { title: '角色管理' }
          },
          {
            path: 'department',
            name: 'SystemDepartment',
            component: () => import('@/views/system/Department.vue'),
            meta: { title: '部门管理' }
          }
        ]
      },
      // 会员管理
      {
        path: 'member',
        name: 'Member',
        redirect: '/member/list',
        meta: { title: '会员管理', icon: 'User' },
        children: [
          {
            path: 'list',
            name: 'MemberList',
            component: () => import('@/views/member/List.vue'),
            meta: { title: '会员列表' }
          },
          {
            path: 'level',
            name: 'MemberLevel',
            component: () => import('@/views/member/Level.vue'),
            meta: { title: '会员等级' }
          },
          {
            path: 'card',
            name: 'MemberCard',
            component: () => import('@/views/member/Card.vue'),
            meta: { title: '会员卡套餐' }
          },
          {
            path: 'card-order',
            name: 'MemberCardOrder',
            component: () => import('@/views/member/CardOrder.vue'),
            meta: { title: '会员卡订单' }
          }
        ]
      },
      // 打卡管理
      {
        path: 'checkin',
        name: 'Checkin',
        redirect: '/checkin/records',
        meta: { title: '打卡管理', icon: 'Clock' },
        children: [
          {
            path: 'records',
            name: 'CheckinRecords',
            component: () => import('@/views/checkin/Records.vue'),
            meta: { title: '打卡记录' }
          },
          {
            path: 'rules',
            name: 'CheckinRules',
            component: () => import('@/views/checkin/Rules.vue'),
            meta: { title: '积分规则' }
          },
          {
            path: 'leaderboard',
            name: 'CheckinLeaderboard',
            component: () => import('@/views/checkin/Leaderboard.vue'),
            meta: { title: '排行榜' }
          }
        ]
      },
      // 场地管理
      {
        path: 'venue',
        name: 'Venue',
        redirect: '/venue/list',
        meta: { title: '场地管理', icon: 'Location' },
        children: [
          {
            path: 'list',
            name: 'VenueList',
            component: () => import('@/views/venue/List.vue'),
            meta: { title: '场地列表' }
          },
          {
            path: 'type',
            name: 'VenueType',
            component: () => import('@/views/venue/Type.vue'),
            meta: { title: '场地类型' }
          },
          {
            path: 'price',
            name: 'VenuePrice',
            component: () => import('@/views/venue/Price.vue'),
            meta: { title: '价格管理' }
          }
        ]
      },
      // 预约管理
      {
        path: 'reservation',
        name: 'Reservation',
        redirect: '/reservation/list',
        meta: { title: '预约管理', icon: 'Calendar' },
        children: [
          {
            path: 'list',
            name: 'ReservationList',
            component: () => import('@/views/reservation/List.vue'),
            meta: { title: '预约记录' }
          }
        ]
      },
      // 教练管理
      {
        path: 'coach',
        name: 'Coach',
        redirect: '/coach/list',
        meta: { title: '教练管理', icon: 'Avatar' },
        children: [
          {
            path: 'list',
            name: 'CoachList',
            component: () => import('@/views/coach/List.vue'),
            meta: { title: '教练列表' }
          },
          {
            path: 'application',
            name: 'CoachApplication',
            component: () => import('@/views/coach/Application.vue'),
            meta: { title: '教练申请' }
          }
        ]
      },
      // 活动管理
      {
        path: 'activity',
        name: 'Activity',
        redirect: '/activity/list',
        meta: { title: '活动管理', icon: 'Flag' },
        children: [
          {
            path: 'list',
            name: 'ActivityList',
            component: () => import('@/views/activity/List.vue'),
            meta: { title: '活动列表' }
          }
        ]
      },
      // 点餐管理
      {
        path: 'food',
        name: 'Food',
        redirect: '/food/list',
        meta: { title: '点餐管理', icon: 'Food' },
        children: [
          {
            path: 'category',
            name: 'FoodCategory',
            component: () => import('@/views/food/Category.vue'),
            meta: { title: '餐饮分类' }
          },
          {
            path: 'list',
            name: 'FoodList',
            component: () => import('@/views/food/List.vue'),
            meta: { title: '餐饮商品' }
          },
          {
            path: 'order',
            name: 'FoodOrder',
            component: () => import('@/views/food/Order.vue'),
            meta: { title: '餐饮订单' }
          }
        ]
      },
      // 票券管理
      {
        path: 'coupon',
        name: 'Coupon',
        redirect: '/coupon/template',
        meta: { title: '票券管理', icon: 'Ticket' },
        children: [
          {
            path: 'template',
            name: 'CouponTemplate',
            component: () => import('@/views/coupon/Template.vue'),
            meta: { title: '优惠券模板' }
          },
          {
            path: 'record',
            name: 'CouponRecord',
            component: () => import('@/views/coupon/Record.vue'),
            meta: { title: '发放记录' }
          }
        ]
      },
      // 商城管理
      {
        path: 'mall',
        name: 'Mall',
        redirect: '/mall/product',
        meta: { title: '商城管理', icon: 'ShoppingCart' },
        children: [
          {
            path: 'category',
            name: 'MallCategory',
            component: () => import('@/views/mall/Category.vue'),
            meta: { title: '商品分类' }
          },
          {
            path: 'product',
            name: 'MallProduct',
            component: () => import('@/views/mall/Product.vue'),
            meta: { title: '积分商品' }
          },
          {
            path: 'order',
            name: 'MallOrder',
            component: () => import('@/views/mall/Order.vue'),
            meta: { title: '兑换订单' }
          }
        ]
      },
      // 财务管理
      {
        path: 'finance',
        name: 'Finance',
        redirect: '/finance/overview',
        meta: { title: '财务管理', icon: 'Wallet' },
        children: [
          {
            path: 'overview',
            name: 'FinanceOverview',
            component: () => import('@/views/finance/Overview.vue'),
            meta: { title: '财务概览' }
          },
          {
            path: 'recharge',
            name: 'FinanceRecharge',
            component: () => import('@/views/finance/Recharge.vue'),
            meta: { title: '充值记录' }
          },
          {
            path: 'consume',
            name: 'FinanceConsume',
            component: () => import('@/views/finance/Consume.vue'),
            meta: { title: '消费记录' }
          },
          {
            path: 'settlement',
            name: 'FinanceSettlement',
            component: () => import('@/views/finance/Settlement.vue'),
            meta: { title: '教练结算' }
          }
        ]
      },
      // 消息通知
      {
        path: 'message',
        name: 'Message',
        redirect: '/message/send',
        meta: { title: '消息通知', icon: 'Bell' },
        children: [
          {
            path: 'send',
            name: 'MessageSend',
            component: () => import('@/views/message/Send.vue'),
            meta: { title: '消息管理' }
          },
          {
            path: 'template',
            name: 'MessageTemplate',
            component: () => import('@/views/message/Template.vue'),
            meta: { title: '消息模板' }
          },
          {
            path: 'announcement',
            name: 'MessageAnnouncement',
            component: () => import('@/views/message/Announcement.vue'),
            meta: { title: '公告管理' }
          },
          {
            path: 'banner',
            name: 'MessageBanner',
            component: () => import('@/views/message/Banner.vue'),
            meta: { title: '轮播图管理' }
          }
        ]
      },
      // UI素材管理
      {
        path: 'ui-assets/icon',
        name: 'UIIcon',
        component: () => import('@/views/ui-assets/Icon.vue'),
        meta: { title: '图标管理', icon: 'Picture' }
      },
      {
        path: 'ui-assets/theme',
        name: 'UITheme',
        component: () => import('@/views/ui-assets/Theme.vue'),
        meta: { title: '主题配色', icon: 'Picture' }
      },
      {
        path: 'ui-assets/image',
        name: 'UIImage',
        component: () => import('@/views/ui-assets/Image.vue'),
        meta: { title: '图片素材', icon: 'Picture' }
      },
      // UI可视化编辑器
      {
        path: 'ui-editor',
        name: 'UIEditor',
        component: () => import('@/views/ui-editor/index.vue'),
        meta: { title: '小程序布局编辑器', icon: 'Edit' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta.title || ''} - 场馆管理系统`

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
    } catch (e) {
      userStore.logout()
      next('/login')
      return
    }
  }

  next()
})

export default router

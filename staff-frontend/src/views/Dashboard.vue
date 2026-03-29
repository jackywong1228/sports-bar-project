<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getDashboardStats } from '@/api/dashboard'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({
  today_orders: 0,
  today_reservations: 0,
  today_checkins: 0,
  active_members: 0
})

const menuItems = [
  { icon: 'orders-o', text: '餐饮订单', path: '/food/orders', color: '#ee6723' },
  { icon: 'calendar-o', text: '预约管理', path: '/reservation/list', color: '#1989fa' },
  { icon: 'scan', text: '扫码核销', path: '/scan', color: '#07c160' },
  { icon: 'friends-o', text: '会员查询', path: '/member/search', color: '#C9A962' },
  { icon: 'clock-o', text: '打卡记录', path: '/checkin/records', color: '#7232dd' },
  { icon: 'user-o', text: '个人中心', path: '/profile', color: '#969799' }
]

const navigate = (path: string) => {
  router.push(path)
}

onMounted(async () => {
  try {
    const res = await getDashboardStats()
    if (res.data) {
      stats.value = {
        today_orders: res.data.today_orders || 0,
        today_reservations: res.data.today_reservations || 0,
        today_checkins: res.data.today_checkins || 0,
        active_members: res.data.active_members || 0
      }
    }
  } catch (_e) {
    // 忽略
  }
})
</script>

<template>
  <div class="page-container">
    <!-- 顶部导航 -->
    <van-nav-bar title="工作台" :border="false" class="top-bar">
      <template #right>
        <van-icon name="setting-o" size="20" @click="navigate('/profile')" />
      </template>
    </van-nav-bar>

    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <div class="greeting">你好，{{ userStore.userInfo?.name || userStore.userInfo?.username || '员工' }}</div>
        <div class="date">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</div>
      </div>
    </div>

    <!-- 今日统计 -->
    <div class="stats-section">
      <van-grid :column-num="4" :border="false" class="stats-grid">
        <van-grid-item>
          <div class="stat-value">{{ stats.today_orders }}</div>
          <div class="stat-label">今日订单</div>
        </van-grid-item>
        <van-grid-item>
          <div class="stat-value">{{ stats.today_reservations }}</div>
          <div class="stat-label">今日预约</div>
        </van-grid-item>
        <van-grid-item>
          <div class="stat-value">{{ stats.today_checkins }}</div>
          <div class="stat-label">今日打卡</div>
        </van-grid-item>
        <van-grid-item>
          <div class="stat-value">{{ stats.active_members }}</div>
          <div class="stat-label">活跃会员</div>
        </van-grid-item>
      </van-grid>
    </div>

    <!-- 功能入口 -->
    <div class="menu-section">
      <van-cell-group inset title="常用功能">
        <van-grid :column-num="3" :border="false">
          <van-grid-item
            v-for="item in menuItems"
            :key="item.path"
            :icon="item.icon"
            :text="item.text"
            :icon-color="item.color"
            @click="navigate(item.path)"
          />
        </van-grid>
      </van-cell-group>
    </div>
  </div>
</template>

<style scoped>
.top-bar {
  background: var(--staff-primary);
}

.top-bar :deep(.van-nav-bar__title) {
  color: #fff;
  font-weight: 600;
}

.top-bar :deep(.van-icon) {
  color: #fff;
}

.welcome-section {
  background: linear-gradient(135deg, var(--staff-primary), var(--staff-primary-light));
  padding: 20px 16px 30px;
  color: #fff;
}

.greeting {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.date {
  font-size: 13px;
  opacity: 0.8;
}

.stats-section {
  margin: -16px 12px 12px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 16px 0;
}

.stats-grid :deep(.van-grid-item__content) {
  padding: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--staff-primary);
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin-top: 4px;
}

.menu-section {
  margin-top: 12px;
}

.menu-section :deep(.van-grid-item__content) {
  padding: 16px 8px;
}

.menu-section :deep(.van-grid-item__icon) {
  font-size: 28px;
}

.menu-section :deep(.van-grid-item__text) {
  margin-top: 8px;
  font-size: 13px;
}
</style>

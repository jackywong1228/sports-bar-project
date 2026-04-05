<template>
  <div class="workbench">
    <!-- 顶栏 -->
    <div class="header">
      <span class="header-title">工作台</span>
      <span class="header-icon" @click="$router.push('/dashboard')">&#9881;</span>
    </div>

    <!-- 问候卡片 -->
    <div class="greeting">
      <div class="greeting-name">你好，{{ userName }}</div>
      <div class="greeting-date">{{ todayText }}</div>
      <div class="stats-row">
        <div class="stat-item" v-for="s in statItems" :key="s.label">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 常用功能 -->
    <div class="section-title">常用功能</div>
    <div class="quick-grid">
      <div
        class="quick-item"
        v-for="item in quickActions"
        :key="item.label"
        @click="$router.push(item.route)"
      >
        <div class="quick-icon" :style="{ background: item.bg }">
          <span v-html="item.icon"></span>
        </div>
        <div class="quick-label">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()
const userName = computed(() => userStore.userInfo?.name || userStore.userInfo?.username || '管理员')

const todayText = computed(() => {
  const d = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日${weekdays[d.getDay()]}`
})

const todayReservations = ref(0)
const todayCheckins = ref(0)
const activeMembers = ref(0)
const todayOrders = ref(0)

const statItems = computed(() => [
  { label: '今日预约', value: todayReservations.value },
  { label: '今日打卡', value: todayCheckins.value },
  { label: '活跃会员', value: activeMembers.value },
  { label: '总会员数', value: todayOrders.value },
])

const quickActions = [
  { label: '预约管理', route: '/reservation/list', icon: '&#128197;', bg: '#E8F4FD' },
  { label: '扫码核销', route: '/staff/scan', icon: '&#128247;', bg: '#E8F8EE' },
  { label: '会员查询', route: '/member/list', icon: '&#128101;', bg: '#FFF8E1' },
  { label: '活动管理', route: '/activity/list', icon: '&#128293;', bg: '#FFEBEE' },
  { label: '打卡记录', route: '/checkin/records', icon: '&#9201;', bg: '#F3E5F5' },
  { label: '票券管理', route: '/coupon/template', icon: '&#127915;', bg: '#E0F2F1' },
]

onMounted(async () => {
  try {
    const res = await request.get('/dashboard/stats')
    const data = res.data?.data || res.data
    if (data?.today) {
      todayReservations.value = data.today.reservations || 0
      todayOrders.value = data.total?.members || 0
    }
    if (data?.total) {
      activeMembers.value = data.total.members || 0
    }
  } catch { /* ignore */ }

  try {
    const res = await request.get('/dashboard/overview-cards')
    const cards = res.data?.data || res.data
    if (Array.isArray(cards)) {
      const checkinCard = cards.find((c: any) => c.key === 'today_checkins' || c.title?.includes('打卡'))
      if (checkinCard) todayCheckins.value = checkinCard.value || 0
    }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.workbench {
  min-height: 100vh;
  background: #F0F2F0;
}
.header {
  background: #1A5D3A;
  color: #fff;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50px;
  position: relative;
  font-size: 17px;
}
.header-title { font-weight: 600; }
.header-icon {
  position: absolute;
  right: 16px;
  font-size: 22px;
  cursor: pointer;
  opacity: 0.85;
}
.greeting {
  background: linear-gradient(135deg, #1A5D3A, #2E7D52);
  color: #fff;
  padding: 20px 20px 16px;
}
.greeting-name { font-size: 20px; font-weight: 600; }
.greeting-date { font-size: 13px; opacity: 0.8; margin-top: 4px; }
.stats-row {
  display: flex;
  background: rgba(255,255,255,0.15);
  border-radius: 10px;
  margin-top: 16px;
  padding: 12px 0;
}
.stat-item {
  flex: 1;
  text-align: center;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.stat-label {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 4px;
}
.section-title {
  padding: 20px 20px 12px;
  font-size: 15px;
  color: #666;
  font-weight: 500;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  background: #fff;
  margin: 0 16px;
  border-radius: 12px;
  padding: 8px 0;
}
.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  cursor: pointer;
}
.quick-item:active { opacity: 0.6; }
.quick-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.quick-label {
  margin-top: 8px;
  font-size: 13px;
  color: #333;
}
</style>

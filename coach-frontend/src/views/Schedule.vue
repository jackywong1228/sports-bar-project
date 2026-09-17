<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getMySessions, type CourseSession } from '@/api/course'

const router = useRouter()
const userStore = useUserStore()

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const CATEGORY_COLORS: Record<string, string> = {
  group: '#07c160',
  golf: '#1989fa',
  squash: '#ff976a',
  pickleball: '#ee0a24'
}

const sessions = ref<CourseSession[]>([])
const loading = ref(false)
const refreshing = ref(false)
const rangeDays = ref(7)
const rangeOptions = [
  { text: '近 7 天', value: 7 },
  { text: '近 30 天', value: 30 }
]

const todayStr = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})()

const todayText = (() => {
  const d = new Date()
  return `${d.getMonth() + 1}月${d.getDate()}日 ${WEEKDAYS[d.getDay()]}`
})()

// 今日概览
const todaySessions = computed(() => sessions.value.filter(s => s.session_date === todayStr))
const todaySessionCount = computed(() => todaySessions.value.filter(s => s.status === 'scheduled').length)
const todayStudentCount = computed(() =>
  todaySessions.value
    .filter(s => s.status === 'scheduled')
    .reduce((sum, s) => sum + (s.booked_count || 0), 0)
)

// 按天分组
interface DayGroup {
  date: string
  weekday: string
  isToday: boolean
  items: CourseSession[]
}

const dayGroups = computed<DayGroup[]>(() => {
  const map = new Map<string, CourseSession[]>()
  for (const s of sessions.value) {
    const list = map.get(s.session_date) || []
    list.push(s)
    map.set(s.session_date, list)
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, items]) => {
      const d = new Date(date.replace(/-/g, '/'))
      return {
        date,
        weekday: WEEKDAYS[d.getDay()] || '',
        isToday: date === todayStr,
        items: items.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''))
      }
    })
})

const formatDate = (offset: number) => {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const res = await getMySessions({
      start_date: formatDate(0),
      end_date: formatDate(rangeDays.value - 1)
    })
    sessions.value = res.data as unknown as CourseSession[]
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  await fetchSessions()
  refreshing.value = false
}

const onRangeChange = () => {
  fetchSessions()
}

const goBookings = (session: CourseSession) => {
  router.push({
    path: `/sessions/${session.id}/bookings`,
    query: {
      course_title: session.course_title || '',
      category_text: session.category_text || '',
      session_date: session.session_date,
      start_time: session.start_time || '',
      end_time: session.end_time || '',
      capacity: String(session.capacity),
      booked_count: String(session.booked_count || 0)
    }
  })
}

onMounted(() => {
  fetchSessions()
})
</script>

<template>
  <div class="page-container">
    <!-- 顶部问候 -->
    <div class="greeting">
      <div>
        <div class="hello">{{ userStore.userInfo?.name || '教练' }}，你好</div>
        <div class="today">{{ todayText }}</div>
      </div>
      <van-dropdown-menu class="range-menu" active-color="#1A5D3A">
        <van-dropdown-item v-model="rangeDays" :options="rangeOptions" @change="onRangeChange" />
      </van-dropdown-menu>
    </div>

    <!-- 今日概览 -->
    <div class="overview">
      <div class="overview-item">
        <div class="overview-value">{{ todaySessionCount }}</div>
        <div class="overview-label">今日课次</div>
      </div>
      <div class="overview-divider"></div>
      <div class="overview-item">
        <div class="overview-value">{{ todayStudentCount }}</div>
        <div class="overview-label">今日学员</div>
      </div>
    </div>

    <!-- 按天分组的课次列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list :loading="loading">
        <div v-if="!loading && dayGroups.length === 0" class="empty-wrap">
          <van-empty description="该时间范围内暂无排课" />
        </div>

        <div v-for="group in dayGroups" :key="group.date" class="day-group">
          <div class="day-header">
            <span class="day-date">{{ group.date.slice(5) }}</span>
            <span class="day-weekday">{{ group.weekday }}</span>
            <span v-if="group.isToday" class="today-badge">今天</span>
          </div>

          <div
            v-for="s in group.items"
            :key="s.id"
            class="session-card"
            :class="{ 'session-cancelled': s.status === 'cancelled' }"
            @click="goBookings(s)"
          >
            <div class="session-time">
              <div class="time-start">{{ s.start_time }}</div>
              <div class="time-end">{{ s.end_time }}</div>
            </div>
            <div class="session-body">
              <div class="session-title-row">
                <span class="session-title">{{ s.course_title }}</span>
                <van-tag
                  v-if="s.category"
                  :color="CATEGORY_COLORS[s.category] || '#999'"
                  class="category-tag"
                >
                  {{ s.category_text }}
                </van-tag>
              </div>
              <div class="session-meta">
                已约 {{ s.booked_count }}/{{ s.capacity }}
                <template v-if="s.remark"> · {{ s.remark }}</template>
              </div>
            </div>
            <div class="session-status">
              <span v-if="s.status === 'cancelled'" class="status-cancelled">已取消</span>
              <van-icon v-else name="arrow" color="#ccc" />
            </div>
          </div>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.greeting {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 16px 12px;
}

.hello {
  font-size: 22px;
  font-weight: 600;
  color: #1A1A1A;
}

.today {
  margin-top: 4px;
  font-size: 13px;
  color: #999;
}

.range-menu {
  width: 110px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.range-menu :deep(.van-dropdown-menu__bar) {
  height: 36px;
  box-shadow: none;
}

.overview {
  display: flex;
  align-items: center;
  margin: 0 16px;
  padding: 20px 0;
  background: linear-gradient(135deg, var(--coach-primary) 0%, var(--coach-primary-light) 100%);
  border-radius: 16px;
  color: #fff;
}

.overview-item {
  flex: 1;
  text-align: center;
}

.overview-value {
  font-size: 28px;
  font-weight: 700;
}

.overview-label {
  margin-top: 4px;
  font-size: 13px;
  opacity: 0.85;
}

.overview-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

.empty-wrap {
  padding-top: 60px;
}

.day-group {
  margin-top: 16px;
}

.day-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px 8px;
}

.day-date {
  font-size: 16px;
  font-weight: 600;
  color: #1A1A1A;
}

.day-weekday {
  font-size: 13px;
  color: #999;
}

.today-badge {
  font-size: 11px;
  color: #fff;
  background: var(--coach-primary);
  border-radius: 8px;
  padding: 2px 8px;
}

.session-card {
  display: flex;
  align-items: center;
  background: #fff;
  margin: 0 16px 10px;
  padding: 14px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.session-cancelled .session-time,
.session-cancelled .session-body {
  opacity: 0.45;
  text-decoration: line-through;
}

.session-time {
  width: 64px;
  flex-shrink: 0;
  text-align: center;
  border-right: 1px solid #F0F0F0;
  padding-right: 12px;
  margin-right: 12px;
}

.time-start {
  font-size: 17px;
  font-weight: 700;
  color: var(--coach-primary);
}

.time-end {
  margin-top: 2px;
  font-size: 12px;
  color: #999;
}

.session-body {
  flex: 1;
  min-width: 0;
}

.session-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.session-title {
  font-size: 15px;
  font-weight: 600;
  color: #1A1A1A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-tag {
  flex-shrink: 0;
  border-radius: 4px;
}

.session-meta {
  margin-top: 6px;
  font-size: 13px;
  color: #666;
}

.session-status {
  flex-shrink: 0;
  margin-left: 8px;
}

.status-cancelled {
  font-size: 12px;
  color: #ee0a24;
}
</style>

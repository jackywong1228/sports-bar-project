<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import * as echarts from 'echarts'

const userStore = useUserStore()

const stats = ref<any>({
  today: { members: 0, reservations: 0, recharge: 0, orders: 0 },
  total: { members: 0, coaches: 0, venues: 0 },
  month: { recharge: 0, reservations: 0 }
})

const overviewCards = ref<any>({
  pending_reservations: 0,
  pending_food_orders: 0,
  pending_coach_apps: 0,
  today_activities: 0
})

const rankings = ref<any>({
  venues: [],
  coaches: [],
  members: []
})

const recentData = ref<any>({
  reservations: [],
  recharges: [],
  activities: []
})

const trendChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const fetchStats = async () => {
  try {
    const res = await request.get('/dashboard/stats')
    stats.value = res.data
  } catch (err) {
    console.error('获取统计数据失败:', err)
  }
}

const fetchOverviewCards = async () => {
  try {
    const res = await request.get('/dashboard/overview-cards')
    overviewCards.value = res.data
  } catch (err) {
    console.error('获取概览卡片失败:', err)
  }
}

const fetchTrend = async () => {
  try {
    const res = await request.get('/dashboard/trend', { params: { days: 7 } })
    renderTrendChart(res.data)
  } catch (err) {
    console.error('获取趋势数据失败:', err)
  }
}

const fetchRankings = async () => {
  try {
    const res = await request.get('/dashboard/rankings')
    rankings.value = res.data
  } catch (err) {
    console.error('获取排行榜失败:', err)
  }
}

const fetchRecentActivities = async () => {
  try {
    const res = await request.get('/dashboard/recent-activities')
    recentData.value = res.data
  } catch (err) {
    console.error('获取最近活动失败:', err)
  }
}

const renderTrendChart = (data: any[]) => {
  if (!trendChartRef.value) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const dates = data.map(d => d.date)
  const members = data.map(d => d.members)
  const reservations = data.map(d => d.reservations)
  const recharge = data.map(d => d.recharge)

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['新增会员', '预约数', '充值金额'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: [
      { type: 'value', name: '数量', position: 'left' },
      { type: 'value', name: '金额', position: 'right' }
    ],
    series: [
      { name: '新增会员', type: 'line', smooth: true, data: members, itemStyle: { color: '#409EFF' } },
      { name: '预约数', type: 'line', smooth: true, data: reservations, itemStyle: { color: '#67C23A' } },
      { name: '充值金额', type: 'bar', yAxisIndex: 1, data: recharge, itemStyle: { color: '#E6A23C' } }
    ]
  })
}

const handleResize = () => {
  trendChart?.resize()
}

onMounted(() => {
  fetchStats()
  fetchOverviewCards()
  fetchTrend()
  fetchRankings()
  fetchRecentActivities()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
})
</script>

<template>
  <div class="dashboard">
    <!-- 欢迎语 -->
    <div class="welcome-bar">
      <span>欢迎回来，{{ userStore.userInfo?.name }}！</span>
      <span class="date">{{ new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}</span>
    </div>

    <!-- 今日数据 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card primary">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><User /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today.members }}</div>
              <div class="stat-label">今日新增会员</div>
              <div class="stat-change" :class="stats.today.members_change >= 0 ? 'up' : 'down'">
                {{ stats.today.members_change >= 0 ? '+' : '' }}{{ stats.today.members_change }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card success">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><Calendar /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today.reservations }}</div>
              <div class="stat-label">今日预约数</div>
              <div class="stat-change" :class="stats.today.reservations_change >= 0 ? 'up' : 'down'">
                {{ stats.today.reservations_change >= 0 ? '+' : '' }}{{ stats.today.reservations_change }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card warning">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><Wallet /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today.recharge.toFixed(0) }}</div>
              <div class="stat-label">今日充值(元)</div>
              <div class="stat-change" :class="stats.today.recharge_change >= 0 ? 'up' : 'down'">
                {{ stats.today.recharge_change >= 0 ? '+' : '' }}{{ stats.today.recharge_change }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card danger">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><ShoppingCart /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today.orders }}</div>
              <div class="stat-label">今日订单数</div>
              <div class="stat-change" :class="stats.today.orders_change >= 0 ? 'up' : 'down'">
                {{ stats.today.orders_change >= 0 ? '+' : '' }}{{ stats.today.orders_change }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待处理事项 -->
    <el-row :gutter="16" class="todo-row">
      <el-col :span="6">
        <el-card shadow="hover" class="todo-card">
          <div class="todo-content">
            <span class="todo-value">{{ overviewCards.pending_reservations }}</span>
            <span class="todo-label">待处理预约</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="todo-card">
          <div class="todo-content">
            <span class="todo-value">{{ overviewCards.pending_food_orders }}</span>
            <span class="todo-label">待处理餐饮订单</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="todo-card">
          <div class="todo-content">
            <span class="todo-value">{{ overviewCards.pending_coach_apps }}</span>
            <span class="todo-label">待审核教练申请</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="todo-card">
          <div class="todo-content">
            <span class="todo-value">{{ overviewCards.today_activities }}</span>
            <span class="todo-label">今日活动</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图 -->
    <el-card class="chart-card">
      <template #header>近7天数据趋势</template>
      <div ref="trendChartRef" style="height: 300px;"></div>
    </el-card>

    <!-- 排行榜和最近动态 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header>热门场地 Top5</template>
          <div v-if="rankings.venues.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="ranking-list">
            <div class="ranking-item" v-for="(item, index) in rankings.venues" :key="item.id">
              <span class="ranking-index" :class="'top' + (Number(index) + 1)">{{ Number(index) + 1 }}</span>
              <span class="ranking-name">{{ item.name }}</span>
              <span class="ranking-value">{{ item.count }} 次</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>热门教练 Top5</template>
          <div v-if="rankings.coaches.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="ranking-list">
            <div class="ranking-item" v-for="(item, index) in rankings.coaches" :key="item.id">
              <span class="ranking-index" :class="'top' + (Number(index) + 1)">{{ Number(index) + 1 }}</span>
              <span class="ranking-name">{{ item.name }}</span>
              <span class="ranking-value">{{ item.count }} 次</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>活跃会员 Top5</template>
          <div v-if="rankings.members.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="ranking-list">
            <div class="ranking-item" v-for="(item, index) in rankings.members" :key="item.id">
              <span class="ranking-index" :class="'top' + (Number(index) + 1)">{{ Number(index) + 1 }}</span>
              <span class="ranking-name">{{ item.name }}</span>
              <span class="ranking-value">{{ item.amount }} 金币</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近动态 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="8">
        <el-card>
          <template #header>最近预约</template>
          <div v-if="recentData.reservations.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="recent-list">
            <div class="recent-item" v-for="item in recentData.reservations" :key="item.id">
              <div class="recent-main">
                <span class="recent-name">{{ item.member_name }}</span>
                <span class="recent-desc">预约了 {{ item.venue_name }}</span>
              </div>
              <div class="recent-time">{{ item.created_at }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>最近充值</template>
          <div v-if="recentData.recharges.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="recent-list">
            <div class="recent-item" v-for="item in recentData.recharges" :key="item.id">
              <div class="recent-main">
                <span class="recent-name">{{ item.member_name }}</span>
                <span class="recent-desc">充值 {{ item.amount }}元，获得 {{ item.coins }}金币</span>
              </div>
              <div class="recent-time">{{ item.pay_time }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>进行中活动</template>
          <div v-if="recentData.activities.length === 0" class="empty-tip">暂无数据</div>
          <div v-else class="recent-list">
            <div class="recent-item" v-for="item in recentData.activities" :key="item.id">
              <div class="recent-main">
                <span class="recent-name">{{ item.title }}</span>
                <span class="recent-desc">{{ item.current_participants }}/{{ item.max_participants || '不限' }}人</span>
              </div>
              <div class="recent-time">{{ item.start_time }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard { padding: 20px; }

.welcome-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
}
.welcome-bar .date { color: #909399; font-size: 14px; }

.stat-row { margin-bottom: 16px; }
.stat-card { border-radius: 8px; }
.stat-card.primary { border-left: 4px solid #409EFF; }
.stat-card.success { border-left: 4px solid #67C23A; }
.stat-card.warning { border-left: 4px solid #E6A23C; }
.stat-card.danger { border-left: 4px solid #F56C6C; }

.stat-content { display: flex; align-items: center; }
.stat-icon { font-size: 40px; margin-right: 16px; color: #409EFF; }
.stat-card.success .stat-icon { color: #67C23A; }
.stat-card.warning .stat-icon { color: #E6A23C; }
.stat-card.danger .stat-icon { color: #F56C6C; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.stat-change { font-size: 12px; margin-top: 4px; }
.stat-change.up { color: #67C23A; }
.stat-change.down { color: #F56C6C; }

.todo-row { margin-bottom: 16px; }
.todo-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.todo-card :deep(.el-card__body) { padding: 16px; }
.todo-content { display: flex; flex-direction: column; align-items: center; color: #fff; }
.todo-value { font-size: 32px; font-weight: bold; }
.todo-label { font-size: 13px; opacity: 0.9; margin-top: 4px; }

.chart-card { margin-bottom: 16px; }

.ranking-list { padding: 0; }
.ranking-item { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.ranking-item:last-child { border-bottom: none; }
.ranking-index {
  width: 24px; height: 24px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: bold; color: #fff; margin-right: 12px;
  background: #909399;
}
.ranking-index.top1 { background: #f7ba2a; }
.ranking-index.top2 { background: #909399; }
.ranking-index.top3 { background: #b87333; }
.ranking-name { flex: 1; font-size: 14px; }
.ranking-value { font-size: 13px; color: #409EFF; }

.recent-list { padding: 0; }
.recent-item { padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.recent-item:last-child { border-bottom: none; }
.recent-main { display: flex; align-items: center; gap: 8px; }
.recent-name { font-weight: 500; }
.recent-desc { color: #666; font-size: 13px; }
.recent-time { font-size: 12px; color: #999; margin-top: 4px; }

.empty-tip { text-align: center; color: #999; padding: 20px 0; }
</style>

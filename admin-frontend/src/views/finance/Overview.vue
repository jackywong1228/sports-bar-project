<template>
  <div class="page-container">
    <!-- 数据卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">今日充值</div>
          <div class="stat-value">{{ overview.today_recharge?.toFixed(2) || '0.00' }} <span class="unit">元</span></div>
          <div class="stat-desc">{{ overview.today_recharge_count || 0 }} 笔</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">本月充值</div>
          <div class="stat-value">{{ overview.month_recharge?.toFixed(2) || '0.00' }} <span class="unit">元</span></div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">今日消费</div>
          <div class="stat-value">{{ overview.today_consume?.toFixed(2) || '0.00' }} <span class="unit">金币</span></div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">本月消费</div>
          <div class="stat-value">{{ overview.month_consume?.toFixed(2) || '0.00' }} <span class="unit">金币</span></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-title">待结算（教练）</div>
          <div class="stat-value">{{ overview.pending_settlement?.toFixed(2) || '0.00' }} <span class="unit">元</span></div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success">
          <div class="stat-title">总会员数</div>
          <div class="stat-value">{{ overview.total_members || 0 }} <span class="unit">人</span></div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card info">
          <div class="stat-title">今日新增会员</div>
          <div class="stat-value">{{ overview.today_new_members || 0 }} <span class="unit">人</span></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>近7天财务趋势</span>
          <el-radio-group v-model="trendDays" size="small" @change="fetchTrend">
            <el-radio-button :value="7">近7天</el-radio-button>
            <el-radio-button :value="14">近14天</el-radio-button>
            <el-radio-button :value="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" style="height: 350px;"></div>
    </el-card>

    <!-- 消费分布 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>消费类型分布</template>
          <div ref="pieChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>消费统计</template>
          <el-table :data="consumeStats" stripe>
            <el-table-column prop="label" label="类型" />
            <el-table-column prop="amount" label="消费金额（金币）">
              <template #default="{ row }">{{ row.amount.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="count" label="订单数" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import request from '@/utils/request'
import * as echarts from 'echarts'

const overview = ref<any>({})
const trendDays = ref(7)
const trendData = ref<any[]>([])
const consumeStats = ref<any[]>([])

const chartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let pieChartInstance: echarts.ECharts | null = null

const fetchOverview = async () => {
  const res = await request.get('/finance/overview')
  overview.value = res.data
}

const fetchTrend = async () => {
  const res = await request.get('/finance/trend', { params: { days: trendDays.value } })
  trendData.value = res.data
  renderChart()
}

const fetchConsumeStats = async () => {
  const res = await request.get('/finance/consume/stats')
  consumeStats.value = res.data.by_type || []
  renderPieChart()
}

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = trendData.value.map(d => d.date)
  const rechargeData = trendData.value.map(d => d.recharge)
  const consumeData = trendData.value.map(d => d.consume)

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['充值金额', '消费金币'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value' },
    series: [
      { name: '充值金额', type: 'line', smooth: true, data: rechargeData, itemStyle: { color: '#409EFF' } },
      { name: '消费金币', type: 'line', smooth: true, data: consumeData, itemStyle: { color: '#67C23A' } }
    ]
  })
}

const renderPieChart = () => {
  if (!pieChartRef.value || !consumeStats.value.length) return

  if (!pieChartInstance) {
    pieChartInstance = echarts.init(pieChartRef.value)
  }

  const data = consumeStats.value.map(s => ({ name: s.label, value: s.amount }))

  pieChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      labelLine: { show: false },
      data
    }]
  })
}

const handleResize = () => {
  chartInstance?.resize()
  pieChartInstance?.resize()
}

onMounted(() => {
  fetchOverview()
  fetchTrend()
  fetchConsumeStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  pieChartInstance?.dispose()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.stat-cards { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-card .stat-title { color: #666; font-size: 14px; margin-bottom: 8px; }
.stat-card .stat-value { font-size: 28px; font-weight: bold; color: #409EFF; }
.stat-card .stat-value .unit { font-size: 14px; font-weight: normal; color: #999; }
.stat-card .stat-desc { font-size: 12px; color: #999; margin-top: 4px; }
.stat-card.warning .stat-value { color: #E6A23C; }
.stat-card.success .stat-value { color: #67C23A; }
.stat-card.info .stat-value { color: #909399; }
.chart-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

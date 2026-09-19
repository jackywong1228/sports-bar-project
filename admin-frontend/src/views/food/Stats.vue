<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" class="search-form">
        <el-form-item label="统计方式">
          <el-radio-group v-model="mode" @change="fetchStats">
            <el-radio-button value="daily">日结（按天）</el-radio-button>
            <el-radio-button value="range">自定义时间段</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="mode === 'daily'" label="日期">
          <el-date-picker
            v-model="statDate"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="fetchStats"
          />
        </el-form-item>
        <el-form-item v-else label="时间段">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 360px;"
          />
        </el-form-item>
        <el-form-item v-if="mode === 'range'">
          <el-button type="primary" @click="fetchStats">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading">
      <el-row :gutter="16" class="stat-cards">
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ stats?.valid_orders ?? '-' }}</div>
            <div class="stat-label">有效单数</div>
            <div class="stat-sub">总单数 {{ stats?.total_orders ?? 0 }} / 取消 {{ stats?.cancelled_orders ?? 0 }}</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value primary">¥{{ fmt(stats?.total_amount) }}</div>
            <div class="stat-label">营业额</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value warning">-¥{{ fmt(stats?.coupon_amount) }}</div>
            <div class="stat-label">优惠券抵扣</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value danger">¥{{ fmt(stats?.refund_amount) }}</div>
            <div class="stat-label">退款金额</div>
            <div class="stat-sub">退款 {{ stats?.refund_count ?? 0 }} 单</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ avgOrderAmount }}</div>
            <div class="stat-label">客单价</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value small">{{ stats?.start_time || '-' }}</div>
            <div class="stat-label">统计区间</div>
            <div class="stat-sub">至 {{ stats?.end_time || '-' }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="10">
          <el-card>
            <template #header><span>按支付方式统计（有效单）</span></template>
            <el-table :data="stats?.by_pay_type || []" size="small" border>
              <el-table-column prop="pay_type_text" label="支付方式" />
              <el-table-column prop="count" label="单数" width="100" />
              <el-table-column label="金额" width="140">
                <template #default="{ row }">¥{{ fmt(row.amount) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="stats && stats.by_pay_type.length === 0" description="暂无数据" :image-size="60" />
          </el-card>
        </el-col>
        <el-col :span="14">
          <el-card>
            <template #header><span>销量 TOP10 菜品</span></template>
            <div ref="chartRef" class="top-chart" v-show="(stats?.top_items?.length || 0) > 0"></div>
            <el-table :data="stats?.top_items || []" size="small" border>
              <el-table-column label="排名" width="70">
                <template #default="{ $index }">
                  <el-tag v-if="$index < 3" type="danger" size="small">{{ $index + 1 }}</el-tag>
                  <span v-else>{{ $index + 1 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="food_name" label="菜品" min-width="160" />
              <el-table-column prop="quantity" label="销量" width="90" />
              <el-table-column label="销售额" width="120">
                <template #default="{ row }">¥{{ fmt(row.amount) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="stats && stats.top_items.length === 0" description="暂无数据" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getFoodDailyStats, getFoodRangeStats, type FoodStats } from '@/api/food'

const mode = ref<'daily' | 'range'>('daily')
const statDate = ref<string>(new Date().toLocaleDateString('sv-SE')) // 本地时区 YYYY-MM-DD
const timeRange = ref<[string, string] | null>(null)
const loading = ref(false)
const stats = ref<FoodStats | null>(null)

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const fmt = (v: number | undefined | null): string => (v ?? 0).toFixed(2)

const avgOrderAmount = computed(() => {
  if (!stats.value || !stats.value.valid_orders) return '¥0.00'
  return `¥${(stats.value.total_amount / stats.value.valid_orders).toFixed(2)}`
})

const fetchStats = async () => {
  if (mode.value === 'range') {
    if (!timeRange.value || !timeRange.value[0] || !timeRange.value[1]) {
      ElMessage.warning('请选择统计时间段')
      return
    }
  }
  loading.value = true
  try {
    const res = mode.value === 'daily'
      ? await getFoodDailyStats(statDate.value)
      : await getFoodRangeStats(timeRange.value![0], timeRange.value![1])
    stats.value = res.data
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  const items = stats.value?.top_items || []
  if (!chartRef.value) return
  if (items.length === 0) {
    chartInstance?.dispose()
    chartInstance = null
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const sorted = [...items].reverse()
  chartInstance.setOption({
    grid: { left: 10, right: 40, top: 10, bottom: 10, containLabel: true },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: sorted.map(i => i.food_name),
      axisLabel: { width: 90, overflow: 'truncate' }
    },
    series: [{
      type: 'bar',
      data: sorted.map(i => i.quantity),
      itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right' },
      barMaxWidth: 22
    }],
    tooltip: { trigger: 'axis' }
  })
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.stat-cards { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-value { font-size: 26px; font-weight: 700; color: #303133; }
.stat-value.primary { color: #409eff; }
.stat-value.warning { color: #e6a23c; }
.stat-value.danger { color: #f56c6c; }
.stat-value.small { font-size: 14px; }
.stat-label { margin-top: 6px; color: #606266; font-size: 13px; }
.stat-sub { margin-top: 4px; color: #909399; font-size: 12px; }
.top-chart { width: 100%; height: 260px; margin-bottom: 12px; }
</style>

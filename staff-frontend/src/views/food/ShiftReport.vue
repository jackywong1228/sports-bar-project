<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getShiftReport, type ShiftReport } from '@/api/food'

const router = useRouter()

const loading = ref(false)
const report = ref<ShiftReport | null>(null)

// 时间范围（datetime-local 格式 YYYY-MM-DDTHH:MM）
const startInput = ref('')
const endInput = ref('')

function toLocalInput(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

function toApiTime(input: string, endOfMinute: 'start' | 'end'): string {
  // datetime-local → "YYYY-MM-DD HH:MM:SS"
  return `${input.replace('T', ' ')}:${endOfMinute === 'start' ? '00' : '59'}`
}

function setToday() {
  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)
  startInput.value = toLocalInput(start)
  endInput.value = toLocalInput(now)
}

function setYesterday() {
  const now = new Date()
  const start = new Date(now)
  start.setDate(start.getDate() - 1)
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setHours(23, 59, 0, 0)
  startInput.value = toLocalInput(start)
  endInput.value = toLocalInput(end)
}

function setLast7Days() {
  const now = new Date()
  const start = new Date(now)
  start.setDate(start.getDate() - 6)
  start.setHours(0, 0, 0, 0)
  startInput.value = toLocalInput(start)
  endInput.value = toLocalInput(now)
}

const fetchReport = async () => {
  if (!startInput.value || !endInput.value) return
  loading.value = true
  try {
    const res = await getShiftReport({
      start_time: toApiTime(startInput.value, 'start'),
      end_time: toApiTime(endInput.value, 'end')
    })
    report.value = res.data
  } finally {
    loading.value = false
  }
}

const onQuickRange = (fn: () => void) => {
  fn()
  fetchReport()
}

function fmtAmount(n: number | undefined | null): string {
  return `¥${(n || 0).toFixed(2)}`
}

const payTypeOrder = ['wechat', 'coin', 'cash']

function sortedPayTypes(list: ShiftReport['by_pay_type']) {
  return [...list].sort(
    (a, b) => payTypeOrder.indexOf(a.pay_type) - payTypeOrder.indexOf(b.pay_type)
  )
}

onMounted(() => {
  setToday()
  fetchReport()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="交班对账" left-arrow @click-left="router.back()" />

    <!-- 时间范围选择 -->
    <van-cell-group inset class="range-group">
      <van-field
        v-model="startInput"
        type="datetime-local"
        label="开始"
        @update:model-value="fetchReport"
      />
      <van-field
        v-model="endInput"
        type="datetime-local"
        label="结束"
        @update:model-value="fetchReport"
      />
      <div class="quick-ranges">
        <van-button size="small" round plain type="primary" @click="onQuickRange(setToday)">今天</van-button>
        <van-button size="small" round plain type="primary" @click="onQuickRange(setYesterday)">昨天</van-button>
        <van-button size="small" round plain type="primary" @click="onQuickRange(setLast7Days)">近7天</van-button>
        <van-button size="small" round type="primary" :loading="loading" @click="fetchReport">查询</van-button>
      </div>
    </van-cell-group>

    <div v-if="loading && !report" class="loading-wrap">
      <van-loading size="36" />
    </div>

    <template v-else-if="report">
      <!-- 统计时间范围 -->
      <div class="range-banner">
        统计范围：{{ report.start_time }} 至 {{ report.end_time }}
      </div>

      <!-- 总计 -->
      <van-cell-group inset class="info-group">
        <van-cell title="有效订单" :value="`${report.total_orders} 单`" />
        <van-cell title="营业额合计">
          <template #value>
            <span class="amount-highlight">{{ fmtAmount(report.total_amount) }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 按支付方式汇总 -->
      <van-cell-group inset title="按支付方式汇总" class="info-group">
        <van-cell v-for="p in sortedPayTypes(report.by_pay_type)" :key="p.pay_type" :title="p.pay_type_text">
          <template #value>
            <span class="pay-count">{{ p.count }} 单</span>
            <span class="pay-amount">{{ fmtAmount(p.amount) }}</span>
          </template>
        </van-cell>
        <van-cell v-if="report.by_pay_type.length === 0" title="该时段无有效订单" />
      </van-cell-group>

      <!-- 退款汇总 -->
      <van-cell-group inset title="退款汇总（按退款时间）" class="info-group">
        <van-cell title="退款单数" :value="`${report.refund_count} 单`" />
        <van-cell title="退款金额">
          <template #value>
            <span class="refund-amount">{{ fmtAmount(report.refund_amount) }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 订单明细 -->
      <van-cell-group inset :title="`订单明细（${report.orders.length}）`" class="info-group">
        <van-cell
          v-for="o in report.orders"
          :key="o.id"
          is-link
          @click="router.push(`/food/orders/${o.id}`)"
        >
          <template #title>
            <div class="detail-title">
              <span class="detail-no">#{{ (o.order_no || '').slice(-6) }}</span>
              <van-tag size="medium" plain type="primary">{{ o.pay_type_text }}</van-tag>
              <van-tag v-if="o.order_type === 'dine_in'" size="medium" plain>桌号{{ o.table_no || '-' }}</van-tag>
              <van-tag v-else size="medium" plain type="warning">{{ o.order_type_text }}</van-tag>
            </div>
          </template>
          <template #label>
            <div class="detail-meta">
              {{ o.member_id || o.member_name ? (o.member_name || '会员') : '散客' }} · {{ o.created_at }}
            </div>
          </template>
          <template #value>
            <span class="detail-amount">{{ fmtAmount(o.pay_amount) }}</span>
          </template>
        </van-cell>
        <van-cell v-if="report.orders.length === 0" title="该时段无订单" />
      </van-cell-group>
    </template>
  </div>
</template>

<style scoped>
.range-group {
  margin-top: 12px;
}

.quick-ranges {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.loading-wrap {
  padding: 60px 0;
  text-align: center;
}

.range-banner {
  margin: 12px 16px 0;
  padding: 10px 14px;
  background: #e8f0ea;
  color: var(--staff-primary);
  border-radius: 8px;
  font-size: 13px;
  text-align: center;
}

.info-group {
  margin-top: 12px;
}

.amount-highlight {
  color: #ee6723;
  font-weight: 700;
  font-size: 16px;
}

.pay-count {
  margin-right: 12px;
  color: #666;
}

.pay-amount {
  font-weight: 600;
  color: #333;
}

.refund-amount {
  color: #ee0a24;
  font-weight: 600;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.detail-no {
  font-weight: 600;
}

.detail-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.detail-amount {
  font-weight: 600;
  color: #ee6723;
}

/* iPad 横屏：汇总区两列 */
@media (min-width: 900px) {
  .info-group {
    max-width: 720px;
    margin-left: auto;
    margin-right: auto;
  }

  .range-group {
    max-width: 720px;
    margin-left: auto;
    margin-right: auto;
  }

  .range-banner {
    max-width: 688px;
    margin-left: auto;
    margin-right: auto;
  }
}
</style>

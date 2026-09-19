<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import {
  getStaffFoodOrders,
  acceptFoodOrder,
  readyFoodOrder,
  completeFoodOrder,
  type FoodOrder,
  type OrderPageResult,
  type SinceIdResult
} from '@/api/food'
import { playNotificationSound, vibrate } from '@/utils/notification'

const router = useRouter()

const statusMap: Record<string, { label: string; type: string }> = {
  paid: { label: '新订单', type: 'danger' },
  preparing: { label: '制作中', type: 'warning' },
  ready: { label: '待取餐', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已退款', type: 'default' }
}

const tabs = [
  { name: 'paid', label: '新订单' },
  { name: 'preparing', label: '制作中' },
  { name: 'ready', label: '待取餐' },
  { name: 'completed', label: '已完成' },
  { name: 'cancelled', label: '已退款' },
  { name: '', label: '全部' }
]

const activeTab = ref('paid')
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const list = ref<FoodOrder[]>([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// ── 新订单实时提醒（since_id 增量轮询）──
const autoRefresh = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null
const STORAGE_KEY = 'staff_food_order_last_max_id'
let lastMaxOrderId = 0
const POLL_INTERVAL = 12000 // 12 秒

// 顶部横幅
const banner = reactive({ show: false, count: 0 })
let bannerTimer: ReturnType<typeof setTimeout> | null = null

function loadLastMaxId(): number {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored ? parseInt(stored) : 0
}

function saveLastMaxId(id: number) {
  lastMaxOrderId = id
  localStorage.setItem(STORAGE_KEY, String(id))
}

function showBanner(count: number) {
  banner.count = count
  banner.show = true
  if (bannerTimer) clearTimeout(bannerTimer)
  bannerTimer = setTimeout(() => {
    banner.show = false
  }, 10000)
}

const fetchList = async (isLoadMore = false) => {
  if (!isLoadMore) {
    pagination.page = 1
    finished.value = false
  }
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (activeTab.value) params.status = activeTab.value
    const res = await getStaffFoodOrders(params)
    const data = res.data as OrderPageResult
    const items = data.items || []
    if (isLoadMore) {
      list.value.push(...items)
    } else {
      list.value = items
    }
    pagination.total = data.total || 0
    if (list.value.length >= pagination.total) {
      finished.value = true
    }
    // 首次加载后同步轮询基线，避免把历史订单当新单提醒
    if (lastMaxOrderId === 0 && items.length > 0) {
      saveLastMaxId(Math.max(...items.map((o) => o.id)))
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const onLoadMore = () => {
  pagination.page++
  fetchList(true)
}

const onRefresh = () => {
  fetchList()
}

const onTabChange = () => {
  list.value = []
  fetchList()
}

const goDetail = (id: number) => {
  router.push(`/food/orders/${id}`)
}

// ── 状态流转（无需二次确认，按钮颜色区分误操作）──
const actionLoading = ref(0)
const handleAction = async (item: FoodOrder) => {
  if (actionLoading.value) return
  actionLoading.value = item.id
  try {
    if (item.status === 'paid') {
      await acceptFoodOrder(item.id)
      showToast({ message: '已接单，开始制作', type: 'success' })
    } else if (item.status === 'preparing') {
      await readyFoodOrder(item.id)
      showToast({ message: '已出餐', type: 'success' })
    } else if (item.status === 'ready') {
      await completeFoodOrder(item.id)
      showToast({ message: '已交付', type: 'success' })
    }
    fetchList()
  } catch (_e) {
    // 拦截器已 toast
  } finally {
    actionLoading.value = 0
  }
}

// ── 增量轮询新订单 ──
async function checkNewOrders() {
  // 页面不可见时不提醒（也不刷新列表）
  if (document.visibilityState !== 'visible') return
  try {
    const res = await getStaffFoodOrders({ since_id: lastMaxOrderId })
    const data = res.data as SinceIdResult
    const newOrders = (data.items || []).filter((o) => o.status === 'paid')
    if (data.max_id > lastMaxOrderId) {
      saveLastMaxId(data.max_id)
    }
    if (newOrders.length > 0) {
      playNotificationSound()
      vibrate(300)
      showBanner(newOrders.length)
      fetchList()
    }
  } catch (_e) {
    // 忽略轮询错误
  }
}

function startPolling() {
  if (pollTimer) return
  if (lastMaxOrderId === 0) lastMaxOrderId = loadLastMaxId()
  pollTimer = setInterval(checkNewOrders, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const toggleRefresh = (val: boolean) => {
  if (val) {
    startPolling()
  } else {
    stopPolling()
    banner.show = false
  }
}

const onVisibilityChange = () => {
  if (document.visibilityState === 'visible' && autoRefresh.value) {
    checkNewOrders()
  }
}

const onBannerClick = () => {
  banner.show = false
  activeTab.value = 'paid'
  list.value = []
  fetchList()
}

// ── 展示辅助 ──
function orderTypeTag(o: FoodOrder): string {
  if (o.order_type === 'dine_in') {
    return `堂食 桌号${o.table_no || '-'}`
  }
  if (o.pickup_time) {
    // pickup_time 格式 YYYY-MM-DD HH:MM（或 HH:MM）
    const m = o.pickup_time.match(/(\d{2}:\d{2})/)
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    if (o.pickup_time.startsWith(todayStr) && m) {
      return `自取 预计${m[1]}`
    }
    return `自取 ${o.pickup_time.slice(5)}`
  }
  return o.order_type_text || '自取'
}

function customerLabel(o: FoodOrder): string {
  if (!o.member_id && !o.member_name) return '散客'
  const name = o.member_name || '会员'
  return o.member_phone ? `${name} ${o.member_phone}` : name
}

function fmtAmount(n: number | undefined | null): string {
  return `¥${(n || 0).toFixed(2)}`
}

onMounted(() => {
  fetchList()
  if (autoRefresh.value) startPolling()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  stopPolling()
  if (bannerTimer) clearTimeout(bannerTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="餐饮接单" left-arrow @click-left="router.back()">
      <template #right>
        <van-switch v-model="autoRefresh" size="20" @change="toggleRefresh" />
      </template>
    </van-nav-bar>

    <!-- 新订单顶部横幅 -->
    <transition name="van-slide-down">
      <div v-if="banner.show" class="new-order-banner" @click="onBannerClick">
        <van-icon name="volume-o" size="18" />
        <span>收到 {{ banner.count }} 个新订单，点击查看</span>
      </div>
    </transition>

    <van-tabs v-model:active="activeTab" sticky @change="onTabChange">
      <van-tab v-for="tab in tabs" :key="tab.name" :name="tab.name" :title="tab.label" />
    </van-tabs>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoadMore"
      >
        <van-cell-group v-for="item in list" :key="item.id" inset class="order-card">
          <van-cell :border="false" @click="goDetail(item.id)">
            <template #title>
              <div class="order-header">
                <span class="order-no">#{{ (item.order_no || '').slice(-6) }}</span>
                <van-tag type="primary" plain size="medium">{{ orderTypeTag(item) }}</van-tag>
                <van-tag :type="(statusMap[item.status]?.type as any) || 'default'" size="medium">
                  {{ statusMap[item.status]?.label || item.status_text }}
                </van-tag>
              </div>
            </template>
            <template #label>
              <div class="order-info">
                <div class="order-items-text">
                  <span v-for="(it, idx) in (item.items || [])" :key="idx" class="order-item-line">
                    {{ it.food_name }}<template v-if="it.specs_text">（{{ it.specs_text }}）</template> x{{ it.quantity }}
                  </span>
                </div>
                <div class="order-meta">
                  <span>{{ customerLabel(item) }}</span>
                  <span>{{ item.pay_type_text }}</span>
                  <span class="order-time">{{ item.created_at }}</span>
                </div>
                <div class="order-amount">{{ fmtAmount(item.pay_amount) }}</div>
              </div>
            </template>
          </van-cell>

          <!-- 操作按钮：颜色区分状态流转，避免误操作 -->
          <van-cell :border="false" v-if="['paid', 'preparing', 'ready'].includes(item.status)">
            <div class="order-actions">
              <van-button
                v-if="item.status === 'paid'"
                type="warning"
                size="small"
                round
                :loading="actionLoading === item.id"
                @click.stop="handleAction(item)"
              >接单</van-button>
              <van-button
                v-if="item.status === 'preparing'"
                type="primary"
                size="small"
                round
                :loading="actionLoading === item.id"
                @click.stop="handleAction(item)"
              >出餐</van-button>
              <van-button
                v-if="item.status === 'ready'"
                type="success"
                size="small"
                round
                :loading="actionLoading === item.id"
                @click.stop="handleAction(item)"
              >交付</van-button>
            </div>
          </van-cell>
        </van-cell-group>

        <van-empty v-if="!loading && list.length === 0" description="暂无订单" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.new-order-banner {
  position: fixed;
  top: 46px;
  left: 12px;
  right: 12px;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: #ee0a24;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(238, 10, 36, 0.35);
  cursor: pointer;
}

.order-card {
  margin-top: 12px;
}

.order-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.order-no {
  font-weight: 600;
  font-size: 16px;
  margin-right: auto;
}

.order-info {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.8;
}

.order-items-text {
  color: #333;
}

.order-item-line {
  display: inline-block;
  margin-right: 10px;
}

.order-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.order-time {
  color: #999;
  font-size: 12px;
}

.order-amount {
  color: #ee6723;
  font-weight: 600;
  font-size: 15px;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* iPad 横屏：卡片两列 */
@media (min-width: 900px) {
  .order-card {
    width: calc(50% - 20px);
    display: inline-block;
    vertical-align: top;
    margin-left: 4px;
    margin-right: 4px;
  }
}
</style>

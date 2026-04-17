<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { getFoodOrders, updateFoodOrderStatus } from '@/api/food'
import { playNotificationSound, vibrate } from '@/utils/notification'

const router = useRouter()

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'default' },
  paid: { label: '已支付', type: 'primary' },
  preparing: { label: '制作中', type: 'warning' },
  ready: { label: '待取餐', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const tabs = [
  { name: '', label: '全部' },
  { name: 'paid', label: '已支付' },
  { name: 'preparing', label: '制作中' },
  { name: 'ready', label: '待取餐' },
  { name: 'completed', label: '已完成' }
]

const activeTab = ref('')
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const list = ref<any[]>([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 新订单提醒
const autoRefresh = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null
const STORAGE_KEY = 'staff_food_order_last_max_id'
let lastMaxOrderId = 0

function loadLastMaxId(): number {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored ? parseInt(stored) : 0
}

function saveLastMaxId(id: number) {
  lastMaxOrderId = id
  localStorage.setItem(STORAGE_KEY, String(id))
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
    const res = await getFoodOrders(params)
    const data = res.data.list || []
    if (isLoadMore) {
      list.value.push(...data)
    } else {
      list.value = data
    }
    pagination.total = res.data.total || 0
    if (list.value.length >= pagination.total) {
      finished.value = true
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

const handleStatusChange = async (item: any, newStatus: string) => {
  const labelMap: Record<string, string> = {
    preparing: '开始制作',
    ready: '制作完成',
    completed: '已取餐',
    cancelled: '取消订单'
  }
  try {
    await showDialog({
      title: '确认操作',
      message: `确定要将订单标记为"${labelMap[newStatus]}"吗？`
    })
    await updateFoodOrderStatus(item.id, { status: newStatus })
    showToast({ message: '更新成功', type: 'success' })
    fetchList()
  } catch (_e) {
    // 取消操作
  }
}

// 轮询检查新订单
async function checkNewOrders() {
  try {
    const res = await getFoodOrders({ page: 1, page_size: 20 })
    const data: any[] = res.data.list || []
    if (data.length === 0) return

    const currentMaxId = Math.max(...data.map((o: any) => o.id))

    if (lastMaxOrderId === 0) {
      saveLastMaxId(currentMaxId)
      return
    }

    if (currentMaxId > lastMaxOrderId) {
      const newOrders = data.filter((o: any) =>
        o.id > lastMaxOrderId && o.status !== 'cancelled'
      )
      if (newOrders.length > 0) {
        playNotificationSound()
        vibrate(300)
        showToast({ message: `${newOrders.length}个新订单`, type: 'success', duration: 3000 })
        fetchList()
      }
      saveLastMaxId(currentMaxId)
    }
  } catch (_e) {
    // 忽略轮询错误
  }
}

function startPolling() {
  if (pollTimer) return
  lastMaxOrderId = loadLastMaxId()
  checkNewOrders()
  pollTimer = setInterval(checkNewOrders, 10000)
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
  }
}

onMounted(() => {
  fetchList()
  if (autoRefresh.value) startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="餐饮订单" left-arrow @click-left="router.back()">
      <template #right>
        <van-switch v-model="autoRefresh" size="20" @change="toggleRefresh" />
      </template>
    </van-nav-bar>

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
                <van-tag :type="(statusMap[item.status]?.type as any) || 'default'" size="medium">
                  {{ statusMap[item.status]?.label || item.status }}
                </van-tag>
              </div>
            </template>
            <template #label>
              <div class="order-info">
                <div>{{ item.member_nickname || '会员' }} | 桌号: {{ item.table_no || '-' }}</div>
                <div class="order-amount">{{ item.pay_amount }} 金币</div>
                <div class="order-time">{{ item.created_at }}</div>
              </div>
            </template>
          </van-cell>

          <!-- 操作按钮 -->
          <van-cell :border="false" v-if="item.status !== 'completed' && item.status !== 'cancelled' && item.status !== 'pending'">
            <div class="order-actions">
              <van-button
                v-if="item.status === 'paid'"
                type="warning"
                size="small"
                round
                @click.stop="handleStatusChange(item, 'preparing')"
              >开始制作</van-button>
              <van-button
                v-if="item.status === 'preparing'"
                type="success"
                size="small"
                round
                @click.stop="handleStatusChange(item, 'ready')"
              >制作完成</van-button>
              <van-button
                v-if="item.status === 'ready'"
                type="primary"
                size="small"
                round
                @click.stop="handleStatusChange(item, 'completed')"
              >已取餐</van-button>
            </div>
          </van-cell>
        </van-cell-group>

        <van-empty v-if="!loading && list.length === 0" description="暂无订单" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.order-card {
  margin-top: 12px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-no {
  font-weight: 600;
  font-size: 16px;
}

.order-info {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.8;
}

.order-amount {
  color: #ee6723;
  font-weight: 600;
}

.order-time {
  color: #999;
  font-size: 12px;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>

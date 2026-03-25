<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="订单号/桌号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="制作中" value="preparing" />
            <el-option label="待取餐" value="ready" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
        <el-form-item style="margin-left: auto;">
          <el-switch
            v-model="autoRefresh"
            active-text="新订单提醒"
            @change="toggleAutoRefresh"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span>餐饮订单</span>
          <el-tag v-if="autoRefresh" type="success" size="small" effect="light">
            自动刷新中 (15s)
          </el-tag>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe :row-class-name="rowClassName">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="member_nickname" label="会员" width="120" />
        <el-table-column prop="table_no" label="桌号" width="80" />
        <el-table-column prop="total_amount" label="总金额" width="100" />
        <el-table-column prop="pay_amount" label="实付金额" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" />
        <el-table-column prop="created_at" label="下单时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-dropdown v-if="row.status !== 'completed' && row.status !== 'cancelled'" trigger="click" @command="(cmd: string) => handleStatusChange(row, cmd)">
              <el-button link type="primary">更新状态</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="row.status === 'paid'" command="preparing">开始制作</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 'preparing'" command="ready">制作完成</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 'ready'" command="completed">已取餐</el-dropdown-item>
                  <el-dropdown-item v-if="row.status !== 'completed'" command="cancelled">取消订单</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单号">{{ detail.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMap[detail.status]?.type">{{ statusMap[detail.status]?.label }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员">{{ detail.member_nickname }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detail.member_phone }}</el-descriptions-item>
        <el-descriptions-item label="桌号">{{ detail.table_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ detail.created_at }}</el-descriptions-item>
        <el-descriptions-item label="总金额">{{ detail.total_amount }} 金币</el-descriptions-item>
        <el-descriptions-item label="实付金额">{{ detail.pay_amount }} 金币</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 20px;">
        <div style="font-weight: bold; margin-bottom: 10px;">商品明细</div>
        <el-table :data="detail.items" border size="small">
          <el-table-column label="商品" min-width="150">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-image v-if="row.food_image" :src="row.food_image" fit="cover" style="width: 40px; height: 40px;" />
                <span>{{ row.food_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="单价" width="80" />
          <el-table-column prop="quantity" label="数量" width="70" />
          <el-table-column prop="subtotal" label="小计" width="80" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import request from '@/utils/request'

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'info' },
  paid: { label: '已支付', type: '' },
  preparing: { label: '制作中', type: 'warning' },
  ready: { label: '待取餐', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const detailVisible = ref(false)
const detail = ref<any>({})

// ==================== 新订单提醒 ====================
const autoRefresh = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null
let lastMaxOrderId = 0  // 追踪最大订单 ID（比总数更可靠）
let isFirstPoll = true
let newOrderIds = new Set<number>()

// 用 Web Audio API 生成提示音（无需音频文件）
function playNotificationSound() {
  try {
    const ctx = new AudioContext()
    const playTone = (freq: number, startTime: number, duration: number) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0.4, startTime)
      gain.gain.exponentialRampToValueAtTime(0.01, startTime + duration)
      osc.start(startTime)
      osc.stop(startTime + duration)
    }
    const now = ctx.currentTime
    // 三声上升音调，重复两遍更醒目
    for (let round = 0; round < 2; round++) {
      const offset = round * 0.6
      playTone(880, now + offset, 0.15)
      playTone(1100, now + offset + 0.18, 0.15)
      playTone(1320, now + offset + 0.36, 0.2)
    }
  } catch (e) {
    console.warn('无法播放提示音:', e)
  }
}

// 高亮新订单行
const rowClassName = ({ row }: { row: any }) => {
  return newOrderIds.has(row.id) ? 'new-order-highlight' : ''
}

// 轮询检查新订单（基于最大订单 ID，不受状态变更影响）
async function checkNewOrders() {
  try {
    // 查询所有状态的最新订单（按 ID 倒序，取前 10 条）
    const res = await request.get('/foods/orders', {
      params: { page: 1, page_size: 10 }
    })
    const list: any[] = res.data.list || []
    if (list.length === 0) return

    // 找到当前最大订单 ID
    const currentMaxId = Math.max(...list.map((o: any) => o.id))

    if (isFirstPoll) {
      // 首次加载：仅记录当前最大 ID，不触发通知
      lastMaxOrderId = currentMaxId
      isFirstPoll = false
      console.log('[订单提醒] 初始化，当前最大订单ID:', lastMaxOrderId)
      return
    }

    if (currentMaxId > lastMaxOrderId) {
      // 找出所有新订单（ID > lastMaxOrderId 且状态为需要处理的）
      const newOrders = list.filter((o: any) =>
        o.id > lastMaxOrderId && o.status !== 'cancelled'
      )

      if (newOrders.length > 0) {
        console.log('[订单提醒] 发现新订单:', newOrders.map((o: any) => o.id))

        // 标记新订单 ID 用于高亮
        newOrders.forEach((o: any) => newOrderIds.add(o.id))

        // 播放提示音
        playNotificationSound()

        // 弹窗提醒（显示每个新订单）
        newOrders.forEach((order: any) => {
          const statusLabel = statusMap[order.status]?.label || order.status
          ElNotification({
            title: '新订单提醒',
            message: `#${order.order_no.slice(-6)} | 桌号: ${order.table_no || '-'} | ${order.member_nickname || '会员'} | ${order.pay_amount}金币 | ${statusLabel}`,
            type: 'warning',
            duration: 15000,
            position: 'top-right'
          })
        })

        // 刷新当前列表
        fetchList()

        // 8秒后取消高亮
        setTimeout(() => {
          newOrderIds.clear()
          tableData.value = [...tableData.value]
        }, 8000)
      }

      lastMaxOrderId = currentMaxId
    }
  } catch (e) {
    // 静默失败，不影响用户操作
    console.warn('[订单提醒] 轮询失败:', e)
  }
}

function startPolling() {
  if (pollTimer) return
  isFirstPoll = true
  checkNewOrders()
  pollTimer = setInterval(checkNewOrders, 10000) // 10秒轮询
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function toggleAutoRefresh(val: boolean) {
  if (val) {
    startPolling()
  } else {
    stopPolling()
  }
}

// ==================== 基础功能 ====================

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/foods/orders', {
      params: { page: pagination.page, page_size: pagination.pageSize, ...searchForm }
    })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  fetchList()
}

const handleDetail = async (row: any) => {
  const res = await request.get(`/foods/orders/${row.id}`)
  detail.value = res.data
  detailVisible.value = true
}

const handleStatusChange = async (row: any, status: string) => {
  await request.put(`/foods/orders/${row.id}/status`, { status })
  ElMessage.success('状态更新成功')
  fetchList()
}

onMounted(() => {
  fetchList()
  if (autoRefresh.value) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
</style>

<style>
/* 新订单高亮动画（全局样式，不能 scoped） */
.new-order-highlight td {
  animation: orderFlash 1s ease-in-out 3;
}

@keyframes orderFlash {
  0%, 100% { background-color: transparent; }
  50% { background-color: #fef0e0; }
}
</style>

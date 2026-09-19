<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="订单号/桌号/姓名/手机号" clearable style="width: 200px;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px;">
            <el-option v-for="(v, k) in statusMap" :key="k" :label="v.label" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="searchForm.pay_type" placeholder="全部" clearable style="width: 110px;">
            <el-option label="微信" value="wechat" />
            <el-option label="金币" value="coin" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="订单类型">
          <el-select v-model="searchForm.order_type" placeholder="全部" clearable style="width: 120px;">
            <el-option label="立即取餐" value="immediate" />
            <el-option label="预约取餐" value="scheduled" />
            <el-option label="堂食" value="dine_in" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px;"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <span>餐饮订单</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column label="顾客" width="120">
          <template #default="{ row }">
            <div>{{ row.member_name || '散客' }}</div>
            <div v-if="row.member_phone" class="sub-text">{{ row.member_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="桌号/取餐" width="130">
          <template #default="{ row }">
            <div v-if="row.table_no">桌号 {{ row.table_no }}</div>
            <div v-if="row.pickup_time" class="sub-text">{{ row.pickup_time }}</div>
            <span v-if="!row.table_no && !row.pickup_time">{{ row.order_type_text }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实付金额" width="100">
          <template #default="{ row }">
            <span class="price">¥{{ row.pay_amount.toFixed(2) }}</span>
            <div v-if="row.coupon_amount > 0" class="sub-text">券抵 ¥{{ row.coupon_amount.toFixed(2) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="支付方式" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.pay_type" size="small" :type="payTypeTagType(row.pay_type)">
              {{ row.pay_type_text }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type" size="small">
              {{ row.status_text || statusMap[row.status]?.label }}
            </el-tag>
            <div v-if="row.refund_amount > 0" class="sub-text refund-text">已退 ¥{{ row.refund_amount.toFixed(2) }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" width="170" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-button
              v-if="canRefund(row)"
              link
              type="danger"
              @click="handleRefund(row)"
            >退款</el-button>
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

    <!-- 订单详情抽屉 -->
    <el-drawer v-model="detailVisible" title="订单详情" size="560px">
      <div v-loading="detailLoading" class="order-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单号" :span="2">{{ detail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusMap[detail.status]?.type" size="small">{{ detail.status_text }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="订单类型">{{ detail.order_type_text }}</el-descriptions-item>
          <el-descriptions-item label="顾客">{{ detail.member_name || '散客' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.member_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="桌号">{{ detail.table_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="取餐时间">{{ detail.pickup_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.created_at }}</el-descriptions-item>
          <el-descriptions-item label="支付时间">{{ detail.pay_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="完成时间" :span="2">{{ detail.complete_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">商品明细</h4>
        <el-table :data="detail.items || []" size="small" border>
          <el-table-column label="商品" min-width="180">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-image v-if="row.food_image" :src="row.food_image" fit="cover" style="width: 36px; height: 36px; border-radius: 4px;" />
                <div>
                  <div>{{ row.food_name }}</div>
                  <div v-if="row.specs_text" class="sub-text">{{ row.specs_text }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="90">
            <template #default="{ row }">¥{{ row.price.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="60" />
          <el-table-column label="小计" width="90">
            <template #default="{ row }">¥{{ row.subtotal.toFixed(2) }}</template>
          </el-table-column>
        </el-table>

        <h4 class="section-title">金额信息</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单总额">¥{{ (detail.total_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="优惠券抵扣">-¥{{ (detail.coupon_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="实付金额">
            <span class="price">¥{{ (detail.pay_amount || 0).toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="支付方式">{{ detail.pay_type_text || '-' }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="detail.refund_amount > 0">
          <h4 class="section-title">退款信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="退款金额">¥{{ detail.refund_amount.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="退款原因">{{ detail.refund_reason || '-' }}</el-descriptions-item>
            <el-descriptions-item label="退款时间">{{ detail.refund_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="操作人">{{ detail.refund_by || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>

        <div class="drawer-footer">
          <el-dropdown
            trigger="click"
            style="margin-right: 10px"
            @command="(t: 'cashier' | 'kitchen') => handleReprint(detail, t)"
          >
            <el-button :loading="reprinting">重打小票</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="cashier">收银票</el-dropdown-item>
                <el-dropdown-item command="kitchen">制作单</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            v-if="canRefund(detail)"
            type="danger"
            @click="handleRefund(detail)"
          >人工退款</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 退款弹窗 -->
    <el-dialog v-model="refundVisible" title="人工退款" width="520px" destroy-on-close>
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
        <template #title>
          <div>订单 {{ refundOrder?.order_no }}，实付 ¥{{ (refundOrder?.pay_amount || 0).toFixed(2) }}</div>
          <div style="margin-top: 4px;">{{ refundMethodTip }}</div>
          <div style="margin-top: 4px;">退款后库存自动回补、优惠券退回（未过期）。</div>
        </template>
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="退款原因" required>
          <el-input
            v-model="refundReason"
            type="textarea"
            :rows="3"
            placeholder="请填写退款原因（必填，将记录到订单）"
            maxlength="500"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundVisible = false">取消</el-button>
        <el-button type="danger" @click="handleRefundSubmit" :loading="refunding">确认退款</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getFoodOrders,
  getFoodOrderDetail,
  refundFoodOrder,
  reprintFoodOrder,
  type FoodOrder
} from '@/api/food'

const statusMap: Record<string, { label: string; type: string }> = {
  unpaid: { label: '待支付', type: 'warning' },
  pending: { label: '待确认', type: 'warning' },
  paid: { label: '已支付', type: 'primary' },
  preparing: { label: '制作中', type: 'primary' },
  ready: { label: '待取餐', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' }
}

const loading = ref(false)
const tableData = ref<FoodOrder[]>([])
const searchForm = reactive({ keyword: '', status: '', pay_type: '', order_type: '' })
const dateRange = ref<[string, string] | null>(null)
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<FoodOrder>({} as FoodOrder)

const refundVisible = ref(false)
const refunding = ref(false)
const refundOrder = ref<FoodOrder | null>(null)
const refundReason = ref('')
const reprinting = ref(false)

const payTypeTagType = (payType: string): string => {
  const map: Record<string, string> = { wechat: 'success', coin: 'warning', cash: 'info' }
  return map[payType] || 'info'
}

// 已支付/制作中/待取餐/已完成 才允许人工退款
const canRefund = (row: Partial<FoodOrder>): boolean => {
  return ['paid', 'preparing', 'ready', 'completed'].includes(row.status || '') && !(row.refund_amount && row.refund_amount > 0)
}

const refundMethodTip = computed(() => {
  const pt = refundOrder.value?.pay_type
  if (pt === 'wechat') return '退款方式：微信支付原路退回（1-3 个工作日到账）'
  if (pt === 'coin') return '退款方式：金币自动退回会员账户'
  if (pt === 'cash') return '退款方式：现金单仅记账，请线下退还现金'
  return '零元订单无需实际退款'
})

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.status) params.status = searchForm.status
    if (searchForm.pay_type) params.pay_type = searchForm.pay_type
    if (searchForm.order_type) params.order_type = searchForm.order_type
    if (dateRange.value && dateRange.value[0]) params.start_date = dateRange.value[0]
    if (dateRange.value && dateRange.value[1]) params.end_date = dateRange.value[1]
    const res = await getFoodOrders(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.pay_type = ''
  searchForm.order_type = ''
  dateRange.value = null
  pagination.page = 1
  fetchList()
}

const handleDetail = async (row: FoodOrder) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getFoodOrderDetail(row.id)
    detail.value = res.data
  } finally {
    detailLoading.value = false
  }
}

const handleRefund = (row: FoodOrder) => {
  refundOrder.value = row
  refundReason.value = ''
  refundVisible.value = true
}

// 重打小票（收银票/制作单，按打印机角色分发）
const handleReprint = async (row: FoodOrder, ticketType: 'cashier' | 'kitchen') => {
  if (!row.id) return
  reprinting.value = true
  try {
    await reprintFoodOrder(row.id, ticketType)
    ElMessage.success(`${ticketType === 'cashier' ? '收银票' : '制作单'}重打已发送`)
  } catch {
    // 报错提示由拦截器统一处理
  } finally {
    reprinting.value = false
  }
}

const handleRefundSubmit = async () => {
  if (!refundReason.value.trim()) {
    ElMessage.error('请填写退款原因')
    return
  }
  if (!refundOrder.value) return
  try {
    await ElMessageBox.confirm(
      `确认对订单 ${refundOrder.value.order_no} 退款 ¥${refundOrder.value.pay_amount.toFixed(2)} 吗？${refundMethodTip.value}`,
      '退款二次确认',
      { type: 'warning', confirmButtonText: '确认退款', cancelButtonText: '再想想' }
    )
  } catch {
    return
  }
  refunding.value = true
  try {
    const res = await refundFoodOrder(refundOrder.value.id, refundReason.value.trim())
    ElMessage.success((res as any).message || '退款处理完成')
    refundVisible.value = false
    // 刷新详情与列表
    if (detailVisible.value && detail.value.id === refundOrder.value.id) {
      const d = await getFoodOrderDetail(refundOrder.value.id)
      detail.value = d.data
    }
    fetchList()
  } finally {
    refunding.value = false
  }
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.price { color: #f56c6c; font-weight: 600; }
.sub-text { color: #909399; font-size: 12px; }
.refund-text { color: #f56c6c; }
.section-title { margin: 18px 0 10px; font-size: 14px; color: #303133; }
.order-detail { padding-bottom: 20px; }
.drawer-footer { margin-top: 24px; text-align: right; }
</style>

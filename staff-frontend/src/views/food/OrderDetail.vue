<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import {
  getStaffFoodOrderDetail,
  acceptFoodOrder,
  readyFoodOrder,
  completeFoodOrder,
  refundFoodOrder,
  type FoodOrder
} from '@/api/food'

const route = useRoute()
const router = useRouter()

const order = ref<FoodOrder | null>(null)
const loading = ref(true)

const statusMap: Record<string, { label: string; type: string }> = {
  paid: { label: '新订单', type: 'danger' },
  preparing: { label: '制作中', type: 'warning' },
  ready: { label: '待取餐', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已退款', type: 'default' }
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getStaffFoodOrderDetail(id)
    order.value = res.data
  } finally {
    loading.value = false
  }
}

// ── 状态流转 ──
const actionLoading = ref(false)
const handleAction = async () => {
  if (!order.value || actionLoading.value) return
  actionLoading.value = true
  try {
    const id = order.value.id
    if (order.value.status === 'paid') {
      await acceptFoodOrder(id)
      showToast({ message: '已接单，开始制作', type: 'success' })
    } else if (order.value.status === 'preparing') {
      await readyFoodOrder(id)
      showToast({ message: '已出餐', type: 'success' })
    } else if (order.value.status === 'ready') {
      await completeFoodOrder(id)
      showToast({ message: '已交付', type: 'success' })
    }
    await fetchDetail()
  } catch (_e) {
    // 拦截器已 toast
  } finally {
    actionLoading.value = false
  }
}

// ── 人工退款 ──
const refundVisible = ref(false)
const refundReason = ref('')
const refundLoading = ref(false)

const refundNote = computed(() => {
  const pt = order.value?.pay_type
  if (pt === 'wechat') return '微信支付订单：退款将原路退回顾客微信。'
  if (pt === 'coin') return '金币支付订单：退款将退回会员金币余额。'
  if (pt === 'cash') return '现金支付订单：系统仅记账，需线下退还顾客现金。'
  return '请按支付方式人工处理退款。'
})

const canRefund = computed(() => {
  return order.value && order.value.status !== 'cancelled'
})

const openRefund = () => {
  refundReason.value = ''
  refundVisible.value = true
}

const submitRefund = async () => {
  if (!order.value || refundLoading.value) return
  try {
    await showConfirmDialog({
      title: '确认退款',
      message: `订单金额 ¥${order.value.pay_amount.toFixed(2)}\n${refundNote.value}\n确认执行人工退款？`,
      confirmButtonText: '确认退款',
      confirmButtonColor: '#ee0a24'
    })
  } catch (_e) {
    return // 取消
  }
  refundLoading.value = true
  try {
    await refundFoodOrder(order.value.id, refundReason.value.trim() || '收银台人工退款')
    showToast({ message: '退款处理完成', type: 'success' })
    refundVisible.value = false
    await fetchDetail()
  } catch (_e) {
    // 拦截器已 toast
  } finally {
    refundLoading.value = false
  }
}

function fmtAmount(n: number | undefined | null): string {
  return `¥${(n || 0).toFixed(2)}`
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="订单详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" style="padding: 40px; text-align: center;">
      <van-loading size="36" />
    </div>

    <template v-else-if="order">
      <!-- 状态区域 -->
      <div class="status-section">
        <van-tag :type="(statusMap[order.status]?.type as any) || 'default'" size="large">
          {{ statusMap[order.status]?.label || order.status_text }}
        </van-tag>
        <div class="order-no">订单号: {{ order.order_no }}</div>
      </div>

      <!-- 订单信息 -->
      <van-cell-group inset title="订单信息" class="info-group">
        <van-cell title="类型">
          <template #value>
            {{ order.order_type_text }}
            <template v-if="order.order_type === 'dine_in' && order.table_no"> · 桌号 {{ order.table_no }}</template>
            <template v-if="order.order_type !== 'dine_in' && order.pickup_time"> · {{ order.pickup_time }}</template>
          </template>
        </van-cell>
        <van-cell title="顾客" :value="order.member_id || order.member_name ? (order.member_name || '会员') : '散客'" />
        <van-cell title="联系电话" :value="order.member_phone || '-'" />
        <van-cell title="下单时间" :value="order.created_at || '-'" />
        <van-cell title="支付方式" :value="order.pay_type_text" />
        <van-cell title="支付时间" :value="order.pay_time || '-'" />
        <van-cell v-if="order.complete_time" title="完成时间" :value="order.complete_time" />
        <van-cell title="总金额" :value="fmtAmount(order.total_amount)" />
        <van-cell v-if="order.discount_amount > 0" title="优惠" :value="`- ${fmtAmount(order.discount_amount)}`" />
        <van-cell title="实付金额">
          <template #value>
            <span class="amount-highlight">{{ fmtAmount(order.pay_amount) }}</span>
          </template>
        </van-cell>
        <van-cell v-if="order.remark" title="备注" :value="order.remark" />
        <van-cell v-if="order.handled_by" title="操作员工" :value="order.handled_by" />
      </van-cell-group>

      <!-- 退款信息 -->
      <van-cell-group v-if="order.status === 'cancelled'" inset title="退款信息" class="info-group">
        <van-cell title="退款金额" :value="fmtAmount(order.refund_amount)" />
        <van-cell title="退款原因" :value="order.refund_reason || '-'" />
        <van-cell title="退款时间" :value="order.refund_time || '-'" />
        <van-cell title="退款操作人" :value="order.refund_by || '-'" />
      </van-cell-group>

      <!-- 商品明细 -->
      <van-cell-group inset title="商品明细" class="info-group">
        <van-cell v-for="(item, index) in (order.items || [])" :key="index">
          <template #title>
            <div class="food-item">
              <van-image
                v-if="item.food_image"
                :src="item.food_image"
                width="40"
                height="40"
                radius="4"
                fit="cover"
              />
              <div class="food-info">
                <div class="food-name">{{ item.food_name }}</div>
                <div v-if="item.specs_text" class="food-specs">{{ item.specs_text }}</div>
                <div class="food-price">{{ fmtAmount(item.price) }} x {{ item.quantity }}</div>
              </div>
              <div class="food-subtotal">{{ fmtAmount(item.subtotal) }}</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 底部操作按钮 -->
      <div class="bottom-actions">
        <template v-if="['paid', 'preparing', 'ready'].includes(order.status)">
          <van-button
            v-if="order.status === 'paid'"
            type="warning"
            block
            round
            size="large"
            :loading="actionLoading"
            @click="handleAction"
          >接单（开始制作）</van-button>
          <van-button
            v-if="order.status === 'preparing'"
            type="primary"
            block
            round
            size="large"
            :loading="actionLoading"
            @click="handleAction"
          >出餐（待取餐）</van-button>
          <van-button
            v-if="order.status === 'ready'"
            type="success"
            block
            round
            size="large"
            :loading="actionLoading"
            @click="handleAction"
          >交付（完成）</van-button>
        </template>
        <van-button
          v-if="canRefund"
          type="danger"
          plain
          block
          round
          size="large"
          style="margin-top: 8px;"
          @click="openRefund"
        >人工退款</van-button>
      </div>
      <div style="height: 120px;"></div>
    </template>

    <!-- 退款弹窗 -->
    <van-dialog
      v-model:show="refundVisible"
      title="人工退款"
      show-cancel-button
      :confirm-button-loading="refundLoading"
      confirm-button-text="提交退款"
      confirm-button-color="#ee0a24"
      :before-close="(action: string) => { if (action === 'confirm') { submitRefund(); return false } return true }"
    >
      <div class="refund-dialog-body">
        <van-notice-bar
          wrapable
          :scrollable="false"
          :text="refundNote"
          color="#ed6a0c"
          background="#fffbe8"
        />
        <van-field
          v-model="refundReason"
          rows="3"
          autosize
          type="textarea"
          maxlength="200"
          placeholder="退款原因（必填，如：顾客取消/商品售罄）"
          show-word-limit
        />
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.status-section {
  background: #fff;
  padding: 20px 16px;
  text-align: center;
}

.order-no {
  margin-top: 8px;
  font-size: 13px;
  color: #999;
}

.info-group {
  margin-top: 12px;
}

.amount-highlight {
  color: #ee6723;
  font-weight: 600;
}

.food-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.food-info {
  flex: 1;
}

.food-name {
  font-size: 14px;
  font-weight: 500;
}

.food-specs {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.food-price {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.food-subtotal {
  font-weight: 600;
  color: #333;
}

.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}

@media (min-width: 900px) {
  .bottom-actions {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
  }
}

.refund-dialog-body {
  padding: 8px 16px 16px;
}
</style>

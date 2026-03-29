<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { getFoodOrderDetail, updateFoodOrderStatus } from '@/api/food'

const route = useRoute()
const router = useRouter()

const order = ref<any>({})
const loading = ref(true)

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'default' },
  paid: { label: '已支付', type: 'primary' },
  preparing: { label: '制作中', type: 'warning' },
  ready: { label: '待取餐', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getFoodOrderDetail(id)
    order.value = res.data
  } finally {
    loading.value = false
  }
}

const handleStatusChange = async (newStatus: string) => {
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
    await updateFoodOrderStatus(order.value.id, { status: newStatus })
    showToast({ message: '更新成功', type: 'success' })
    fetchDetail()
  } catch (_e) {
    // 取消操作
  }
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

    <template v-else>
      <!-- 状态区域 -->
      <div class="status-section">
        <van-tag :type="(statusMap[order.status]?.type as any) || 'default'" size="large">
          {{ statusMap[order.status]?.label || order.status }}
        </van-tag>
        <div class="order-no">订单号: {{ order.order_no }}</div>
      </div>

      <!-- 订单信息 -->
      <van-cell-group inset title="订单信息" class="info-group">
        <van-cell title="会员" :value="order.member_nickname || '-'" />
        <van-cell title="联系电话" :value="order.member_phone || '-'" />
        <van-cell title="桌号" :value="order.table_no || '-'" />
        <van-cell title="下单时间" :value="order.created_at" />
        <van-cell title="总金额" :value="`${order.total_amount} 金币`" />
        <van-cell title="实付金额">
          <template #value>
            <span class="amount-highlight">{{ order.pay_amount }} 金币</span>
          </template>
        </van-cell>
        <van-cell v-if="order.remark" title="备注" :value="order.remark" />
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
                <div class="food-price">{{ item.price }} x {{ item.quantity }}</div>
              </div>
              <div class="food-subtotal">{{ item.subtotal }}</div>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 底部操作按钮 -->
      <div class="bottom-actions" v-if="order.status !== 'completed' && order.status !== 'cancelled' && order.status !== 'pending'">
        <van-button
          v-if="order.status === 'paid'"
          type="warning"
          block
          round
          size="large"
          @click="handleStatusChange('preparing')"
        >开始制作</van-button>
        <van-button
          v-if="order.status === 'preparing'"
          type="success"
          block
          round
          size="large"
          @click="handleStatusChange('ready')"
        >制作完成</van-button>
        <van-button
          v-if="order.status === 'ready'"
          type="primary"
          block
          round
          size="large"
          @click="handleStatusChange('completed')"
        >已取餐</van-button>
      </div>
    </template>
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
</style>

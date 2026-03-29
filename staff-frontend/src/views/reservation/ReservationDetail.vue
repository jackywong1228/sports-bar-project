<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { getReservationDetail, confirmReservation, completeReservation, updateReservationStatus } from '@/api/reservation'

const route = useRoute()
const router = useRouter()

const detail = ref<any>({})
const loading = ref(true)

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待确认', type: 'warning' },
  confirmed: { label: '已确认', type: 'primary' },
  in_progress: { label: '使用中', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getReservationDetail(id)
    detail.value = res.data
  } finally {
    loading.value = false
  }
}

const handleConfirm = async () => {
  try {
    await showDialog({ title: '确认操作', message: '确定要确认该预约吗？' })
    await confirmReservation(detail.value.id)
    showToast({ message: '已确认', type: 'success' })
    fetchDetail()
  } catch (_e) { /* 取消 */ }
}

const handleComplete = async () => {
  try {
    await showDialog({ title: '确认操作', message: '确定要标记为已完成吗？' })
    await completeReservation(detail.value.id)
    showToast({ message: '已完成', type: 'success' })
    fetchDetail()
  } catch (_e) { /* 取消 */ }
}

const handleCancel = async () => {
  try {
    await showDialog({ title: '确认取消', message: '确定要取消该预约吗？' })
    await updateReservationStatus(detail.value.id, { status: 'cancelled' })
    showToast({ message: '已取消', type: 'success' })
    fetchDetail()
  } catch (_e) { /* 取消 */ }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="预约详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" style="padding: 40px; text-align: center;">
      <van-loading size="36" />
    </div>

    <template v-else>
      <div class="status-section">
        <van-tag :type="(statusMap[detail.status]?.type as any) || 'default'" size="large">
          {{ statusMap[detail.status]?.label || detail.status }}
        </van-tag>
        <div class="res-no">{{ detail.reservation_no }}</div>
      </div>

      <van-cell-group inset title="预约信息" class="info-group">
        <van-cell title="场馆" :value="detail.venue_name || '-'" />
        <van-cell title="日期" :value="detail.booking_date" />
        <van-cell title="时段" :value="`${detail.start_time} ~ ${detail.end_time}`" />
        <van-cell title="时长" :value="detail.duration ? `${detail.duration}小时` : '-'" />
        <van-cell title="费用" :value="detail.total_amount ? `${detail.total_amount} 金币` : '-'" />
      </van-cell-group>

      <van-cell-group inset title="会员信息" class="info-group">
        <van-cell title="会员" :value="detail.member_nickname || detail.member_name || '-'" />
        <van-cell title="电话" :value="detail.member_phone || '-'" />
      </van-cell-group>

      <van-cell-group inset title="核销信息" class="info-group" v-if="detail.is_verified">
        <van-cell title="核销状态" value="已核销" />
        <van-cell title="核销人" :value="detail.verified_by || '-'" />
        <van-cell title="核销时间" :value="detail.verified_at || '-'" />
      </van-cell-group>

      <div class="bottom-actions" v-if="detail.status !== 'completed' && detail.status !== 'cancelled'">
        <van-button
          v-if="detail.status === 'pending'"
          type="primary"
          block
          round
          size="large"
          @click="handleConfirm"
        >确认预约</van-button>
        <van-button
          v-if="detail.status === 'confirmed' || detail.status === 'in_progress'"
          type="success"
          block
          round
          size="large"
          @click="handleComplete"
        >标记完成</van-button>
        <van-button
          v-if="detail.status !== 'completed'"
          plain
          type="danger"
          block
          round
          size="large"
          style="margin-top: 10px;"
          @click="handleCancel"
        >取消预约</van-button>
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

.res-no {
  margin-top: 8px;
  font-size: 13px;
  color: #999;
}

.info-group {
  margin-top: 12px;
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

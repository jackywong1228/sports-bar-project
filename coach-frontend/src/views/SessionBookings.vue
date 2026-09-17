<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSessionBookings, type SessionBooking } from '@/api/course'

const route = useRoute()
const router = useRouter()

const bookings = ref<SessionBooking[]>([])
const loading = ref(false)

// 课次信息从 Schedule 跳转时的 query 带入
const info = computed(() => ({
  course_title: String(route.query.course_title || ''),
  category_text: String(route.query.category_text || ''),
  session_date: String(route.query.session_date || ''),
  start_time: String(route.query.start_time || ''),
  end_time: String(route.query.end_time || ''),
  capacity: Number(route.query.capacity || 0),
  booked_count: Number(route.query.booked_count || 0)
}))

const PAY_TYPE_TEXT: Record<string, string> = {
  coin: '金币',
  wechat: '微信'
}

const payTypeText = (payType: string) => PAY_TYPE_TEXT[payType] || payType || '-'

const fetchBookings = async () => {
  loading.value = true
  try {
    const res = await getSessionBookings(Number(route.params.id))
    bookings.value = res.data as unknown as SessionBooking[]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchBookings()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="报名名单" left-arrow @click-left="router.back()" />

    <!-- 课次信息卡 -->
    <div class="session-info">
      <div class="info-title-row">
        <span class="info-title">{{ info.course_title }}</span>
        <van-tag v-if="info.category_text" type="primary" round>{{ info.category_text }}</van-tag>
      </div>
      <div class="info-time">
        <van-icon name="underway-o" />
        <span>{{ info.session_date }} {{ info.start_time }} - {{ info.end_time }}</span>
      </div>
      <div class="info-capacity">
        <van-icon name="friends-o" />
        <span>已报名 {{ info.booked_count }}/{{ info.capacity }}</span>
      </div>
    </div>

    <!-- 学员列表 -->
    <div class="section-title">报名学员（{{ bookings.length }}）</div>

    <van-loading v-if="loading" class="loading-wrap" size="32" color="#1A5D3A" />

    <template v-else>
      <van-empty v-if="bookings.length === 0" description="暂无学员报名" />

      <van-cell-group v-else class="booking-group">
        <van-cell v-for="b in bookings" :key="b.id" :title="b.member_name">
          <template #label>
            <div class="cell-sub">{{ b.member_phone }}</div>
            <div class="cell-sub">{{ b.booking_no }} · {{ payTypeText(b.pay_type) }} {{ b.price }}金币</div>
          </template>
          <template #value>
            <div class="status-col">
              <van-tag :type="b.status === 'confirmed' ? 'success' : 'warning'">
                {{ b.status_text }}
              </van-tag>
              <van-tag v-if="b.is_verified" type="success" plain class="verify-tag">已核销</van-tag>
              <span v-else class="unverified">未核销</span>
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </template>
  </div>
</template>

<style scoped>
.session-info {
  margin: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.info-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-title {
  font-size: 16px;
  font-weight: 600;
  color: #1A1A1A;
}

.info-time,
.info-capacity {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.section-title {
  margin: 4px 16px 10px;
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.loading-wrap {
  display: block;
  margin: 60px auto;
}

.booking-group {
  margin: 0 16px;
  border-radius: 12px;
  overflow: hidden;
}

.cell-sub {
  font-size: 12px;
  color: #999;
  line-height: 1.6;
}

.status-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.verify-tag {
  border-radius: 4px;
}

.unverified {
  font-size: 12px;
  color: #999;
}
</style>

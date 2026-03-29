<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getReservationList } from '@/api/reservation'

const router = useRouter()

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待确认', type: 'warning' },
  confirmed: { label: '已确认', type: 'primary' },
  in_progress: { label: '使用中', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const tabs = [
  { name: '', label: '全部' },
  { name: 'pending', label: '待确认' },
  { name: 'confirmed', label: '已确认' },
  { name: 'in_progress', label: '使用中' },
  { name: 'completed', label: '已完成' }
]

const activeTab = ref('')
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const list = ref<any[]>([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

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
    const res = await getReservationList(params)
    const data = res.data.list || res.data.items || []
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
  router.push(`/reservation/${id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="预约管理" left-arrow @click-left="router.back()" />

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
        <van-cell-group v-for="item in list" :key="item.id" inset class="reservation-card" @click="goDetail(item.id)">
          <van-cell :border="false">
            <template #title>
              <div class="res-header">
                <span class="res-venue">{{ item.venue_name || '场馆' }}</span>
                <van-tag :type="(statusMap[item.status]?.type as any) || 'default'" size="medium">
                  {{ statusMap[item.status]?.label || item.status }}
                </van-tag>
              </div>
            </template>
            <template #label>
              <div class="res-info">
                <div><van-icon name="user-o" /> {{ item.member_nickname || item.member_name || '-' }}</div>
                <div><van-icon name="clock-o" /> {{ item.booking_date }} {{ item.start_time }}~{{ item.end_time }}</div>
                <div class="res-no">{{ item.reservation_no }}</div>
              </div>
            </template>
          </van-cell>
        </van-cell-group>

        <van-empty v-if="!loading && list.length === 0" description="暂无预约" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.reservation-card {
  margin-top: 10px;
}

.res-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.res-venue {
  font-weight: 600;
  font-size: 16px;
}

.res-info {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
  line-height: 2;
}

.res-info .van-icon {
  margin-right: 4px;
}

.res-no {
  font-size: 12px;
  color: #999;
}
</style>

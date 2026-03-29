<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCheckinRecords } from '@/api/checkin'

const router = useRouter()

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
    const res = await getCheckinRecords({
      page: pagination.page,
      page_size: pagination.pageSize
    })
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

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="打卡记录" left-arrow @click-left="router.back()" />

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoadMore"
      >
        <van-cell-group v-for="item in list" :key="item.id" inset class="checkin-card">
          <van-cell>
            <template #title>
              <div class="checkin-header">
                <span class="checkin-member">{{ item.member_nickname || item.member_name || '-' }}</span>
                <van-tag :type="item.check_type === 'in' ? 'success' : 'warning'" size="medium">
                  {{ item.check_type === 'in' ? '入场' : '出场' }}
                </van-tag>
              </div>
            </template>
            <template #label>
              <div class="checkin-info">
                <div><van-icon name="location-o" /> {{ item.venue_name || '-' }}</div>
                <div><van-icon name="clock-o" /> {{ item.created_at || item.check_time || '-' }}</div>
              </div>
            </template>
          </van-cell>
        </van-cell-group>

        <van-empty v-if="!loading && list.length === 0" description="暂无打卡记录" />
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.checkin-card {
  margin-top: 10px;
}

.checkin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checkin-member {
  font-weight: 600;
  font-size: 15px;
}

.checkin-info {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
  line-height: 2;
}

.checkin-info .van-icon {
  margin-right: 4px;
}
</style>

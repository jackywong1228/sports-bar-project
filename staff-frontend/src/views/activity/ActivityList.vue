<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { getActivityList, updateActivityStatus } from '@/api/activity'

const router = useRouter()

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'default' },
  published: { label: '已发布', type: 'primary' },
  ongoing: { label: '进行中', type: 'warning' },
  ended: { label: '已结束', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const tabs = [
  { name: '', label: '全部' },
  { name: 'draft', label: '草稿' },
  { name: 'published', label: '已发布' },
  { name: 'ongoing', label: '进行中' },
  { name: 'ended', label: '已结束' }
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
    const res = await getActivityList(params)
    const data = res.data?.list || []
    if (isLoadMore) {
      list.value.push(...data)
    } else {
      list.value = data
    }
    pagination.total = res.data?.total || 0
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

const goCreate = () => {
  router.push('/activity/create')
}

const goEdit = (id: number) => {
  router.push(`/activity/edit/${id}`)
}

const handlePublish = async (item: any) => {
  try {
    await showDialog({
      title: '确认发布',
      message: `确定要发布活动"${item.title}"吗？发布后用户即可看到。`
    })
    await updateActivityStatus(item.id, { status: 'published' })
    showToast({ message: '发布成功', type: 'success' })
    fetchList()
  } catch (_e) {
    // 取消
  }
}

const handleCancel = async (item: any) => {
  try {
    await showDialog({
      title: '确认取消',
      message: `确定要取消活动"${item.title}"吗？`
    })
    await updateActivityStatus(item.id, { status: 'cancelled' })
    showToast({ message: '已取消', type: 'success' })
    fetchList()
  } catch (_e) {
    // 取消
  }
}

const formatTime = (time: string) => {
  if (!time) return ''
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="活动管理" left-arrow @click-left="router.back()">
      <template #right>
        <van-icon name="plus" size="20" @click="goCreate" />
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
        <van-cell-group v-for="item in list" :key="item.id" inset class="activity-card">
          <van-cell :border="false" @click="goEdit(item.id)">
            <template #title>
              <div class="activity-header">
                <span class="activity-title">{{ item.title }}</span>
                <van-tag :type="(statusMap[item.status]?.type as any) || 'default'" size="medium">
                  {{ statusMap[item.status]?.label || item.status }}
                </van-tag>
              </div>
            </template>
            <template #label>
              <div class="activity-info">
                <div class="activity-time">{{ formatTime(item.start_time) }} ~ {{ formatTime(item.end_time) }}</div>
                <div v-if="item.location" class="activity-location">{{ item.location }}</div>
                <div class="activity-meta">
                  <span>报名: {{ item.current_participants || 0 }}{{ item.max_participants ? `/${item.max_participants}` : '' }}人</span>
                  <span v-if="item.price > 0" class="activity-price">{{ item.price }} 金币</span>
                  <span v-else class="activity-free">免费</span>
                </div>
              </div>
            </template>
          </van-cell>

          <van-cell :border="false" v-if="item.status === 'draft' || item.status === 'published'">
            <div class="activity-actions">
              <van-button
                v-if="item.status === 'draft'"
                type="primary"
                size="small"
                round
                @click.stop="handlePublish(item)"
              >发布</van-button>
              <van-button
                size="small"
                round
                @click.stop="goEdit(item.id)"
              >编辑</van-button>
              <van-button
                v-if="item.status === 'published'"
                type="danger"
                size="small"
                round
                plain
                @click.stop="handleCancel(item)"
              >取消活动</van-button>
            </div>
          </van-cell>
        </van-cell-group>

        <van-empty v-if="!loading && list.length === 0" description="暂无活动" />
      </van-list>
    </van-pull-refresh>

    <!-- 底部新建按钮 -->
    <div class="fab-container">
      <van-button type="primary" round icon="plus" class="fab-btn" @click="goCreate">
        新建活动
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.activity-card {
  margin-top: 10px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-title {
  font-weight: 600;
  font-size: 16px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.activity-info {
  margin-top: 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.8;
}

.activity-time {
  color: #1989fa;
}

.activity-location {
  color: #666;
}

.activity-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.activity-price {
  color: #ee6723;
  font-weight: 600;
}

.activity-free {
  color: #07c160;
  font-weight: 500;
}

.activity-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.fab-container {
  position: fixed;
  bottom: 24px;
  right: 16px;
  z-index: 99;
}

.fab-btn {
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.4);
}
</style>

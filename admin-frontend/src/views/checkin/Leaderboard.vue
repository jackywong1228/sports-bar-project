<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface LeaderboardItem {
  rank: number
  member_id: number
  member_name: string
  member_phone: string
  avatar: string
  level_name: string
  total_duration: number
  check_count: number
}

interface VenueType {
  id: number
  name: string
}

const loading = ref(false)
const refreshing = ref(false)
const tableData = ref<LeaderboardItem[]>([])
const venueTypes = ref<VenueType[]>([])

const queryParams = reactive({
  period: 'daily' as 'daily' | 'weekly' | 'monthly',
  venue_type_id: null as number | null,
  limit: 50
})

const periodOptions = [
  { label: '日榜', value: 'daily' },
  { label: '周榜', value: 'weekly' },
  { label: '月榜', value: 'monthly' }
]

// 获取场馆类型
const fetchVenueTypes = async () => {
  try {
    const res = await request.get('/venues/types')
    venueTypes.value = res.data || []
  } catch {
    // ignore
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/checkin/leaderboard', { params: queryParams })
    tableData.value = res.data || []
  } catch (err) {
    console.error('获取排行榜失败:', err)
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    await request.post('/checkin/leaderboard/refresh', { period: queryParams.period })
    ElMessage.success('刷新成功')
    fetchData()
  } catch (err) {
    console.error('刷新排行榜失败:', err)
  } finally {
    refreshing.value = false
  }
}

const formatDuration = (minutes: number) => {
  if (!minutes) return '-'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

const getRankClass = (rank: number) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

onMounted(() => {
  fetchVenueTypes()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="周期">
          <el-radio-group v-model="queryParams.period" @change="fetchData">
            <el-radio-button v-for="o in periodOptions" :key="o.value" :value="o.value">
              {{ o.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="场馆类型">
          <el-select
            v-model="queryParams.venue_type_id"
            placeholder="综合排行"
            clearable
            @change="fetchData"
          >
            <el-option v-for="t in venueTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="refreshing" @click="handleRefresh">
            刷新排行榜
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <span>
          {{ queryParams.period === 'daily' ? '日榜' : queryParams.period === 'weekly' ? '周榜' : '月榜' }}
          <span v-if="queryParams.venue_type_id">
            - {{ venueTypes.find(t => t.id === queryParams.venue_type_id)?.name }}
          </span>
          <span v-else>- 综合排行</span>
        </span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="rank" label="排名" width="100">
          <template #default="{ row }">
            <span :class="['rank-num', getRankClass(row.rank)]">
              {{ row.rank }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :src="row.avatar" :size="40">
                {{ row.member_name?.charAt(0) }}
              </el-avatar>
              <div class="user-info">
                <div class="user-name">{{ row.member_name }}</div>
                <div class="user-phone">{{ row.member_phone }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="level_name" label="会员等级" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.level_name" type="success">{{ row.level_name }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="运动时长" width="150">
          <template #default="{ row }">
            <span class="duration-text">{{ formatDuration(row.total_duration) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="check_count" label="打卡次数" width="120">
          <template #default="{ row }">
            {{ row.check_count }}次
          </template>
        </el-table-column>
      </el-table>

      <div v-if="tableData.length === 0 && !loading" class="empty-tip">
        暂无排行数据
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-card {
  margin-bottom: 0;
}

.rank-num {
  display: inline-block;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 50%;
  font-weight: bold;
}

.rank-gold {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
}

.rank-silver {
  background: linear-gradient(135deg, #C0C0C0, #A0A0A0);
  color: #fff;
}

.rank-bronze {
  background: linear-gradient(135deg, #CD7F32, #B87333);
  color: #fff;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 500;
  color: #303133;
}

.user-phone {
  font-size: 12px;
  color: #909399;
}

.duration-text {
  font-weight: 500;
  color: #1A5D3A;
}

.empty-tip {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}
</style>

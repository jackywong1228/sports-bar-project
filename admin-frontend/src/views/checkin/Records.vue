<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface CheckinRecord {
  id: number
  member_id: number
  member_name: string
  member_phone: string
  venue_id: number
  venue_name: string
  venue_type_name: string
  gate_id: string
  check_in_time: string
  check_out_time: string
  duration: number
  points_earned: number
  points_settled: boolean
  check_date: string
}

interface Venue {
  id: number
  name: string
}

const loading = ref(false)
const tableData = ref<CheckinRecord[]>([])
const total = ref(0)
const venues = ref<Venue[]>([])

const queryParams = reactive({
  page: 1,
  page_size: 10,
  member_id: null as number | null,
  venue_id: null as number | null,
  start_date: '',
  end_date: ''
})

// 获取场馆列表
const fetchVenues = async () => {
  try {
    const res = await request.get('/venues', { params: { page_size: 100 } })
    venues.value = res.data.items || []
  } catch {
    // ignore
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/checkin/records', { params: queryParams })
    tableData.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取打卡记录失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.member_id = null
  queryParams.venue_id = null
  queryParams.start_date = ''
  queryParams.end_date = ''
  handleSearch()
}

const formatDuration = (minutes: number) => {
  if (!minutes) return '-'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

onMounted(() => {
  fetchVenues()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="场馆">
          <el-select v-model="queryParams.venue_id" placeholder="全部场馆" clearable>
            <el-option v-for="v in venues" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="queryParams.start_date"
            type="date"
            placeholder="开始日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
          <span style="margin: 0 8px">-</span>
          <el-date-picker
            v-model="queryParams.end_date"
            type="date"
            placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <span>打卡记录</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="check_date" label="打卡日期" width="120" />
        <el-table-column prop="member_name" label="会员" width="100" />
        <el-table-column prop="member_phone" label="手机号" width="120" />
        <el-table-column prop="venue_name" label="场馆" width="150" />
        <el-table-column prop="venue_type_name" label="场馆类型" width="100" />
        <el-table-column prop="gate_id" label="闸机ID" width="100" />
        <el-table-column label="入场时间" width="180">
          <template #default="{ row }">
            {{ row.check_in_time?.substring(0, 19) }}
          </template>
        </el-table-column>
        <el-table-column label="出场时间" width="180">
          <template #default="{ row }">
            {{ row.check_out_time ? row.check_out_time.substring(0, 19) : '进行中' }}
          </template>
        </el-table-column>
        <el-table-column label="停留时长" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="points_earned" label="获得积分" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.points_earned > 0" type="success">+{{ row.points_earned }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="points_settled" label="积分状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.points_settled ? 'success' : 'warning'">
              {{ row.points_settled ? '已结算' : '未结算' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
        @change="fetchData"
      />
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
</style>

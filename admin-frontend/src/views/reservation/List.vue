<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface Reservation {
  id: number
  reservation_no: string
  member_id: number
  member_name: string
  member_phone: string
  venue_id: number
  venue_name: string
  coach_id: number
  coach_name: string
  start_time: string
  end_time: string
  duration: number
  venue_fee: number
  coach_fee: number
  total_fee: number
  status: number
  status_text: string
  type: string
  remark: string
  created_at: string
}

const loading = ref(false)
const tableData = ref<Reservation[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  status: null as number | null,
  type: ''
})

const statusOptions = [
  { label: '待确认', value: 0 },
  { label: '已确认', value: 1 },
  { label: '进行中', value: 2 },
  { label: '已完成', value: 3 },
  { label: '已取消', value: 4 }
]

const statusMap: Record<number, { text: string; type: string }> = {
  0: { text: '待确认', type: 'info' },
  1: { text: '已确认', type: 'primary' },
  2: { text: '进行中', type: 'warning' },
  3: { text: '已完成', type: 'success' },
  4: { text: '已取消', type: 'danger' }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/reservations', { params: queryParams })
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.status = null
  queryParams.type = ''
  handleSearch()
}

const handleCancel = async (row: Reservation) => {
  try {
    await ElMessageBox.confirm('确定要取消该预约吗？', '提示', { type: 'warning' })
    await request.put(`/reservations/${row.id}/cancel`)
    ElMessage.success('取消成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

const handleDelete = async (row: Reservation) => {
  try {
    await ElMessageBox.confirm('确定要删除该预约记录吗？', '提示', { type: 'warning' })
    await request.delete(`/reservations/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable>
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryParams.type" placeholder="全部" clearable>
            <el-option label="普通预约" value="normal" />
            <el-option label="活动预约" value="activity" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <span>预约记录</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="reservation_no" label="预约编号" width="200" />
        <el-table-column prop="member_name" label="会员" width="100" />
        <el-table-column prop="member_phone" label="联系电话" width="120" />
        <el-table-column prop="venue_name" label="场地" width="120" />
        <el-table-column prop="coach_name" label="教练" width="100" />
        <el-table-column label="预约时间" width="180">
          <template #default="{ row }">
            {{ row.start_time?.substring(0, 16) }} - {{ row.end_time?.substring(11, 16) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(分钟)" width="100" />
        <el-table-column prop="total_fee" label="总费用" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any">
              {{ statusMap[row.status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            {{ row.type === 'normal' ? '普通' : '活动' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button
              v-if="row.status < 3"
              type="warning"
              link
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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

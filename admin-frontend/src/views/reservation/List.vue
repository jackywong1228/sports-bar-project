<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElTable } from 'element-plus'
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
  status: string
  status_text: string
  type: string
  remark: string
  created_at: string
  is_verified?: boolean
  verified_at?: string
}

const loading = ref(false)
const tableData = ref<Reservation[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  status: null as string | null,
  type: ''
})

const statusOptions = [
  { label: '待确认', value: 'pending' },
  { label: '已确认', value: 'confirmed' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' }
]

const statusMap: Record<string, { text: string; type: string }> = {
  pending:     { text: '待确认', type: 'info' },
  confirmed:   { text: '已确认', type: 'primary' },
  in_progress: { text: '进行中', type: 'warning' },
  completed:   { text: '已完成', type: 'success' },
  cancelled:   { text: '已取消', type: 'danger' }
}

const finalStatuses = new Set(['completed', 'cancelled'])

const tableRef = ref<InstanceType<typeof ElTable>>()
const selectedRows = ref<Reservation[]>([])

const handleSelectionChange = (rows: Reservation[]) => {
  selectedRows.value = rows
}

// 批量确认/取消/删除：单个「确认」按钮也复用此逻辑（ids 只传一个）
const batchUpdateStatus = async (ids: number[], action: 'confirm' | 'cancel' | 'delete') => {
  const actionTextMap = { confirm: '确认', cancel: '取消', delete: '删除' } as const
  const actionText = actionTextMap[action]
  try {
    await ElMessageBox.confirm(
      action === 'delete'
        ? `确定要删除选中的 ${ids.length} 条预约记录吗？删除后不可恢复！`
        : `确定要${actionText}选中的 ${ids.length} 条预约吗？`,
      '提示',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const res = await request.post('/reservations/batch-status', { ids, action })
    const { success_count, fail_count, failures } = res.data
    if (success_count > 0) {
      ElMessage.success(`成功${actionText} ${success_count} 条`)
    }
    if (fail_count > 0) {
      const detail = (failures as { id: number; reason: string }[])
        .slice(0, 3)
        .map(f => `ID ${f.id}：${f.reason}`)
        .join('；')
      ElMessage.warning(`${fail_count} 条失败：${detail}${fail_count > 3 ? ' 等' : ''}`)
    }
    tableRef.value?.clearSelection()
    fetchData()
  } catch {
    // 请求错误（request 封装已提示）
  }
}

const handleBatchConfirm = () => {
  batchUpdateStatus(selectedRows.value.map(r => r.id), 'confirm')
}

const handleBatchCancel = () => {
  batchUpdateStatus(selectedRows.value.map(r => r.id), 'cancel')
}

const handleBatchDelete = () => {
  batchUpdateStatus(selectedRows.value.map(r => r.id), 'delete')
}

const handleConfirm = (row: Reservation) => {
  batchUpdateStatus([row.id], 'confirm')
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
        <div class="card-header">
          <span>预约记录</span>
          <div class="batch-actions">
            <el-button
              type="primary"
              :disabled="selectedRows.length === 0"
              @click="handleBatchConfirm"
            >
              批量确认{{ selectedRows.length ? ` (${selectedRows.length})` : '' }}
            </el-button>
            <el-button
              type="warning"
              :disabled="selectedRows.length === 0"
              @click="handleBatchCancel"
            >
              批量取消{{ selectedRows.length ? ` (${selectedRows.length})` : '' }}
            </el-button>
            <el-button
              type="danger"
              :disabled="selectedRows.length === 0"
              @click="handleBatchDelete"
            >
              批量删除{{ selectedRows.length ? ` (${selectedRows.length})` : '' }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        ref="tableRef"
        :data="tableData"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="50"
        />
        <el-table-column prop="reservation_no" label="预约编号" width="200" class-name="col-secondary" />
        <el-table-column prop="member_name" label="会员" width="100" />
        <el-table-column prop="member_phone" label="联系电话" width="120" />
        <el-table-column prop="venue_name" label="场地" width="120" />
        <el-table-column prop="coach_name" label="教练" width="100" />
        <el-table-column label="预约时间" min-width="220">
          <template #default="{ row }">
            <!-- 后端 reservation_date 为 Date，start_time/end_time 为 Time(HH:MM:SS) -->
            {{ row.reservation_date }} {{ row.start_time?.substring(0, 5) }} - {{ row.end_time?.substring(0, 5) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(分钟)" width="100" />
        <el-table-column prop="total_fee" label="总费用" width="100" />
        <el-table-column prop="status" label="状态" width="160">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'">
              {{ statusMap[row.status]?.text || row.status_text || row.status }}
            </el-tag>
            <el-tag
              v-if="row.is_verified"
              type="success"
              size="small"
              style="margin-left: 4px;"
            >
              已核销
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100" class-name="col-secondary">
          <template #default="{ row }">
            {{ row.type === 'normal' ? '普通' : '活动' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" class-name="col-secondary" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              link
              @click="handleConfirm(row)"
            >
              确认
            </el-button>
            <el-button
              v-if="!finalStatuses.has(row.status)"
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

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.batch-actions {
  display: flex;
  gap: 8px;
}
</style>

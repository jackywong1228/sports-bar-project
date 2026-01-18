<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface CoachApplication {
  id: number
  member_id: number
  member_nickname: string
  name: string
  phone: string
  type: string
  introduction: string
  status: number
  status_text: string
  audit_time: string
  audit_remark: string
  created_at: string
}

const loading = ref(false)
const tableData = ref<CoachApplication[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  name: '',
  status: null as number | null
})

const statusOptions = [
  { label: '待审核', value: 0 },
  { label: '通过', value: 1 },
  { label: '拒绝', value: 2 }
]

const statusMap: Record<number, { text: string; type: string }> = {
  0: { text: '待审核', type: 'warning' },
  1: { text: '通过', type: 'success' },
  2: { text: '拒绝', type: 'danger' }
}

const auditVisible = ref(false)
const auditForm = reactive({
  id: 0,
  status: 1,
  audit_remark: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/coaches/applications', { params: queryParams })
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
  queryParams.name = ''
  queryParams.status = null
  handleSearch()
}

const handleAudit = (row: CoachApplication) => {
  auditForm.id = row.id
  auditForm.status = 1
  auditForm.audit_remark = ''
  auditVisible.value = true
}

const submitAudit = async () => {
  try {
    await request.put(`/coaches/applications/${auditForm.id}/audit`, {
      status: auditForm.status,
      audit_remark: auditForm.audit_remark
    })
    ElMessage.success('审核完成')
    auditVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const typeText = (type: string) => {
  return { technical: '技术型', entertainment: '娱乐型' }[type] || type
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="姓名">
          <el-input v-model="queryParams.name" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable>
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
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
        <span>教练申请</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="member_nickname" label="会员昵称" width="120" />
        <el-table-column label="申请类型" width="100">
          <template #default="{ row }">{{ typeText(row.type) }}</template>
        </el-table-column>
        <el-table-column prop="introduction" label="个人介绍" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any">
              {{ statusMap[row.status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column prop="audit_time" label="审核时间" width="180" />
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 0"
              type="primary"
              link
              @click="handleAudit(row)"
            >
              审核
            </el-button>
            <span v-else>-</span>
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

    <el-dialog v-model="auditVisible" title="审核申请" width="400px">
      <el-form :model="auditForm" label-width="80px">
        <el-form-item label="审核结果">
          <el-radio-group v-model="auditForm.status">
            <el-radio :value="1">通过</el-radio>
            <el-radio :value="2">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核备注">
          <el-input v-model="auditForm.audit_remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAudit">确定</el-button>
      </template>
    </el-dialog>
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

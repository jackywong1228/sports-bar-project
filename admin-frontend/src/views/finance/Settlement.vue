<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="教练">
          <el-select v-model="searchForm.coach_id" placeholder="全部" clearable filterable>
            <el-option v-for="c in coaches" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="待确认" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已支付" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>教练结算</span>
          <el-button type="primary" @click="handleCreate">创建结算单</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="settlement_no" label="结算单号" width="180" />
        <el-table-column prop="coach_name" label="教练" width="100" />
        <el-table-column label="结算周期" width="200">
          <template #default="{ row }">{{ row.period_start }} 至 {{ row.period_end }}</template>
        </el-table-column>
        <el-table-column prop="total_lessons" label="总课时" width="80" />
        <el-table-column prop="total_amount" label="总金额" width="100">
          <template #default="{ row }">{{ row.total_amount }} 元</template>
        </el-table-column>
        <el-table-column prop="platform_fee" label="平台费" width="90">
          <template #default="{ row }">{{ row.platform_fee }} 元</template>
        </el-table-column>
        <el-table-column prop="settlement_amount" label="结算金额" width="110">
          <template #default="{ row }">
            <span style="font-weight: bold; color: #67C23A;">{{ row.settlement_amount }} 元</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pay_time" label="支付时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" link type="primary" @click="handleConfirm(row)">确认</el-button>
            <el-button v-if="row.status === 'confirmed'" link type="success" @click="handlePay(row)">支付</el-button>
            <el-button link type="info" @click="handleDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 创建结算单弹窗 -->
    <el-dialog v-model="createDialogVisible" title="创建结算单" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="选择教练" prop="coach_id">
          <el-select v-model="createForm.coach_id" placeholder="请选择教练" filterable style="width: 100%;">
            <el-option v-for="c in coaches" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="结算周期" prop="period">
          <el-date-picker
            v-model="createForm.period"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="平台抽成">
          <el-input-number v-model="createForm.platform_rate" :min="0" :max="1" :step="0.05" :precision="2" style="width: 100%;" />
          <div class="form-tip">默认20%（0.2）</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 支付弹窗 -->
    <el-dialog v-model="payDialogVisible" title="支付结算单" width="500px">
      <el-form :model="payForm" label-width="100px">
        <el-form-item label="结算金额">
          <div style="font-size: 20px; font-weight: bold; color: #67C23A;">{{ currentSettlement?.settlement_amount }} 元</div>
        </el-form-item>
        <el-form-item label="收款账户">
          <el-input v-model="payForm.pay_account" placeholder="请输入收款账户信息" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="payForm.pay_remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePaySubmit" :loading="paying">确认支付</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import request from '@/utils/request'

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待确认', type: 'info' },
  confirmed: { label: '已确认', type: 'warning' },
  paid: { label: '已支付', type: 'success' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const coaches = ref<any[]>([])
const searchForm = reactive({ coach_id: null, status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const createDialogVisible = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({ coach_id: null, period: [], platform_rate: 0.2 })
const createRules = {
  coach_id: [{ required: true, message: '请选择教练', trigger: 'change' }],
  period: [{ required: true, message: '请选择结算周期', trigger: 'change' }]
}

const payDialogVisible = ref(false)
const paying = ref(false)
const currentSettlement = ref<any>(null)
const payForm = reactive({ pay_account: '', pay_remark: '' })

const fetchCoaches = async () => {
  const res = await request.get('/coaches', { params: { page_size: 100 } })
  coaches.value = res.data.items || []
}

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.coach_id) params.coach_id = searchForm.coach_id
    if (searchForm.status) params.status = searchForm.status
    const res = await request.get('/finance/settlement', { params })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.coach_id = null
  searchForm.status = ''
  pagination.page = 1
  fetchList()
}

const handleCreate = () => {
  createForm.coach_id = null
  createForm.period = []
  createForm.platform_rate = 0.2
  createDialogVisible.value = true
}

const handleCreateSubmit = async () => {
  await createFormRef.value?.validate()
  if (!createForm.period || createForm.period.length !== 2) {
    ElMessage.warning('请选择结算周期')
    return
  }
  creating.value = true
  try {
    await request.post('/finance/settlement/create', {
      coach_id: createForm.coach_id,
      period_start: createForm.period[0],
      period_end: createForm.period[1],
      platform_rate: createForm.platform_rate
    })
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    fetchList()
  } finally {
    creating.value = false
  }
}

const handleConfirm = (row: any) => {
  ElMessageBox.confirm('确定要确认该结算单吗？', '提示', { type: 'warning' })
    .then(async () => {
      await request.put(`/finance/settlement/${row.id}/confirm`)
      ElMessage.success('已确认')
      fetchList()
    })
}

const handlePay = (row: any) => {
  currentSettlement.value = row
  payForm.pay_account = ''
  payForm.pay_remark = ''
  payDialogVisible.value = true
}

const handlePaySubmit = async () => {
  paying.value = true
  try {
    await request.put(`/finance/settlement/${currentSettlement.value.id}/pay`, payForm)
    ElMessage.success('支付成功')
    payDialogVisible.value = false
    fetchList()
  } finally {
    paying.value = false
  }
}

const handleDetail = (row: any) => {
  ElMessageBox.alert(`
    结算单号：${row.settlement_no}<br>
    教练：${row.coach_name}<br>
    结算周期：${row.period_start} 至 ${row.period_end}<br>
    总课时：${row.total_lessons}<br>
    总金额：${row.total_amount} 元<br>
    平台费：${row.platform_fee} 元<br>
    结算金额：${row.settlement_amount} 元<br>
    状态：${statusMap[row.status]?.label}
  `, '结算单详情', { dangerouslyUseHTMLString: true })
}

onMounted(() => { fetchCoaches(); fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.form-tip { font-size: 12px; color: #999; }
</style>

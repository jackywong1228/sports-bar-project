<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="订单号/商品名/收货人" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="待发货" value="pending" />
            <el-option label="已发货" value="shipped" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
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
        <span>兑换订单</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="member_nickname" label="会员" width="100" />
        <el-table-column label="商品" min-width="180">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-image v-if="row.product_image" :src="row.product_image" fit="cover" style="width: 40px; height: 40px;" />
              <span>{{ row.product_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="70" />
        <el-table-column prop="points_used" label="消耗积分" width="90" />
        <el-table-column label="消耗金币" width="90">
          <template #default="{ row }">{{ row.coins_used || 0 }}</template>
        </el-table-column>
        <el-table-column prop="receiver_name" label="收货人" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'pending'" link type="primary" @click="handleShip(row)">发货</el-button>
            <el-button v-if="row.status === 'shipped'" link type="success" @click="handleComplete(row)">完成</el-button>
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

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单号">{{ detail.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMap[detail.status]?.type">{{ statusMap[detail.status]?.label }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员">{{ detail.member_nickname }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detail.member_phone }}</el-descriptions-item>
        <el-descriptions-item label="商品名称">{{ detail.product_name }}</el-descriptions-item>
        <el-descriptions-item label="兑换数量">{{ detail.quantity }}</el-descriptions-item>
        <el-descriptions-item label="消耗积分">{{ detail.points_used }}</el-descriptions-item>
        <el-descriptions-item label="消耗金币">{{ detail.coins_used || 0 }}</el-descriptions-item>
        <el-descriptions-item label="收货人">{{ detail.receiver_name }}</el-descriptions-item>
        <el-descriptions-item label="收货电话">{{ detail.receiver_phone }}</el-descriptions-item>
        <el-descriptions-item label="收货地址" :span="2">{{ detail.receiver_address }}</el-descriptions-item>
        <el-descriptions-item label="快递公司">{{ detail.express_company || '-' }}</el-descriptions-item>
        <el-descriptions-item label="快递单号">{{ detail.express_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ detail.created_at }}</el-descriptions-item>
        <el-descriptions-item label="发货时间">{{ detail.ship_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 发货弹窗 -->
    <el-dialog v-model="shipDialogVisible" title="订单发货" width="500px">
      <el-form :model="shipForm" :rules="shipRules" ref="shipFormRef" label-width="80px">
        <el-form-item label="快递公司" prop="express_company">
          <el-select v-model="shipForm.express_company" placeholder="请选择快递公司" style="width: 100%;">
            <el-option label="顺丰速运" value="顺丰速运" />
            <el-option label="中通快递" value="中通快递" />
            <el-option label="圆通速递" value="圆通速递" />
            <el-option label="韵达快递" value="韵达快递" />
            <el-option label="申通快递" value="申通快递" />
            <el-option label="京东物流" value="京东物流" />
            <el-option label="邮政EMS" value="邮政EMS" />
          </el-select>
        </el-form-item>
        <el-form-item label="快递单号" prop="express_no">
          <el-input v-model="shipForm.express_no" placeholder="请输入快递单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleShipSubmit" :loading="shipping">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import request from '@/utils/request'

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待发货', type: 'warning' },
  shipped: { label: '已发货', type: '' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'info' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const detailVisible = ref(false)
const detail = ref<any>({})

const shipDialogVisible = ref(false)
const shipping = ref(false)
const shipFormRef = ref<FormInstance>()
const shipForm = reactive({ express_company: '', express_no: '' })
const shipRules = {
  express_company: [{ required: true, message: '请选择快递公司', trigger: 'change' }],
  express_no: [{ required: true, message: '请输入快递单号', trigger: 'blur' }]
}
let currentOrderId = 0

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/mall/orders', {
      params: { page: pagination.page, page_size: pagination.pageSize, ...searchForm }
    })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  fetchList()
}

const handleDetail = async (row: any) => {
  const res = await request.get(`/mall/orders/${row.id}`)
  detail.value = res.data
  detailVisible.value = true
}

const handleShip = (row: any) => {
  currentOrderId = row.id
  shipForm.express_company = ''
  shipForm.express_no = ''
  shipDialogVisible.value = true
}

const handleShipSubmit = async () => {
  await shipFormRef.value?.validate()
  shipping.value = true
  try {
    await request.put(`/mall/orders/${currentOrderId}/ship`, shipForm)
    ElMessage.success('发货成功')
    shipDialogVisible.value = false
    fetchList()
  } finally {
    shipping.value = false
  }
}

const handleComplete = (row: any) => {
  ElMessageBox.confirm('确定要完成该订单吗？', '提示', { type: 'warning' })
    .then(async () => {
      await request.put(`/mall/orders/${row.id}/status`, { status: 'completed' })
      ElMessage.success('操作成功')
      fetchList()
    })
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
</style>

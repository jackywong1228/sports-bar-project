<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const total = ref(0)
const queryParams = ref({
  page: 1,
  page_size: 10,
  keyword: '',
  status: ''
})

const statusOptions = [
  { label: '待支付', value: 'pending', type: 'warning' },
  { label: '已支付', value: 'paid', type: 'success' },
  { label: '已取消', value: 'cancelled', type: 'info' },
  { label: '已退款', value: 'refunded', type: 'danger' }
]

const payTypeOptions = [
  { label: '金币支付', value: 'coin' },
  { label: '微信支付', value: 'wechat' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = { ...queryParams.value }
    if (params.status === '') delete params.status
    const res = await request.get('/member-cards/orders', { params })
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.value.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.value = { page: 1, page_size: 10, keyword: '', status: '' }
  fetchData()
}

const handleSizeChange = (size: number) => {
  queryParams.value.page_size = size
  fetchData()
}

const handleCurrentChange = (page: number) => {
  queryParams.value.page = page
  fetchData()
}

const getStatusLabel = (status: string) => {
  const item = statusOptions.find(s => s.value === status)
  return item ? item.label : status
}

const getStatusType = (status: string) => {
  const item = statusOptions.find(s => s.value === status)
  return item ? item.type : 'info'
}

const getPayTypeLabel = (type: string) => {
  const item = payTypeOptions.find(t => t.value === type)
  return item ? item.label : type
}

const formatDuration = (days: number) => {
  if (!days) return '-'
  if (days >= 365) {
    const years = Math.floor(days / 365)
    return `${years}年`
  } else if (days >= 30) {
    const months = Math.floor(days / 30)
    return `${months}个月`
  } else {
    return `${days}天`
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="订单号">
          <el-input v-model="queryParams.keyword" placeholder="订单号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card>
      <template #header>
        <span>会员卡订单</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column label="会员信息" width="150">
          <template #default="{ row }">
            <div>{{ row.member_name || '-' }}</div>
            <div class="text-muted">{{ row.member_phone || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="card_name" label="套餐名称" width="120" />
        <el-table-column prop="level_name" label="会员等级" width="100" />
        <el-table-column label="金额" width="140">
          <template #default="{ row }">
            <div>
              <span class="price">{{ row.pay_amount }}</span>元
              <span v-if="row.original_price > row.pay_amount" class="original-price">{{ row.original_price }}元</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="赠送" width="130">
          <template #default="{ row }">
            <div v-if="row.bonus_coins > 0 || row.bonus_points > 0">
              <span v-if="row.bonus_coins > 0">{{ row.bonus_coins }}金币</span>
              <span v-if="row.bonus_coins > 0 && row.bonus_points > 0"><br/></span>
              <span v-if="row.bonus_points > 0">{{ row.bonus_points }}积分</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration_days" label="有效期" width="80">
          <template #default="{ row }">{{ formatDuration(row.duration_days) }}</template>
        </el-table-column>
        <el-table-column label="会员时间" width="170">
          <template #default="{ row }">
            <div v-if="row.start_time">
              <div>{{ row.start_time?.substring(0, 10) }}</div>
              <div>至 {{ row.expire_time?.substring(0, 10) }}</div>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="pay_type" label="支付方式" width="100">
          <template #default="{ row }">{{ getPayTypeLabel(row.pay_type) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pay_time" label="支付时间" width="170" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }

.price {
  font-size: 14px;
  font-weight: bold;
  color: #F56C6C;
}

.original-price {
  font-size: 12px;
  color: #909399;
  text-decoration: line-through;
  margin-left: 4px;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}
</style>

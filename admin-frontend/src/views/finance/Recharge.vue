<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="订单号/会员昵称/手机号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已失败" value="failed" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="8">
        <el-card class="stat-mini">
          <div class="label">充值总金额</div>
          <div class="value">{{ stats.total_amount?.toFixed(2) || '0.00' }} 元</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-mini">
          <div class="label">发放金币总数</div>
          <div class="value">{{ stats.total_coins || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-mini">
          <div class="label">充值笔数</div>
          <div class="value">{{ stats.total_count || 0 }} 笔</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <template #header>充值记录</template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column label="会员" width="150">
          <template #default="{ row }">
            <div>{{ row.member_nickname }}</div>
            <div style="color: #999; font-size: 12px;">{{ row.member_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="充值金额" width="100">
          <template #default="{ row }">{{ row.amount }} 元</template>
        </el-table-column>
        <el-table-column label="获得金币" width="120">
          <template #default="{ row }">
            {{ row.coins }}
            <span v-if="row.bonus_coins" style="color: #E6A23C;">+{{ row.bonus_coins }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pay_type" label="支付方式" width="90">
          <template #default="{ row }">{{ row.pay_type === 'wechat' ? '微信支付' : row.pay_type }}</template>
        </el-table-column>
        <el-table-column prop="transaction_id" label="交易号" width="200" />
        <el-table-column prop="pay_time" label="支付时间" width="170" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import request from '@/utils/request'

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待支付', type: 'info' },
  paid: { label: '已支付', type: 'success' },
  failed: { label: '已失败', type: 'danger' },
  refunded: { label: '已退款', type: 'warning' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const stats = ref<any>({})
const dateRange = ref<string[]>([])
const searchForm = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await request.get('/finance/recharge', { params })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  const params: any = {}
  if (dateRange.value?.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  const res = await request.get('/finance/recharge/stats', { params })
  stats.value = res.data
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.status = ''
  dateRange.value = []
  pagination.page = 1
  fetchList()
  fetchStats()
}

watch(dateRange, () => {
  fetchStats()
})

onMounted(() => { fetchList(); fetchStats() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.stat-row { margin-bottom: 16px; }
.stat-mini { text-align: center; padding: 12px; }
.stat-mini .label { font-size: 13px; color: #666; }
.stat-mini .value { font-size: 22px; font-weight: bold; color: #409EFF; margin-top: 4px; }
</style>

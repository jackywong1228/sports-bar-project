<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="会员ID">
          <el-input v-model="searchForm.member_id" placeholder="会员ID" clearable type="number" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="未使用" value="unused" />
            <el-option label="已使用" value="used" />
            <el-option label="已过期" value="expired" />
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
        <span>会员优惠券</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="member_nickname" label="会员" width="120" />
        <el-table-column prop="name" label="券名称" min-width="150" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag>{{ typeMap[row.type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优惠内容" width="120">
          <template #default="{ row }">
            <span v-if="row.type === 'discount'">{{ row.discount_value }}折</span>
            <span v-else-if="row.type === 'cash'">减{{ row.discount_value }}金币</span>
            <span v-else>礼品</span>
          </template>
        </el-table-column>
        <el-table-column prop="min_amount" label="最低消费" width="100" />
        <el-table-column label="有效期" width="180">
          <template #default="{ row }">
            {{ row.start_time }} 至 {{ row.end_time }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="use_time" label="使用时间" width="170" />
        <el-table-column prop="created_at" label="领取时间" width="170" />
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
import { ref, reactive, onMounted } from 'vue'
import request from '@/utils/request'

const typeMap: Record<string, string> = { discount: '折扣券', cash: '代金券', gift: '礼品券' }
const statusMap: Record<string, { label: string; type: string }> = {
  unused: { label: '未使用', type: '' },
  used: { label: '已使用', type: 'success' },
  expired: { label: '已过期', type: 'info' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ member_id: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.member_id) params.member_id = parseInt(searchForm.member_id)
    if (searchForm.status) params.status = searchForm.status
    const res = await request.get('/coupons/member-coupons', { params })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.member_id = ''
  searchForm.status = ''
  pagination.page = 1
  fetchList()
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
</style>

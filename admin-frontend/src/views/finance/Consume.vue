<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="会员ID">
          <el-input v-model="searchForm.member_id" placeholder="会员ID" clearable type="number" />
        </el-form-item>
        <el-form-item label="消费类型">
          <el-select v-model="searchForm.consume_type" placeholder="全部" clearable>
            <el-option label="场馆预约" value="venue" />
            <el-option label="教练预约" value="coach" />
            <el-option label="在线点餐" value="food" />
            <el-option label="活动报名" value="activity" />
            <el-option label="积分商城" value="mall" />
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

    <el-card class="table-card">
      <template #header>消费记录</template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="member_nickname" label="会员" width="120" />
        <el-table-column prop="consume_type_label" label="消费类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.consume_type_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="title" label="消费描述" min-width="200" />
        <el-table-column prop="amount" label="原金额" width="100">
          <template #default="{ row }">{{ row.amount }} 金币</template>
        </el-table-column>
        <el-table-column prop="discount_amount" label="优惠" width="90">
          <template #default="{ row }">
            <span v-if="row.discount_amount" style="color: #E6A23C;">-{{ row.discount_amount }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_amount" label="实付金额" width="100">
          <template #default="{ row }">
            <span style="font-weight: bold; color: #409EFF;">{{ row.actual_amount }} 金币</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="消费时间" width="170" />
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

const loading = ref(false)
const tableData = ref<any[]>([])
const dateRange = ref<string[]>([])
const searchForm = reactive({ member_id: '', consume_type: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (searchForm.member_id) params.member_id = parseInt(searchForm.member_id)
    if (searchForm.consume_type) params.consume_type = searchForm.consume_type
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await request.get('/finance/consume', { params })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.member_id = ''
  searchForm.consume_type = ''
  dateRange.value = []
  pagination.page = 1
  fetchList()
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
</style>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="评分">
          <el-select v-model="searchForm.rating" placeholder="全部" clearable>
            <el-option label="5星" :value="5" />
            <el-option label="4星" :value="4" />
            <el-option label="3星" :value="3" />
            <el-option label="2星" :value="2" />
            <el-option label="1星" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.target_type" placeholder="全部" clearable>
            <el-option label="场地" value="venue" />
            <el-option label="教练" value="coach" />
            <el-option label="活动" value="activity" />
            <el-option label="餐饮" value="food" />
          </el-select>
        </el-form-item>
        <el-form-item label="显示状态">
          <el-select v-model="searchForm.is_visible" placeholder="全部" clearable>
            <el-option label="显示" :value="true" />
            <el-option label="隐藏" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>评论管理</template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="会员" width="130">
          <template #default="{ row }">
            <div>{{ row.member_nickname || '-' }}</div>
            <div style="color: #999; font-size: 12px;">{{ row.member_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="评价对象" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ targetTypeMap[row.target_type] || row.target_type }}</el-tag>
            <div style="font-size: 12px; margin-top: 2px;">{{ row.target_name || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="130">
          <template #default="{ row }">
            <el-rate v-model="row.rating" disabled />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评价内容" min-width="200" show-overflow-tooltip />
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <span v-if="row.images && row.images.length">{{ row.images.length }}张</span>
            <span v-else style="color: #999;">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="reply" label="管理员回复" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.reply">{{ row.reply }}</span>
            <span v-else style="color: #999;">未回复</span>
          </template>
        </el-table-column>
        <el-table-column label="显示" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_visible" @change="handleToggleVisible(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="评价时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleReply(row)">回复</el-button>
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

    <!-- 回复弹窗 -->
    <el-dialog v-model="replyDialogVisible" title="回复评论" width="500px" destroy-on-close>
      <div style="margin-bottom: 16px;">
        <div style="margin-bottom: 8px; color: #666;">评论内容：</div>
        <div style="padding: 10px; background: #f5f7fa; border-radius: 4px;">{{ currentReview?.content }}</div>
      </div>
      <el-form label-width="80px">
        <el-form-item label="回复内容">
          <el-input v-model="replyContent" type="textarea" :rows="4" placeholder="请输入回复内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReplySubmit" :loading="replying">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getReviews, replyReview, toggleReviewVisible } from '@/api/review'

const targetTypeMap: Record<string, string> = {
  venue: '场地', coach: '教练', activity: '活动', food: '餐饮'
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ rating: null as number | null, target_type: '', is_visible: null as boolean | null })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const replyDialogVisible = ref(false)
const replying = ref(false)
const replyContent = ref('')
const currentReview = ref<any>(null)

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.rating !== null) params.rating = searchForm.rating
    if (searchForm.target_type) params.target_type = searchForm.target_type
    if (searchForm.is_visible !== null) params.is_visible = searchForm.is_visible
    const res = await getReviews(params)
    tableData.value = res.data?.list || res.data || []
    pagination.total = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.rating = null
  searchForm.target_type = ''
  searchForm.is_visible = null
  pagination.page = 1
  fetchList()
}

const handleToggleVisible = async (row: any) => {
  try {
    await toggleReviewVisible(row.id, { is_visible: row.is_visible })
    ElMessage.success(row.is_visible ? '已显示' : '已隐藏')
  } catch (e) {
    row.is_visible = !row.is_visible
    console.error('切换显示状态失败:', e)
  }
}

const handleReply = (row: any) => {
  currentReview.value = row
  replyContent.value = row.reply || ''
  replyDialogVisible.value = true
}

const handleReplySubmit = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  replying.value = true
  try {
    await replyReview(currentReview.value.id, { reply: replyContent.value.trim() })
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    fetchList()
  } finally {
    replying.value = false
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
</style>

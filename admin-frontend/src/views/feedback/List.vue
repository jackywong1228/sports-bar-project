<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已回复" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.category" placeholder="全部" clearable>
            <el-option label="建议" value="suggestion" />
            <el-option label="Bug" value="bug" />
            <el-option label="投诉" value="complaint" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="搜索反馈内容" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>反馈管理</template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="会员" width="130">
          <template #default="{ row }">
            <div>{{ row.member_nickname || '-' }}</div>
            <div style="color: #999; font-size: 12px;">{{ row.member_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="categoryTagType(row.category)">
              {{ categoryMap[row.category] || row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="反馈内容" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="管理员回复" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.admin_reply">{{ row.admin_reply }}</span>
            <span v-else style="color: #999;">未回复</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-button link type="primary" @click="handleReply(row)">回复</el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
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
    <el-dialog v-model="detailDialogVisible" title="反馈详情" width="600px" destroy-on-close>
      <template v-if="currentFeedback">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="会员">{{ currentFeedback.member_nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ currentFeedback.member_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ categoryMap[currentFeedback.category] }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="small" :type="statusTagType(currentFeedback.status)">
              {{ statusMap[currentFeedback.status] }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="联系方式" :span="2">{{ currentFeedback.contact || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间" :span="2">{{ currentFeedback.created_at }}</el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 16px;">
          <div style="font-weight: 500; margin-bottom: 8px;">反馈内容：</div>
          <div style="padding: 12px; background: #f5f7fa; border-radius: 4px; white-space: pre-wrap;">{{ currentFeedback.content }}</div>
        </div>

        <div v-if="parsedImages.length" style="margin-top: 16px;">
          <div style="font-weight: 500; margin-bottom: 8px;">图片：</div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-image
              v-for="(img, idx) in parsedImages"
              :key="idx"
              :src="img"
              :preview-src-list="parsedImages"
              style="width: 120px; height: 120px; border-radius: 4px;"
              fit="cover"
            />
          </div>
        </div>

        <div v-if="currentFeedback.admin_reply" style="margin-top: 16px;">
          <div style="font-weight: 500; margin-bottom: 8px;">管理员回复：</div>
          <div style="padding: 12px; background: #f0f9eb; border-radius: 4px; white-space: pre-wrap;">{{ currentFeedback.admin_reply }}</div>
          <div v-if="currentFeedback.reply_time" style="font-size: 12px; color: #999; margin-top: 4px;">回复时间：{{ currentFeedback.reply_time }}</div>
        </div>
      </template>
    </el-dialog>

    <!-- 回复弹窗 -->
    <el-dialog v-model="replyDialogVisible" title="回复反馈" width="500px" destroy-on-close>
      <div style="margin-bottom: 16px;">
        <div style="margin-bottom: 8px; color: #666;">反馈内容：</div>
        <div style="padding: 10px; background: #f5f7fa; border-radius: 4px;">{{ currentFeedback?.content }}</div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFeedbackList, getFeedbackDetail, replyFeedback, deleteFeedback } from '@/api/feedback'

const categoryMap: Record<string, string> = {
  suggestion: '建议', bug: 'Bug', complaint: '投诉', other: '其他'
}

const statusMap: Record<string, string> = {
  pending: '待处理', processing: '处理中', resolved: '已回复', closed: '已关闭'
}

const categoryTagType = (cat: string) => {
  const map: Record<string, string> = { suggestion: '', bug: 'danger', complaint: 'warning', other: 'info' }
  return map[cat] || 'info'
}

const statusTagType = (s: string) => {
  const map: Record<string, string> = { pending: 'info', processing: 'warning', resolved: 'success', closed: 'info' }
  return map[s] || 'info'
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ status: '', category: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const detailDialogVisible = ref(false)
const replyDialogVisible = ref(false)
const replying = ref(false)
const replyContent = ref('')
const currentFeedback = ref<any>(null)

const parsedImages = computed(() => {
  if (!currentFeedback.value?.images) return []
  try {
    const imgs = JSON.parse(currentFeedback.value.images)
    return Array.isArray(imgs) ? imgs : []
  } catch {
    return []
  }
})

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.status) params.status = searchForm.status
    if (searchForm.category) params.category = searchForm.category
    if (searchForm.keyword) params.keyword = searchForm.keyword
    const res = await getFeedbackList(params)
    tableData.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.status = ''
  searchForm.category = ''
  searchForm.keyword = ''
  pagination.page = 1
  fetchList()
}

const handleDetail = async (row: any) => {
  try {
    const res = await getFeedbackDetail(row.id)
    currentFeedback.value = res.data
    detailDialogVisible.value = true
  } catch (e) {
    console.error('获取详情失败:', e)
  }
}

const handleReply = (row: any) => {
  currentFeedback.value = row
  replyContent.value = row.admin_reply || ''
  replyDialogVisible.value = true
}

const handleReplySubmit = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  replying.value = true
  try {
    await replyFeedback(currentFeedback.value.id, { reply: replyContent.value.trim() })
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    fetchList()
  } finally {
    replying.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteFeedback(id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    console.error('删除失败:', e)
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

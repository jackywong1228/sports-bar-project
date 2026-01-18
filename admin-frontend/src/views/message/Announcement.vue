<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

const dialogVisible = ref(false)
const dialogTitle = ref('新增公告')
const formRef = ref()
const form = ref({
  id: null as number | null,
  title: '',
  content: '',
  type: 'normal',
  target: 'all',
  is_top: false,
  status: 'draft',
  start_time: '',
  end_time: ''
})

const rules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }]
}

const typeOptions = [
  { label: '普通公告', value: 'normal' },
  { label: '重要公告', value: 'important' },
  { label: '紧急公告', value: 'urgent' }
]

const targetOptions = [
  { label: '全部用户', value: 'all' },
  { label: '会员', value: 'member' },
  { label: '教练', value: 'coach' }
]

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已下线', value: 'offline' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/messages/announcements', { params: queryParams.value })
    tableData.value = res.data.list
    total.value = res.data.total
  } catch (err) {
    console.error('获取公告列表失败:', err)
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

const handleAdd = () => {
  dialogTitle.value = '新增公告'
  form.value = {
    id: null,
    title: '',
    content: '',
    type: 'normal',
    target: 'all',
    is_top: false,
    status: 'draft',
    start_time: '',
    end_time: ''
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑公告'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该公告吗？', '提示', { type: 'warning' })
    await request.delete(`/messages/announcements/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const handlePublish = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要发布该公告吗？', '提示', { type: 'info' })
    await request.put(`/messages/announcements/${row.id}/publish`)
    ElMessage.success('发布成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '发布失败')
    }
  }
}

const handleOffline = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要下线该公告吗？', '提示', { type: 'warning' })
    await request.put(`/messages/announcements/${row.id}`, { status: 'offline' })
    ElMessage.success('下线成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '下线失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (form.value.id) {
      await request.put(`/messages/announcements/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/messages/announcements', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  }
}

const handleSizeChange = (size: number) => {
  queryParams.value.page_size = size
  fetchData()
}

const handleCurrentChange = (page: number) => {
  queryParams.value.page = page
  fetchData()
}

const getTypeLabel = (type: string) => {
  const item = typeOptions.find(t => t.value === type)
  return item ? item.label : type
}

const getTypeTagType = (type: string) => {
  const map: Record<string, string> = { normal: 'info', important: 'warning', urgent: 'danger' }
  return map[type] || 'info'
}

const getStatusLabel = (status: string) => {
  const item = statusOptions.find(s => s.value === status)
  return item ? item.label : status
}

const getStatusTagType = (status: string) => {
  const map: Record<string, string> = { draft: 'info', published: 'success', offline: 'danger' }
  return map[status] || 'info'
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
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="公告标题" clearable style="width: 200px" />
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
        <div class="card-header">
          <span>公告列表</span>
          <el-button type="primary" @click="handleAdd">新增公告</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="公告标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="目标用户" width="100">
          <template #default="{ row }">
            {{ row.target === 'all' ? '全部' : row.target === 'member' ? '会员' : '教练' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_top" label="置顶" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_top" type="warning">置顶</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="170" />
        <el-table-column prop="start_time" label="生效时间" width="140" />
        <el-table-column prop="end_time" label="失效时间" width="140" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" link type="success" @click="handlePublish(row)">发布</el-button>
            <el-button v-if="row.status === 'published'" link type="warning" @click="handleOffline(row)">下线</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="公告标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="公告内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="请输入公告内容" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="公告类型">
              <el-select v-model="form.type" placeholder="请选择类型" style="width: 100%">
                <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标用户">
              <el-select v-model="form.target" placeholder="请选择目标" style="width: 100%">
                <el-option v-for="item in targetOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="生效时间">
              <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm" placeholder="选择生效时间" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失效时间">
              <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm" placeholder="选择失效时间" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="是否置顶">
          <el-switch v-model="form.is_top" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>

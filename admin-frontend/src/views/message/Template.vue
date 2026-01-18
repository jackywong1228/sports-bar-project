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
  type: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增模板')
const formRef = ref()
const form = ref({
  id: null as number | null,
  code: '',
  name: '',
  type: 'system',
  title: '',
  content: '',
  variables: '',
  push_wechat: true,
  wechat_template_id: '',
  is_active: true
})

const rules = {
  code: [{ required: true, message: '请输入模板编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择消息类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入消息标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }]
}

const typeOptions = [
  { label: '系统通知', value: 'system' },
  { label: '活动通知', value: 'activity' },
  { label: '订单通知', value: 'order' },
  { label: '预约通知', value: 'reservation' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/messages/templates', { params: queryParams.value })
    tableData.value = res.data.list
    total.value = res.data.total
  } catch (err) {
    console.error('获取模板列表失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.value.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.value = { page: 1, page_size: 10, keyword: '', type: '' }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增模板'
  form.value = {
    id: null,
    code: '',
    name: '',
    type: 'system',
    title: '',
    content: '',
    variables: '',
    push_wechat: true,
    wechat_template_id: '',
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑模板'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该模板吗？', '提示', { type: 'warning' })
    await request.delete(`/messages/templates/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (form.value.id) {
      await request.put(`/messages/templates/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/messages/templates', form.value)
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
          <el-input v-model="queryParams.keyword" placeholder="模板编码/名称" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryParams.type" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
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
          <span>消息模板列表</span>
          <el-button type="primary" @click="handleAdd">新增模板</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="code" label="模板编码" width="150" />
        <el-table-column prop="name" label="模板名称" width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="消息标题" show-overflow-tooltip />
        <el-table-column prop="push_wechat" label="微信推送" width="100">
          <template #default="{ row }">
            <el-tag :type="row.push_wechat ? 'success' : 'info'">{{ row.push_wechat ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模板编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入模板编码" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="消息类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择消息类型">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入消息标题" />
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请输入消息内容，支持变量如 {member_name}" />
        </el-form-item>
        <el-form-item label="变量说明">
          <el-input v-model="form.variables" type="textarea" :rows="2" placeholder="变量说明，如：member_name=会员名称" />
        </el-form-item>
        <el-form-item label="微信推送">
          <el-switch v-model="form.push_wechat" />
        </el-form-item>
        <el-form-item label="微信模板ID" v-if="form.push_wechat">
          <el-input v-model="form.wechat_template_id" placeholder="请输入微信订阅消息模板ID" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
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

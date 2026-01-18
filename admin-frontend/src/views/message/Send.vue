<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const total = ref(0)
const queryParams = ref({
  page: 1,
  page_size: 10,
  receiver_type: '',
  type: '',
  is_read: ''
})

const dialogVisible = ref(false)
const formRef = ref()
const form = ref({
  receiver_type: 'all',
  receiver_ids: [] as number[],
  type: 'system',
  title: '',
  content: ''
})

const rules = {
  title: [{ required: true, message: '请输入消息标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }]
}

const typeOptions = [
  { label: '系统通知', value: 'system' },
  { label: '活动通知', value: 'activity' },
  { label: '订单通知', value: 'order' },
  { label: '预约通知', value: 'reservation' }
]

const receiverTypeOptions = [
  { label: '全部', value: 'all' },
  { label: '会员', value: 'member' },
  { label: '教练', value: 'coach' }
]

const memberOptions = ref<any[]>([])
const coachOptions = ref<any[]>([])

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = { ...queryParams.value }
    if (params.is_read === '') delete params.is_read
    const res = await request.get('/messages/list', { params })
    tableData.value = res.data.list
    total.value = res.data.total
  } catch (err) {
    console.error('获取消息列表失败:', err)
  } finally {
    loading.value = false
  }
}

const fetchMembers = async () => {
  try {
    const res = await request.get('/members', { params: { page: 1, page_size: 100 } })
    memberOptions.value = res.data.list || []
  } catch (err) {
    console.error('获取会员列表失败:', err)
  }
}

const fetchCoaches = async () => {
  try {
    const res = await request.get('/coaches', { params: { page: 1, page_size: 100, status: 1 } })
    coachOptions.value = res.data.items || []
  } catch (err) {
    console.error('获取教练列表失败:', err)
  }
}

const handleSearch = () => {
  queryParams.value.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.value = { page: 1, page_size: 10, receiver_type: '', type: '', is_read: '' }
  fetchData()
}

const handleSend = () => {
  form.value = {
    receiver_type: 'all',
    receiver_ids: [],
    type: 'system',
    title: '',
    content: ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    await request.post('/messages/send', form.value)
    ElMessage.success('发送成功')
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

const getReceiverTypeLabel = (type: string) => {
  const item = receiverTypeOptions.find(t => t.value === type)
  return item ? item.label : type
}

onMounted(() => {
  fetchData()
  fetchMembers()
  fetchCoaches()
})
</script>

<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="接收者类型">
          <el-select v-model="queryParams.receiver_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="会员" value="member" />
            <el-option label="教练" value="coach" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息类型">
          <el-select v-model="queryParams.type" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.is_read" placeholder="全部" clearable style="width: 100px">
            <el-option label="未读" :value="false" />
            <el-option label="已读" :value="true" />
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
          <span>消息列表</span>
          <el-button type="primary" @click="handleSend">发送消息</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="消息标题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="content" label="消息内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="receiver_type" label="接收者类型" width="100">
          <template #default="{ row }">{{ getReceiverTypeLabel(row.receiver_type) }}</template>
        </el-table-column>
        <el-table-column prop="receiver_name" label="接收者" width="120" />
        <el-table-column prop="is_read" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'success' : 'warning'">{{ row.is_read ? '已读' : '未读' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="read_time" label="阅读时间" width="170" />
        <el-table-column prop="created_at" label="发送时间" width="170" />
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

    <!-- 发送消息弹窗 -->
    <el-dialog v-model="dialogVisible" title="发送消息" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="接收者类型">
          <el-radio-group v-model="form.receiver_type">
            <el-radio v-for="item in receiverTypeOptions" :key="item.value" :value="item.value">{{ item.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择会员" v-if="form.receiver_type === 'member'">
          <el-select v-model="form.receiver_ids" multiple placeholder="不选则发送给所有会员" style="width: 100%">
            <el-option v-for="item in memberOptions" :key="item.id" :label="item.nickname" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择教练" v-if="form.receiver_type === 'coach'">
          <el-select v-model="form.receiver_ids" multiple placeholder="不选则发送给所有教练" style="width: 100%">
            <el-option v-for="item in coachOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息类型">
          <el-select v-model="form.type" placeholder="请选择消息类型">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入消息标题" />
        </el-form-item>
        <el-form-item label="消息内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请输入消息内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">发送</el-button>
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

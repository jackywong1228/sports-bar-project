<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="活动标题" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="ended" />
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
        <div class="card-header">
          <span>活动列表</span>
          <el-button type="primary" @click="handleAdd">新增活动</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="活动标题" min-width="180" />
        <el-table-column label="封面" width="100">
          <template #default="{ row }">
            <el-image v-if="row.cover_image" :src="row.cover_image" :preview-src-list="[row.cover_image]" fit="cover" style="width: 60px; height: 60px;" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="活动地点" width="150" />
        <el-table-column label="活动时间" width="180">
          <template #default="{ row }">
            <div>{{ row.start_time }}</div>
            <div>至 {{ row.end_time }}</div>
          </template>
        </el-table-column>
        <el-table-column label="报名人数" width="100">
          <template #default="{ row }">
            {{ row.current_participants }} / {{ row.max_participants || '不限' }}
          </template>
        </el-table-column>
        <el-table-column prop="price" label="报名费(金币)" width="110" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleRegistrations(row)">报名</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="活动标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入活动标题" />
        </el-form-item>
        <el-form-item label="封面图片" prop="cover_image">
          <el-input v-model="formData.cover_image" placeholder="请输入图片URL" />
        </el-form-item>
        <el-form-item label="活动描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入活动描述" />
        </el-form-item>
        <el-form-item label="活动详情">
          <el-input v-model="formData.content" type="textarea" :rows="4" placeholder="请输入活动详情" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker v-model="formData.start_time" type="datetime" placeholder="选择开始时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker v-model="formData.end_time" type="datetime" placeholder="选择结束时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="报名截止">
          <el-date-picker v-model="formData.registration_deadline" type="datetime" placeholder="选择报名截止时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="活动地点">
          <el-input v-model="formData.location" placeholder="请输入活动地点" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大人数">
              <el-input-number v-model="formData.max_participants" :min="0" placeholder="0表示不限" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报名费用">
              <el-input-number v-model="formData.price" :min="0" :precision="2" placeholder="金币" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="formData.status" style="width: 100%;">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="进行中" value="ongoing" />
                <el-option label="已结束" value="ended" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="formData.sort_order" :min="0" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标签">
          <el-input v-model="formData.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 报名列表弹窗 -->
    <el-dialog v-model="regDialogVisible" title="报名列表" width="800px" destroy-on-close>
      <el-table :data="regTableData" v-loading="regLoading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="member_nickname" label="会员昵称" width="120" />
        <el-table-column prop="name" label="报名姓名" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="pay_amount" label="支付金额" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'attended' ? 'success' : (row.status === 'cancelled' ? 'info' : '')">
              {{ row.status === 'attended' ? '已签到' : (row.status === 'cancelled' ? '已取消' : '已报名') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="check_in_time" label="签到时间" width="160" />
        <el-table-column prop="created_at" label="报名时间" width="160" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button v-if="row.status === 'registered'" link type="primary" @click="handleCheckIn(row)">签到</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="regPagination.page"
        v-model:page-size="regPagination.pageSize"
        :total="regPagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchRegistrations"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import request from '@/utils/request'

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: '' },
  ongoing: { label: '进行中', type: 'success' },
  ended: { label: '已结束', type: 'warning' },
  cancelled: { label: '已取消', type: 'danger' }
}

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  id: 0,
  title: '',
  cover_image: '',
  description: '',
  content: '',
  start_time: '',
  end_time: '',
  registration_deadline: '',
  location: '',
  max_participants: 0,
  price: 0,
  status: 'draft',
  tags: '',
  sort_order: 0
})
const formRules = {
  title: [{ required: true, message: '请输入活动标题', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

const regDialogVisible = ref(false)
const regLoading = ref(false)
const regTableData = ref<any[]>([])
const regPagination = reactive({ page: 1, pageSize: 10, total: 0 })
let currentActivityId = 0

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/activities', {
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

const handleAdd = () => {
  dialogTitle.value = '新增活动'
  Object.assign(formData, {
    id: 0, title: '', cover_image: '', description: '', content: '',
    start_time: '', end_time: '', registration_deadline: '', location: '',
    max_participants: 0, price: 0, status: 'draft', tags: '', sort_order: 0
  })
  dialogVisible.value = true
}

const handleEdit = async (row: any) => {
  dialogTitle.value = '编辑活动'
  const res = await request.get(`/activities/${row.id}`)
  Object.assign(formData, res.data)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await request.put(`/activities/${formData.id}`, formData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/activities/create', formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该活动吗？', '提示', { type: 'warning' })
    .then(async () => {
      await request.delete(`/activities/${row.id}`)
      ElMessage.success('删除成功')
      fetchList()
    })
}

const handleRegistrations = (row: any) => {
  currentActivityId = row.id
  regPagination.page = 1
  fetchRegistrations()
  regDialogVisible.value = true
}

const fetchRegistrations = async () => {
  regLoading.value = true
  try {
    const res = await request.get(`/activities/${currentActivityId}/registrations`, {
      params: { page: regPagination.page, page_size: regPagination.pageSize }
    })
    regTableData.value = res.data.list
    regPagination.total = res.data.total
  } finally {
    regLoading.value = false
  }
}

const handleCheckIn = async (row: any) => {
  await request.put(`/activities/registrations/${row.id}/check-in`)
  ElMessage.success('签到成功')
  fetchRegistrations()
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

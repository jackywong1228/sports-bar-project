<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface Coach {
  id: number
  coach_no: string
  name: string
  phone: string
  avatar: string
  gender: number
  type: string
  level: number
  price: number
  introduction: string
  status: number
  total_courses: number
  total_income: number
  created_at: string
}

const loading = ref(false)
const tableData = ref<Coach[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  name: '',
  coach_no: '',
  type: '',
  status: null as number | null
})

const statusOptions = [
  { label: '离职', value: 0 },
  { label: '在职', value: 1 },
  { label: '休假', value: 2 }
]

const statusMap: Record<number, { text: string; type: string }> = {
  0: { text: '离职', type: 'danger' },
  1: { text: '在职', type: 'success' },
  2: { text: '休假', type: 'warning' }
}

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = reactive({
  id: 0,
  name: '',
  phone: '',
  gender: 0,
  type: 'technical',
  level: 1,
  price: 0,
  introduction: '',
  status: 1
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入电话', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/coaches', { params: queryParams })
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.name = ''
  queryParams.coach_no = ''
  queryParams.type = ''
  queryParams.status = null
  handleSearch()
}

const handleAdd = () => {
  dialogTitle.value = '新增教练'
  Object.assign(form, {
    id: 0,
    name: '',
    phone: '',
    gender: 0,
    type: 'technical',
    level: 1,
    price: 0,
    introduction: '',
    status: 1
  })
  dialogVisible.value = true
}

const handleEdit = (row: Coach) => {
  dialogTitle.value = '编辑教练'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.id) {
      await request.put(`/coaches/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/coaches', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: Coach) => {
  try {
    await ElMessageBox.confirm('确定要删除该教练吗？', '提示', { type: 'warning' })
    await request.delete(`/coaches/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

const genderText = (gender: number) => {
  return { 0: '未知', 1: '男', 2: '女' }[gender] || '未知'
}

const typeText = (type: string) => {
  return { technical: '技术型', entertainment: '娱乐型' }[type] || type
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="姓名">
          <el-input v-model="queryParams.name" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="编号">
          <el-input v-model="queryParams.coach_no" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryParams.type" placeholder="全部" clearable>
            <el-option label="技术型" value="technical" />
            <el-option label="娱乐型" value="entertainment" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable>
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>教练列表</span>
          <el-button type="primary" @click="handleAdd">新增教练</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="coach_no" label="编号" width="180" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column label="性别" width="60">
          <template #default="{ row }">{{ genderText(row.gender) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ typeText(row.type) }}</template>
        </el-table-column>
        <el-table-column prop="level" label="星级" width="80">
          <template #default="{ row }">
            <el-rate v-model="row.level" disabled />
          </template>
        </el-table-column>
        <el-table-column prop="price" label="课时单价" width="100" />
        <el-table-column prop="total_courses" label="累计课程" width="100" />
        <el-table-column prop="total_income" label="累计收入" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any">
              {{ statusMap[row.status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
        @change="fetchData"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="0">未知</el-radio>
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width: 100%;">
            <el-option label="技术型" value="technical" />
            <el-option label="娱乐型" value="entertainment" />
          </el-select>
        </el-form-item>
        <el-form-item label="星级">
          <el-rate v-model="form.level" />
        </el-form-item>
        <el-form-item label="课时单价">
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.introduction" type="textarea" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
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
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

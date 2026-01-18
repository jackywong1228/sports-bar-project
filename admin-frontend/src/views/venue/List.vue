<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface Venue {
  id: number
  name: string
  type_id: number
  type_name: string
  location: string
  capacity: number
  price: number
  status: number
  sort: number
}

const loading = ref(false)
const tableData = ref<Venue[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  name: '',
  type_id: null as number | null,
  status: null as number | null
})

const venueTypes = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = reactive({
  id: 0,
  name: '',
  type_id: null as number | null,
  location: '',
  capacity: 0,
  price: 0,
  description: '',
  status: 1,
  sort: 0
})

const rules = {
  name: [{ required: true, message: '请输入场地名称', trigger: 'blur' }],
  type_id: [{ required: true, message: '请选择场地类型', trigger: 'change' }]
}

const statusOptions = [
  { label: '停用', value: 0 },
  { label: '空闲', value: 1 },
  { label: '使用中', value: 2 }
]

const statusMap: Record<number, { text: string; type: string }> = {
  0: { text: '停用', type: 'danger' },
  1: { text: '空闲', type: 'success' },
  2: { text: '使用中', type: 'warning' }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/venues', { params: queryParams })
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const fetchTypes = async () => {
  const res = await request.get('/venues/types')
  venueTypes.value = res.data
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.name = ''
  queryParams.type_id = null
  queryParams.status = null
  handleSearch()
}

const handleAdd = () => {
  dialogTitle.value = '新增场地'
  Object.assign(form, {
    id: 0,
    name: '',
    type_id: null,
    location: '',
    capacity: 0,
    price: 0,
    description: '',
    status: 1,
    sort: 0
  })
  dialogVisible.value = true
}

const handleEdit = (row: Venue) => {
  dialogTitle.value = '编辑场地'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.id) {
      await request.put(`/venues/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/venues', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: Venue) => {
  try {
    await ElMessageBox.confirm('确定要删除该场地吗？', '提示', { type: 'warning' })
    await request.delete(`/venues/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

onMounted(() => {
  fetchData()
  fetchTypes()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="场地名称">
          <el-input v-model="queryParams.name" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="场地类型">
          <el-select v-model="queryParams.type_id" placeholder="全部" clearable>
            <el-option v-for="t in venueTypes" :key="t.id" :label="t.name" :value="t.id" />
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
          <span>场地列表</span>
          <el-button type="primary" @click="handleAdd">新增场地</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="场地名称" width="150" />
        <el-table-column prop="type_name" label="场地类型" width="120" />
        <el-table-column prop="location" label="位置" width="150" />
        <el-table-column prop="capacity" label="容纳人数" width="100" />
        <el-table-column prop="price" label="价格(金币/小时)" width="130" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any">
              {{ statusMap[row.status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="80" />
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
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="场地名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="场地类型" prop="type_id">
          <el-select v-model="form.type_id" style="width: 100%;">
            <el-option v-for="t in venueTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="容纳人数">
          <el-input-number v-model="form.capacity" :min="0" />
        </el-form-item>
        <el-form-item label="价格(金币)">
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
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

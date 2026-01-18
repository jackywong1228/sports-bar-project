<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface User {
  id: number
  username: string
  name: string
  phone: string
  email: string
  department_id: number
  department_name: string
  status: boolean
  role_ids: number[]
  role_names: string[]
  created_at: string
}

const loading = ref(false)
const tableData = ref<User[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  username: '',
  name: '',
  phone: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = reactive({
  id: 0,
  username: '',
  password: '',
  name: '',
  phone: '',
  email: '',
  department_id: null as number | null,
  status: true,
  role_ids: [] as number[]
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const departments = ref<any[]>([])
const roles = ref<any[]>([])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/staff/users', { params: queryParams })
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const fetchDepartments = async () => {
  const res = await request.get('/staff/departments')
  departments.value = res.data
}

const fetchRoles = async () => {
  const res = await request.get('/staff/roles', { params: { page: 1, page_size: 100 } })
  roles.value = res.data.items
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.username = ''
  queryParams.name = ''
  queryParams.phone = ''
  handleSearch()
}

const handleAdd = () => {
  dialogTitle.value = '新增用户'
  Object.assign(form, {
    id: 0,
    username: '',
    password: '',
    name: '',
    phone: '',
    email: '',
    department_id: null,
    status: true,
    role_ids: []
  })
  dialogVisible.value = true
}

const handleEdit = (row: User) => {
  dialogTitle.value = '编辑用户'
  Object.assign(form, {
    id: row.id,
    username: row.username,
    password: '',
    name: row.name,
    phone: row.phone,
    email: row.email,
    department_id: row.department_id,
    status: row.status,
    role_ids: row.role_ids
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.id) {
      const { password, username, ...updateData } = form
      await request.put(`/staff/users/${form.id}`, updateData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/staff/users', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: User) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' })
    await request.delete(`/staff/users/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

const handleStatusChange = async (row: User) => {
  try {
    await request.put(`/staff/users/${row.id}/status?status=${row.status}`)
    ElMessage.success('更新成功')
  } catch {
    row.status = !row.status
  }
}

onMounted(() => {
  fetchData()
  fetchDepartments()
  fetchRoles()
})
</script>

<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="用户名">
          <el-input v-model="queryParams.username" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="queryParams.name" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="queryParams.phone" placeholder="请输入" clearable />
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
          <span>用户列表</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="department_name" label="部门" width="120" />
        <el-table-column prop="role_names" label="角色" width="150">
          <template #default="{ row }">
            <el-tag v-for="name in row.role_names" :key="name" size="small" style="margin-right: 4px;">
              {{ name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.status" @change="handleStatusChange(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
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

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="部门">
          <el-tree-select
            v-model="form.department_id"
            :data="departments"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            check-strictly
            clearable
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple style="width: 100%;">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" />
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

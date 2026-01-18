<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface Department {
  id: number
  name: string
  parent_id: number | null
  sort: number
  status: boolean
  remark: string
  children?: Department[]
}

const loading = ref(false)
const tableData = ref<Department[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = reactive({
  id: 0,
  name: '',
  parent_id: null as number | null,
  sort: 0,
  status: true,
  remark: ''
})

const rules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/staff/departments')
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

const handleAdd = (parentId: number | null = null) => {
  dialogTitle.value = '新增部门'
  Object.assign(form, {
    id: 0,
    name: '',
    parent_id: parentId,
    sort: 0,
    status: true,
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: Department) => {
  dialogTitle.value = '编辑部门'
  Object.assign(form, {
    id: row.id,
    name: row.name,
    parent_id: row.parent_id,
    sort: row.sort,
    status: row.status,
    remark: row.remark
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.id) {
      await request.put(`/staff/departments/${form.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await request.post('/staff/departments', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: Department) => {
  try {
    await ElMessageBox.confirm('确定要删除该部门吗？', '提示', { type: 'warning' })
    await request.delete(`/staff/departments/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>部门管理</span>
          <el-button type="primary" @click="handleAdd(null)">新增部门</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" row-key="id" default-expand-all>
        <el-table-column prop="name" label="部门名称" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleAdd(row.id)">新增子部门</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="上级部门">
          <el-tree-select
            v-model="form.parent_id"
            :data="tableData"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            check-strictly
            clearable
            style="width: 100%;"
            placeholder="无 (顶级部门)"
          />
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" />
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

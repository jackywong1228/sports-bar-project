<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>菜品分类</span>
          <el-button type="primary" @click="handleAdd">新增分类</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="分类名称" min-width="140" />
        <el-table-column label="图标" width="100">
          <template #default="{ row }">
            <el-image v-if="row.icon" :src="row.icon" fit="cover" style="width: 40px; height: 40px;" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_count" label="菜品数" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.item_count > 0 ? '' : 'info'">{{ row.item_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="100" />
        <el-table-column prop="is_active" label="状态" width="110">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val: boolean) => handleToggle(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="如：酒水饮料 / 简餐小食 / 咖啡饮品" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="formData.icon" placeholder="图标图片URL（选填）" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" />
          <span class="form-tip">数值越大越靠前</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  getFoodCategories,
  createFoodCategory,
  updateFoodCategory,
  deleteFoodCategory,
  type FoodCategory
} from '@/api/food'

const loading = ref(false)
const tableData = ref<FoodCategory[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({ id: 0, name: '', icon: '', sort_order: 0, is_active: true })
const formRules = { name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }] }

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getFoodCategories()
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增分类'
  Object.assign(formData, { id: 0, name: '', icon: '', sort_order: 0, is_active: true })
  dialogVisible.value = true
}

const handleEdit = (row: FoodCategory) => {
  dialogTitle.value = '编辑分类'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    icon: row.icon || '',
    sort_order: row.sort_order,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = {
      name: formData.name,
      icon: formData.icon || null,
      sort_order: formData.sort_order,
      is_active: formData.is_active
    }
    if (formData.id) {
      await updateFoodCategory(formData.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createFoodCategory(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleToggle = async (row: FoodCategory, val: boolean) => {
  try {
    await updateFoodCategory(row.id, {
      name: row.name,
      icon: row.icon,
      sort_order: row.sort_order,
      is_active: val
    })
    row.is_active = val
    ElMessage.success(val ? '已启用' : '已停用')
  } catch {
    // 报错提示由拦截器统一处理
  }
}

const handleDelete = (row: FoodCategory) => {
  const tip = row.item_count > 0
    ? `该分类下还有 ${row.item_count} 个菜品，删除将被后端拒绝，确定继续吗？`
    : '确定要删除该分类吗？'
  ElMessageBox.confirm(tip, '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    .then(async () => {
      await deleteFoodCategory(row.id)
      ElMessage.success('删除成功')
      fetchList()
    })
    .catch(() => {})
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.form-tip { margin-left: 10px; color: #909399; font-size: 12px; }
</style>

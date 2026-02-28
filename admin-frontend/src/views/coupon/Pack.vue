<template>
  <div class="page-container">
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>优惠券合集</span>
          <el-button type="primary" @click="handleAdd">新增合集</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="合集名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="包含券数" width="100" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.item_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="售价(元)" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleItems(row)">明细</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑合集弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="合集名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入合集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="售价(元)" prop="price">
          <el-input-number v-model="formData.price" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 合集明细弹窗 -->
    <el-dialog v-model="itemDialogVisible" :title="`合集明细 - ${currentPack?.name || ''}`" width="700px" destroy-on-close>
      <div style="margin-bottom: 16px; text-align: right;">
        <el-button type="primary" size="small" @click="showAddItem = true">添加优惠券</el-button>
      </div>

      <el-table :data="itemList" v-loading="itemLoading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="coupon_template_name" label="优惠券名称" min-width="150" />
        <el-table-column prop="coupon_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag>{{ typeMap[row.coupon_type] || row.coupon_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleRemoveItem(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 添加优惠券行 -->
      <div v-if="showAddItem" style="margin-top: 16px; display: flex; gap: 12px; align-items: center;">
        <el-select v-model="newItem.coupon_template_id" placeholder="选择优惠券模板" filterable style="flex: 1;">
          <el-option v-for="t in couponTemplates" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-input-number v-model="newItem.quantity" :min="1" placeholder="数量" style="width: 120px;" />
        <el-button type="primary" size="small" @click="handleAddItem">确定</el-button>
        <el-button size="small" @click="showAddItem = false">取消</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { getCouponPacks, createCouponPack, updateCouponPack, deleteCouponPack, getPackItems, addPackItem, removePackItem } from '@/api/couponPack'
import request from '@/utils/request'

const typeMap: Record<string, string> = { discount: '折扣券', cash: '代金券', gift: '礼品券', experience: '体验券' }

const loading = ref(false)
const tableData = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  id: 0,
  name: '',
  description: '',
  price: 0,
  sort_order: 0,
  is_active: true
})
const formRules = {
  name: [{ required: true, message: '请输入合集名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }]
}

// 合集明细相关
const itemDialogVisible = ref(false)
const itemLoading = ref(false)
const itemList = ref<any[]>([])
const currentPack = ref<any>(null)
const showAddItem = ref(false)
const newItem = reactive({ coupon_template_id: null as number | null, quantity: 1 })
const couponTemplates = ref<any[]>([])

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getCouponPacks()
    tableData.value = res.data || []
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增合集'
  Object.assign(formData, { id: 0, name: '', description: '', price: 0, sort_order: 0, is_active: true })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑合集'
  Object.assign(formData, { id: row.id, name: row.name, description: row.description, price: row.price, sort_order: row.sort_order, is_active: row.is_active })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data = { name: formData.name, description: formData.description, price: formData.price, sort_order: formData.sort_order, is_active: formData.is_active }
    if (formData.id) {
      await updateCouponPack(formData.id, data)
      ElMessage.success('更新成功')
    } else {
      await createCouponPack(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该合集吗？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteCouponPack(row.id)
      ElMessage.success('删除成功')
      fetchList()
    })
}

const handleItems = async (row: any) => {
  currentPack.value = row
  showAddItem.value = false
  newItem.coupon_template_id = null
  newItem.quantity = 1
  itemDialogVisible.value = true
  fetchItems(row.id)
  fetchCouponTemplates()
}

const fetchItems = async (packId: number) => {
  itemLoading.value = true
  try {
    const res = await getPackItems(packId)
    itemList.value = res.data || []
  } finally {
    itemLoading.value = false
  }
}

const fetchCouponTemplates = async () => {
  try {
    const res = await request.get('/coupons/templates', { params: { page_size: 100, is_active: true } })
    couponTemplates.value = res.data?.list || res.data || []
  } catch (e) {
    console.error('获取优惠券模板失败:', e)
  }
}

const handleAddItem = async () => {
  if (!newItem.coupon_template_id) {
    ElMessage.warning('请选择优惠券模板')
    return
  }
  try {
    await addPackItem(currentPack.value.id, { coupon_template_id: newItem.coupon_template_id, quantity: newItem.quantity })
    ElMessage.success('添加成功')
    showAddItem.value = false
    newItem.coupon_template_id = null
    newItem.quantity = 1
    fetchItems(currentPack.value.id)
    fetchList()
  } catch (e) {
    console.error('添加失败:', e)
  }
}

const handleRemoveItem = (row: any) => {
  ElMessageBox.confirm('确定要移除该优惠券吗？', '提示', { type: 'warning' })
    .then(async () => {
      await removePackItem(currentPack.value.id, row.id)
      ElMessage.success('移除成功')
      fetchItems(currentPack.value.id)
      fetchList()
    })
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

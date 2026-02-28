<template>
  <div class="page-container">
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>充值套餐配置</span>
          <el-button type="primary" @click="handleAdd">新增套餐</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="套餐名称" min-width="130" />
        <el-table-column prop="amount" label="充值金额(元)" width="120" />
        <el-table-column prop="coins" label="获得金币" width="100" />
        <el-table-column prop="bonus_coins" label="赠送金币" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.bonus_coins > 0 ? '#E6A23C' : '' }">{{ row.bonus_coins || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="总金币" width="100">
          <template #default="{ row }">
            <strong>{{ (row.coins || 0) + (row.bonus_coins || 0) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="套餐名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入套餐名称" />
        </el-form-item>
        <el-form-item label="充值金额" prop="amount">
          <el-input-number v-model="formData.amount" :min="0.01" :precision="2" style="width: 100%;" />
          <div class="form-tip">用户实际支付的金额（元）</div>
        </el-form-item>
        <el-form-item label="获得金币" prop="coins">
          <el-input-number v-model="formData.coins" :min="1" style="width: 100%;" />
          <div class="form-tip">充值后直接获得的金币数量</div>
        </el-form-item>
        <el-form-item label="赠送金币">
          <el-input-number v-model="formData.bonus_coins" :min="0" style="width: 100%;" />
          <div class="form-tip">额外赠送的金币数量（0表示不赠送）</div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" style="width: 100%;" />
          <div class="form-tip">数值越小越靠前</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="停用" />
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
import { getRechargePackages, createRechargePackage, updateRechargePackage, deleteRechargePackage } from '@/api/rechargePackage'

const loading = ref(false)
const tableData = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: 0,
  name: '',
  amount: 0,
  coins: 0,
  bonus_coins: 0,
  sort_order: 0,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入充值金额', trigger: 'blur' }],
  coins: [{ required: true, message: '请输入获得金币数', trigger: 'blur' }]
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getRechargePackages()
    tableData.value = res.data || []
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增套餐'
  Object.assign(formData, { id: 0, name: '', amount: 0, coins: 0, bonus_coins: 0, sort_order: 0, is_active: true })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑套餐'
  Object.assign(formData, {
    id: row.id, name: row.name, amount: row.amount, coins: row.coins,
    bonus_coins: row.bonus_coins || 0, sort_order: row.sort_order || 0, is_active: row.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data = {
      name: formData.name, amount: formData.amount, coins: formData.coins,
      bonus_coins: formData.bonus_coins, sort_order: formData.sort_order, is_active: formData.is_active
    }
    if (formData.id) {
      await updateRechargePackage(formData.id, data)
      ElMessage.success('更新成功')
    } else {
      await createRechargePackage(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该套餐吗？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteRechargePackage(row.id)
      ElMessage.success('删除成功')
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
.form-tip { font-size: 12px; color: #999; }
</style>

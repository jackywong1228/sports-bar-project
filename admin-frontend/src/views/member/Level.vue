<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface MemberLevel {
  id: number
  name: string
  level: number
  type: string
  discount: number
  icon: string
  description: string
  venue_permissions: any
  benefits: string
  status: boolean
}

const loading = ref(false)
const tableData = ref<MemberLevel[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref({
  id: 0,
  name: '',
  level: 1,
  type: 'normal',
  discount: 1.00,
  icon: '',
  description: '',
  venue_permissions: '',
  benefits: '',
  status: true
})

const rules = {
  name: [{ required: true, message: '请输入等级名称', trigger: 'blur' }],
  level: [{ required: true, message: '请输入等级值', trigger: 'blur' }],
  type: [{ required: true, message: '请选择等级类型', trigger: 'change' }]
}

const typeOptions = [
  { label: '普通会员', value: 'normal', color: '#909399' },
  { label: '健身会员', value: 'fitness', color: '#67C23A' },
  { label: '球类会员', value: 'ball', color: '#409EFF' },
  { label: '顶级会员', value: 'vip', color: '#E6A23C' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/member-cards/levels')
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增等级'
  form.value = {
    id: 0,
    name: '',
    level: tableData.value.length + 1,
    type: 'normal',
    discount: 1.00,
    icon: '',
    description: '',
    venue_permissions: '',
    benefits: '',
    status: true
  }
  dialogVisible.value = true
}

const handleEdit = (row: MemberLevel) => {
  dialogTitle.value = '编辑等级'
  form.value = {
    ...row,
    venue_permissions: row.venue_permissions ? JSON.stringify(row.venue_permissions, null, 2) : ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const submitData = { ...form.value }
    // 解析场馆权限JSON
    if (submitData.venue_permissions) {
      try {
        submitData.venue_permissions = JSON.parse(submitData.venue_permissions)
      } catch {
        ElMessage.error('场馆权限格式错误，请输入有效的JSON')
        return
      }
    }

    if (form.value.id) {
      await request.put(`/member-cards/levels/${form.value.id}`, submitData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/member-cards/levels', submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) {
    if (e.message) {
      ElMessage.error(e.message)
    }
  }
}

const handleDelete = async (row: MemberLevel) => {
  try {
    await ElMessageBox.confirm('确定要删除该等级吗？', '提示', { type: 'warning' })
    await request.delete(`/member-cards/levels/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) {
    if (e !== 'cancel' && e.message) {
      ElMessage.error(e.message)
    }
  }
}

const getTypeLabel = (type: string) => {
  const item = typeOptions.find(t => t.value === type)
  return item ? item.label : type
}

const getTypeColor = (type: string) => {
  const item = typeOptions.find(t => t.value === type)
  return item ? item.color : '#909399'
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
          <span>会员等级</span>
          <el-button type="primary" @click="handleAdd">新增等级</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="level" label="等级值" width="80" />
        <el-table-column prop="name" label="等级名称" width="120" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :color="getTypeColor(row.type)" effect="dark">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discount" label="折扣率" width="100">
          <template #default="{ row }">{{ (row.discount * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="benefits" label="会员权益" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="等级名称" prop="name">
              <el-input v-model="form.name" placeholder="如：顶级会员" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="等级值" prop="level">
              <el-input-number v-model="form.level" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="等级类型" prop="type">
              <el-select v-model="form.type" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value">
                  <span :style="{ color: item.color }">{{ item.label }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="折扣率">
              <el-input-number v-model="form.discount" :min="0.5" :max="1" :step="0.01" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="等级图标">
          <el-input v-model="form.icon" placeholder="图标URL地址" />
        </el-form-item>
        <el-form-item label="等级描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="描述该等级的特点" />
        </el-form-item>
        <el-form-item label="会员权益">
          <el-input v-model="form.benefits" type="textarea" :rows="3" placeholder="描述该等级的权益，如：免费使用健身房、优先预约等" />
        </el-form-item>
        <el-form-item label="场馆权限">
          <el-input v-model="form.venue_permissions" type="textarea" :rows="4" placeholder="JSON格式，如：{&quot;free_venues&quot;: [1,2,3], &quot;discount_venues&quot;: {&quot;4&quot;: 0.8}}" />
          <div class="form-tip">配置该等级可使用的场馆权限，JSON格式，留空表示无特殊权限</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" active-text="启用" inactive-text="禁用" />
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
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

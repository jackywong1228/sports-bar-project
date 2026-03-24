<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface MemberLevel {
  id: number
  name: string
  level: number
  level_code: string
  type: string
  discount: number
  icon: string
  description: string
  venue_permissions: any
  benefits: string
  status: boolean
  can_book_venue: boolean
  daily_free_hours: number
  monthly_invite_count: number
  display_benefits: string[]
  booking_range_days: number
  theme_color: string
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
  status: true,
  can_book_venue: false,
  daily_free_hours: 0,
  monthly_invite_count: 0,
  booking_range_days: 0,
  theme_color: '#999999'
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
    status: true,
    can_book_venue: false,
    daily_free_hours: 0,
    monthly_invite_count: 0,
    booking_range_days: 0,
    theme_color: '#999999'
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
        <el-table-column prop="level" label="等级值" width="70" />
        <el-table-column prop="level_code" label="等级代码" width="90" />
        <el-table-column prop="name" label="等级名称" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.theme_color || '#333' }">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="can_book_venue" label="可预约" width="80">
          <template #default="{ row }">
            <el-tag :type="row.can_book_venue ? 'success' : 'info'" size="small">
              {{ row.can_book_venue ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="booking_range_days" label="预约天数" width="90" />
        <el-table-column prop="daily_free_hours" label="免费小时/天" width="100" />
        <el-table-column prop="monthly_invite_count" label="月邀请次数" width="100" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
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
        <el-divider content-position="left">预约与权益配置</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="可预约场馆">
              <el-switch v-model="form.can_book_venue" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="预约天数">
              <el-input-number v-model="form.booking_range_days" :min="0" :max="30" style="width: 100%" />
              <div class="form-tip">0=仅当天，3=提前3天</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="主题色">
              <el-color-picker v-model="form.theme_color" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="每日免费小时">
              <el-input-number v-model="form.daily_free_hours" :min="0" :max="24" style="width: 100%" />
              <div class="form-tip">SSS=3，其他=0</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="月邀请次数">
              <el-input-number v-model="form.monthly_invite_count" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="场馆权限">
          <el-input v-model="form.venue_permissions" type="textarea" :rows="3" placeholder="JSON格式（可选）" />
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

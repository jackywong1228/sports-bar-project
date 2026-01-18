<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const total = ref(0)
const queryParams = ref({
  page: 1,
  page_size: 10,
  keyword: '',
  level_id: '',
  is_active: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const form = ref({
  id: null as number | null,
  name: '',
  level_id: null as number | null,
  original_price: 0,
  price: 0,
  duration_days: 30,
  bonus_coins: 0,
  bonus_points: 0,
  cover_image: '',
  description: '',
  highlights: [] as string[],
  sort_order: 0,
  is_recommended: false,
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  level_id: [{ required: true, message: '请选择会员等级', trigger: 'change' }],
  original_price: [{ required: true, message: '请输入原价', trigger: 'blur' }],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
  duration_days: [{ required: true, message: '请输入有效天数', trigger: 'blur' }]
}

const levelOptions = ref<any[]>([])
const highlightInput = ref('')

const typeOptions = [
  { label: '普通会员', value: 'normal', color: '#909399' },
  { label: '健身会员', value: 'fitness', color: '#67C23A' },
  { label: '球类会员', value: 'ball', color: '#409EFF' },
  { label: '顶级会员', value: 'vip', color: '#E6A23C' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = { ...queryParams.value }
    if (params.is_active === '') delete params.is_active
    if (params.level_id === '') delete params.level_id
    const res = await request.get('/member-cards/cards', { params })
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const fetchLevels = async () => {
  try {
    const res = await request.get('/member-cards/levels')
    levelOptions.value = res.data
  } catch (err) {
    console.error('获取等级列表失败:', err)
  }
}

const handleSearch = () => {
  queryParams.value.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.value = { page: 1, page_size: 10, keyword: '', level_id: '', is_active: '' }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增套餐'
  form.value = {
    id: null,
    name: '',
    level_id: null,
    original_price: 0,
    price: 0,
    duration_days: 30,
    bonus_coins: 0,
    bonus_points: 0,
    cover_image: '',
    description: '',
    highlights: [],
    sort_order: 0,
    is_recommended: false,
    is_active: true
  }
  highlightInput.value = ''
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑套餐'
  form.value = { ...row, highlights: row.highlights || [] }
  highlightInput.value = ''
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该套餐吗？', '提示', { type: 'warning' })
    await request.delete(`/member-cards/cards/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) {
    if (e !== 'cancel' && e.message) {
      ElMessage.error(e.message)
    }
  }
}

const handleToggleActive = async (row: any) => {
  try {
    await request.put(`/member-cards/cards/${row.id}/toggle-active`)
    ElMessage.success(row.is_active ? '已下架' : '已上架')
    fetchData()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (form.value.id) {
      await request.put(`/member-cards/cards/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/member-cards/cards', form.value)
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

const addHighlight = () => {
  if (highlightInput.value.trim()) {
    form.value.highlights.push(highlightInput.value.trim())
    highlightInput.value = ''
  }
}

const removeHighlight = (index: number) => {
  form.value.highlights.splice(index, 1)
}

const handleSizeChange = (size: number) => {
  queryParams.value.page_size = size
  fetchData()
}

const handleCurrentChange = (page: number) => {
  queryParams.value.page = page
  fetchData()
}

const getTypeColor = (type: string) => {
  const item = typeOptions.find(t => t.value === type)
  return item ? item.color : '#909399'
}

const formatDuration = (days: number) => {
  if (days >= 365) {
    const years = Math.floor(days / 365)
    return `${years}年`
  } else if (days >= 30) {
    const months = Math.floor(days / 30)
    return `${months}个月`
  } else {
    return `${days}天`
  }
}

onMounted(() => {
  fetchData()
  fetchLevels()
})
</script>

<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="套餐名称" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="queryParams.level_id" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in levelOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.is_active" placeholder="全部" clearable style="width: 100px">
            <el-option label="上架" :value="true" />
            <el-option label="下架" :value="false" />
          </el-select>
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
          <span>会员卡套餐</span>
          <el-button type="primary" @click="handleAdd">新增套餐</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="套餐名称" min-width="150">
          <template #default="{ row }">
            <div class="card-name">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_recommended" type="danger" size="small">推荐</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="level_name" label="会员等级" width="120">
          <template #default="{ row }">
            <el-tag :color="getTypeColor(row.level_type)" effect="dark">{{ row.level_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="价格" width="150">
          <template #default="{ row }">
            <div>
              <span class="price">{{ row.price }}</span>元
              <span v-if="row.original_price > row.price" class="original-price">{{ row.original_price }}元</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration_days" label="有效期" width="100">
          <template #default="{ row }">{{ formatDuration(row.duration_days) }}</template>
        </el-table-column>
        <el-table-column label="赠送" width="150">
          <template #default="{ row }">
            <div v-if="row.bonus_coins > 0 || row.bonus_points > 0">
              <span v-if="row.bonus_coins > 0">{{ row.bonus_coins }}金币</span>
              <span v-if="row.bonus_coins > 0 && row.bonus_points > 0"> + </span>
              <span v-if="row.bonus_points > 0">{{ row.bonus_points }}积分</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sales_count" label="销量" width="80" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '上架' : '下架' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link :type="row.is_active ? 'warning' : 'success'" @click="handleToggleActive(row)">
              {{ row.is_active ? '下架' : '上架' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="套餐名称" prop="name">
              <el-input v-model="form.name" placeholder="如：月卡、季卡、年卡" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="会员等级" prop="level_id">
              <el-select v-model="form.level_id" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in levelOptions" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="原价" prop="original_price">
              <el-input-number v-model="form.original_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="售价" prop="price">
              <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="有效天数" prop="duration_days">
              <el-input-number v-model="form.duration_days" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="赠送金币">
              <el-input-number v-model="form.bonus_coins" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="赠送积分">
              <el-input-number v-model="form.bonus_points" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="封面图">
          <el-input v-model="form.cover_image" placeholder="图片URL地址" />
        </el-form-item>
        <el-form-item label="套餐描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述套餐特点和权益" />
        </el-form-item>
        <el-form-item label="套餐亮点">
          <div class="highlights-wrapper">
            <div class="highlights-input">
              <el-input v-model="highlightInput" placeholder="输入亮点后按回车添加" @keyup.enter="addHighlight" />
              <el-button type="primary" @click="addHighlight">添加</el-button>
            </div>
            <div class="highlights-tags">
              <el-tag v-for="(item, index) in form.highlights" :key="index" closable @close="removeHighlight(index)">
                {{ item }}
              </el-tag>
            </div>
          </div>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="推荐">
              <el-switch v-model="form.is_recommended" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" active-text="上架" inactive-text="下架" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: flex-end; }

.card-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price {
  font-size: 16px;
  font-weight: bold;
  color: #F56C6C;
}

.original-price {
  font-size: 12px;
  color: #909399;
  text-decoration: line-through;
  margin-left: 8px;
}

.text-muted {
  color: #909399;
}

.highlights-wrapper {
  width: 100%;
}

.highlights-input {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.highlights-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>

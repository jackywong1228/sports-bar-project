<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const queryParams = ref({
  position: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增轮播图')
const formRef = ref()
const form = ref({
  id: null as number | null,
  title: '',
  image: '',
  link_type: 'none',
  link_value: '',
  position: 'home',
  sort_order: 0,
  is_active: true,
  start_time: '',
  end_time: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  image: [{ required: true, message: '请输入图片地址', trigger: 'blur' }]
}

const positionOptions = [
  { label: '首页', value: 'home' },
  { label: '活动页', value: 'activity' },
  { label: '商城页', value: 'mall' }
]

const linkTypeOptions = [
  { label: '无跳转', value: 'none' },
  { label: '页面', value: 'page' },
  { label: '活动', value: 'activity' },
  { label: '外部链接', value: 'url' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryParams.value.position) params.position = queryParams.value.position
    const res = await request.get('/messages/banners', { params })
    tableData.value = res.data || []
  } catch (err) {
    console.error('获取轮播图列表失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchData()
}

const handleReset = () => {
  queryParams.value = { position: '' }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增轮播图'
  form.value = {
    id: null,
    title: '',
    image: '',
    link_type: 'none',
    link_value: '',
    position: 'home',
    sort_order: 0,
    is_active: true,
    start_time: '',
    end_time: ''
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑轮播图'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该轮播图吗？', '提示', { type: 'warning' })
    await request.delete(`/messages/banners/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const handleToggleActive = async (row: any) => {
  try {
    await request.put(`/messages/banners/${row.id}`, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已禁用' : '已启用')
    fetchData()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (form.value.id) {
      await request.put(`/messages/banners/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await request.post('/messages/banners', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  }
}

const getPositionLabel = (position: string) => {
  const item = positionOptions.find(p => p.value === position)
  return item ? item.label : position
}

const getLinkTypeLabel = (type: string) => {
  const item = linkTypeOptions.find(t => t.value === type)
  return item ? item.label : type
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="显示位置">
          <el-select v-model="queryParams.position" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in positionOptions" :key="item.value" :label="item.label" :value="item.value" />
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
          <span>轮播图列表</span>
          <el-button type="primary" @click="handleAdd">新增轮播图</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="image" label="图片" width="150">
          <template #default="{ row }">
            <el-image :src="row.image" :preview-src-list="[row.image]" fit="cover" style="width: 120px; height: 60px; border-radius: 4px;" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="position" label="显示位置" width="100">
          <template #default="{ row }">
            <el-tag>{{ getPositionLabel(row.position) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="link_type" label="跳转类型" width="100">
          <template #default="{ row }">{{ getLinkTypeLabel(row.link_type) }}</template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="140" />
        <el-table-column prop="end_time" label="结束时间" width="140" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link :type="row.is_active ? 'warning' : 'success'" @click="handleToggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="图片地址" prop="image">
          <el-input v-model="form.image" placeholder="请输入图片URL" />
        </el-form-item>
        <el-form-item label="图片预览" v-if="form.image">
          <el-image :src="form.image" fit="cover" style="width: 200px; height: 100px; border-radius: 4px;" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="显示位置">
              <el-select v-model="form.position" placeholder="请选择位置" style="width: 100%">
                <el-option v-for="item in positionOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="跳转类型">
              <el-select v-model="form.link_type" placeholder="请选择跳转类型" style="width: 100%">
                <el-option v-for="item in linkTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="跳转值" v-if="form.link_type !== 'none'">
              <el-input v-model="form.link_value" placeholder="页面路径/活动ID/URL" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DD HH:mm" placeholder="选择开始时间" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DD HH:mm" placeholder="选择结束时间" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
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
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

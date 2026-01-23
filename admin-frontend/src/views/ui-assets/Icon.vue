<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const options = ref<any>({})
const queryParams = ref({
  app_type: '',
  category: '',
  keyword: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增图标')
const formRef = ref()
const form = ref({
  id: null as number | null,
  code: '',
  name: '',
  app_type: 'user',
  category: 'tabbar',
  icon_normal: '',
  icon_active: '',
  description: '',
  sort_order: 0
})

const rules = {
  code: [{ required: true, message: '请输入图标编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入图标名称', trigger: 'blur' }],
  app_type: [{ required: true, message: '请选择应用类型', trigger: 'change' }],
  category: [{ required: true, message: '请选择图标分类', trigger: 'change' }]
}

const uploadUrl = '/api/v1/upload/image?folder=icons'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const fetchOptions = async () => {
  try {
    const res = await request.get('/ui-assets/options')
    options.value = res.data || {}
  } catch (err) {
    console.error('获取选项失败:', err)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryParams.value.app_type) params.app_type = queryParams.value.app_type
    if (queryParams.value.category) params.category = queryParams.value.category
    if (queryParams.value.keyword) params.keyword = queryParams.value.keyword
    const res = await request.get('/ui-assets/icons', { params })
    tableData.value = res.data || []
  } catch (err) {
    console.error('获取图标列表失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchData()
}

const handleReset = () => {
  queryParams.value = { app_type: '', category: '', keyword: '' }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增图标'
  form.value = {
    id: null,
    code: '',
    name: '',
    app_type: 'user',
    category: 'tabbar',
    icon_normal: '',
    icon_active: '',
    description: '',
    sort_order: 0
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑图标'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该图标吗？', '提示', { type: 'warning' })
    await request.delete(`/ui-assets/icons/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    const submitData: any = {
      code: form.value.code,
      name: form.value.name,
      app_type: form.value.app_type,
      category: form.value.category,
      icon_normal: form.value.icon_normal,
      icon_active: form.value.icon_active,
      description: form.value.description,
      sort_order: form.value.sort_order
    }

    if (form.value.id) {
      await request.put(`/ui-assets/icons/${form.value.id}`, null, { params: submitData })
      ElMessage.success('更新成功')
    } else {
      await request.post('/ui-assets/icons', null, { params: submitData })
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

const handleUploadSuccess = (response: any, type: 'normal' | 'active') => {
  if (response.code === 200 && response.data) {
    if (type === 'normal') {
      form.value.icon_normal = response.data.url
    } else {
      form.value.icon_active = response.data.url
    }
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

const getAppTypeLabel = (value: string) => {
  const item = options.value.app_types?.find((t: any) => t.value === value)
  return item ? item.label : value
}

const getCategoryLabel = (value: string) => {
  const item = options.value.icon_categories?.find((c: any) => c.value === value)
  return item ? item.label : value
}

onMounted(() => {
  fetchOptions()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <!-- 页面说明 -->
    <el-alert
      title="图标管理说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #default>
        <p style="margin: 0; line-height: 1.8">
          在这里管理小程序的图标素材。上传图标后，开发人员可以根据图标编码在小程序中使用这些图标。
          <br />
          <strong>建议尺寸：</strong>底部导航栏图标建议 81x81 像素，其他图标根据实际使用场景调整。
          <br />
          <strong>格式要求：</strong>支持 PNG、JPG、GIF、WebP 格式，建议使用 PNG 格式以支持透明背景。
        </p>
      </template>
    </el-alert>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="应用类型">
          <el-select v-model="queryParams.app_type" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in options.app_types" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="图标分类">
          <el-select v-model="queryParams.category" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in options.icon_categories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="搜索图标名称" clearable style="width: 180px" />
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
          <span>图标列表</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增图标</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="code" label="图标编码" width="150" show-overflow-tooltip />
        <el-table-column prop="name" label="图标名称" width="120" />
        <el-table-column prop="app_type" label="应用类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.app_type === 'user' ? 'success' : row.app_type === 'coach' ? 'warning' : 'info'">
              {{ getAppTypeLabel(row.app_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">{{ getCategoryLabel(row.category) }}</template>
        </el-table-column>
        <el-table-column label="普通状态" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.icon_normal"
              :src="row.icon_normal"
              :preview-src-list="[row.icon_normal]"
              fit="contain"
              style="width: 48px; height: 48px; background: #f5f5f5; border-radius: 4px; padding: 4px;"
            />
            <span v-else style="color: #999">未上传</span>
          </template>
        </el-table-column>
        <el-table-column label="选中状态" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.icon_active"
              :src="row.icon_active"
              :preview-src-list="[row.icon_active]"
              fit="contain"
              style="width: 48px; height: 48px; background: #f5f5f5; border-radius: 4px; padding: 4px;"
            />
            <span v-else style="color: #999">未上传</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column prop="updated_at" label="更新时间" width="140" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="图标编码" prop="code">
              <el-input v-model="form.code" placeholder="如 tabbar-home" :disabled="!!form.id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="图标名称" prop="name">
              <el-input v-model="form.name" placeholder="如 首页图标" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="应用类型" prop="app_type">
              <el-select v-model="form.app_type" placeholder="请选择" style="width: 100%" :disabled="!!form.id">
                <el-option v-for="item in options.app_types" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="图标分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in options.icon_categories" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="普通状态">
              <div class="upload-area">
                <el-upload
                  class="icon-uploader"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :show-file-list="false"
                  accept="image/*"
                  :on-success="(res: any) => handleUploadSuccess(res, 'normal')"
                  :on-error="handleUploadError"
                >
                  <div class="upload-box">
                    <el-image v-if="form.icon_normal" :src="form.icon_normal" fit="contain" class="uploaded-icon" />
                    <div v-else class="upload-placeholder">
                      <el-icon><Upload /></el-icon>
                      <span>点击上传</span>
                    </div>
                  </div>
                </el-upload>
                <div class="upload-tip">未选中时显示的图标</div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选中状态">
              <div class="upload-area">
                <el-upload
                  class="icon-uploader"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :show-file-list="false"
                  accept="image/*"
                  :on-success="(res: any) => handleUploadSuccess(res, 'active')"
                  :on-error="handleUploadError"
                >
                  <div class="upload-box">
                    <el-image v-if="form.icon_active" :src="form.icon_active" fit="contain" class="uploaded-icon" />
                    <div v-else class="upload-placeholder">
                      <el-icon><Upload /></el-icon>
                      <span>点击上传</span>
                    </div>
                  </div>
                </el-upload>
                <div class="upload-tip">选中时显示的图标</div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
          <span style="margin-left: 10px; color: #999; font-size: 12px">数值越小越靠前</span>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="图标使用说明（可选）" />
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

.upload-area {
  text-align: center;
}

.upload-box {
  width: 100px;
  height: 100px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-box:hover {
  border-color: #409eff;
}

.uploaded-icon {
  width: 80px;
  height: 80px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #999;
}

.upload-placeholder .el-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.upload-placeholder span {
  font-size: 12px;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>

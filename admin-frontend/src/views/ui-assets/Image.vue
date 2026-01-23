<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Picture } from '@element-plus/icons-vue'
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
const dialogTitle = ref('新增图片素材')
const formRef = ref()
const form = ref({
  id: null as number | null,
  code: '',
  name: '',
  app_type: 'user',
  category: 'common',
  image_url: '',
  suggested_width: null as number | null,
  suggested_height: null as number | null,
  description: '',
  sort_order: 0
})

const rules = {
  code: [{ required: true, message: '请输入图片编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入图片名称', trigger: 'blur' }],
  app_type: [{ required: true, message: '请选择应用类型', trigger: 'change' }],
  image_url: [{ required: true, message: '请上传图片', trigger: 'change' }]
}

const uploadUrl = '/api/v1/upload/image?folder=ui-images'
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
    const res = await request.get('/ui-assets/images', { params })
    tableData.value = res.data || []
  } catch (err) {
    console.error('获取图片列表失败:', err)
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
  dialogTitle.value = '新增图片素材'
  form.value = {
    id: null,
    code: '',
    name: '',
    app_type: 'user',
    category: 'common',
    image_url: '',
    suggested_width: null,
    suggested_height: null,
    description: '',
    sort_order: 0
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑图片素材'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该图片素材吗？', '提示', { type: 'warning' })
    await request.delete(`/ui-assets/images/${row.id}`)
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
      image_url: form.value.image_url,
      suggested_width: form.value.suggested_width,
      suggested_height: form.value.suggested_height,
      description: form.value.description,
      sort_order: form.value.sort_order
    }

    if (form.value.id) {
      await request.put(`/ui-assets/images/${form.value.id}`, null, { params: submitData })
      ElMessage.success('更新成功')
    } else {
      await request.post('/ui-assets/images', null, { params: submitData })
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

const handleUploadSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    form.value.image_url = response.data.url
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
  const item = options.value.image_categories?.find((c: any) => c.value === value)
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
      title="图片素材管理说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #default>
        <p style="margin: 0; line-height: 1.8">
          在这里管理小程序中使用的各类图片素材，包括背景图、空状态图、Logo等。
          <br />
          <strong>格式要求：</strong>支持 PNG、JPG、GIF、WebP 格式，建议使用 PNG 或 WebP 以获得更好的质量和透明背景支持。
          <br />
          <strong>建议尺寸：</strong>上传时请注意填写建议尺寸，便于后续替换时参考。
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
        <el-form-item label="图片分类">
          <el-select v-model="queryParams.category" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="item in options.image_categories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="搜索图片名称" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图片列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>图片素材列表</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增图片</el-button>
        </div>
      </template>

      <div v-loading="loading" class="image-grid">
        <div v-for="item in tableData" :key="item.id" class="image-card">
          <!-- 图片预览 -->
          <div class="image-preview">
            <el-image
              :src="item.image_url"
              :preview-src-list="[item.image_url]"
              fit="contain"
              class="preview-img"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                  <span>加载失败</span>
                </div>
              </template>
            </el-image>
          </div>

          <!-- 图片信息 -->
          <div class="image-info">
            <div class="image-name">{{ item.name }}</div>
            <div class="image-meta">
              <el-tag size="small" :type="item.app_type === 'user' ? 'success' : item.app_type === 'coach' ? 'warning' : 'info'">
                {{ getAppTypeLabel(item.app_type) }}
              </el-tag>
              <el-tag size="small" type="info">{{ getCategoryLabel(item.category) }}</el-tag>
            </div>
            <div class="image-code">{{ item.code }}</div>
            <div class="image-size" v-if="item.suggested_width && item.suggested_height">
              建议尺寸: {{ item.suggested_width }} x {{ item.suggested_height }}
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="image-actions">
            <el-button type="primary" size="small" @click="handleEdit(item)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(item)">删除</el-button>
          </div>
        </div>

        <div v-if="tableData.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无图片素材" />
        </div>
      </div>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="图片编码" prop="code">
              <el-input v-model="form.code" placeholder="如 empty-order" :disabled="!!form.id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="图片名称" prop="name">
              <el-input v-model="form.name" placeholder="如 订单空状态图" />
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
            <el-form-item label="图片分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in options.image_categories" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="上传图片" prop="image_url">
          <div class="upload-area">
            <el-upload
              class="image-uploader"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              accept="image/*"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
            >
              <div class="upload-box" :class="{ 'has-image': form.image_url }">
                <el-image v-if="form.image_url" :src="form.image_url" fit="contain" class="uploaded-image" />
                <div v-else class="upload-placeholder">
                  <el-icon><Upload /></el-icon>
                  <span>点击上传图片</span>
                </div>
              </div>
            </el-upload>
            <div class="upload-tip">支持 PNG、JPG、GIF、WebP 格式，最大 10MB</div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="建议宽度">
              <el-input-number v-model="form.suggested_width" :min="0" placeholder="像素" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="建议高度">
              <el-input-number v-model="form.suggested_height" :min="0" placeholder="像素" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="图片使用说明（可选）" />
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

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.image-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.image-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-preview {
  height: 160px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #909399;
}

.image-error .el-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.image-info {
  padding: 12px;
}

.image-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.image-code {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
  margin-bottom: 4px;
}

.image-size {
  font-size: 12px;
  color: #606266;
}

.image-actions {
  padding: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 40px;
}

/* 上传区域 */
.upload-area {
  width: 100%;
}

.upload-box {
  width: 200px;
  height: 150px;
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

.upload-box.has-image {
  border-style: solid;
  border-color: #409eff;
}

.uploaded-image {
  max-width: 180px;
  max-height: 130px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #999;
}

.upload-placeholder .el-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-placeholder span {
  font-size: 13px;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>

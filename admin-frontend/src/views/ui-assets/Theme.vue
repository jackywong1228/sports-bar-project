<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const tableData = ref<any[]>([])
const options = ref<any>({})
const queryParams = ref({
  app_type: ''
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增主题')
const formRef = ref()
const form = ref({
  id: null as number | null,
  code: '',
  name: '',
  app_type: 'user',
  colors: {
    primary: '#1A5D3A',
    primaryDark: '#145A32',
    primaryLight: '#E8F5E9',
    secondary: '#6B5B95',
    secondaryLight: '#EDE7F6',
    background: '#F5F7F5',
    cardBg: '#FFFFFF',
    textPrimary: '#2C3E2D',
    textSecondary: '#6B7B6E',
    textMuted: '#8E9A8F',
    success: '#4CAF50',
    warning: '#FF9800',
    danger: '#F44336',
    gold: '#C9A962'
  },
  preview_image: '',
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入主题编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入主题名称', trigger: 'blur' }],
  app_type: [{ required: true, message: '请选择应用类型', trigger: 'change' }]
}

// 颜色配置项
const colorFields = [
  { key: 'primary', label: '主色调', description: '品牌主色，用于按钮、链接等' },
  { key: 'primaryDark', label: '主色（深）', description: '主色的深色变体' },
  { key: 'primaryLight', label: '主色（浅）', description: '主色的浅色背景' },
  { key: 'secondary', label: '辅助色', description: '次要强调色' },
  { key: 'secondaryLight', label: '辅助色（浅）', description: '辅助色的浅色背景' },
  { key: 'background', label: '页面背景', description: '整体页面背景色' },
  { key: 'cardBg', label: '卡片背景', description: '卡片、模块背景色' },
  { key: 'textPrimary', label: '主文字', description: '标题、重要文字颜色' },
  { key: 'textSecondary', label: '次文字', description: '正文、说明文字颜色' },
  { key: 'textMuted', label: '辅助文字', description: '提示、禁用文字颜色' },
  { key: 'success', label: '成功色', description: '成功状态颜色' },
  { key: 'warning', label: '警告色', description: '警告状态颜色' },
  { key: 'danger', label: '危险色', description: '错误、危险状态颜色' },
  { key: 'gold', label: '金色', description: '会员、积分等特殊元素' }
]

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
    const res = await request.get('/ui-assets/themes', { params })
    tableData.value = res.data || []
  } catch (err) {
    console.error('获取主题列表失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchData()
}

const handleReset = () => {
  queryParams.value = { app_type: '' }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增主题'
  form.value = {
    id: null,
    code: '',
    name: '',
    app_type: 'user',
    colors: {
      primary: '#1A5D3A',
      primaryDark: '#145A32',
      primaryLight: '#E8F5E9',
      secondary: '#6B5B95',
      secondaryLight: '#EDE7F6',
      background: '#F5F7F5',
      cardBg: '#FFFFFF',
      textPrimary: '#2C3E2D',
      textSecondary: '#6B7B6E',
      textMuted: '#8E9A8F',
      success: '#4CAF50',
      warning: '#FF9800',
      danger: '#F44336',
      gold: '#C9A962'
    },
    preview_image: '',
    description: ''
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑主题'
  form.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    app_type: row.app_type,
    colors: { ...row.colors },
    preview_image: row.preview_image || '',
    description: row.description || ''
  }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  if (row.is_current) {
    ElMessage.warning('当前使用中的主题不能删除')
    return
  }
  try {
    await ElMessageBox.confirm('确定要删除该主题吗？', '提示', { type: 'warning' })
    await request.delete(`/ui-assets/themes/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const handleSetCurrent = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定将「${row.name}」设为当前主题吗？`, '提示', { type: 'info' })
    await request.put(`/ui-assets/themes/${row.id}/set-current`)
    ElMessage.success('设置成功')
    fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '设置失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    const submitData = {
      code: form.value.code,
      name: form.value.name,
      app_type: form.value.app_type,
      colors: form.value.colors,
      preview_image: form.value.preview_image,
      description: form.value.description
    }

    if (form.value.id) {
      await request.put(`/ui-assets/themes/${form.value.id}`, submitData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/ui-assets/themes', submitData)
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

const getAppTypeLabel = (value: string) => {
  const item = options.value.app_types?.find((t: any) => t.value === value)
  return item ? item.label : value
}

// 预览颜色
const previewColors = computed(() => form.value.colors)

onMounted(() => {
  fetchOptions()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <!-- 页面说明 -->
    <el-alert
      title="主题配色管理说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #default>
        <p style="margin: 0; line-height: 1.8">
          在这里管理小程序和后台的主题配色方案。每种应用类型可以有多个主题，但只能有一个当前使用的主题。
          <br />
          <strong>配色建议：</strong>主色调应与品牌色保持一致，辅助色用于强调次要元素，背景色应保证文字可读性。
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
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 主题列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>主题列表</span>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增主题</el-button>
        </div>
      </template>

      <div v-loading="loading" class="theme-grid">
        <div v-for="theme in tableData" :key="theme.id" class="theme-card" :class="{ current: theme.is_current }">
          <!-- 主题预览 -->
          <div class="theme-preview" :style="{ background: theme.colors?.background || '#f5f5f5' }">
            <div class="preview-header" :style="{ background: theme.colors?.primary || '#1890ff' }">
              <span style="color: #fff">{{ theme.name }}</span>
            </div>
            <div class="preview-body">
              <div class="preview-card" :style="{ background: theme.colors?.cardBg || '#fff' }">
                <div class="preview-title" :style="{ color: theme.colors?.textPrimary || '#333' }">标题文字</div>
                <div class="preview-text" :style="{ color: theme.colors?.textSecondary || '#666' }">正文内容</div>
                <div class="preview-btn" :style="{ background: theme.colors?.primary || '#1890ff' }">按钮</div>
              </div>
              <div class="preview-tags">
                <span class="tag" :style="{ background: theme.colors?.primaryLight || '#e6f7ff', color: theme.colors?.primary || '#1890ff' }">标签</span>
                <span class="tag" :style="{ background: theme.colors?.secondaryLight || '#f0f0f0', color: theme.colors?.secondary || '#666' }">辅助</span>
              </div>
            </div>
          </div>

          <!-- 主题信息 -->
          <div class="theme-info">
            <div class="theme-name">
              {{ theme.name }}
              <el-tag v-if="theme.is_current" type="success" size="small">当前使用</el-tag>
            </div>
            <div class="theme-meta">
              <span>{{ getAppTypeLabel(theme.app_type) }}</span>
              <span>{{ theme.code }}</span>
            </div>
            <div class="theme-desc" v-if="theme.description">{{ theme.description }}</div>
          </div>

          <!-- 操作按钮 -->
          <div class="theme-actions">
            <el-button v-if="!theme.is_current" type="success" size="small" :icon="Check" @click="handleSetCurrent(theme)">
              设为当前
            </el-button>
            <el-button type="primary" size="small" @click="handleEdit(theme)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(theme)" :disabled="theme.is_current">删除</el-button>
          </div>
        </div>

        <div v-if="tableData.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无主题配色" />
        </div>
      </div>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="900px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主题编码" prop="code">
              <el-input v-model="form.code" placeholder="如 wimbledon" :disabled="!!form.id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主题名称" prop="name">
              <el-input v-model="form.name" placeholder="如 温网风格" />
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
            <el-form-item label="说明">
              <el-input v-model="form.description" placeholder="主题说明（可选）" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">颜色配置</el-divider>

        <el-row :gutter="16">
          <el-col :span="16">
            <div class="color-grid">
              <div v-for="field in colorFields" :key="field.key" class="color-item">
                <div class="color-picker-wrapper">
                  <el-color-picker v-model="(form.colors as any)[field.key]" show-alpha />
                </div>
                <div class="color-info">
                  <div class="color-label">{{ field.label }}</div>
                  <div class="color-desc">{{ field.description }}</div>
                  <div class="color-value">{{ (form.colors as any)[field.key] }}</div>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="preview-panel">
              <div class="preview-title-bar">实时预览</div>
              <div class="live-preview" :style="{ background: previewColors.background }">
                <div class="preview-header-bar" :style="{ background: previewColors.primary }">
                  <span style="color: #fff; font-size: 14px">导航栏</span>
                </div>
                <div class="preview-content">
                  <div class="preview-card-item" :style="{ background: previewColors.cardBg }">
                    <div :style="{ color: previewColors.textPrimary, fontWeight: 'bold', marginBottom: '8px' }">标题文字</div>
                    <div :style="{ color: previewColors.textSecondary, fontSize: '12px', marginBottom: '8px' }">这是正文内容示例</div>
                    <div :style="{ color: previewColors.textMuted, fontSize: '11px' }">辅助说明文字</div>
                  </div>
                  <div class="preview-buttons">
                    <span class="btn" :style="{ background: previewColors.primary, color: '#fff' }">主按钮</span>
                    <span class="btn" :style="{ background: previewColors.secondary, color: '#fff' }">辅助</span>
                  </div>
                  <div class="preview-status">
                    <span :style="{ color: previewColors.success }">成功</span>
                    <span :style="{ color: previewColors.warning }">警告</span>
                    <span :style="{ color: previewColors.danger }">错误</span>
                    <span :style="{ color: previewColors.gold }">金币</span>
                  </div>
                </div>
              </div>
            </div>
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

.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.theme-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.theme-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.theme-card.current {
  border-color: #67c23a;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2);
}

.theme-preview {
  padding: 12px;
  min-height: 140px;
}

.preview-header {
  padding: 8px 12px;
  border-radius: 4px 4px 0 0;
  font-size: 12px;
}

.preview-body {
  padding: 12px;
}

.preview-card {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.preview-title {
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 4px;
}

.preview-text {
  font-size: 11px;
  margin-bottom: 8px;
}

.preview-btn {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
}

.preview-tags {
  display: flex;
  gap: 8px;
}

.preview-tags .tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
}

.theme-info {
  padding: 12px;
  border-top: 1px solid #ebeef5;
}

.theme-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.theme-desc {
  font-size: 12px;
  color: #606266;
  margin-top: 8px;
}

.theme-actions {
  padding: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 40px;
}

/* 颜色配置 */
.color-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.color-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px;
  background: #fafafa;
  border-radius: 6px;
}

.color-picker-wrapper {
  flex-shrink: 0;
}

.color-info {
  flex: 1;
  min-width: 0;
}

.color-label {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.color-desc {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.color-value {
  font-size: 11px;
  color: #606266;
  font-family: monospace;
  margin-top: 4px;
}

/* 实时预览面板 */
.preview-panel {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  position: sticky;
  top: 20px;
}

.preview-title-bar {
  padding: 10px;
  background: #f5f7fa;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  border-bottom: 1px solid #ebeef5;
}

.live-preview {
  min-height: 300px;
}

.preview-header-bar {
  padding: 10px;
  text-align: center;
}

.preview-content {
  padding: 12px;
}

.preview-card-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.preview-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.preview-buttons .btn {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 12px;
}

.preview-status {
  display: flex;
  gap: 12px;
  font-size: 12px;
  font-weight: 500;
}
</style>

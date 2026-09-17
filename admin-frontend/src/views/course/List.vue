<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { getCoachList } from '@/api/coach'
import {
  getCourseList, createCourse, updateCourse, updateCourseStatus, deleteCourse,
  type Course, type CourseFormData
} from '@/api/course'

const router = useRouter()

const loading = ref(false)
const tableData = ref<Course[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  category: null as string | null,
  status: null as string | null,
  coach_id: null as number | null
})

const categoryOptions = [
  { label: '团课', value: 'group' },
  { label: '高尔夫', value: 'golf' },
  { label: '壁球', value: 'squash' },
  { label: '匹克球', value: 'pickleball' }
]

const categoryTagMap: Record<string, string> = {
  group: 'success',
  golf: 'primary',
  squash: 'warning',
  pickleball: 'danger'
}

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已上架', value: 'on' },
  { label: '已下架', value: 'off' }
]

const statusMap: Record<string, { text: string; type: string }> = {
  draft: { text: '草稿', type: 'info' },
  on:    { text: '已上架', type: 'success' },
  off:   { text: '已下架', type: 'warning' }
}

// 教练下拉选项
interface CoachOption { id: number; name: string }
const coachOptions = ref<CoachOption[]>([])

const fetchCoaches = async () => {
  try {
    const res = await getCoachList({ page: 1, page_size: 100 })
    const items = res.data.items || res.data || []
    coachOptions.value = items.map((c: any) => ({ id: c.id, name: c.name }))
  } catch {
    // 教练列表加载失败不阻塞页面
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getCourseList(queryParams)
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.category = null
  queryParams.status = null
  queryParams.coach_id = null
  handleSearch()
}

// ============ 创建/编辑对话框 ============

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)

const emptyForm = (): CourseFormData => ({
  coach_id: undefined as unknown as number,
  category: 'group',
  title: '',
  subtitle: '',
  cover_image: '',
  description: '',
  duration_minutes: 60,
  price: 0
})

const form = reactive<CourseFormData>(emptyForm())

const uploadUrl = '/api/v1/upload/image?folder=courses'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))
const handleUploadSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    form.cover_image = response.data.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}
const handleUploadError = () => ElMessage.error('上传失败')

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

const openEditDialog = (row: Course) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    coach_id: row.coach_id,
    category: row.category,
    title: row.title,
    subtitle: row.subtitle || '',
    cover_image: row.cover_image || '',
    description: row.description || '',
    duration_minutes: row.duration_minutes,
    price: row.price
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.coach_id) {
    ElMessage.warning('请选择教练')
    return
  }
  if (!form.title.trim()) {
    ElMessage.warning('请输入课程名')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value && editingId.value) {
      await updateCourse(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createCourse(form)
      ElMessage.success('创建成功（草稿状态，上架后才能排课）')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // request 封装已提示
  } finally {
    submitting.value = false
  }
}

// ============ 行操作 ============

const handleToggleStatus = async (row: Course) => {
  const target = row.status === 'on' ? 'off' : 'on'
  const actionText = target === 'on' ? '上架' : '下架'
  try {
    await ElMessageBox.confirm(
      target === 'on'
        ? `确定上架「${row.title}」吗？上架后即教练必到，可开始排课。`
        : `确定下架「${row.title}」吗？下架后小程序不可见且不能再排新课次。`,
      '提示',
      { type: 'warning' }
    )
    await updateCourseStatus(row.id, target)
    ElMessage.success(`${actionText}成功`)
    fetchData()
  } catch {
    // 取消或错误
  }
}

const handleDelete = async (row: Course) => {
  try {
    await ElMessageBox.confirm(`确定删除课程「${row.title}」吗？`, '提示', { type: 'warning' })
    await deleteCourse(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误（如有报名的未来课次，后端会拒绝并提示）
  }
}

const goSessions = (row: Course) => {
  router.push(`/course/sessions/${row.id}`)
}

onMounted(() => {
  fetchCoaches()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="分类">
          <el-select v-model="queryParams.category" placeholder="全部" clearable style="width: 140px;">
            <el-option v-for="o in categoryOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 140px;">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="教练">
          <el-select v-model="queryParams.coach_id" placeholder="全部" clearable filterable style="width: 160px;">
            <el-option v-for="c in coachOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>课程列表</span>
          <el-button type="primary" @click="openCreateDialog">新建课程</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column label="封面" width="90">
          <template #default="{ row }">
            <el-image
              v-if="row.cover_image"
              :src="row.cover_image"
              :preview-src-list="[row.cover_image]"
              fit="cover"
              style="width: 56px; height: 56px; border-radius: 6px;"
            />
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="课程名" min-width="160">
          <template #default="{ row }">
            <div>{{ row.title }}</div>
            <div v-if="row.subtitle" class="text-muted" style="font-size: 12px;">{{ row.subtitle }}</div>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="100">
          <template #default="{ row }">
            <el-tag :type="(categoryTagMap[row.category] as any) || 'info'">
              {{ row.category_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="coach_name" label="教练" width="100" />
        <el-table-column prop="price" label="价格(金币)" width="100" />
        <el-table-column prop="duration_minutes" label="时长(分钟)" width="90" />
        <el-table-column label="课次" width="120">
          <template #default="{ row }">
            {{ row.upcoming_session_count }} / {{ row.session_count }}
            <div class="text-muted" style="font-size: 12px;">未来 / 全部</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'">
              {{ statusMap[row.status]?.text || row.status_text || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="260">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-button
              :type="row.status === 'on' ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'on' ? '下架' : '上架' }}
            </el-button>
            <el-button type="primary" link @click="goSessions(row)">课次管理</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无课程，点击右上角「新建课程」开始" />
        </template>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end;"
        @change="fetchData"
      />
    </el-card>

    <!-- 创建/编辑课程对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑课程' : '新建课程'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="教练" required>
          <el-select v-model="form.coach_id" placeholder="请选择教练" filterable style="width: 100%;">
            <el-option v-for="c in coachOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="form.category" style="width: 100%;">
            <el-option v-for="o in categoryOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程名" required>
          <el-input v-model="form.title" placeholder="如：高尔夫入门一对一" maxlength="100" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" placeholder="选填" maxlength="200" />
        </el-form-item>
        <el-form-item label="封面图">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            accept="image/*"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
          >
            <el-image
              v-if="form.cover_image"
              :src="form.cover_image"
              fit="cover"
              style="width: 148px; height: 148px; border-radius: 8px;"
            />
            <div v-else class="upload-placeholder">
              <el-icon><Upload /></el-icon>
              <span>点击上传</span>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="课程简介">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="课程详细介绍" />
        </el-form-item>
        <el-form-item label="时长(分钟)" required>
          <el-input-number v-model="form.duration_minutes" :min="1" :max="600" />
        </el-form-item>
        <el-form-item label="价格(金币)" required>
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.text-muted {
  color: #909399;
}

.upload-placeholder {
  width: 148px;
  height: 148px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  cursor: pointer;
}

.upload-placeholder:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
</style>

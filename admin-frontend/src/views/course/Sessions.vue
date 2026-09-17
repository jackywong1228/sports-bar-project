<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import {
  getCourseDetail, getCourseSessions, createCourseSessions,
  updateCourseSession, cancelCourseSession, getSessionBookings,
  type CourseDetail, type CourseSession, type CourseBooking, type SessionItemInput
} from '@/api/course'

const route = useRoute()
const router = useRouter()
const courseId = Number(route.params.id)

const course = ref<CourseDetail | null>(null)
const courseLoading = ref(false)
const sessions = ref<CourseSession[]>([])
const loading = ref(false)

const dateRange = ref<[string, string] | null>(null)

const statusMap: Record<string, { text: string; type: string }> = {
  scheduled: { text: '已排课', type: 'success' },
  cancelled: { text: '已取消', type: 'danger' },
  finished:  { text: '已结束', type: 'info' }
}

const fetchCourse = async () => {
  courseLoading.value = true
  try {
    const res = await getCourseDetail(courseId)
    course.value = res.data
  } finally {
    courseLoading.value = false
  }
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const params: { start_date?: string; end_date?: string } = {}
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getCourseSessions(courseId, params)
    sessions.value = res.data
  } finally {
    loading.value = false
  }
}

const handleRangeChange = () => fetchSessions()

// ============ 批量新增课次 ============

interface SessionRow {
  start_time: string
  end_time: string
  capacity: number
}

const createDialogVisible = ref(false)
const createDate = ref('')
const sessionRows = ref<SessionRow[]>([{ start_time: '', end_time: '', capacity: 1 }])
const creating = ref(false)

const openCreateDialog = () => {
  if (course.value && course.value.status !== 'on') {
    ElMessage.warning('课程未上架，请先在课程列表上架后再排课')
    return
  }
  createDate.value = ''
  sessionRows.value = [{ start_time: '', end_time: '', capacity: 1 }]
  createDialogVisible.value = true
}

const addRow = () => {
  sessionRows.value.push({ start_time: '', end_time: '', capacity: 1 })
}

const removeRow = (index: number) => {
  sessionRows.value.splice(index, 1)
}

const handleCreateSessions = async () => {
  if (!createDate.value) {
    ElMessage.warning('请选择上课日期')
    return
  }
  if (sessionRows.value.length === 0) {
    ElMessage.warning('请至少添加一个时间段')
    return
  }
  for (const [i, row] of sessionRows.value.entries()) {
    if (!row.start_time || !row.end_time) {
      ElMessage.warning(`第 ${i + 1} 行：请选择开始和结束时间`)
      return
    }
    if (row.end_time <= row.start_time) {
      ElMessage.warning(`第 ${i + 1} 行：结束时间必须大于开始时间`)
      return
    }
    if (!row.capacity || row.capacity < 1) {
      ElMessage.warning(`第 ${i + 1} 行：容量必须 ≥ 1`)
      return
    }
  }

  const items: SessionItemInput[] = sessionRows.value.map(row => ({
    session_date: createDate.value,
    start_time: row.start_time,
    end_time: row.end_time,
    capacity: row.capacity
  }))

  creating.value = true
  try {
    const res = await createCourseSessions(courseId, items)
    ElMessage.success((res as any).message || `成功创建 ${items.length} 个课次`)
    createDialogVisible.value = false
    fetchSessions()
  } catch {
    // request 封装已提示（含时间重叠等校验错误）
  } finally {
    creating.value = false
  }
}

// ============ 修改课次 ============

const editDialogVisible = ref(false)
const editingSession = ref<CourseSession | null>(null)
const editForm = reactive({
  session_date: '',
  start_time: '',
  end_time: '',
  capacity: 1,
  remark: ''
})
const editSubmitting = ref(false)

const openEditDialog = (row: CourseSession) => {
  editingSession.value = row
  editForm.session_date = row.session_date
  editForm.start_time = row.start_time || ''
  editForm.end_time = row.end_time || ''
  editForm.capacity = row.capacity
  editForm.remark = row.remark || ''
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  if (!editingSession.value) return
  const hasBooking = (editingSession.value.booked_count || 0) > 0
  if (!hasBooking && editForm.end_time <= editForm.start_time) {
    ElMessage.warning('结束时间必须大于开始时间')
    return
  }
  editSubmitting.value = true
  try {
    // 有报名时后端只允许改备注，此处对应只提交备注
    const payload: Partial<SessionItemInput> = hasBooking
      ? { remark: editForm.remark }
      : {
          session_date: editForm.session_date,
          start_time: editForm.start_time,
          end_time: editForm.end_time,
          capacity: editForm.capacity,
          remark: editForm.remark
        }
    await updateCourseSession(courseId, editingSession.value.id, payload)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchSessions()
  } catch {
    // request 封装已提示
  } finally {
    editSubmitting.value = false
  }
}

// ============ 取消课次 ============

const handleCancelSession = async (row: CourseSession) => {
  let reason = '教练请假，课程取消'
  try {
    const { value } = await ElMessageBox.prompt(
      `确定取消 ${row.session_date} ${row.start_time}-${row.end_time} 的课次吗？` +
      (row.booked_count > 0
        ? `\n该课次已有 ${row.booked_count} 人报名，取消后所有报名将一并取消，金币支付的报名自动退款。`
        : ''),
      '取消课次',
      {
        confirmButtonText: '确认取消课次',
        cancelButtonText: '再想想',
        type: 'warning',
        inputPlaceholder: '取消原因（将写入报名记录）',
        inputValue: reason
      }
    )
    reason = value || reason
  } catch {
    return
  }

  try {
    const res = await cancelCourseSession(courseId, row.id, reason)
    ElMessage.success((res as any).message || '课次已取消')
    fetchSessions()
  } catch {
    // request 封装已提示
  }
}

// ============ 报名名单抽屉 ============

const bookingsDrawerVisible = ref(false)
const bookings = ref<CourseBooking[]>([])
const bookingsLoading = ref(false)
const currentSession = ref<CourseSession | null>(null)

const bookingStatusMap: Record<string, { text: string; type: string }> = {
  pending:   { text: '待支付', type: 'warning' },
  confirmed: { text: '已确认', type: 'primary' },
  completed: { text: '已完成', type: 'success' },
  cancelled: { text: '已取消', type: 'danger' }
}

const payTypeText = (t: string) => (t === 'coin' ? '金币' : t === 'wechat' ? '微信' : t || '-')

const openBookingsDrawer = async (row: CourseSession) => {
  currentSession.value = row
  bookingsDrawerVisible.value = true
  bookingsLoading.value = true
  try {
    const res = await getSessionBookings(courseId, row.id)
    bookings.value = res.data
  } finally {
    bookingsLoading.value = false
  }
}

onMounted(() => {
  fetchCourse()
  fetchSessions()
})
</script>

<template>
  <div class="page-container">
    <!-- 课程信息卡片 -->
    <el-card v-loading="courseLoading">
      <template #header>
        <div class="card-header">
          <span>课次管理</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <div v-if="course" class="course-info">
        <el-image
          v-if="course.cover_image"
          :src="course.cover_image"
          fit="cover"
          style="width: 72px; height: 72px; border-radius: 8px;"
        />
        <div class="course-meta">
          <div class="course-title">
            {{ course.title }}
            <el-tag size="small" style="margin-left: 8px;">{{ course.category_text }}</el-tag>
            <el-tag
              size="small"
              :type="course.status === 'on' ? 'success' : course.status === 'draft' ? 'info' : 'warning'"
              style="margin-left: 4px;"
            >
              {{ course.status_text }}
            </el-tag>
          </div>
          <div class="text-muted">
            教练：{{ course.coach_name || '-' }} · 时长 {{ course.duration_minutes }} 分钟 · {{ course.price }} 金币/人
          </div>
        </div>
      </div>
      <el-alert
        v-if="course && course.status !== 'on'"
        type="warning"
        :closable="false"
        title="课程未上架，不能新增课次（请先在课程列表上架）"
        style="margin-top: 12px;"
      />
    </el-card>

    <!-- 课次表格 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-filters">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              clearable
              @change="handleRangeChange"
            />
          </div>
          <el-button
            type="primary"
            :disabled="!course || course.status !== 'on'"
            @click="openCreateDialog"
          >
            新增课次
          </el-button>
        </div>
      </template>

      <el-table :data="sessions" v-loading="loading" stripe>
        <el-table-column prop="session_date" label="日期" width="120" />
        <el-table-column label="时间" width="150">
          <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
        </el-table-column>
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column label="已约/剩余" width="120">
          <template #default="{ row }">
            {{ row.booked_count }} / {{ Math.max(row.capacity - row.booked_count, 0) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'">
              {{ statusMap[row.status]?.text || row.status_text || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" fixed="right" width="240">
          <template #default="{ row }">
            <el-button type="primary" link @click="openBookingsDrawer(row)">
              报名名单{{ row.booked_count ? `(${row.booked_count})` : '' }}
            </el-button>
            <template v-if="row.status === 'scheduled'">
              <el-button type="primary" link @click="openEditDialog(row)">修改</el-button>
              <el-button type="danger" link @click="handleCancelSession(row)">取消课次</el-button>
            </template>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无课次，点击右上角「新增课次」排课" />
        </template>
      </el-table>
    </el-card>

    <!-- 批量新增课次对话框 -->
    <el-dialog v-model="createDialogVisible" title="新增课次（可批量）" width="640px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="上课日期" required>
          <el-date-picker
            v-model="createDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            :disabled-date="(d: Date) => d.getTime() < Date.now() - 86400000"
          />
        </el-form-item>
        <el-form-item label="时间段" required>
          <div class="session-rows">
            <div v-for="(row, index) in sessionRows" :key="index" class="session-row">
              <el-time-picker
                v-model="row.start_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="开始"
                style="width: 110px;"
              />
              <span class="row-sep">至</span>
              <el-time-picker
                v-model="row.end_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="结束"
                style="width: 110px;"
              />
              <span class="row-sep">容量</span>
              <el-input-number v-model="row.capacity" :min="1" :max="100" style="width: 110px;" />
              <el-button
                type="danger"
                link
                :icon="Delete"
                :disabled="sessionRows.length <= 1"
                @click="removeRow(index)"
              />
            </div>
            <el-button type="primary" link :icon="Plus" @click="addRow">添加时间段</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreateSessions">
          提交（{{ sessionRows.length }} 个课次）
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改课次对话框 -->
    <el-dialog v-model="editDialogVisible" title="修改课次" width="520px" destroy-on-close>
      <el-alert
        v-if="editingSession && editingSession.booked_count > 0"
        type="info"
        :closable="false"
        :title="`该课次已有 ${editingSession.booked_count} 人报名，只能修改备注`"
        style="margin-bottom: 16px;"
      />
      <el-form label-width="90px">
        <el-form-item label="日期">
          <el-date-picker
            v-model="editForm.session_date"
            type="date"
            value-format="YYYY-MM-DD"
            :disabled="!!editingSession && editingSession.booked_count > 0"
          />
        </el-form-item>
        <el-form-item label="时间">
          <el-time-picker
            v-model="editForm.start_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="开始"
            style="width: 120px;"
            :disabled="!!editingSession && editingSession.booked_count > 0"
          />
          <span class="row-sep">至</span>
          <el-time-picker
            v-model="editForm.end_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="结束"
            style="width: 120px;"
            :disabled="!!editingSession && editingSession.booked_count > 0"
          />
        </el-form-item>
        <el-form-item label="容量">
          <el-input-number
            v-model="editForm.capacity"
            :min="Math.max(editingSession?.booked_count || 1, 1)"
            :max="100"
            :disabled="!!editingSession && editingSession.booked_count > 0"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" placeholder="如：请假原因、注意事项" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleEditSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 报名名单抽屉 -->
    <el-drawer
      v-model="bookingsDrawerVisible"
      :title="`报名名单${currentSession ? `（${currentSession.session_date} ${currentSession.start_time}-${currentSession.end_time}）` : ''}`"
      size="560px"
    >
      <el-table :data="bookings" v-loading="bookingsLoading" stripe>
        <el-table-column prop="member_name" label="会员" width="110">
          <template #default="{ row }">{{ row.member_name || '未知' }}</template>
        </el-table-column>
        <el-table-column prop="member_phone" label="手机号" width="120" />
        <el-table-column label="支付" width="90">
          <template #default="{ row }">
            {{ payTypeText(row.pay_type) }}
            <span class="text-muted">¥{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="(bookingStatusMap[row.status]?.type as any) || 'info'" size="small">
              {{ bookingStatusMap[row.status]?.text || row.status_text || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="核销" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_verified" type="success" size="small">已核销</el-tag>
            <span v-else class="text-muted">未核销</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="报名时间" min-width="150" />
        <template #empty>
          <el-empty description="暂无报名" />
        </template>
      </el-table>
    </el-drawer>
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.course-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.course-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 6px;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

.session-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.session-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.row-sep {
  color: #909399;
  margin: 0 4px;
}
</style>

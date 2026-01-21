<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface PointRule {
  id: number
  name: string
  description: string
  rule_type: 'duration' | 'daily'
  venue_type_id: number | null
  venue_type_name: string
  duration_unit: number
  points_per_unit: number
  max_daily_points: number
  daily_fixed_points: number
  is_active: boolean
  created_at: string
}

interface VenueType {
  id: number
  name: string
}

const loading = ref(false)
const tableData = ref<PointRule[]>([])
const total = ref(0)
const venueTypes = ref<VenueType[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('新增积分规则')
const editingId = ref<number | null>(null)

const ruleForm = reactive({
  name: '',
  description: '',
  rule_type: 'duration' as 'duration' | 'daily',
  venue_type_id: null as number | null,
  duration_unit: 30,
  points_per_unit: 10,
  max_daily_points: 100,
  daily_fixed_points: 50,
  is_active: true
})

const queryParams = reactive({
  page: 1,
  page_size: 10
})

// 获取场馆类型
const fetchVenueTypes = async () => {
  try {
    const res = await request.get('/venues/types')
    venueTypes.value = res.data || []
  } catch {
    // ignore
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/checkin/point-rules', { params: queryParams })
    tableData.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取积分规则失败:', err)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增积分规则'
  editingId.value = null
  Object.assign(ruleForm, {
    name: '',
    description: '',
    rule_type: 'duration',
    venue_type_id: null,
    duration_unit: 30,
    points_per_unit: 10,
    max_daily_points: 100,
    daily_fixed_points: 50,
    is_active: true
  })
  dialogVisible.value = true
}

const handleEdit = (row: PointRule) => {
  dialogTitle.value = '编辑积分规则'
  editingId.value = row.id
  Object.assign(ruleForm, {
    name: row.name,
    description: row.description || '',
    rule_type: row.rule_type,
    venue_type_id: row.venue_type_id,
    duration_unit: row.duration_unit,
    points_per_unit: row.points_per_unit,
    max_daily_points: row.max_daily_points,
    daily_fixed_points: row.daily_fixed_points,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!ruleForm.name) {
    ElMessage.warning('请输入规则名称')
    return
  }

  try {
    if (editingId.value) {
      await request.put(`/checkin/point-rules/${editingId.value}`, ruleForm)
      ElMessage.success('更新成功')
    } else {
      await request.post('/checkin/point-rules', ruleForm)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (err) {
    console.error('保存失败:', err)
  }
}

const handleDelete = async (row: PointRule) => {
  try {
    await ElMessageBox.confirm('确定要删除该积分规则吗？', '提示', { type: 'warning' })
    await request.delete(`/checkin/point-rules/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // 取消或错误
  }
}

const handleToggleStatus = async (row: PointRule) => {
  try {
    await request.put(`/checkin/point-rules/${row.id}`, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已禁用' : '已启用')
    fetchData()
  } catch (err) {
    console.error('切换状态失败:', err)
  }
}

onMounted(() => {
  fetchVenueTypes()
  fetchData()
})
</script>

<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>积分规则配置</span>
          <el-button type="primary" @click="handleAdd">新增规则</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="规则名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="rule_type" label="规则类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.rule_type === 'duration' ? 'primary' : 'success'">
              {{ row.rule_type === 'duration' ? '按时长' : '每日固定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="venue_type_name" label="适用场馆" width="120">
          <template #default="{ row }">
            {{ row.venue_type_name || '所有场馆' }}
          </template>
        </el-table-column>
        <el-table-column label="积分设置" width="200">
          <template #default="{ row }">
            <div v-if="row.rule_type === 'duration'">
              每{{ row.duration_unit }}分钟 {{ row.points_per_unit }}积分
            </div>
            <div v-else>
              每日固定 {{ row.daily_fixed_points }}积分
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="max_daily_points" label="每日上限" width="100">
          <template #default="{ row }">
            {{ row.max_daily_points }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用中' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="ruleForm.description" type="textarea" placeholder="请输入规则描述" />
        </el-form-item>
        <el-form-item label="规则类型" required>
          <el-radio-group v-model="ruleForm.rule_type">
            <el-radio value="duration">按时长计算</el-radio>
            <el-radio value="daily">每日固定积分</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="适用场馆">
          <el-select v-model="ruleForm.venue_type_id" placeholder="所有场馆" clearable style="width: 100%">
            <el-option v-for="t in venueTypes" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <div class="form-tip">不选择则适用于所有场馆类型</div>
        </el-form-item>

        <template v-if="ruleForm.rule_type === 'duration'">
          <el-form-item label="时长单位">
            <el-input-number v-model="ruleForm.duration_unit" :min="1" :max="480" />
            <span style="margin-left: 8px">分钟</span>
          </el-form-item>
          <el-form-item label="每单位积分">
            <el-input-number v-model="ruleForm.points_per_unit" :min="1" :max="1000" />
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="每日积分">
            <el-input-number v-model="ruleForm.daily_fixed_points" :min="1" :max="1000" />
          </el-form-item>
        </template>

        <el-form-item label="每日上限">
          <el-input-number v-model="ruleForm.max_daily_points" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="ruleForm.is_active" />
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
  display: flex;
  flex-direction: column;
  gap: 16px;
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

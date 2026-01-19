<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="券名称" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.type" placeholder="全部" clearable>
            <el-option label="折扣券" value="discount" />
            <el-option label="代金券" value="cash" />
            <el-option label="礼品券" value="gift" />
            <el-option label="体验券" value="experience" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="停用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>优惠券模板</span>
          <el-button type="primary" @click="handleAdd">新增模板</el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="券名称" min-width="150" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag>{{ typeMap[row.type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优惠内容" width="180">
          <template #default="{ row }">
            <span v-if="row.type === 'discount'">{{ row.discount_value }}折</span>
            <span v-else-if="row.type === 'cash'">减{{ row.discount_value }}金币</span>
            <span v-else-if="row.type === 'experience'">{{ row.experience_level_name || '会员' }}体验{{ row.experience_days }}天</span>
            <span v-else>礼品</span>
          </template>
        </el-table-column>
        <el-table-column prop="min_amount" label="最低消费" width="100" />
        <el-table-column label="有效期" width="180">
          <template #default="{ row }">
            <span v-if="row.valid_days">领取后{{ row.valid_days }}天</span>
            <span v-else>{{ row.start_time }} 至 {{ row.end_time }}</span>
          </template>
        </el-table-column>
        <el-table-column label="发放情况" width="120">
          <template #default="{ row }">
            {{ row.issued_count }} / {{ row.total_count || '不限' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleIssue(row)">发放</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="券名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入券名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择类型" style="width: 100%;">
            <el-option label="折扣券" value="discount" />
            <el-option label="代金券" value="cash" />
            <el-option label="礼品券" value="gift" />
            <el-option label="体验券" value="experience" />
          </el-select>
        </el-form-item>
        <!-- 体验券专用字段 -->
        <template v-if="formData.type === 'experience'">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="会员等级" required>
                <el-select v-model="formData.experience_level_id" placeholder="请选择会员等级" style="width: 100%;">
                  <el-option v-for="level in memberLevels" :key="level.id" :label="level.name" :value="level.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="体验天数" required>
                <el-input-number v-model="formData.experience_days" :min="1" placeholder="天数" style="width: 100%;" />
              </el-form-item>
            </el-col>
          </el-row>
          <div class="form-tip" style="margin-bottom: 16px; color: #909399;">使用该券后，用户将自动升级为所选等级的会员，体验期结束后恢复原等级</div>
        </template>
        <!-- 折扣券/代金券字段 -->
        <template v-else>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="优惠值" prop="discount_value">
                <el-input-number v-model="formData.discount_value" :min="0" :precision="2" style="width: 100%;" />
                <div class="form-tip">折扣券填折扣(如0.8)，代金券填金额</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最低消费">
                <el-input-number v-model="formData.min_amount" :min="0" :precision="2" style="width: 100%;" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="最大优惠">
            <el-input-number v-model="formData.max_discount" :min="0" :precision="2" placeholder="折扣券时限制最大优惠金额" style="width: 100%;" />
          </el-form-item>
          <el-form-item label="适用类型">
            <el-select v-model="formData.applicable_type" style="width: 100%;">
              <el-option label="全场通用" value="all" />
              <el-option label="场地预约" value="venue" />
              <el-option label="在线点餐" value="food" />
              <el-option label="教练预约" value="coach" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="有效期类型">
          <el-radio-group v-model="validType">
            <el-radio label="days">领取后N天</el-radio>
            <el-radio label="fixed">固定时间</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="validType === 'days'" label="有效天数">
          <el-input-number v-model="formData.valid_days" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-row v-else :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker v-model="formData.start_time" type="datetime" placeholder="选择开始时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker v-model="formData.end_time" type="datetime" placeholder="选择结束时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发放总量">
              <el-input-number v-model="formData.total_count" :min="0" placeholder="0表示不限" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每人限领">
              <el-input-number v-model="formData.per_limit" :min="1" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
        <el-form-item label="使用说明">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入使用说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 发放弹窗 -->
    <el-dialog v-model="issueDialogVisible" title="发放优惠券" width="500px">
      <el-form label-width="80px">
        <el-form-item label="选择会员">
          <el-select v-model="selectedMembers" multiple filterable remote reserve-keyword placeholder="搜索会员" :remote-method="searchMembers" :loading="memberLoading" style="width: 100%;">
            <el-option v-for="m in memberOptions" :key="m.id" :label="`${m.nickname} (${m.phone})`" :value="m.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="issueDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleIssueSubmit" :loading="issuing">发放</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import request from '@/utils/request'

const typeMap: Record<string, string> = { discount: '折扣券', cash: '代金券', gift: '礼品券', experience: '体验券' }

const loading = ref(false)
const tableData = ref<any[]>([])
const searchForm = reactive({ keyword: '', type: '', is_active: null })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()
const validType = ref('days')

const formData = reactive({
  id: 0, name: '', type: '', discount_value: 0, min_amount: 0, max_discount: null,
  applicable_type: 'all', applicable_ids: '', valid_days: 7, start_time: '', end_time: '',
  total_count: 0, per_limit: 1, is_active: true, description: '',
  experience_days: null as number | null, experience_level_id: null as number | null
})

// 会员等级列表
const memberLevels = ref<any[]>([])
const formRules = {
  name: [{ required: true, message: '请输入券名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const issueDialogVisible = ref(false)
const issuing = ref(false)
const selectedMembers = ref<number[]>([])
const memberOptions = ref<any[]>([])
const memberLoading = ref(false)
let currentTemplateId = 0

const fetchList = async () => {
  loading.value = true
  try {
    const res = await request.get('/coupons/templates', {
      params: { page: pagination.page, page_size: pagination.pageSize, ...searchForm }
    })
    tableData.value = res.data.list
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.type = ''
  searchForm.is_active = null
  pagination.page = 1
  fetchList()
}

const handleAdd = () => {
  dialogTitle.value = '新增模板'
  Object.assign(formData, {
    id: 0, name: '', type: '', discount_value: 0, min_amount: 0, max_discount: null,
    applicable_type: 'all', applicable_ids: '', valid_days: 7, start_time: '', end_time: '',
    total_count: 0, per_limit: 1, is_active: true, description: '',
    experience_days: null, experience_level_id: null
  })
  validType.value = 'days'
  dialogVisible.value = true
}

const handleEdit = async (row: any) => {
  dialogTitle.value = '编辑模板'
  const res = await request.get(`/coupons/templates/${row.id}`)
  Object.assign(formData, res.data)
  validType.value = res.data.valid_days ? 'days' : 'fixed'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  const data = { ...formData }
  if (validType.value === 'days') {
    data.start_time = ''
    data.end_time = ''
  } else {
    data.valid_days = null as any
  }
  try {
    if (formData.id) {
      await request.put(`/coupons/templates/${formData.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await request.post('/coupons/templates', data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该模板吗？', '提示', { type: 'warning' })
    .then(async () => {
      await request.delete(`/coupons/templates/${row.id}`)
      ElMessage.success('删除成功')
      fetchList()
    })
}

const handleIssue = (row: any) => {
  currentTemplateId = row.id
  selectedMembers.value = []
  memberOptions.value = []
  issueDialogVisible.value = true
}

const searchMembers = async (query: string) => {
  if (!query) return
  memberLoading.value = true
  try {
    const res = await request.get('/members/list', { params: { keyword: query, page_size: 20 } })
    memberOptions.value = res.data.list
  } finally {
    memberLoading.value = false
  }
}

const handleIssueSubmit = async () => {
  if (!selectedMembers.value.length) {
    ElMessage.warning('请选择要发放的会员')
    return
  }
  issuing.value = true
  try {
    await request.post(`/coupons/templates/${currentTemplateId}/issue`, { member_ids: selectedMembers.value })
    ElMessage.success('发放成功')
    issueDialogVisible.value = false
    fetchList()
  } finally {
    issuing.value = false
  }
}

const fetchMemberLevels = async () => {
  try {
    const res = await request.get('/member-cards/levels')
    memberLevels.value = res.data || []
  } catch (e) {
    console.error('获取会员等级失败:', e)
  }
}

onMounted(() => {
  fetchList()
  fetchMemberLevels()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.form-tip { font-size: 12px; color: #999; }
</style>

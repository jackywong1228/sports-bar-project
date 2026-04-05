<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface Member {
  id: number
  nickname: string
  phone: string
  avatar: string
  real_name: string
  gender: number
  level_id: number
  level_name: string
  coin_balance: number
  point_balance: number
  member_expire_time: string
  status: boolean
  tag_names: string[]
  created_at: string
}

const loading = ref(false)
const tableData = ref<Member[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  page_size: 10,
  nickname: '',
  phone: '',
  level_id: null as number | null
})

const levels = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const form = reactive({
  id: 0,
  nickname: '',
  phone: '',
  real_name: '',
  gender: 0,
  level_id: null as number | null,
  status: true,
  tag_ids: [] as number[]
})

// 编辑金币/积分弹窗
const rechargeVisible = ref(false)
const rechargeType = ref<'coin' | 'point'>('coin')
const adjustAction = ref<'add' | 'deduct'>('add')
const currentBalance = ref(0)
const rechargeForm = reactive({
  member_id: 0,
  amount: 0,
  remark: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.get('/members', { params: queryParams })
    tableData.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const fetchLevels = async () => {
  const res = await request.get('/members/levels')
  levels.value = res.data
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.nickname = ''
  queryParams.phone = ''
  queryParams.level_id = null
  handleSearch()
}

const handleEdit = (row: Member) => {
  dialogTitle.value = '编辑会员'
  Object.assign(form, {
    id: row.id,
    nickname: row.nickname,
    phone: row.phone,
    real_name: row.real_name,
    gender: row.gender,
    level_id: row.level_id,
    status: row.status
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await request.put(`/members/${form.id}`, form)
    ElMessage.success('更新成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleAdjust = (row: Member, type: 'coin' | 'point') => {
  rechargeType.value = type
  adjustAction.value = 'add'
  currentBalance.value = type === 'coin' ? row.coin_balance : row.point_balance
  rechargeForm.member_id = row.id
  rechargeForm.amount = 0
  rechargeForm.remark = ''
  rechargeVisible.value = true
}

const submitAdjust = async () => {
  if (rechargeForm.amount <= 0) {
    ElMessage.warning('请输入有效数值')
    return
  }
  if (adjustAction.value === 'deduct' && rechargeForm.amount > currentBalance.value) {
    ElMessage.warning(`余额不足，当前余额: ${currentBalance.value}`)
    return
  }
  const actualAmount = adjustAction.value === 'deduct' ? -rechargeForm.amount : rechargeForm.amount
  try {
    await request.post(`/members/recharge/${rechargeType.value}`, {
      member_id: rechargeForm.member_id,
      amount: actualAmount,
      remark: rechargeForm.remark
    })
    ElMessage.success(adjustAction.value === 'add' ? '增加成功' : '扣减成功')
    rechargeVisible.value = false
    fetchData()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: Member) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会员「${row.nickname || row.phone || 'ID:' + row.id}」吗？删除后该会员将无法登录。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    await request.delete(`/members/${row.id}`)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) {
    if (e !== 'cancel' && e?.toString() !== 'cancel') {
      // 非用户取消的错误
    }
  }
}

const genderText = (gender: number) => {
  return { 0: '未知', 1: '男', 2: '女' }[gender] || '未知'
}

onMounted(() => {
  fetchData()
  fetchLevels()
})
</script>

<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="昵称">
          <el-input v-model="queryParams.nickname" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="queryParams.phone" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="queryParams.level_id" placeholder="全部" clearable>
            <el-option v-for="l in levels" :key="l.id" :label="l.name" :value="l.id" />
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
        <span>会员列表</span>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="real_name" label="真实姓名" width="100" />
        <el-table-column label="性别" width="60" class-name="col-secondary">
          <template #default="{ row }">{{ genderText(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="level_name" label="会员等级" width="100" />
        <el-table-column prop="coin_balance" label="金币余额" width="100" />
        <el-table-column prop="point_balance" label="积分余额" width="100" />
        <el-table-column prop="tag_names" label="标签" width="150" class-name="col-secondary">
          <template #default="{ row }">
            <el-tag v-for="name in row.tag_names" :key="name" size="small" style="margin-right: 4px;">
              {{ name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" class-name="col-secondary" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" link @click="handleAdjust(row, 'coin')">编辑金币</el-button>
            <el-button type="warning" link @click="handleAdjust(row, 'point')">编辑积分</el-button>
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

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="0">未知</el-radio>
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="form.level_id" clearable style="width: 100%;">
            <el-option v-for="l in levels" :key="l.id" :label="l.name" :value="l.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑金币/积分弹窗 -->
    <el-dialog v-model="rechargeVisible" :title="rechargeType === 'coin' ? '编辑金币' : '编辑积分'" width="440px">
      <el-form :model="rechargeForm" label-width="80px">
        <el-form-item label="当前余额">
          <span style="font-weight: bold; font-size: 16px;">{{ currentBalance }}</span>
          <span style="margin-left: 4px; color: #999;">{{ rechargeType === 'coin' ? '金币' : '积分' }}</span>
        </el-form-item>
        <el-form-item label="操作类型">
          <el-radio-group v-model="adjustAction">
            <el-radio value="add">增加</el-radio>
            <el-radio value="deduct">减少</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="adjustAction === 'add' ? '增加数量' : '减少数量'">
          <el-input-number v-model="rechargeForm.amount" :min="1" :max="adjustAction === 'deduct' ? currentBalance : undefined" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="rechargeForm.remark" type="textarea" placeholder="可选，说明调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rechargeVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdjust">确定</el-button>
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
</style>

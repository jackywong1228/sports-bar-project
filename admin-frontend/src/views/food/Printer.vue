<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>打印机管理（云打印：飞鹅 / 易联云）</span>
          <el-button type="primary" @click="handleAdd">新增打印机</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        账号级凭据（飞鹅 USER/UKEY、易联云 client_id/secret）在服务器 .env 中配置；
        此处维护设备级信息（SN/KEY、打印角色、启用状态）。
      </el-alert>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="provider_text" label="厂商" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.provider === 'feie' ? 'primary' : 'success'">{{ row.provider_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sn" label="设备编号(SN)" min-width="140" />
        <el-table-column prop="role_text" label="打印角色" width="110" />
        <el-table-column label="在线状态" width="130">
          <template #default="{ row }">
            <span v-if="statusMap[row.id] === undefined">未查询</span>
            <el-tag v-else-if="statusMap[row.id]" size="small" type="success">{{ statusMap[row.id] }}</el-tag>
            <el-tag v-else size="small" type="info">查询失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="90">
          <template #default="{ row }">
            <el-switch
              :model-value="row.enabled"
              @change="(val: boolean) => handleToggle(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-dropdown trigger="click" style="margin: 0 10px" @command="(t: 'cashier' | 'kitchen') => handleTestPrint(row, t)">
              <el-button link type="warning">测试打印</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="cashier">收银票</el-dropdown-item>
                  <el-dropdown-item command="kitchen">制作单</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button link @click="handleQueryStatus(row)">查状态</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="110px">
        <el-form-item label="厂商" prop="provider">
          <el-radio-group v-model="formData.provider">
            <el-radio-button value="feie">飞鹅</el-radio-button>
            <el-radio-button value="yilianyun">易联云</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="如：吧台收银打印机 / 出品区制作打印机" />
        </el-form-item>
        <el-form-item label="设备编号" prop="sn">
          <el-input v-model="formData.sn" placeholder="飞鹅 SN / 易联云 machine_code（打印机底部标签）" />
        </el-form-item>
        <el-form-item label="设备密钥">
          <el-input v-model="formData.printer_key" placeholder="飞鹅 KEY / 易联云 msign（选填）" show-password />
        </el-form-item>
        <el-form-item label="打印角色" prop="role">
          <el-radio-group v-model="formData.role">
            <el-radio-button value="cashier">收银票</el-radio-button>
            <el-radio-button value="kitchen">制作单</el-radio-button>
            <el-radio-button value="both">两者都打</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.remark" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  getPrinters,
  createPrinter,
  updatePrinter,
  deletePrinter,
  togglePrinter,
  testPrint,
  getPrinterStatus,
  type PrinterConfig
} from '@/api/food'

const loading = ref(false)
const tableData = ref<PrinterConfig[]>([])
const statusMap = ref<Record<number, string | null>>({})
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: 0,
  provider: 'feie' as 'feie' | 'yilianyun',
  name: '',
  sn: '',
  printer_key: '',
  role: 'both' as 'cashier' | 'kitchen' | 'both',
  enabled: true,
  remark: ''
})
const formRules = {
  provider: [{ required: true, message: '请选择厂商', trigger: 'change' }],
  name: [{ required: true, message: '请输入打印机名称', trigger: 'blur' }],
  sn: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  role: [{ required: true, message: '请选择打印角色', trigger: 'change' }]
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getPrinters()
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogTitle.value = '新增打印机'
  Object.assign(formData, { id: 0, provider: 'feie', name: '', sn: '', printer_key: '', role: 'both', enabled: true, remark: '' })
  dialogVisible.value = true
}

const handleEdit = (row: PrinterConfig) => {
  dialogTitle.value = '编辑打印机'
  Object.assign(formData, {
    id: row.id,
    provider: row.provider,
    name: row.name,
    sn: row.sn,
    printer_key: row.printer_key || '',
    role: row.role,
    enabled: row.enabled,
    remark: row.remark || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = {
      provider: formData.provider,
      name: formData.name,
      sn: formData.sn,
      printer_key: formData.printer_key || null,
      role: formData.role,
      enabled: formData.enabled,
      remark: formData.remark || null
    }
    if (formData.id) {
      await updatePrinter(formData.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createPrinter(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

const handleToggle = async (row: PrinterConfig, val: boolean) => {
  try {
    await togglePrinter(row.id, val)
    row.enabled = val
    ElMessage.success(val ? '已启用' : '已停用')
  } catch {
    // 报错提示由拦截器统一处理
  }
}

const handleTestPrint = async (row: PrinterConfig, ticketType: 'cashier' | 'kitchen') => {
  try {
    await testPrint(row.id, ticketType)
    ElMessage.success(`测试${ticketType === 'cashier' ? '收银票' : '制作单'}已发送，请查看打印机`)
  } catch {
    // 报错提示由拦截器统一处理
  }
}

const handleQueryStatus = async (row: PrinterConfig) => {
  try {
    const res = await getPrinterStatus(row.id)
    const raw = res.data?.raw
    statusMap.value[row.id] = raw ? String(raw) : null
    ElMessage.info((res as any).message || '查询完成')
  } catch {
    statusMap.value[row.id] = null
  }
}

const handleDelete = (row: PrinterConfig) => {
  ElMessageBox.confirm(`确定要删除打印机「${row.name}」吗？`, '删除确认', {
    type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
  })
    .then(async () => {
      await deletePrinter(row.id)
      ElMessage.success('删除成功')
      fetchList()
    })
    .catch(() => {})
}

onMounted(() => { fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>

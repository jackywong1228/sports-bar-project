<template>
  <div class="page-container">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="菜品名称" clearable style="width: 160px;" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="searchForm.category_id" placeholder="全部" clearable style="width: 140px;">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部" clearable style="width: 110px;">
            <el-option label="上架" :value="true" />
            <el-option label="下架" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="优惠券">
          <el-select v-model="searchForm.coupon_enabled" placeholder="全部" clearable style="width: 110px;">
            <el-option label="可用券" :value="true" />
            <el-option label="不可用券" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <div>
            <el-button type="primary" @click="handleAdd">新增菜品</el-button>
            <el-button
              type="success"
              :disabled="selectedRows.length === 0"
              @click="handleBatchStatus(true)"
            >批量上架{{ selectedRows.length ? `(${selectedRows.length})` : '' }}</el-button>
            <el-button
              type="warning"
              :disabled="selectedRows.length === 0"
              @click="handleBatchStatus(false)"
            >批量下架{{ selectedRows.length ? `(${selectedRows.length})` : '' }}</el-button>
          </div>
          <span class="header-tip">共 {{ pagination.total }} 个菜品</span>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column label="图片" width="80">
          <template #default="{ row }">
            <el-image
              v-if="row.image"
              :src="row.image"
              :preview-src-list="[row.image]"
              preview-teleported
              fit="cover"
              style="width: 50px; height: 50px; border-radius: 4px;"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="菜品名称" min-width="140">
          <template #default="{ row }">
            <div>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.has_specs" size="small" type="warning" style="margin-left: 6px;">规格</el-tag>
              <el-tag v-if="row.is_recommend" size="small" type="danger" style="margin-left: 4px;">荐</el-tag>
            </div>
            <div v-if="row.tags" class="tags-text">{{ row.tags }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="110" />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">
            <span class="price">¥{{ row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="库存" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.stock <= 10 ? 'danger' : row.stock <= 30 ? 'warning' : 'success'"
              style="cursor: pointer;"
              @click="handleQuickStock(row)"
            >{{ row.stock }}</el-tag>
            <span v-if="row.stock <= 10" class="low-stock-tip">低库存</span>
          </template>
        </el-table-column>
        <el-table-column prop="sales" label="销量" width="80" />
        <el-table-column label="可用券" width="90">
          <template #default="{ row }">
            <el-tag :type="row.coupon_enabled ? 'success' : 'info'" size="small">
              {{ row.coupon_enabled ? '可用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="(val: any) => handleToggleStatus(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleQuickStock(row)">调库存</el-button>
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

    <!-- 新增/编辑菜品 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px" destroy-on-close top="5vh">
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="菜品名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入菜品名称" maxlength="100" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类" prop="category_id">
              <el-select v-model="formData.category_id" placeholder="请选择分类" style="width: 100%;" @change="handleCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="formData.sort_order" :min="0" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="菜品图片">
          <el-upload
            class="food-uploader"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            accept="image/*"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
          >
            <img v-if="formData.image" :src="formData.image" class="food-image" alt="" />
            <div v-else class="upload-placeholder">
              <el-icon><Plus /></el-icon>
              <span>上传图片</span>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="口味、份量等说明（选填）" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="售价" prop="price">
              <el-input-number v-model="formData.price" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="原价">
              <el-input-number v-model="formData.original_price" :min="0" :precision="2" style="width: 100%;" placeholder="划线价（选填）" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="库存" prop="stock">
              <el-input-number v-model="formData.stock" :min="0" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="上架">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="推荐">
              <el-switch v-model="formData.is_recommend" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="可用优惠券">
              <el-switch v-model="formData.coupon_enabled" />
              <div class="form-tip">酒水类请关闭</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标签">
          <el-input v-model="formData.tags" placeholder="多个标签用逗号分隔，如：热销,微辣" />
        </el-form-item>

        <!-- 规格组编辑器 -->
        <el-divider content-position="left">
          <span>规格设置</span>
          <span class="form-tip" style="margin-left: 8px;">瓶装酒水等无规格商品可留空</span>
        </el-divider>
        <div class="spec-editor">
          <div v-for="(group, gi) in formData.spec_groups" :key="gi" class="spec-group">
            <div class="spec-group-header">
              <el-input v-model="group.name" placeholder="规格组名称，如：杯型 / 加料" style="width: 200px;" />
              <el-radio-group v-model="group.select_type">
                <el-radio-button value="single">单选</el-radio-button>
                <el-radio-button value="multi">多选</el-radio-button>
              </el-radio-group>
              <el-checkbox v-model="group.required">必选</el-checkbox>
              <el-button link type="danger" @click="removeSpecGroup(gi)">删除规格组</el-button>
            </div>
            <div class="spec-options">
              <div v-for="(opt, oi) in group.options" :key="oi" class="spec-option-row">
                <el-input v-model="opt.name" placeholder="选项名称，如：大杯" style="width: 200px;" />
                <el-input-number v-model="opt.price_delta" :precision="2" :step="0.5" style="width: 150px;" />
                <span class="form-tip">加价（元）</span>
                <el-button link type="danger" @click="removeSpecOption(gi, oi)">删除</el-button>
              </div>
              <el-button link type="primary" @click="addSpecOption(gi)">+ 添加选项</el-button>
            </div>
          </div>
          <el-button type="primary" plain @click="addSpecGroup">+ 添加规格组</el-button>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getFoodCategories,
  getFoodItems,
  getFoodItemDetail,
  createFoodItem,
  updateFoodItem,
  deleteFoodItem,
  adjustFoodItemStock,
  updateFoodItemStatus,
  batchUpdateFoodItemStatus,
  type FoodCategory,
  type FoodItem,
  type FoodSpecGroup
} from '@/api/food'

const loading = ref(false)
const tableData = ref<FoodItem[]>([])
const categories = ref<FoodCategory[]>([])
const selectedRows = ref<FoodItem[]>([])
const searchForm = reactive<{
  keyword: string
  category_id: number | null
  is_active: boolean | null
  coupon_enabled: boolean | null
}>({ keyword: '', category_id: null, is_active: null, coupon_enabled: null })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

interface ItemForm {
  id: number
  category_id: number | null
  name: string
  image: string
  description: string
  price: number
  original_price: number | null
  stock: number
  sort_order: number
  is_active: boolean
  is_recommend: boolean
  coupon_enabled: boolean
  tags: string
  spec_groups: FoodSpecGroup[]
}

const emptyForm = (): ItemForm => ({
  id: 0,
  category_id: null,
  name: '',
  image: '',
  description: '',
  price: 0,
  original_price: null,
  stock: 999,
  sort_order: 0,
  is_active: true,
  is_recommend: false,
  coupon_enabled: true,
  tags: '',
  spec_groups: []
})

const formData = reactive<ItemForm>(emptyForm())
const formRules = {
  name: [{ required: true, message: '请输入菜品名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }]
}

const uploadUrl = '/api/v1/upload/image?folder=food'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))
const handleUploadSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    formData.image = response.data.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}
const handleUploadError = () => ElMessage.error('上传失败')

const fetchCategories = async () => {
  const res = await getFoodCategories()
  categories.value = res.data
}

const fetchList = async () => {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.category_id) params.category_id = searchForm.category_id
    if (searchForm.is_active !== null) params.is_active = searchForm.is_active
    if (searchForm.coupon_enabled !== null) params.coupon_enabled = searchForm.coupon_enabled
    const res = await getFoodItems(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchList()
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.category_id = null
  searchForm.is_active = null
  searchForm.coupon_enabled = null
  pagination.page = 1
  fetchList()
}

const handleSelectionChange = (rows: FoodItem[]) => {
  selectedRows.value = rows
}

// ── 新增 / 编辑 ──

const handleAdd = () => {
  dialogTitle.value = '新增菜品'
  Object.assign(formData, emptyForm())
  dialogVisible.value = true
}

const handleEdit = async (row: FoodItem) => {
  dialogTitle.value = '编辑菜品'
  const res = await getFoodItemDetail(row.id)
  const d = res.data as FoodItem
  Object.assign(formData, {
    id: d.id,
    category_id: d.category_id,
    name: d.name,
    image: d.image || '',
    description: d.description || '',
    price: d.price,
    original_price: d.original_price,
    stock: d.stock,
    sort_order: d.sort_order,
    is_active: d.is_active,
    is_recommend: d.is_recommend,
    coupon_enabled: d.coupon_enabled,
    tags: d.tags || '',
    spec_groups: (d.spec_groups || []).map(g => ({
      name: g.name,
      select_type: g.select_type,
      required: g.required,
      sort_order: g.sort_order,
      options: (g.options || []).map(o => ({
        name: o.name,
        price_delta: o.price_delta,
        is_active: o.is_active,
        sort_order: o.sort_order
      }))
    }))
  })
  dialogVisible.value = true
}

// 选中酒水类分类时自动关闭优惠券（可手动改回）
const handleCategoryChange = (categoryId: number | null) => {
  const c = categories.value.find(x => x.id === categoryId)
  if (c && /酒/.test(c.name)) {
    formData.coupon_enabled = false
    ElMessage.info('检测到酒水类分类，已自动关闭优惠券开关')
  }
}

// ── 规格组编辑器 ──

const addSpecGroup = () => {
  formData.spec_groups.push({
    name: '',
    select_type: 'single',
    required: false,
    sort_order: formData.spec_groups.length,
    options: [{ name: '', price_delta: 0, is_active: true, sort_order: 0 }]
  })
}

const removeSpecGroup = (gi: number) => {
  formData.spec_groups.splice(gi, 1)
}

const addSpecOption = (gi: number) => {
  const group = formData.spec_groups[gi]
  if (!group) return
  group.options.push({ name: '', price_delta: 0, is_active: true, sort_order: group.options.length })
}

const removeSpecOption = (gi: number, oi: number) => {
  formData.spec_groups[gi]?.options.splice(oi, 1)
}

const validateSpecGroups = (): boolean => {
  for (const g of formData.spec_groups) {
    if (!g.name.trim()) {
      ElMessage.error('规格组名称不能为空')
      return false
    }
    const validOptions = g.options.filter(o => o.name.trim())
    if (validOptions.length === 0) {
      ElMessage.error(`规格组「${g.name}」至少需要一个选项`)
      return false
    }
  }
  return true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  if (!validateSpecGroups()) return
  submitting.value = true
  try {
    // 过滤掉空选项，规格组整体提交（后端为整体替换）
    const specGroups = formData.spec_groups.map((g, gi) => ({
      name: g.name.trim(),
      select_type: g.select_type,
      required: g.required,
      sort_order: gi,
      options: g.options
        .filter(o => o.name.trim())
        .map((o, oi) => ({
          name: o.name.trim(),
          price_delta: o.price_delta,
          is_active: o.is_active,
          sort_order: oi
        }))
    }))
    const payload = {
      category_id: formData.category_id,
      name: formData.name,
      image: formData.image || null,
      description: formData.description || null,
      price: formData.price,
      original_price: formData.original_price,
      stock: formData.stock,
      sort_order: formData.sort_order,
      is_active: formData.is_active,
      is_recommend: formData.is_recommend,
      coupon_enabled: formData.coupon_enabled,
      tags: formData.tags || null,
      spec_groups: specGroups
    }
    if (formData.id) {
      await updateFoodItem(formData.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createFoodItem(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ── 库存 / 状态 / 删除 ──

const handleQuickStock = (row: FoodItem) => {
  ElMessageBox.prompt(`调整「${row.name}」的库存（当前 ${row.stock}）`, '库存调整', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: String(row.stock),
    inputPattern: /^\d+$/,
    inputErrorMessage: '请输入非负整数'
  }).then(async ({ value }) => {
    const stock = parseInt(value, 10)
    await adjustFoodItemStock(row.id, stock)
    ElMessage.success('库存已更新')
    fetchList()
  }).catch(() => {})
}

const handleToggleStatus = async (row: FoodItem, val: boolean) => {
  try {
    await updateFoodItemStatus(row.id, val)
    row.is_active = val
    ElMessage.success(val ? '已上架' : '已下架')
  } catch {
    // 报错提示由拦截器统一处理
  }
}

const handleBatchStatus = (isActive: boolean) => {
  const ids = selectedRows.value.map(r => r.id)
  const action = isActive ? '上架' : '下架'
  ElMessageBox.confirm(`确定要批量${action}选中的 ${ids.length} 个菜品吗？`, '批量操作', { type: 'warning' })
    .then(async () => {
      await batchUpdateFoodItemStatus(ids, isActive)
      ElMessage.success(`批量${action}成功`)
      fetchList()
    })
    .catch(() => {})
}

const handleDelete = (row: FoodItem) => {
  ElMessageBox.confirm(`确定要删除「${row.name}」吗？历史订单明细不受影响。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      await deleteFoodItem(row.id)
      ElMessage.success('删除成功')
      fetchList()
    })
    .catch(() => {})
}

onMounted(() => { fetchCategories(); fetchList() })
</script>

<style scoped>
.page-container { padding: 20px; }
.search-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-tip { color: #909399; font-size: 13px; }
.price { color: #f56c6c; font-weight: 600; }
.tags-text { color: #909399; font-size: 12px; }
.low-stock-tip { color: #f56c6c; font-size: 12px; margin-left: 4px; }
.form-tip { color: #909399; font-size: 12px; }
.food-uploader :deep(.el-upload) {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}
.food-uploader :deep(.el-upload:hover) { border-color: #409eff; }
.food-image { width: 120px; height: 120px; object-fit: cover; display: block; }
.upload-placeholder {
  width: 120px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
  font-size: 13px;
}
.spec-editor { width: 100%; }
.spec-group {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fafafa;
}
.spec-group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.spec-options { padding-left: 8px; }
.spec-option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>

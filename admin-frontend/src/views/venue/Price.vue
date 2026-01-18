<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

interface VenueItem {
  id: number
  name: string
  price: number
  status: number
  editing?: boolean
  newPrice?: number
}

interface TypeGroup {
  type_id: number
  type_name: string
  venues: VenueItem[]
}

const loading = ref(false)
const priceGroups = ref<TypeGroup[]>([])
const selectedVenues = ref<number[]>([])
const batchPrice = ref<number>(0)
const batchDialogVisible = ref(false)
const selectedTypeName = ref('')

const statusMap: Record<number, { text: string; type: string }> = {
  0: { text: '停用', type: 'danger' },
  1: { text: '空闲', type: 'success' },
  2: { text: '使用中', type: 'warning' }
}

const fetchPrices = async () => {
  loading.value = true
  try {
    const res = await request.get('/venues/prices/summary')
    priceGroups.value = res.data.map((group: TypeGroup) => ({
      ...group,
      venues: group.venues.map(v => ({ ...v, editing: false, newPrice: v.price }))
    }))
  } finally {
    loading.value = false
  }
}

// 开始编辑价格
const startEdit = (venue: VenueItem) => {
  venue.editing = true
  venue.newPrice = venue.price
}

// 取消编辑
const cancelEdit = (venue: VenueItem) => {
  venue.editing = false
  venue.newPrice = venue.price
}

// 保存单个价格
const savePrice = async (venue: VenueItem) => {
  if (venue.newPrice === undefined || venue.newPrice < 0) {
    ElMessage.warning('请输入有效的价格')
    return
  }

  try {
    await request.put(`/venues/${venue.id}/price?price=${venue.newPrice}`)
    venue.price = venue.newPrice
    venue.editing = false
    ElMessage.success('价格更新成功')
  } catch (e) {
    // 错误已在拦截器处理
  }
}

// 打开批量修改对话框
const openBatchDialog = (group: TypeGroup) => {
  selectedTypeName.value = group.type_name
  selectedVenues.value = group.venues.map(v => v.id)
  batchPrice.value = group.venues[0]?.price || 0
  batchDialogVisible.value = true
}

// 批量更新价格
const handleBatchUpdate = async () => {
  if (selectedVenues.value.length === 0) {
    ElMessage.warning('请选择要修改的场馆')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定将选中的 ${selectedVenues.value.length} 个场馆价格修改为 ${batchPrice.value} 金币/小时吗？`,
      '批量修改价格',
      { type: 'warning' }
    )

    await request.put('/venues/batch/price', {
      venue_ids: selectedVenues.value,
      price: batchPrice.value
    })

    ElMessage.success('批量更新成功')
    batchDialogVisible.value = false
    fetchPrices()
  } catch (e) {
    // 取消或错误
  }
}

// 快速调价按钮
const quickAdjust = async (venue: VenueItem, adjustment: number) => {
  const newPrice = Math.max(0, venue.price + adjustment)
  try {
    await request.put(`/venues/${venue.id}/price?price=${newPrice}`)
    venue.price = newPrice
    venue.newPrice = newPrice
    ElMessage.success(`价格已${adjustment > 0 ? '上调' : '下调'}至 ${newPrice} 金币/小时`)
  } catch (e) {
    // 错误已在拦截器处理
  }
}

onMounted(() => {
  fetchPrices()
})
</script>

<template>
  <div class="page-container">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h2>场馆价格管理</h2>
          <p class="description">根据高峰低峰时段，实时调整场馆预约价格</p>
        </div>
        <el-button type="primary" @click="fetchPrices" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新价格
        </el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="price-groups">
      <el-card v-for="group in priceGroups" :key="group.type_id" class="type-card">
        <template #header>
          <div class="type-header">
            <span class="type-name">{{ group.type_name }}</span>
            <el-button type="primary" size="small" @click="openBatchDialog(group)">
              批量调价
            </el-button>
          </div>
        </template>

        <el-table :data="group.venues" stripe>
          <el-table-column prop="name" label="场馆名称" width="180" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.status]?.type as any" size="small">
                {{ statusMap[row.status]?.text }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="当前价格(金币/小时)" width="200">
            <template #default="{ row }">
              <div v-if="!row.editing" class="price-display">
                <span class="price-value">{{ row.price }}</span>
                <el-button type="primary" link size="small" @click="startEdit(row)">
                  修改
                </el-button>
              </div>
              <div v-else class="price-edit">
                <el-input-number
                  v-model="row.newPrice"
                  :min="0"
                  :precision="2"
                  size="small"
                  style="width: 120px;"
                />
                <el-button type="success" size="small" @click="savePrice(row)">保存</el-button>
                <el-button size="small" @click="cancelEdit(row)">取消</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="快速调价" width="200">
            <template #default="{ row }">
              <div class="quick-adjust">
                <el-button-group size="small">
                  <el-button @click="quickAdjust(row, -10)">-10</el-button>
                  <el-button @click="quickAdjust(row, -5)">-5</el-button>
                  <el-button type="primary" @click="quickAdjust(row, 5)">+5</el-button>
                  <el-button type="primary" @click="quickAdjust(row, 10)">+10</el-button>
                </el-button-group>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 批量修改对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量修改价格" width="400px">
      <el-form label-width="100px">
        <el-form-item label="场馆类型">
          <el-tag type="info">{{ selectedTypeName }}</el-tag>
        </el-form-item>
        <el-form-item label="场馆数量">
          <span>{{ selectedVenues.length }} 个</span>
        </el-form-item>
        <el-form-item label="统一价格">
          <el-input-number
            v-model="batchPrice"
            :min="0"
            :precision="2"
            style="width: 200px;"
          />
          <span style="margin-left: 8px;">金币/小时</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchUpdate">确定批量修改</el-button>
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

.header-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-card :deep(.el-card__body) {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.header-content h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.header-content .description {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.header-content .el-button {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.header-content .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.price-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.type-card {
  border-radius: 8px;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.price-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.price-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.price-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-adjust {
  display: flex;
  gap: 4px;
}
</style>

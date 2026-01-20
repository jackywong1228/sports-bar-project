<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import draggable from 'vuedraggable'
import ConfigPanel from './components/ConfigPanel.vue'
import PhonePreview from './components/PhonePreview.vue'
import MenuItemEditor from './components/MenuItemEditor.vue'
import {
  getPageList,
  getPageDetail,
  updatePage,
  getBlockList,
  updateBlock,
  getMenuItemList,
  createMenuItem,
  updateMenuItem,
  deleteMenuItem,
  batchSortMenuItems,
  publishConfig,
  getVersionList,
  rollbackVersion,
  initDefaultData
} from '@/api/ui-editor'
import type { UIPageConfig, UIBlockConfig, UIMenuItem } from './types'

// 数据状态
const loading = ref(false)
const pages = ref<UIPageConfig[]>([])
const blocks = ref<UIBlockConfig[]>([])
const menuItems = ref<UIMenuItem[]>([])
const tabBarItems = ref<UIMenuItem[]>([])
const versions = ref<any[]>([])

// 当前选中
const currentPageCode = ref('home')
const currentPage = computed(() => pages.value.find(p => p.page_code === currentPageCode.value))

// 弹窗状态
const menuEditorVisible = ref(false)
const editingMenuItem = ref<UIMenuItem | null>(null)
const menuEditorMode = ref<'add' | 'edit'>('add')
const menuEditorType = ref<'quick_entry' | 'tabbar'>('quick_entry')

const versionDialogVisible = ref(false)
const publishDialogVisible = ref(false)
const publishNote = ref('')

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    const [pagesRes, blocksRes, menuRes] = await Promise.all([
      getPageList(),
      getBlockList(),
      getMenuItemList()
    ])
    pages.value = pagesRes.data || []
    blocks.value = blocksRes.data || []

    const allMenuItems = menuRes.data || []
    menuItems.value = allMenuItems.filter((m: UIMenuItem) => m.menu_type !== 'tabbar')
    tabBarItems.value = allMenuItems.filter((m: UIMenuItem) => m.menu_type === 'tabbar')
      .sort((a: UIMenuItem, b: UIMenuItem) => a.sort_order - b.sort_order)
  } catch (err: any) {
    ElMessage.error(err.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 获取当前页面的区块
const currentBlocks = computed(() => {
  return blocks.value
    .filter(b => b.page_code === currentPageCode.value)
    .sort((a, b) => a.sort_order - b.sort_order)
})

// 获取当前页面的快捷入口菜单项
const currentQuickEntries = computed(() => {
  const quickEntryBlock = currentBlocks.value.find(b => b.block_type === 'quick_entry')
  if (!quickEntryBlock) return []
  return menuItems.value
    .filter(m => m.menu_type === 'quick_entry' && m.block_id === quickEntryBlock.id)
    .sort((a, b) => a.sort_order - b.sort_order)
})

// 切换区块可见性
const toggleBlockVisible = async (block: UIBlockConfig) => {
  try {
    await updateBlock(block.id, { is_active: !block.is_active })
    block.is_active = !block.is_active
    ElMessage.success('更新成功')
  } catch (err: any) {
    ElMessage.error(err.message || '更新失败')
  }
}

// 区块排序改变
const onBlocksOrderChange = async () => {
  const updates = currentBlocks.value.map((b, index) => ({
    id: b.id,
    sort_order: index
  }))

  try {
    for (const item of updates) {
      await updateBlock(item.id, { sort_order: item.sort_order })
    }
    ElMessage.success('排序已保存')
  } catch (err: any) {
    ElMessage.error(err.message || '保存排序失败')
  }
}

// 快捷入口菜单排序改变
const onQuickEntriesOrderChange = async () => {
  const items = currentQuickEntries.value.map((m, index) => ({
    id: m.id,
    sort_order: index
  }))

  try {
    await batchSortMenuItems({ items })
    ElMessage.success('排序已保存')
  } catch (err: any) {
    ElMessage.error(err.message || '保存排序失败')
  }
}

// TabBar排序改变
const onTabBarOrderChange = async () => {
  const items = tabBarItems.value.map((m, index) => ({
    id: m.id,
    sort_order: index
  }))

  try {
    await batchSortMenuItems({ items })
    ElMessage.success('排序已保存')
  } catch (err: any) {
    ElMessage.error(err.message || '保存排序失败')
  }
}

// 添加快捷入口
const handleAddQuickEntry = () => {
  menuEditorMode.value = 'add'
  menuEditorType.value = 'quick_entry'
  editingMenuItem.value = null
  menuEditorVisible.value = true
}

// 编辑快捷入口
const handleEditQuickEntry = (item: UIMenuItem) => {
  menuEditorMode.value = 'edit'
  menuEditorType.value = 'quick_entry'
  editingMenuItem.value = { ...item }
  menuEditorVisible.value = true
}

// 删除快捷入口
const handleDeleteQuickEntry = async (item: UIMenuItem) => {
  try {
    await ElMessageBox.confirm('确定要删除该快捷入口吗？', '提示', { type: 'warning' })
    await deleteMenuItem(item.id)
    ElMessage.success('删除成功')
    await fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

// 添加TabBar项
const handleAddTabBar = () => {
  if (tabBarItems.value.length >= 5) {
    ElMessage.warning('TabBar最多只能有5个项目')
    return
  }
  menuEditorMode.value = 'add'
  menuEditorType.value = 'tabbar'
  editingMenuItem.value = null
  menuEditorVisible.value = true
}

// 编辑TabBar项
const handleEditTabBar = (item: UIMenuItem) => {
  menuEditorMode.value = 'edit'
  menuEditorType.value = 'tabbar'
  editingMenuItem.value = { ...item }
  menuEditorVisible.value = true
}

// 删除TabBar项
const handleDeleteTabBar = async (item: UIMenuItem) => {
  try {
    await ElMessageBox.confirm('确定要删除该TabBar项吗？', '提示', { type: 'warning' })
    await deleteMenuItem(item.id)
    ElMessage.success('删除成功')
    await fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

// 切换菜单项可见性
const toggleMenuItemVisible = async (item: UIMenuItem) => {
  try {
    await updateMenuItem(item.id, { is_visible: !item.is_visible })
    item.is_visible = !item.is_visible
    ElMessage.success('更新成功')
  } catch (err: any) {
    ElMessage.error(err.message || '更新失败')
  }
}

// 保存菜单项
const handleSaveMenuItem = async (formData: any) => {
  try {
    const quickEntryBlock = currentBlocks.value.find(b => b.block_type === 'quick_entry')

    const data = {
      ...formData,
      menu_type: menuEditorType.value,
      block_id: menuEditorType.value === 'quick_entry' ? quickEntryBlock?.id : null
    }

    if (menuEditorMode.value === 'add') {
      data.sort_order = menuEditorType.value === 'tabbar'
        ? tabBarItems.value.length
        : currentQuickEntries.value.length
      await createMenuItem(data)
      ElMessage.success('添加成功')
    } else {
      await updateMenuItem(editingMenuItem.value!.id, data)
      ElMessage.success('更新成功')
    }

    menuEditorVisible.value = false
    await fetchData()
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  }
}

// 打开版本历史
const handleOpenVersions = async () => {
  try {
    const res = await getVersionList({ limit: 20 })
    versions.value = res.data || []
    versionDialogVisible.value = true
  } catch (err: any) {
    ElMessage.error(err.message || '获取版本历史失败')
  }
}

// 回滚版本
const handleRollback = async (version: any) => {
  try {
    await ElMessageBox.confirm(`确定要回滚到版本 ${version.version} 吗？`, '提示', { type: 'warning' })
    await rollbackVersion(version.id)
    ElMessage.success('回滚成功')
    versionDialogVisible.value = false
    await fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '回滚失败')
    }
  }
}

// 发布配置
const handlePublish = async () => {
  try {
    await publishConfig({ publish_note: publishNote.value })
    ElMessage.success('发布成功')
    publishDialogVisible.value = false
    publishNote.value = ''
  } catch (err: any) {
    ElMessage.error(err.message || '发布失败')
  }
}

// 初始化默认数据
const handleInitDefaultData = async () => {
  try {
    await ElMessageBox.confirm('确定要初始化默认配置数据吗？这将覆盖现有配置。', '提示', { type: 'warning' })
    await initDefaultData()
    ElMessage.success('初始化成功')
    await fetchData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '初始化失败')
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="ui-editor" v-loading="loading">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-radio-group v-model="currentPageCode" size="default">
          <el-radio-button v-for="page in pages" :key="page.page_code" :value="page.page_code">
            {{ page.page_name }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="toolbar-right">
        <el-button @click="handleInitDefaultData">初始化默认数据</el-button>
        <el-button @click="handleOpenVersions">版本历史</el-button>
        <el-button type="primary" @click="publishDialogVisible = true">发布配置</el-button>
      </div>
    </div>

    <!-- 主编辑区 -->
    <div class="editor-main">
      <!-- 左侧配置面板 -->
      <div class="config-panel">
        <ConfigPanel
          :current-page="currentPage"
          :blocks="currentBlocks"
          :quick-entries="currentQuickEntries"
          :tab-bar-items="tabBarItems"
          @toggle-block="toggleBlockVisible"
          @blocks-order-change="onBlocksOrderChange"
          @add-quick-entry="handleAddQuickEntry"
          @edit-quick-entry="handleEditQuickEntry"
          @delete-quick-entry="handleDeleteQuickEntry"
          @quick-entries-order-change="onQuickEntriesOrderChange"
          @add-tabbar="handleAddTabBar"
          @edit-tabbar="handleEditTabBar"
          @delete-tabbar="handleDeleteTabBar"
          @tabbar-order-change="onTabBarOrderChange"
          @toggle-menu-visible="toggleMenuItemVisible"
        />
      </div>

      <!-- 右侧手机预览 -->
      <div class="preview-panel">
        <PhonePreview
          :blocks="currentBlocks"
          :quick-entries="currentQuickEntries"
          :tab-bar-items="tabBarItems"
        />
      </div>
    </div>

    <!-- 菜单项编辑弹窗 -->
    <MenuItemEditor
      v-model:visible="menuEditorVisible"
      :mode="menuEditorMode"
      :menu-type="menuEditorType"
      :initial-data="editingMenuItem"
      @save="handleSaveMenuItem"
    />

    <!-- 版本历史弹窗 -->
    <el-dialog v-model="versionDialogVisible" title="版本历史" width="700px">
      <el-table :data="versions" stripe>
        <el-table-column prop="version" label="版本号" width="80" />
        <el-table-column prop="version_name" label="版本名称" />
        <el-table-column prop="publish_note" label="发布说明" />
        <el-table-column prop="created_at" label="发布时间" width="180" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" type="success">当前</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleRollback(row)" :disabled="row.is_current">
              回滚
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 发布弹窗 -->
    <el-dialog v-model="publishDialogVisible" title="发布配置" width="500px">
      <el-form>
        <el-form-item label="发布说明">
          <el-input v-model="publishNote" type="textarea" :rows="3" placeholder="请输入发布说明（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePublish">确认发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ui-editor {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 20px;
  gap: 20px;
}

.config-panel {
  width: 400px;
  background: #fff;
  border-radius: 8px;
  overflow-y: auto;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.preview-panel {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 20px;
}
</style>

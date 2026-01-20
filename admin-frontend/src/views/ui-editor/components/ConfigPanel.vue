<script setup lang="ts">
import { computed } from 'vue'
import draggable from 'vuedraggable'
import type { UIPageConfig, UIBlockConfig, UIMenuItem } from '../types'

const props = defineProps<{
  currentPage?: UIPageConfig
  blocks: UIBlockConfig[]
  quickEntries: UIMenuItem[]
  tabBarItems: UIMenuItem[]
}>()

const emit = defineEmits<{
  (e: 'toggle-block', block: UIBlockConfig): void
  (e: 'blocks-order-change'): void
  (e: 'add-quick-entry'): void
  (e: 'edit-quick-entry', item: UIMenuItem): void
  (e: 'delete-quick-entry', item: UIMenuItem): void
  (e: 'quick-entries-order-change'): void
  (e: 'add-tabbar'): void
  (e: 'edit-tabbar', item: UIMenuItem): void
  (e: 'delete-tabbar', item: UIMenuItem): void
  (e: 'tabbar-order-change'): void
  (e: 'toggle-menu-visible', item: UIMenuItem): void
}>()

const localBlocks = computed({
  get: () => props.blocks,
  set: () => emit('blocks-order-change')
})

const localQuickEntries = computed({
  get: () => props.quickEntries,
  set: () => emit('quick-entries-order-change')
})

const localTabBarItems = computed({
  get: () => props.tabBarItems,
  set: () => emit('tabbar-order-change')
})

const getBlockTypeName = (type: string) => {
  const map: Record<string, string> = {
    banner: '轮播图',
    quick_entry: '快捷入口',
    list: '列表区块',
    scroll: '横向滚动',
    custom: '自定义'
  }
  return map[type] || type
}
</script>

<template>
  <div class="config-panel">
    <!-- 页面信息 -->
    <div class="panel-section">
      <div class="section-header">
        <span class="section-title">页面信息</span>
      </div>
      <div class="section-content" v-if="currentPage">
        <div class="info-item">
          <span class="label">页面编码:</span>
          <span class="value">{{ currentPage.page_code }}</span>
        </div>
        <div class="info-item">
          <span class="label">页面名称:</span>
          <span class="value">{{ currentPage.page_name }}</span>
        </div>
        <div class="info-item">
          <span class="label">页面类型:</span>
          <el-tag size="small">{{ currentPage.page_type === 'tabbar' ? 'TabBar页' : '普通页' }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 区块排序 -->
    <div class="panel-section">
      <div class="section-header">
        <span class="section-title">区块管理</span>
        <span class="section-tip">拖拽调整顺序</span>
      </div>
      <div class="section-content">
        <draggable
          v-model="localBlocks"
          item-key="id"
          handle=".drag-handle"
          @end="emit('blocks-order-change')"
          class="block-list"
        >
          <template #item="{ element }">
            <div class="block-item" :class="{ disabled: !element.is_active }">
              <el-icon class="drag-handle"><Rank /></el-icon>
              <div class="block-info">
                <span class="block-name">{{ element.block_name }}</span>
                <el-tag size="small" type="info">{{ getBlockTypeName(element.block_type) }}</el-tag>
              </div>
              <el-switch
                :model-value="element.is_active"
                size="small"
                @change="emit('toggle-block', element)"
              />
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- 快捷入口管理 -->
    <div class="panel-section">
      <div class="section-header">
        <span class="section-title">快捷入口</span>
        <el-button type="primary" link size="small" @click="emit('add-quick-entry')">
          <el-icon><Plus /></el-icon>添加
        </el-button>
      </div>
      <div class="section-content">
        <draggable
          v-model="localQuickEntries"
          item-key="id"
          handle=".drag-handle"
          @end="emit('quick-entries-order-change')"
          class="menu-list"
        >
          <template #item="{ element }">
            <div class="menu-item" :class="{ hidden: !element.is_visible }">
              <el-icon class="drag-handle"><Rank /></el-icon>
              <div class="menu-icon">
                <el-image v-if="element.icon" :src="element.icon" fit="contain" />
                <el-icon v-else><Picture /></el-icon>
              </div>
              <div class="menu-info">
                <span class="menu-title">{{ element.title }}</span>
                <span class="menu-link">{{ element.link_value || '无跳转' }}</span>
              </div>
              <div class="menu-actions">
                <el-button link size="small" @click="emit('toggle-menu-visible', element)">
                  <el-icon><View v-if="element.is_visible" /><Hide v-else /></el-icon>
                </el-button>
                <el-button link size="small" @click="emit('edit-quick-entry', element)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button link size="small" type="danger" @click="emit('delete-quick-entry', element)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
        </draggable>
        <div v-if="quickEntries.length === 0" class="empty-tip">
          暂无快捷入口，点击上方添加
        </div>
      </div>
    </div>

    <!-- TabBar管理 -->
    <div class="panel-section">
      <div class="section-header">
        <span class="section-title">底部TabBar</span>
        <el-button type="primary" link size="small" @click="emit('add-tabbar')" :disabled="tabBarItems.length >= 5">
          <el-icon><Plus /></el-icon>添加
        </el-button>
      </div>
      <div class="section-content">
        <draggable
          v-model="localTabBarItems"
          item-key="id"
          handle=".drag-handle"
          @end="emit('tabbar-order-change')"
          class="menu-list"
        >
          <template #item="{ element }">
            <div class="menu-item tabbar-item" :class="{ hidden: !element.is_visible }">
              <el-icon class="drag-handle"><Rank /></el-icon>
              <div class="menu-icon">
                <el-image v-if="element.icon" :src="element.icon" fit="contain" />
                <el-icon v-else><Picture /></el-icon>
              </div>
              <div class="menu-info">
                <span class="menu-title">{{ element.title }}</span>
                <span class="menu-link">{{ element.link_value || '无跳转' }}</span>
              </div>
              <div class="menu-actions">
                <el-button link size="small" @click="emit('toggle-menu-visible', element)">
                  <el-icon><View v-if="element.is_visible" /><Hide v-else /></el-icon>
                </el-button>
                <el-button link size="small" @click="emit('edit-tabbar', element)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button link size="small" type="danger" @click="emit('delete-tabbar', element)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
        </draggable>
        <div v-if="tabBarItems.length === 0" class="empty-tip">
          暂无TabBar项，点击上方添加
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-panel {
  padding: 16px;
}

.panel-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.section-tip {
  font-size: 12px;
  color: #909399;
}

.section-content {
  padding: 4px 0;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 13px;
}

.info-item .label {
  width: 80px;
  color: #909399;
}

.info-item .value {
  color: #303133;
}

.block-list,
.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.block-item,
.menu-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  transition: all 0.2s;
}

.block-item:hover,
.menu-item:hover {
  background: #ecf5ff;
}

.block-item.disabled,
.menu-item.hidden {
  opacity: 0.5;
}

.drag-handle {
  cursor: move;
  color: #909399;
  margin-right: 10px;
}

.block-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.block-name {
  font-size: 13px;
  color: #303133;
}

.menu-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 6px;
  margin-right: 10px;
  overflow: hidden;
}

.menu-icon .el-image {
  width: 24px;
  height: 24px;
}

.menu-icon .el-icon {
  font-size: 18px;
  color: #c0c4cc;
}

.menu-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.menu-title {
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-link {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-actions {
  display: flex;
  gap: 4px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  font-size: 12px;
  padding: 20px 0;
}
</style>

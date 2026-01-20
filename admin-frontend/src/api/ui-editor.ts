import request from '@/utils/request'

// ==================== 页面配置 ====================

// 获取页面列表
export function getPageList() {
  return request.get('/ui-editor/pages')
}

// 获取页面详情
export function getPageDetail(pageCode: string) {
  return request.get(`/ui-editor/pages/${pageCode}`)
}

// 创建页面
export function createPage(data: any) {
  return request.post('/ui-editor/pages', data)
}

// 更新页面
export function updatePage(pageCode: string, data: any) {
  return request.put(`/ui-editor/pages/${pageCode}`, data)
}

// ==================== 区块配置 ====================

// 获取区块列表
export function getBlockList(params?: { page_code?: string }) {
  return request.get('/ui-editor/blocks', { params })
}

// 创建区块
export function createBlock(data: any) {
  return request.post('/ui-editor/blocks', data)
}

// 更新区块
export function updateBlock(id: number, data: any) {
  return request.put(`/ui-editor/blocks/${id}`, data)
}

// 删除区块
export function deleteBlock(id: number) {
  return request.delete(`/ui-editor/blocks/${id}`)
}

// ==================== 菜单项配置 ====================

// 获取菜单项列表
export function getMenuItemList(params?: { menu_type?: string; block_id?: number }) {
  return request.get('/ui-editor/menu-items', { params })
}

// 创建菜单项
export function createMenuItem(data: any) {
  return request.post('/ui-editor/menu-items', data)
}

// 更新菜单项
export function updateMenuItem(id: number, data: any) {
  return request.put(`/ui-editor/menu-items/${id}`, data)
}

// 删除菜单项
export function deleteMenuItem(id: number) {
  return request.delete(`/ui-editor/menu-items/${id}`)
}

// 批量排序菜单项
export function batchSortMenuItems(data: { items: Array<{ id: number; sort_order: number }> }) {
  return request.put('/ui-editor/menu-items/batch-sort', data)
}

// ==================== 发布与版本 ====================

// 发布配置
export function publishConfig(data?: { publish_note?: string }) {
  return request.post('/ui-editor/publish', data)
}

// 获取版本历史
export function getVersionList(params?: { page?: number; limit?: number }) {
  return request.get('/ui-editor/versions', { params })
}

// 回滚到指定版本
export function rollbackVersion(versionId: number) {
  return request.post(`/ui-editor/versions/${versionId}/rollback`)
}

// 初始化默认数据
export function initDefaultData() {
  return request.post('/ui-editor/init-default-data')
}

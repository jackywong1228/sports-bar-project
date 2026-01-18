import request from '@/utils/request'

// 消息模板列表
export function getMessageTemplates(params?: any) {
  return request.get('/messages/templates', { params })
}

// 创建消息模板
export function createMessageTemplate(data: any) {
  return request.post('/messages/templates', data)
}

// 更新消息模板
export function updateMessageTemplate(id: number, data: any) {
  return request.put(`/messages/templates/${id}`, data)
}

// 删除消息模板
export function deleteMessageTemplate(id: number) {
  return request.delete(`/messages/templates/${id}`)
}

// 发送消息
export function sendMessage(data: any) {
  return request.post('/messages/send', data)
}

// 批量发送消息
export function batchSendMessage(data: any) {
  return request.post('/messages/batch-send', data)
}

// 消息记录列表
export function getMessageRecords(params?: any) {
  return request.get('/messages/list', { params })
}

// 公告列表
export function getAnnouncements(params?: any) {
  return request.get('/messages/announcements', { params })
}

// 创建公告
export function createAnnouncement(data: any) {
  return request.post('/messages/announcements', data)
}

// 更新公告
export function updateAnnouncement(id: number, data: any) {
  return request.put(`/messages/announcements/${id}`, data)
}

// 删除公告
export function deleteAnnouncement(id: number) {
  return request.delete(`/messages/announcements/${id}`)
}

// 发布/取消发布公告
export function updateAnnouncementStatus(id: number, data: { is_published: boolean }) {
  return request.put(`/messages/announcements/${id}/publish`, data)
}

// 轮播图列表
export function getBanners(params?: any) {
  return request.get('/messages/banners', { params })
}

// 创建轮播图
export function createBanner(data: any) {
  return request.post('/messages/banners', data)
}

// 更新轮播图
export function updateBanner(id: number, data: any) {
  return request.put(`/messages/banners/${id}`, data)
}

// 删除轮播图
export function deleteBanner(id: number) {
  return request.delete(`/messages/banners/${id}`)
}

// 更新轮播图排序
export function updateBannerSort(data: { ids: number[] }) {
  return request.put('/messages/banners/sort', data)
}

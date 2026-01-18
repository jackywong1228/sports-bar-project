import request from '@/utils/request'

// 活动列表
export function getActivityList(params?: any) {
  return request.get('/activities', { params })
}

// 活动详情
export function getActivityDetail(id: number) {
  return request.get(`/activities/${id}`)
}

// 创建活动
export function createActivity(data: any) {
  return request.post('/activities', data)
}

// 更新活动
export function updateActivity(id: number, data: any) {
  return request.put(`/activities/${id}`, data)
}

// 删除活动
export function deleteActivity(id: number) {
  return request.delete(`/activities/${id}`)
}

// 更新活动状态
export function updateActivityStatus(id: number, data: { status: string }) {
  return request.put(`/activities/${id}/status`, data)
}

// 发布活动
export function publishActivity(id: number) {
  return request.post(`/activities/${id}/publish`)
}

// 取消活动
export function cancelActivity(id: number, data?: { reason: string }) {
  return request.post(`/activities/${id}/cancel`, data)
}

// 活动报名列表
export function getActivityRegistrations(activityId: number, params?: any) {
  return request.get(`/activities/${activityId}/registrations`, { params })
}

// 活动统计
export function getActivityStats(params?: any) {
  return request.get('/activities/stats', { params })
}

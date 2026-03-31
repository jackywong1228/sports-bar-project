import request from '@/utils/request'

export function getActivityList(params?: Record<string, unknown>) {
  return request.get('/activities', { params })
}

export function getActivityDetail(id: number) {
  return request.get(`/activities/${id}`)
}

export function createActivity(data: Record<string, unknown>) {
  return request.post('/activities/create', data)
}

export function updateActivity(id: number, data: Record<string, unknown>) {
  return request.put(`/activities/${id}`, data)
}

export function updateActivityStatus(id: number, data: { status: string }) {
  return request.put(`/activities/${id}/status`, data)
}

export function deleteActivity(id: number) {
  return request.delete(`/activities/${id}`)
}

import request from '@/utils/request'

// 教练列表
export function getCoachList(params?: any) {
  return request.get('/coaches', { params })
}

// 教练详情
export function getCoachDetail(id: number) {
  return request.get(`/coaches/${id}`)
}

// 创建教练
export function createCoach(data: any) {
  return request.post('/coaches', data)
}

// 更新教练
export function updateCoach(id: number, data: any) {
  return request.put(`/coaches/${id}`, data)
}

// 删除教练
export function deleteCoach(id: number) {
  return request.delete(`/coaches/${id}`)
}

// 更新教练状态
export function updateCoachStatus(id: number, data: { status: string }) {
  return request.put(`/coaches/${id}/status`, data)
}

// 教练申请列表
export function getCoachApplications(params?: any) {
  return request.get('/coach-applications', { params })
}

// 审核教练申请
export function reviewCoachApplication(id: number, data: { status: string; remark?: string }) {
  return request.put(`/coach-applications/${id}/review`, data)
}

// 教练排期
export function getCoachSchedules(coachId: number, params?: any) {
  return request.get(`/coaches/${coachId}/schedules`, { params })
}

// 更新教练排期
export function updateCoachSchedules(coachId: number, data: any) {
  return request.put(`/coaches/${coachId}/schedules`, data)
}

// 教练收入统计
export function getCoachIncome(coachId: number, params?: any) {
  return request.get(`/coaches/${coachId}/income`, { params })
}

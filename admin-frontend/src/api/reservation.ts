import request from '@/utils/request'

// 预约列表
export function getReservationList(params: any) {
  return request.get('/reservations', { params })
}

// 预约详情
export function getReservationDetail(id: number) {
  return request.get(`/reservations/${id}`)
}

// 更新预约状态
export function updateReservationStatus(id: number, data: { status: string; remark?: string }) {
  return request.put(`/reservations/${id}/status`, data)
}

// 取消预约
export function cancelReservation(id: number, data: { reason: string }) {
  return request.post(`/reservations/${id}/cancel`, data)
}

// 确认预约
export function confirmReservation(id: number) {
  return request.post(`/reservations/${id}/confirm`)
}

// 完成预约
export function completeReservation(id: number) {
  return request.post(`/reservations/${id}/complete`)
}

// 预约统计
export function getReservationStats(params?: any) {
  return request.get('/reservations/stats', { params })
}

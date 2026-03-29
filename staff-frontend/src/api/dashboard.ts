import request from '@/utils/request'

export function getDashboardStats() {
  return request.get('/dashboard/stats')
}

export function getTodayStats() {
  return request.get('/dashboard/today')
}

import request from '@/utils/request'

// 获取仪表板统计数据
export function getDashboardStats() {
  return request.get('/dashboard/stats')
}

// 获取今日统计
export function getTodayStats() {
  return request.get('/dashboard/today')
}

// 获取趋势数据
export function getTrendData(params?: { days?: number }) {
  return request.get('/dashboard/trend', { params })
}

// 获取排行榜数据
export function getRankingData(type: 'venue' | 'coach' | 'member', params?: { limit?: number }) {
  return request.get(`/dashboard/ranking/${type}`, { params })
}

// 获取最近活动
export function getRecentActivities(params?: { limit?: number }) {
  return request.get('/dashboard/recent-activities', { params })
}

// 获取最近订单
export function getRecentOrders(params?: { limit?: number }) {
  return request.get('/dashboard/recent-orders', { params })
}

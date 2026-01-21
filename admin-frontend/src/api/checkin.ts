import request from '@/utils/request'

// ==================== 打卡记录 ====================

/**
 * 获取打卡记录列表
 */
export function getCheckinRecords(params: {
  page?: number
  page_size?: number
  member_id?: number
  venue_id?: number
  start_date?: string
  end_date?: string
}) {
  return request({
    url: '/checkin/records',
    method: 'get',
    params
  })
}

/**
 * 获取打卡记录详情
 */
export function getCheckinRecordDetail(id: number) {
  return request({
    url: `/checkin/records/${id}`,
    method: 'get'
  })
}

/**
 * 获取打卡统计
 */
export function getCheckinStats(params: {
  start_date?: string
  end_date?: string
  venue_id?: number
}) {
  return request({
    url: '/checkin/stats',
    method: 'get',
    params
  })
}

// ==================== 积分规则 ====================

/**
 * 获取积分规则列表
 */
export function getPointRules(params?: {
  page?: number
  page_size?: number
  is_active?: boolean
}) {
  return request({
    url: '/checkin/point-rules',
    method: 'get',
    params
  })
}

/**
 * 获取积分规则详情
 */
export function getPointRuleDetail(id: number) {
  return request({
    url: `/checkin/point-rules/${id}`,
    method: 'get'
  })
}

/**
 * 创建积分规则
 */
export function createPointRule(data: {
  name: string
  description?: string
  rule_type: 'duration' | 'daily'
  venue_type_id?: number
  duration_unit?: number
  points_per_unit?: number
  max_daily_points?: number
  daily_fixed_points?: number
  is_active?: boolean
}) {
  return request({
    url: '/checkin/point-rules',
    method: 'post',
    data
  })
}

/**
 * 更新积分规则
 */
export function updatePointRule(id: number, data: {
  name?: string
  description?: string
  rule_type?: 'duration' | 'daily'
  venue_type_id?: number
  duration_unit?: number
  points_per_unit?: number
  max_daily_points?: number
  daily_fixed_points?: number
  is_active?: boolean
}) {
  return request({
    url: `/checkin/point-rules/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除积分规则
 */
export function deletePointRule(id: number) {
  return request({
    url: `/checkin/point-rules/${id}`,
    method: 'delete'
  })
}

// ==================== 排行榜 ====================

/**
 * 获取排行榜数据
 */
export function getLeaderboard(params: {
  period: 'daily' | 'weekly' | 'monthly'
  venue_type_id?: number
  limit?: number
}) {
  return request({
    url: '/checkin/leaderboard',
    method: 'get',
    params
  })
}

/**
 * 刷新排行榜
 */
export function refreshLeaderboard(params: {
  period: 'daily' | 'weekly' | 'monthly'
}) {
  return request({
    url: '/checkin/leaderboard/refresh',
    method: 'post',
    data: params
  })
}

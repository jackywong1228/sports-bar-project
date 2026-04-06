import request from '@/utils/request'

// 员工扫会员动态二维码 → 返回会员资料 + 今日待核销预约
export function staffScanMember(data: { token: string; current_venue_id?: number }) {
  return request.post('/staff/scan-member', data)
}

// 核销预约 + 同步写打卡（一个事务）
export function staffVerifyWithCheckin(data: { reservation_id: number }) {
  return request.post('/staff/verify-with-checkin', data)
}

// 散客到店登记（duration=0），可选扣邀请人配额
export function staffWalkInCheckin(data: {
  member_id: number
  current_venue_id: number
  inviter_token?: string
}) {
  return request.post('/staff/walk-in-checkin', data)
}

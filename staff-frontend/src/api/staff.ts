import request from '@/utils/request'

// 员工扫会员动态码（MEMBER:xxx）→ 会员资料 + 今日待核销预约
export function staffScanMember(data: { token: string; current_venue_id?: number }) {
  return request.post('/staff/scan-member', data)
}

// 员工按手机号查找会员 → 返回结构同 scan-member
export function staffLookupMember(phone: string) {
  return request.post('/staff/lookup-member', { phone })
}

// 核销预约 + 同步打卡
export function staffVerifyWithCheckin(reservationId: number) {
  return request.post('/staff/verify-with-checkin', { reservation_id: reservationId })
}

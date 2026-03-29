import request from '@/utils/request'

export function getMemberList(params?: Record<string, unknown>) {
  return request.get('/members', { params })
}

export function getMemberDetail(id: number) {
  return request.get(`/members/${id}`)
}

export function rechargeCoin(data: { member_id: number; amount: number; remark?: string }) {
  return request.post('/members/recharge/coin', data)
}

export function rechargePoint(data: { member_id: number; amount: number; remark?: string }) {
  return request.post('/members/recharge/point', data)
}

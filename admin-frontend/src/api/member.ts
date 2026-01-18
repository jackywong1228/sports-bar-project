import request from '@/utils/request'

// 会员列表
export function getMemberList(params: any) {
  return request.get('/members', { params })
}

// 会员详情
export function getMemberDetail(id: number) {
  return request.get(`/members/${id}`)
}

// 更新会员
export function updateMember(id: number, data: any) {
  return request.put(`/members/${id}`, data)
}

// 会员金币充值
export function rechargeCoin(data: { member_id: number; amount: number; remark?: string }) {
  return request.post('/members/recharge/coin', data)
}

// 会员积分充值
export function rechargePoint(data: { member_id: number; amount: number; remark?: string }) {
  return request.post('/members/recharge/point', data)
}

// 会员等级列表
export function getMemberLevels() {
  return request.get('/members/levels')
}

// 创建会员等级
export function createMemberLevel(data: any) {
  return request.post('/members/levels', data)
}

// 更新会员等级
export function updateMemberLevel(id: number, data: any) {
  return request.put(`/members/levels/${id}`, data)
}

// 删除会员等级
export function deleteMemberLevel(id: number) {
  return request.delete(`/members/levels/${id}`)
}

// 会员标签列表
export function getMemberTags() {
  return request.get('/members/tags')
}

// 创建会员标签
export function createMemberTag(data: any) {
  return request.post('/members/tags', data)
}

// 更新会员标签
export function updateMemberTag(id: number, data: any) {
  return request.put(`/members/tags/${id}`, data)
}

// 删除会员标签
export function deleteMemberTag(id: number) {
  return request.delete(`/members/tags/${id}`)
}

// 会员金币记录
export function getMemberCoinRecords(memberId: number, params?: any) {
  return request.get(`/members/${memberId}/coin-records`, { params })
}

// 会员积分记录
export function getMemberPointRecords(memberId: number, params?: any) {
  return request.get(`/members/${memberId}/point-records`, { params })
}

// 会员卡套餐列表
export function getMemberCards(params?: any) {
  return request.get('/member-cards/cards', { params })
}

// 会员卡套餐详情
export function getMemberCardDetail(id: number) {
  return request.get(`/member-cards/cards/${id}`)
}

// 创建会员卡套餐
export function createMemberCard(data: any) {
  return request.post('/member-cards/cards', data)
}

// 更新会员卡套餐
export function updateMemberCard(id: number, data: any) {
  return request.put(`/member-cards/cards/${id}`, data)
}

// 删除会员卡套餐
export function deleteMemberCard(id: number) {
  return request.delete(`/member-cards/cards/${id}`)
}

// 会员卡订单列表
export function getMemberCardOrders(params: any) {
  return request.get('/member-cards/orders', { params })
}

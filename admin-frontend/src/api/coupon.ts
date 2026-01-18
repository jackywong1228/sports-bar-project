import request from '@/utils/request'

// 优惠券模板列表
export function getCouponTemplates(params?: any) {
  return request.get('/coupons/templates', { params })
}

// 优惠券模板详情
export function getCouponTemplateDetail(id: number) {
  return request.get(`/coupons/templates/${id}`)
}

// 创建优惠券模板
export function createCouponTemplate(data: any) {
  return request.post('/coupons/templates', data)
}

// 更新优惠券模板
export function updateCouponTemplate(id: number, data: any) {
  return request.put(`/coupons/templates/${id}`, data)
}

// 删除优惠券模板
export function deleteCouponTemplate(id: number) {
  return request.delete(`/coupons/templates/${id}`)
}

// 更新模板状态
export function updateCouponTemplateStatus(id: number, data: { is_active: boolean }) {
  return request.put(`/coupons/templates/${id}/status`, data)
}

// 发放优惠券
export function issueCoupon(templateId: number, data: { member_ids: number[] }) {
  return request.post(`/coupons/templates/${templateId}/issue`, data)
}

// 批量发放优惠券
export function batchIssueCoupon(templateId: number, data: { member_level_id?: number; all_members?: boolean }) {
  return request.post(`/coupons/templates/${templateId}/issue`, data)
}

// 会员优惠券列表（发放记录）
export function getMemberCoupons(params?: any) {
  return request.get('/coupons/member-coupons', { params })
}

// 优惠券统计
export function getCouponStats(params?: any) {
  return request.get('/coupons/stats', { params })
}

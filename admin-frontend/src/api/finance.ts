import request from '@/utils/request'

// 财务概览
export function getFinanceOverview(params?: any) {
  return request.get('/finance/overview', { params })
}

// 收入趋势
export function getIncomeTrend(params?: any) {
  return request.get('/finance/trend', { params })
}

// 充值记录列表
export function getRechargeRecords(params?: any) {
  return request.get('/finance/recharge', { params })
}

// 充值统计
export function getRechargeStats(params?: any) {
  return request.get('/finance/recharge/stats', { params })
}

// 消费记录列表
export function getConsumeRecords(params?: any) {
  return request.get('/finance/consume', { params })
}

// 消费统计
export function getConsumeStats(params?: any) {
  return request.get('/finance/consume/stats', { params })
}

// 教练结算列表
export function getCoachSettlements(params?: any) {
  return request.get('/finance/settlement', { params })
}

// 创建教练结算单
export function createCoachSettlement(data: any) {
  return request.post('/finance/settlement/create', data)
}

// 确认结算
export function confirmSettlement(id: number) {
  return request.put(`/finance/settlement/${id}/confirm`)
}

// 完成结算（支付）
export function completeSettlement(id: number, data?: { remark: string }) {
  return request.put(`/finance/settlement/${id}/pay`, data)
}

// 金币记录
export function getCoinRecords(params?: any) {
  return request.get('/finance/coin-records', { params })
}

// 财务统计
export function getFinanceStats(params?: any) {
  return request.get('/finance/stats', { params })
}

// 导出财务报表
export function exportFinanceReport(params?: any) {
  return request.get('/finance/export', { params, responseType: 'blob' })
}

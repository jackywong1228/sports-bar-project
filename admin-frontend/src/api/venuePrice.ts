import request from '@/utils/request'

export function getVenuePriceRules(venueId: number) {
  return request({ url: `/venues/${venueId}/price-rules`, method: 'get' })
}
export function batchSetPriceRules(venueId: number, data: { rules: any[] }) {
  return request({ url: `/venues/${venueId}/price-rules`, method: 'post', data })
}
export function updatePriceRule(ruleId: number, price: number) {
  return request({ url: `/venues/price-rules/${ruleId}`, method: 'put', params: { price } })
}
export function deletePriceRule(ruleId: number) {
  return request({ url: `/venues/price-rules/${ruleId}`, method: 'delete' })
}
export function previewPriceTable(venueId: number, date: string) {
  return request({ url: `/venues/${venueId}/price-table`, method: 'get', params: { date } })
}
export function copyPriceRules(venueId: number, data: { source_day: number; target_days: number[] }) {
  return request({ url: `/venues/${venueId}/price-rules/copy`, method: 'post', data })
}

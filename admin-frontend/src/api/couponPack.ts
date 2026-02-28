import request from '@/utils/request'

export function getCouponPacks() {
  return request({ url: '/coupon-packs/packs', method: 'get' })
}
export function createCouponPack(data: any) {
  return request({ url: '/coupon-packs/packs', method: 'post', data })
}
export function updateCouponPack(id: number, data: any) {
  return request({ url: `/coupon-packs/packs/${id}`, method: 'put', data })
}
export function deleteCouponPack(id: number) {
  return request({ url: `/coupon-packs/packs/${id}`, method: 'delete' })
}
export function getPackItems(packId: number) {
  return request({ url: `/coupon-packs/packs/${packId}/items`, method: 'get' })
}
export function addPackItem(packId: number, data: any) {
  return request({ url: `/coupon-packs/packs/${packId}/items`, method: 'post', data })
}
export function removePackItem(packId: number, itemId: number) {
  return request({ url: `/coupon-packs/packs/${packId}/items/${itemId}`, method: 'delete' })
}

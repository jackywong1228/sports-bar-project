import request from '@/utils/request'

export function getRechargePackages() {
  return request({ url: '/finance/recharge-packages', method: 'get' })
}
export function createRechargePackage(data: any) {
  return request({ url: '/finance/recharge-packages', method: 'post', data })
}
export function updateRechargePackage(id: number, data: any) {
  return request({ url: `/finance/recharge-packages/${id}`, method: 'put', data })
}
export function deleteRechargePackage(id: number) {
  return request({ url: `/finance/recharge-packages/${id}`, method: 'delete' })
}

import request from '@/utils/request'

export function getFoodOrders(params?: Record<string, unknown>) {
  return request.get('/foods/orders', { params })
}

export function getFoodOrderDetail(id: number) {
  return request.get(`/foods/orders/${id}`)
}

export function updateFoodOrderStatus(id: number, data: { status: string }) {
  return request.put(`/foods/orders/${id}/status`, data)
}

import request from '@/utils/request'

// 餐饮分类列表
export function getFoodCategories(params?: any) {
  return request.get('/foods/categories', { params })
}

// 创建餐饮分类
export function createFoodCategory(data: any) {
  return request.post('/foods/categories', data)
}

// 更新餐饮分类
export function updateFoodCategory(id: number, data: any) {
  return request.put(`/foods/categories/${id}`, data)
}

// 删除餐饮分类
export function deleteFoodCategory(id: number) {
  return request.delete(`/foods/categories/${id}`)
}

// 餐饮商品列表
export function getFoodList(params?: any) {
  return request.get('/foods/items', { params })
}

// 餐饮商品详情
export function getFoodDetail(id: number) {
  return request.get(`/foods/items/${id}`)
}

// 创建餐饮商品
export function createFood(data: any) {
  return request.post('/foods/items', data)
}

// 更新餐饮商品
export function updateFood(id: number, data: any) {
  return request.put(`/foods/items/${id}`, data)
}

// 删除餐饮商品
export function deleteFood(id: number) {
  return request.delete(`/foods/items/${id}`)
}

// 更新商品状态（上架/下架）
export function updateFoodStatus(id: number, data: { is_active: boolean }) {
  return request.put(`/foods/items/${id}/status`, data)
}

// 餐饮订单列表
export function getFoodOrders(params?: any) {
  return request.get('/foods/orders', { params })
}

// 餐饮订单详情
export function getFoodOrderDetail(id: number) {
  return request.get(`/foods/orders/${id}`)
}

// 更新订单状态
export function updateFoodOrderStatus(id: number, data: { status: string }) {
  return request.put(`/foods/orders/${id}/status`, data)
}

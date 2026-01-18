import request from '@/utils/request'

// 商品分类列表
export function getProductCategories(params?: any) {
  return request.get('/mall/categories', { params })
}

// 创建商品分类
export function createProductCategory(data: any) {
  return request.post('/mall/categories', data)
}

// 更新商品分类
export function updateProductCategory(id: number, data: any) {
  return request.put(`/mall/categories/${id}`, data)
}

// 删除商品分类
export function deleteProductCategory(id: number) {
  return request.delete(`/mall/categories/${id}`)
}

// 积分商品列表
export function getProductList(params?: any) {
  return request.get('/mall/products', { params })
}

// 商品详情
export function getProductDetail(id: number) {
  return request.get(`/mall/products/${id}`)
}

// 创建商品
export function createProduct(data: any) {
  return request.post('/mall/products', data)
}

// 更新商品
export function updateProduct(id: number, data: any) {
  return request.put(`/mall/products/${id}`, data)
}

// 删除商品
export function deleteProduct(id: number) {
  return request.delete(`/mall/products/${id}`)
}

// 更新商品状态
export function updateProductStatus(id: number, data: { is_active: boolean }) {
  return request.put(`/mall/products/${id}/status`, data)
}

// 兑换订单列表
export function getProductOrders(params?: any) {
  return request.get('/mall/orders', { params })
}

// 订单详情
export function getProductOrderDetail(id: number) {
  return request.get(`/mall/orders/${id}`)
}

// 更新订单状态
export function updateProductOrderStatus(id: number, data: { status: string }) {
  return request.put(`/mall/orders/${id}/status`, data)
}

// 发货
export function shipProductOrder(id: number, data: { express_company: string; express_no: string }) {
  return request.put(`/mall/orders/${id}/ship`, data)
}

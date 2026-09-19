import request from '@/utils/request'

// ──────────────────────────────────────────────
// 类型定义（与后端 /api/v1/food-admin 契约一致）
// ──────────────────────────────────────────────

export interface FoodCategory {
  id: number
  name: string
  icon: string | null
  sort_order: number
  is_active: boolean
  item_count: number
}

export interface FoodSpecOption {
  id?: number
  name: string
  price_delta: number
  is_active: boolean
  sort_order: number
}

export interface FoodSpecGroup {
  id?: number
  name: string
  select_type: 'single' | 'multi'
  required: boolean
  sort_order: number
  options: FoodSpecOption[]
}

export interface FoodItem {
  id: number
  category_id: number
  category_name: string | null
  name: string
  image: string | null
  description: string | null
  price: number
  original_price: number | null
  stock: number
  sales: number
  sold_out: boolean
  is_active: boolean
  is_recommend: boolean
  coupon_enabled: boolean
  has_specs: boolean
  tags: string | null
  sort_order: number
  created_at: string | null
  spec_groups?: FoodSpecGroup[]
}

export interface FoodOrderItem {
  id: number
  food_id: number
  food_name: string
  food_image: string | null
  specs_text: string | null
  price: number
  quantity: number
  subtotal: number
}

export interface FoodOrder {
  id: number
  order_no: string
  member_id: number | null
  member_name: string | null
  member_phone: string | null
  total_amount: number
  pay_amount: number
  coupon_id: number | null
  coupon_amount: number
  discount_amount: number
  status: string
  status_text: string
  order_type: string
  order_type_text: string
  table_no: string | null
  pickup_time: string | null
  pay_type: string | null
  pay_type_text: string | null
  staff_id: number | null
  handled_by: string | null
  remark: string | null
  pay_time: string | null
  complete_time: string | null
  refund_amount: number
  refund_reason: string | null
  refund_time: string | null
  refund_by: string | null
  created_at: string | null
  items?: FoodOrderItem[]
}

export interface FoodStatsPayGroup {
  pay_type: string
  pay_type_text: string
  count: number
  amount: number
}

export interface FoodStatsTopItem {
  food_id: number
  food_name: string
  quantity: number
  amount: number
}

export interface FoodStats {
  start_time: string
  end_time: string
  total_orders: number
  valid_orders: number
  cancelled_orders: number
  total_amount: number
  coupon_amount: number
  by_pay_type: FoodStatsPayGroup[]
  refund_count: number
  refund_amount: number
  top_items: FoodStatsTopItem[]
  stat_date?: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// ──────────────────────────────────────────────
// 分类管理
// ──────────────────────────────────────────────

export function getFoodCategories() {
  return request.get('/food-admin/categories')
}

export function createFoodCategory(data: Partial<FoodCategory>) {
  return request.post('/food-admin/categories', data)
}

export function updateFoodCategory(id: number, data: Partial<FoodCategory>) {
  return request.put(`/food-admin/categories/${id}`, data)
}

export function deleteFoodCategory(id: number) {
  return request.delete(`/food-admin/categories/${id}`)
}

// ──────────────────────────────────────────────
// 菜品管理
// ──────────────────────────────────────────────

export function getFoodItems(params?: any) {
  return request.get('/food-admin/items', { params })
}

export function getFoodItemDetail(id: number) {
  return request.get(`/food-admin/items/${id}`)
}

export function createFoodItem(data: any) {
  return request.post('/food-admin/items', data)
}

export function updateFoodItem(id: number, data: any) {
  return request.put(`/food-admin/items/${id}`, data)
}

export function deleteFoodItem(id: number) {
  return request.delete(`/food-admin/items/${id}`)
}

export function adjustFoodItemStock(id: number, stock: number) {
  return request.put(`/food-admin/items/${id}/stock`, { stock })
}

export function updateFoodItemStatus(id: number, is_active: boolean) {
  return request.put(`/food-admin/items/${id}/status`, { is_active })
}

export function batchUpdateFoodItemStatus(ids: number[], is_active: boolean) {
  return request.post('/food-admin/items/batch-status', { ids, is_active })
}

// ──────────────────────────────────────────────
// 订单管理
// ──────────────────────────────────────────────

export function getFoodOrders(params?: any) {
  return request.get('/food-admin/orders', { params })
}

export function getFoodOrderDetail(id: number) {
  return request.get(`/food-admin/orders/${id}`)
}

export function refundFoodOrder(id: number, reason: string) {
  return request.post(`/food-admin/orders/${id}/refund`, { reason })
}

// ──────────────────────────────────────────────
// 营业统计
// ──────────────────────────────────────────────

export function getFoodDailyStats(statDate?: string) {
  return request.get('/food-admin/stats/daily', { params: statDate ? { stat_date: statDate } : {} })
}

export function getFoodRangeStats(startTime: string, endTime: string) {
  return request.get('/food-admin/stats/range', {
    params: { start_time: startTime, end_time: endTime }
  })
}

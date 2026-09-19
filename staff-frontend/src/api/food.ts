import request from '@/utils/request'

// ─────────────────────────────────────────────────────────────
// 类型定义（契约：backend/app/services/food_service.py serialize_order）
// ─────────────────────────────────────────────────────────────

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
  coupon_amount: number
  discount_amount: number
  status: string
  status_text: string
  order_type: string
  order_type_text: string
  table_no: string | null
  pickup_time: string | null
  pay_type: string
  pay_type_text: string
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

export interface OrderPageResult {
  items: FoodOrder[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface SinceIdResult {
  items: FoodOrder[]
  max_id: number
}

// 收银台菜单（契约：backend/app/api/v1/food_member.py GET /member/food/menu，无需会员鉴权）
export interface MenuSpecOption {
  id: number
  name: string
  price_delta: number
}

export interface MenuSpecGroup {
  id: number
  name: string
  select_type: 'single' | 'multi'
  required: boolean
  options: MenuSpecOption[]
}

export interface MenuItem {
  id: number
  name: string
  image: string | null
  description: string | null
  price: number
  original_price: number | null
  sold_out: boolean
  coupon_enabled: boolean
  has_specs: boolean
  tags: string[]
  spec_groups: MenuSpecGroup[]
}

export interface MenuCategory {
  id: number
  name: string
  icon: string | null
  items: MenuItem[]
}

export interface ShiftReport {
  start_time: string
  end_time: string
  total_amount: number
  total_orders: number
  by_pay_type: { pay_type: string; pay_type_text: string; count: number; amount: number }[]
  refund_count: number
  refund_amount: number
  orders: FoodOrder[]
}

export interface WalkInItem {
  item_id: number
  specs?: Record<string, number[]>
  quantity: number
}

export interface WalkInOrderPayload {
  items: WalkInItem[]
  pay_type: 'cash'
  order_type: 'dine_in' | 'pickup'
  table_no?: string
  pickup_time?: string
  customer_name?: string
  customer_phone?: string
  remark?: string
}

// ─────────────────────────────────────────────────────────────
// 员工端餐饮 API（前缀 /staff/food）
// ─────────────────────────────────────────────────────────────

/** 订单流（分页）；传 since_id 时为增量轮询模式 */
export function getStaffFoodOrders(params: {
  status?: string
  since_id?: number
  page?: number
  page_size?: number
}) {
  return request.get<any, { data: OrderPageResult | SinceIdResult }>('/staff/food/orders', { params })
}

export function getStaffFoodOrderDetail(id: number) {
  return request.get<any, { data: FoodOrder }>(`/staff/food/orders/${id}`)
}

/** 接单 paid → preparing */
export function acceptFoodOrder(id: number) {
  return request.post(`/staff/food/orders/${id}/accept`)
}

/** 出餐 preparing → ready */
export function readyFoodOrder(id: number) {
  return request.post(`/staff/food/orders/${id}/ready`)
}

/** 交付 ready → completed */
export function completeFoodOrder(id: number) {
  return request.post(`/staff/food/orders/${id}/complete`)
}

/** 人工退款 */
export function refundFoodOrder(id: number, reason: string) {
  return request.post(`/staff/food/orders/${id}/refund`, { reason })
}

/** 代客下单（收银台现金收款） */
export function createWalkInOrder(data: WalkInOrderPayload) {
  return request.post<any, { data: { order_id: number; order_no: string; pay_amount: number; status: string } }>(
    '/staff/food/walk-in-orders',
    data
  )
}

/** 交班对账 */
export function getShiftReport(params: { start_time: string; end_time: string }) {
  return request.get<any, { data: ShiftReport }>('/staff/food/shift-report', { params })
}

/**
 * 收银台菜单（分类+商品+规格一次返回）
 * 注意：员工端 /staff/food 暂无菜单接口，复用会员端 /member/food/menu（该接口无鉴权要求）
 */
export function getFoodMenu() {
  return request.get<any, { data: MenuCategory[] }>('/member/food/menu')
}

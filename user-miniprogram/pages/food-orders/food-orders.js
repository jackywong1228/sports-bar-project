const app = getApp()
const api = require('../../utils/api')

const TABS = [
  { key: '', label: '全部' },
  { key: 'unpaid', label: '待支付' },
  { key: 'preparing', label: '制作中' },
  { key: 'ready', label: '待取餐' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已退款' },
]

const STATUS_STYLE = {
  unpaid:    { text: '待支付', color: '#E6A23C' },
  pending:   { text: '待确认', color: '#E6A23C' },
  paid:      { text: '已支付', color: '#1A5D3A' },
  preparing: { text: '制作中', color: '#1A5D3A' },
  ready:     { text: '待取餐', color: '#2E7D52' },
  completed: { text: '已完成', color: '#909399' },
  cancelled: { text: '已取消/退款', color: '#F56C6C' },
}

Page({
  data: {
    tabs: TABS,
    activeTab: '',
    orders: [],
    page: 1,
    pageSize: 10,
    total: 0,
    loading: false,
    loaded: false,
  },

  onLoad() {
    if (!app.checkLogin()) return
    this.loadOrders(true)
  },

  onShow() {
    // 从详情/支付返回时刷新（待支付可能已流转）
    if (this.data.loaded) this.loadOrders(true)
  },

  onPullDownRefresh() {
    this.loadOrders(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    const { page, pageSize, total, loading } = this.data
    if (loading || page * pageSize >= total) return
    this.loadOrders(false)
  },

  onTabChange(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.activeTab) return
    this.setData({ activeTab: key })
    this.loadOrders(true)
  },

  async loadOrders(reset) {
    if (this.data.loading) return
    const page = reset ? 1 : this.data.page + 1
    this.setData({ loading: true })
    try {
      const params = { page, page_size: this.data.pageSize }
      if (this.data.activeTab) params.status = this.data.activeTab
      const res = await api.getFoodOrders(params)
      const body = res.data || {}
      const items = (body.items || []).map(o => this.decorate(o))
      this.setData({
        orders: reset ? items : this.data.orders.concat(items),
        page,
        total: body.total || 0,
        loaded: true,
      })
    } catch (err) {
      console.error('加载餐饮订单失败:', err)
      this.setData({ loaded: true })
    } finally {
      this.setData({ loading: false })
    }
  },

  decorate(o) {
    const style = STATUS_STYLE[o.status] || {}
    const items = o.items || []
    const names = items.slice(0, 2).map(i => i.food_name + (i.specs_text ? `（${i.specs_text}）` : ''))
    const totalQty = items.reduce((sum, i) => sum + (i.quantity || 0), 0)
    return {
      ...o,
      status_text_display: style.text || o.status_text,
      status_color: style.color || '#666',
      // 类型行：堂食 → 桌号；预约取餐 → 取餐时间
      type_line: o.order_type === 'dine_in'
        ? `堂食 · 桌号 ${o.table_no || '-'}`
        : `预约取餐 · ${o.pickup_time || '-'}`,
      summary: names.join('、') + (items.length > 2 ? ` 等${items.length}种` : ''),
      total_qty: totalQty,
      pay_amount_text: (Math.round((o.pay_amount || 0) * 100) / 100).toFixed(2),
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/food-order-detail/food-order-detail?id=${id}` })
  },

  goMenu() {
    wx.navigateTo({ url: '/pages/food-menu/food-menu' })
  },
})

const app = getApp()
const api = require('../../utils/api')

const STATUS_STYLE = {
  unpaid:    { text: '待支付', color: '#E6A23C' },
  pending:   { text: '待确认', color: '#E6A23C' },
  paid:      { text: '已支付', color: '#1A5D3A' },
  preparing: { text: '制作中', color: '#1A5D3A' },
  ready:     { text: '待取餐', color: '#2E7D52' },
  completed: { text: '已完成', color: '#909399' },
  cancelled: { text: '已取消/退款', color: '#F56C6C' },
}

// 简化状态时间线
const FLOW_STEPS = [
  { key: 'created', label: '提交订单' },
  { key: 'paid', label: '支付成功' },
  { key: 'preparing', label: '开始制作' },
  { key: 'ready', label: '制作完成/待取餐' },
  { key: 'completed', label: '订单完成' },
]

Page({
  data: {
    orderId: null,
    order: null,
    timeline: [],
    loading: true,
    paying: false,
  },

  onLoad(options) {
    if (!app.checkLogin()) {
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    if (!options || !options.id) {
      wx.showToast({ title: '订单参数错误', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }
    this.setData({ orderId: Number(options.id) })
    this.loadDetail()
  },

  onShow() {
    // 支付后返回刷新状态
    if (this.data.orderId && !this.data.loading) this.loadDetail()
  },

  async loadDetail() {
    this.setData({ loading: true })
    try {
      const res = await api.getFoodOrderDetail(this.data.orderId)
      const o = res.data || {}
      const style = STATUS_STYLE[o.status] || {}
      const order = {
        ...o,
        status_text_display: style.text || o.status_text,
        status_color: style.color || '#666',
        total_amount_text: (Math.round((o.total_amount || 0) * 100) / 100).toFixed(2),
        pay_amount_text: (Math.round((o.pay_amount || 0) * 100) / 100).toFixed(2),
        discount_text: (Math.round((o.discount_amount || 0) * 100) / 100).toFixed(2),
        refund_amount_text: (Math.round((o.refund_amount || 0) * 100) / 100).toFixed(2),
        type_line: o.order_type === 'dine_in'
          ? `堂食 · 桌号 ${o.table_no || '-'}`
          : `预约取餐 · ${o.pickup_time || '-'}`,
        items: (o.items || []).map(i => ({
          ...i,
          food_image: app.resolveImageUrl(i.food_image),
          price_text: (Math.round((i.price || 0) * 100) / 100).toFixed(2),
          subtotal_text: (Math.round((i.subtotal || 0) * 100) / 100).toFixed(2),
        })),
        can_pay: o.status === 'unpaid' && o.pay_type === 'wechat',
      }
      this.setData({ order, timeline: this.buildTimeline(o) })
    } catch (err) {
      console.error('加载订单详情失败:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  // 时间线：取消/退款单独一条；正常流程按状态点亮
  buildTimeline(o) {
    if (o.status === 'cancelled') {
      const steps = [
        { label: '提交订单', time: o.created_at, active: true },
        { label: o.refund_amount > 0 ? '已退款' : '订单已取消', time: o.refund_time || o.created_at, active: true },
      ]
      return steps
    }
    const statusOrder = ['unpaid', 'paid', 'preparing', 'ready', 'completed']
    const reached = statusOrder.indexOf(o.status)
    const timeMap = {
      created: o.created_at,
      paid: o.pay_time,
      completed: o.complete_time,
    }
    return FLOW_STEPS.map((step, idx) => ({
      label: step.label,
      time: timeMap[step.key] || '',
      // unpaid 时点亮「提交订单」；paid 点亮前两步，以此类推
      active: idx <= reached,
    }))
  },

  copyOrderNo() {
    if (!this.data.order) return
    wx.setClipboardData({ data: this.data.order.order_no })
  },

  // 待支付 → 重新拉起微信支付（repay 接口，镜像 course-bookings 模式）
  async handleRepay() {
    const { orderId, paying } = this.data
    if (paying) return
    this.setData({ paying: true })
    try {
      const res = await api.repayFoodOrder(orderId)
      const data = res.data || {}
      if (!data.pay_params) {
        wx.showToast({ title: '无法拉起支付', icon: 'none' })
        this.setData({ paying: false })
        return
      }
      wx.requestPayment({
        ...data.pay_params,
        success: () => {
          wx.showLoading({ title: '支付确认中...' })
          this.pollPayStatus(orderId, 0)
        },
        fail: (err) => {
          this.setData({ paying: false })
          if (err.errMsg && err.errMsg.includes('cancel')) {
            wx.showToast({ title: '已取消支付', icon: 'none' })
          } else {
            wx.showToast({ title: '支付失败', icon: 'none' })
          }
        },
      })
    } catch (err) {
      console.error('重新支付失败:', err)
      this.setData({ paying: false })
      // 订单可能已超时关闭，刷新详情
      this.loadDetail()
    }
  },

  async pollPayStatus(orderId, attempt) {
    if (attempt >= 10) {
      wx.hideLoading()
      this.setData({ paying: false })
      wx.showToast({ title: '支付处理中，请稍后查看', icon: 'none' })
      this.loadDetail()
      return
    }
    try {
      const res = await api.getFoodOrderPayStatus(orderId)
      if (res.data && res.data.status !== 'unpaid') {
        wx.hideLoading()
        this.setData({ paying: false })
        wx.showToast({ title: '支付成功', icon: 'success' })
        this.loadDetail()
        return
      }
    } catch (err) {
      console.error('查询支付状态失败:', err)
    }
    setTimeout(() => this.pollPayStatus(orderId, attempt + 1), 1000)
  },
})

const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    tabs: [
      { id: 'all', name: '全部' },
      { id: 'unpaid', name: '待支付' },
      { id: 'confirmed', name: '已确认' },
      { id: 'completed', name: '已完成' }
    ],
    currentTab: 'all',
    orderType: 'all', // all, reservation, activity
    orders: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad(options) {
    if (options.type) {
      this.setData({ orderType: options.type })
    }
    this.loadOrders()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadOrders().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 切换标签
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({
      currentTab: tab,
      page: 1,
      hasMore: true,
      orders: []
    })
    this.loadOrders()
  },

  // 加载订单
  async loadOrders() {
    this.setData({ loading: true })

    try {
      const { currentTab, orderType, page } = this.data
      let url = `/member/orders?page=${page}&limit=10`

      if (currentTab !== 'all') {
        url += `&status=${currentTab}`
      }
      if (orderType !== 'all') {
        url += `&type=${orderType}`
      }

      const res = await app.request({ url })
      const orders = (res.data || []).map(item => ({
        ...item,
        image: app.resolveImageUrl(item.image),
        statusInfo: util.getOrderStatus(item.status)
      }))

      this.setData({
        orders: page === 1 ? orders : [...this.data.orders, ...orders],
        hasMore: orders.length >= 10,
        loading: false
      })
    } catch (err) {
      console.error('加载订单失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadOrders()
  },

  // 订单详情
  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/order-detail/order-detail?id=${id}`
    })
  },

  // 支付订单
  async payOrder(e) {
    const id = e.currentTarget.dataset.id
    wx.showLoading({ title: '支付中...' })

    try {
      await app.request({
        url: `/member/orders/${id}/pay`,
        method: 'POST'
      })

      wx.hideLoading()
      wx.showToast({ title: '支付成功', icon: 'success' })
      this.loadOrders()
    } catch (err) {
      wx.hideLoading()
      console.error('支付失败:', err)
    }
  },

  // 取消预约（原因选择 + 二次确认 + 新接口）
  cancelOrder(e) {
    const id = e.currentTarget.dataset.id
    const order = this.data.orders.find(o => o.id === id) || {}
    const reasons = ['临时有事', '时间冲突', '场地不合适', '误操作', '其他原因']
    wx.showActionSheet({
      itemList: reasons,
      success: (sheetRes) => {
        const reason = reasons[sheetRes.tapIndex]
        const tipLine = this._refundTip(order)
        wx.showModal({
          title: '确认取消预约',
          content: `原因：${reason}${tipLine ? '\n' + tipLine : ''}`,
          confirmText: '确认取消',
          cancelText: '再想想',
          success: async (modalRes) => {
            if (!modalRes.confirm) return
            wx.showLoading({ title: '取消中...', mask: true })
            try {
              const res = await app.request({
                url: `/member/reservations/${id}/cancel`,
                method: 'POST',
                data: { reason }
              })
              wx.hideLoading()
              const tip = (res && res.data && res.data.refund && res.data.refund.desc) || '已取消'
              wx.showToast({ title: tip, icon: 'success', duration: 2500 })
              this.setData({ page: 1, hasMore: true })
              this.loadOrders()
            } catch (err) {
              wx.hideLoading()
              const msg = (err && err.data && err.data.detail) || '取消失败'
              wx.showToast({ title: msg, icon: 'none', duration: 2500 })
            }
          }
        })
      }
    })
  },

  // 根据订单生成退款提示文案
  _refundTip(order) {
    if (!order) return ''
    if (order.status === 'unpaid') return '订单未支付，取消不涉及退款'
    if (!order.total_price || Number(order.total_price) <= 0) return '免费预约，取消后释放免费时长'
    if (order.pay_type === 'coin') return `将退还 ${order.total_price} 金币到余额`
    if (order.pay_type === 'wechat') return `将发起微信退款 ¥${order.total_price}`
    return ''
  }
})

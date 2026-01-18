const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    tabs: [
      { id: 'all', name: '全部' },
      { id: 'pending', name: '待支付' },
      { id: 'paid', name: '已支付' },
      { id: 'completed', name: '已完成' }
    ],
    currentTab: 'all',
    orderType: 'all', // all, reservation, food, activity
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

  // 取消订单
  cancelOrder(e) {
    const id = e.currentTarget.dataset.id

    wx.showModal({
      title: '取消订单',
      content: '确定要取消该订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await app.request({
              url: `/member/orders/${id}/cancel`,
              method: 'POST'
            })

            wx.showToast({ title: '已取消', icon: 'success' })
            this.loadOrders()
          } catch (err) {
            console.error('取消失败:', err)
          }
        }
      }
    })
  }
})

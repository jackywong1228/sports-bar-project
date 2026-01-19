const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    orderList: [],
    currentFilter: 'all',
    loading: false
  },

  onLoad() {
    this.loadOrderList()
  },

  onPullDownRefresh() {
    this.loadOrderList().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 设置筛选
  setFilter(e) {
    const filter = e.currentTarget.dataset.filter
    this.setData({ currentFilter: filter })
    this.loadOrderList()
  },

  // 加载订单列表
  async loadOrderList() {
    this.setData({ loading: true })

    try {
      const { currentFilter } = this.data
      let url = '/coach/orders'
      if (currentFilter !== 'all') {
        url += `?status=${currentFilter}`
      }

      const res = await app.request({ url })

      const statusMap = {
        pending: '待支付',
        paid: '已支付',
        completed: '已完成',
        cancelled: '已取消'
      }

      const list = (res.data || []).map(item => ({
        ...item,
        statusText: statusMap[item.status] || '未知',
        created_at: util.formatDate(item.created_at, 'YYYY-MM-DD HH:mm')
      }))

      this.setData({
        orderList: list,
        loading: false
      })
    } catch (err) {
      console.error('加载订单列表失败:', err)
      this.setData({ loading: false })
    }
  },

  // 查看详情
  viewDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
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
              url: `/coach/orders/${id}/cancel`,
              method: 'POST'
            })
            wx.showToast({
              title: '已取消',
              icon: 'success'
            })
            this.loadOrderList()
          } catch (err) {
            console.error('取消订单失败:', err)
          }
        }
      }
    })
  },

  // 支付订单
  payOrder(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  }
})

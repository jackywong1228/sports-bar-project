const app = getApp()

Page({
  data: {
    id: null,
    order: null,
    loading: true,
    statusConfig: {
      unpaid:      { text: '待支付',  subtitle: '请尽快完成支付', icon: '💳' },
      pending:     { text: '待确认',  subtitle: '到店出示二维码核销', icon: '⏳' },
      confirmed:   { text: '已确认',  subtitle: '到店出示二维码核销', icon: '✅' },
      in_progress: { text: '进行中',  subtitle: '运动愉快', icon: '🏃' },
      completed:   { text: '已完成',  subtitle: '期待您的下次光临', icon: '🎉' },
      cancelled:   { text: '已取消',  subtitle: '', icon: '❌' },
      paid:        { text: '已支付',  subtitle: '请等待制作', icon: '✅' },
      preparing:   { text: '制作中',  subtitle: '请稍候', icon: '👨‍🍳' }
    }
  },

  onLoad(options) {
    this.setData({ id: options.id })
    this.loadDetail()
  },

  onShow() {
    if (this.data.id && !this.data.loading) {
      this.loadDetail()
    }
  },

  async loadDetail() {
    this.setData({ loading: true })
    try {
      const res = await app.request({ url: `/member/orders/${this.data.id}` })
      if (res.data) {
        this.setData({ order: res.data, loading: false })
      } else {
        this.setData({ loading: false })
        wx.showToast({ title: '订单不存在', icon: 'none' })
      }
    } catch (err) {
      console.error('加载订单详情失败:', err)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 预览二维码大图
  previewQrcode() {
    if (this.data.order && this.data.order.qrcode_base64) {
      wx.previewImage({
        urls: [this.data.order.qrcode_base64],
        current: this.data.order.qrcode_base64
      })
    }
  },

  // 取消订单
  cancelOrder() {
    wx.showModal({
      title: '确认取消',
      content: '确定要取消此订单吗？',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '取消中...' })
          try {
            await app.request({
              url: `/member/reservations/${this.data.id}/cancel`,
              method: 'POST'
            })
            wx.hideLoading()
            wx.showToast({ title: '已取消', icon: 'success' })
            this.loadDetail()
          } catch (err) {
            wx.hideLoading()
            wx.showToast({ title: '取消失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 去支付
  payOrder() {
    wx.showLoading({ title: '支付中...' })
    app.request({
      url: `/member/reservations/${this.data.id}/pay`,
      method: 'POST'
    }).then(() => {
      wx.hideLoading()
      wx.showToast({ title: '支付成功', icon: 'success' })
      this.loadDetail()
    }).catch(() => {
      wx.hideLoading()
      wx.showToast({ title: '支付失败', icon: 'none' })
    })
  }
})

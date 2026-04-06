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

  // 取消预约（原因选择 + 二次确认）
  cancelOrder() {
    const reasons = ['临时有事', '时间冲突', '场地不合适', '误操作', '其他原因']
    wx.showActionSheet({
      itemList: reasons,
      success: (sheetRes) => {
        const reason = reasons[sheetRes.tapIndex]
        const tipLine = this._buildRefundTipText()
        wx.showModal({
          title: '确认取消预约',
          content: `原因：${reason}${tipLine ? '\n' + tipLine : ''}`,
          confirmText: '确认取消',
          cancelText: '再想想',
          success: (modalRes) => {
            if (modalRes.confirm) {
              this._doCancel(reason)
            }
          }
        })
      }
    })
  },

  // 根据当前订单信息生成退款提示文案
  _buildRefundTipText() {
    const o = this.data.order || {}
    if (o.status === 'unpaid') return '当前订单未支付，取消不涉及退款'
    if (!o.total_price || Number(o.total_price) <= 0) return '免费预约，取消后释放免费时长'
    if (o.pay_type === 'coin') return `将退还 ${o.total_price} 金币到余额`
    if (o.pay_type === 'wechat') return `将发起微信退款 ¥${o.total_price}，1-3 工作日到账`
    return ''
  },

  async _doCancel(reason) {
    wx.showLoading({ title: '取消中...', mask: true })
    try {
      const res = await app.request({
        url: `/member/reservations/${this.data.id}/cancel`,
        method: 'POST',
        data: { reason }
      })
      wx.hideLoading()
      const tip = (res && res.data && res.data.refund && res.data.refund.desc) || '已取消'
      wx.showToast({ title: tip, icon: 'success', duration: 2500 })
      this.loadDetail()
    } catch (err) {
      wx.hideLoading()
      const msg = (err && err.data && err.data.detail) || (err && err.errMsg) || '取消失败'
      wx.showToast({ title: msg, icon: 'none', duration: 2500 })
    }
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

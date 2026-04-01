const app = getApp()

Page({
  data: {
    coupons: [],
    loading: true,
    activeTab: 'unused' // unused / used / expired
  },

  onLoad() {
    this.loadCoupons()
  },

  onShow() {
    this.loadCoupons()
  },

  // 切换 tab
  onTabChange(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
    this.loadCoupons()
  },

  async loadCoupons() {
    this.setData({ loading: true })
    try {
      const res = await app.request({ url: '/member/coupons' })
      const now = new Date().getTime()
      const list = (res.data || []).map(item => {
        // 计算是否过期
        const endTime = item.end_time ? new Date(item.end_time.replace(/-/g, '/')).getTime() : 0
        const isExpired = item.status === 'expired' || (endTime > 0 && endTime < now)
        const isUsed = item.status === 'used'

        // 计算显示状态
        let displayStatus = 'unused'
        if (isUsed) displayStatus = 'used'
        else if (isExpired) displayStatus = 'expired'

        // 格式化到期时间
        let expireText = ''
        if (item.end_time) {
          const endDate = item.end_time.substring(0, 10)
          const today = new Date().toISOString().substring(0, 10)
          if (endDate === today) {
            expireText = '今日 ' + item.end_time.substring(11, 16) + ' 到期'
          } else {
            expireText = endDate + ' 到期'
          }
        }

        // 左侧显示内容（根据类型）
        let leftLabel = ''
        let leftValue = ''
        if (item.type === 'gift') {
          leftLabel = '赠品'
          leftValue = '免费'
        } else if (item.type === 'hour_free') {
          leftLabel = '时长券'
          leftValue = (item.discount_value || 1) + 'h'
        } else if (item.type === 'cash') {
          leftLabel = '代金券'
          leftValue = '¥' + (item.discount_value || 0)
        } else if (item.type === 'discount') {
          leftLabel = '折扣券'
          leftValue = (item.discount_value || 0) + '折'
        } else {
          leftLabel = ''
          leftValue = '¥' + (item.discount_value || 0)
        }

        return {
          ...item,
          displayStatus,
          isExpired,
          isUsed,
          expireText,
          leftLabel,
          leftValue,
          conditionText: item.min_amount > 0 ? '满' + item.min_amount + '可用' : '无门槛'
        }
      })

      // 按 tab 过滤
      const tab = this.data.activeTab
      const filtered = list.filter(item => item.displayStatus === tab)

      this.setData({ coupons: filtered, loading: false })
    } catch (err) {
      console.error('加载优惠券失败:', err)
      this.setData({ loading: false })
    }
  },

  // 点击优惠券
  onCouponTap(e) {
    const coupon = e.currentTarget.dataset.coupon
    if (coupon.displayStatus !== 'unused') return

    // 跳转到预约场馆
    wx.switchTab({ url: '/pages/venue/venue' })
  }
})

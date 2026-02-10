const app = getApp()
const api = require('../../utils/api')

const LEVEL_BENEFITS = {
  TRIAL: { advanceDays: 1, dailyLimit: '1次', concurrent: 1, discount: '无' },
  S:     { advanceDays: 3, dailyLimit: '1次', concurrent: 1, discount: '9.8折' },
  SS:    { advanceDays: 7, dailyLimit: '2次', concurrent: 1, discount: '9.5折' },
  SSS:   { advanceDays: 14, dailyLimit: '不限', concurrent: 1, discount: '9折' },
}

Page({
  data: {
    memberInfo: {},
    cards: [],
    benefits: LEVEL_BENEFITS.TRIAL,
    buying: false
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    // 每次显示时刷新数据（支付完成后返回）
    this.loadData()
  },

  async loadData() {
    try {
      const [memberRes, cardsRes] = await Promise.all([
        app.request({ url: '/member/profile' }),
        app.request({ url: '/member/cards' })
      ])
      const levelCode = memberRes.data?.level_code || 'TRIAL'
      this.setData({
        memberInfo: memberRes.data || {},
        cards: cardsRes.data || [],
        benefits: LEVEL_BENEFITS[levelCode] || LEVEL_BENEFITS.TRIAL
      })
    } catch (err) {
      console.error('加载数据失败:', err)
    }
  },

  // 购买会员卡
  async buyCard(e) {
    const cardId = e.currentTarget.dataset.id
    const card = this.data.cards.find(c => c.id === cardId)

    if (!card) {
      wx.showToast({ title: '套餐不存在', icon: 'none' })
      return
    }

    // 检查登录状态
    if (!app.globalData.token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      setTimeout(() => {
        wx.navigateTo({ url: '/pages/login/login' })
      }, 1500)
      return
    }

    // 确认购买
    wx.showModal({
      title: '确认购买',
      content: `确定购买「${card.name}」？\n价格：¥${card.price}\n有效期：${card.duration_days}天`,
      success: async (res) => {
        if (res.confirm) {
          this.doPurchase(cardId)
        }
      }
    })
  },

  // 执行购买
  async doPurchase(cardId) {
    if (this.data.buying) return
    this.setData({ buying: true })

    wx.showLoading({ title: '正在创建订单...' })

    try {
      // 调用购买接口
      const result = await api.purchaseMemberCard(cardId)

      if (result.code !== 0 && result.code !== 200) {
        throw new Error(result.message || '创建订单失败')
      }

      const { order_no, pay_params } = result.data

      wx.hideLoading()

      // 调用微信支付
      wx.requestPayment({
        ...pay_params,
        success: async () => {
          wx.showLoading({ title: '正在处理...' })

          // 查询订单状态确认支付成功
          try {
            const orderResult = await api.queryMemberCardOrder(order_no)
            wx.hideLoading()

            if (orderResult.data && orderResult.data.status === 'paid') {
              wx.showToast({ title: '购买成功', icon: 'success' })
              // 刷新页面数据
              this.loadData()
            } else {
              wx.showToast({ title: '支付处理中，请稍后查看', icon: 'none' })
            }
          } catch (err) {
            wx.hideLoading()
            wx.showToast({ title: '支付成功，请稍后查看', icon: 'success' })
            this.loadData()
          }
        },
        fail: (err) => {
          console.log('支付取消或失败:', err)
          if (err.errMsg.includes('cancel')) {
            wx.showToast({ title: '已取消支付', icon: 'none' })
          } else {
            wx.showToast({ title: '支付失败', icon: 'none' })
          }
        }
      })
    } catch (err) {
      wx.hideLoading()
      console.error('购买失败:', err)
      wx.showToast({ title: err.message || '购买失败', icon: 'none' })
    } finally {
      this.setData({ buying: false })
    }
  }
})

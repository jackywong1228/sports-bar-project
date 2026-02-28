const app = getApp()
const api = require('../../utils/api')

// 单一会员制权益介绍
const MEMBER_BENEFITS = {
  GUEST: {
    title: '普通用户',
    description: '注册即可浏览场馆信息',
    features: [
      { icon: 'view', text: '浏览场馆信息' },
      { icon: 'activity', text: '参与公开活动' }
    ]
  },
  MEMBER: {
    title: '尊享会员',
    description: '解锁全部场馆预约与专属权益',
    features: [
      { icon: 'booking', text: '自主预约场馆' },
      { icon: 'discount', text: '餐饮专属折扣' },
      { icon: 'priority', text: '活动优先报名' },
      { icon: 'coach', text: '教练课程预约' },
      { icon: 'points', text: '积分加倍累积' },
      { icon: 'golf', text: '高尔夫场馆使用' }
    ]
  }
}

// 旧等级映射到新等级（兼容）
const LEGACY_LEVEL_MAP = {
  TRIAL: 'GUEST',
  S: 'MEMBER',
  SS: 'MEMBER',
  SSS: 'MEMBER'
}

Page({
  data: {
    memberInfo: {},
    cards: [],
    isMember: false,
    currentLevel: 'GUEST',
    benefits: MEMBER_BENEFITS.GUEST,
    memberExpireTime: null,
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
      const rawLevel = memberRes.data?.level_code || memberRes.data?.member_level || 'GUEST'
      const currentLevel = LEGACY_LEVEL_MAP[rawLevel] || rawLevel
      const isMember = (currentLevel === 'MEMBER')
      this.setData({
        memberInfo: memberRes.data || {},
        cards: cardsRes.data || [],
        isMember: isMember,
        currentLevel: currentLevel,
        benefits: MEMBER_BENEFITS[currentLevel] || MEMBER_BENEFITS.GUEST,
        memberExpireTime: memberRes.data?.member_expire_time || null
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

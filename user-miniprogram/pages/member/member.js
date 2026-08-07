const app = getApp()
const api = require('../../utils/api')

// 三级会员制权益介绍
const MEMBER_BENEFITS = {
  S: {
    title: 'S级会员',
    description: '注册即可浏览场馆信息',
    features: [
      { icon: 'view', text: '浏览场馆信息' },
      { icon: 'activity', text: '参与公开活动' }
    ]
  },
  SS: {
    title: 'SS级会员',
    description: '当天预约场馆 + 月度券 + 邀请朋友',
    features: [
      { icon: 'booking', text: '当天预约场馆' },
      { icon: 'coupon', text: '每月场地券+饮品券' },
      { icon: 'invite', text: '每月1次邀请朋友' },
      { icon: 'coach', text: '教练课程预约' },
      { icon: 'golf', text: '高尔夫场馆使用' },
      { icon: 'gift', text: '入会礼（实物+数字券包）' }
    ]
  },
  SSS: {
    title: 'SSS级会员',
    description: '提前3天预约 + 每日2小时免费 + 顶级权益',
    features: [
      { icon: 'booking', text: '提前3天预约场馆' },
      { icon: 'free', text: '每日2小时免费场地' },
      { icon: 'drink', text: '每日饮品券' },
      { icon: 'invite', text: '每月10次邀请朋友' },
      { icon: 'locker', text: '专属储物柜' },
      { icon: 'parking', text: '免费停车位' },
      { icon: 'car', text: '专车接送服务' },
      { icon: 'bath', text: '豪华卫浴' },
      { icon: 'vip', text: '包场权限' },
      { icon: 'gift', text: '入会礼（实物+数字券包）' }
    ]
  }
}

// 旧等级映射到新等级（兼容）
const LEGACY_LEVEL_MAP = {
  GUEST: 'S',
  TRIAL: 'S',
  MEMBER: 'SS'
}

Page({
  data: {
    memberInfo: {},
    cards: [],
    isMember: false,
    currentLevel: 'S',
    benefits: MEMBER_BENEFITS.S,
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
      const rawLevel = memberRes.data?.level_code || memberRes.data?.member_level || 'S'
      const currentLevel = LEGACY_LEVEL_MAP[rawLevel] || rawLevel
      const isMember = (currentLevel === 'SS' || currentLevel === 'SSS')
      this.setData({
        memberInfo: memberRes.data || {},
        cards: cardsRes.data || [],
        isMember: isMember,
        currentLevel: currentLevel,
        benefits: MEMBER_BENEFITS[currentLevel] || MEMBER_BENEFITS.S,
        memberExpireTime: memberRes.data?.member_expire_time || null
      })
    } catch (err) {
      console.error('加载数据失败:', err)
    }
  },

  // 会员套餐点击：引导到店开通
  buyCard(e) {
    const cardId = e.currentTarget.dataset.id
    const card = this.data.cards.find(c => c.id === cardId)

    if (!card) {
      wx.showToast({ title: '套餐不存在', icon: 'none' })
      return
    }

    wx.showModal({
      title: '到店开通',
      content: `「${card.name}」\n价格：¥${card.price}\n有效期：${card.duration_days}天\n\n会员开通与续费请前往门店前台办理`,
      confirmText: '我知道了',
      showCancel: false
    })
  }
})

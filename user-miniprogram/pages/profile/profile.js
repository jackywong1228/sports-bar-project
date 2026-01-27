const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    memberInfo: null,
    isLoggedIn: false,
    isCoach: false,
    // 会员等级相关
    memberLevel: 'TRIAL',
    memberTheme: null,
    checkinStats: {
      month_count: 0,
      month_duration: 0,
      month_points: 0
    },
    menus: [
      { icon: '/assets/icons/order.png', text: '我的订单', url: '/pages/orders/orders' },
      { icon: '/assets/icons/reservation.png', text: '我的预约', url: '/pages/orders/orders?type=reservation' },
      { icon: '/assets/icons/coupon.png', text: '我的优惠券', url: '/pages/coupons/coupons' },
      { icon: '/assets/icons/member-card.png', text: '会员中心', url: '/pages/member/member' }
    ],
    tools: [
      { icon: '/assets/icons/service.png', text: '联系客服', action: 'contact' },
      { icon: '/assets/icons/feedback.png', text: '意见反馈', action: 'feedback' },
      { icon: '/assets/icons/settings.png', text: '设置', url: '/pages/settings/settings' },
      { icon: '/assets/icons/about.png', text: '关于我们', action: 'about' }
    ]
  },

  onLoad() {
    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
  },

  // 检查登录状态
  checkLoginStatus() {
    const isLoggedIn = !!app.globalData.token
    this.setData({
      isLoggedIn,
      memberInfo: app.globalData.memberInfo,
      memberLevel: app.globalData.memberLevel || 'TRIAL',
      memberTheme: app.globalData.memberTheme
    })

    if (isLoggedIn && !app.globalData.memberInfo) {
      app.getMemberInfo()
      setTimeout(() => {
        this.setData({
          memberInfo: app.globalData.memberInfo,
          memberLevel: app.globalData.memberLevel || 'TRIAL',
          memberTheme: app.globalData.memberTheme
        })
      }, 500)
    }

    // 检查是否是教练
    if (isLoggedIn) {
      this.checkCoachStatus()
      this.loadCheckinStats()
    }
  },

  // 加载打卡统计
  async loadCheckinStats() {
    try {
      const res = await api.getCheckinStats()
      if (res.code === 200) {
        this.setData({
          checkinStats: res.data
        })
      }
    } catch (err) {
      console.error('加载打卡统计失败:', err)
    }
  },

  // 检查教练身份
  async checkCoachStatus() {
    try {
      const coachToken = wx.getStorageSync('coach_token')
      if (coachToken) {
        this.setData({ isCoach: true })
        return
      }
      // 可以调用后端接口检查用户是否有教练身份
      // 这里简化处理，默认显示"申请成为教练"
    } catch (err) {
      console.error('检查教练状态失败:', err)
    }
  },

  // 跳转教练中心
  goToCoachCenter() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }

    const coachToken = wx.getStorageSync('coach_token')
    if (coachToken) {
      // 已是教练，直接进入教练首页
      wx.navigateTo({
        url: '/pages/coach-home/coach-home'
      })
    } else {
      // 未登录教练，跳转教练登录页
      wx.navigateTo({
        url: '/pages/coach-login/coach-login'
      })
    }
  },

  // 登录
  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  // 菜单点击
  onMenuTap(e) {
    const { url } = e.currentTarget.dataset
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({ url })
  },

  // 工具点击
  onToolTap(e) {
    const { action, url } = e.currentTarget.dataset

    if (url) {
      wx.navigateTo({ url })
      return
    }

    switch (action) {
      case 'contact':
        wx.makePhoneCall({
          phoneNumber: '400-000-0000'
        })
        break
      case 'feedback':
        wx.showToast({ title: '功能开发中', icon: 'none' })
        break
      case 'about':
        wx.showModal({
          title: '关于我们',
          content: '运动社交 v1.0.0\n专业的体育场馆服务平台',
          showCancel: false
        })
        break
    }
  },

  // 跳转钱包
  goToWallet() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/wallet/wallet'
    })
  },

  // 充值
  goToRecharge() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/recharge/recharge'
    })
  },

  // 跳转训练日历
  goToCalendar() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/checkin-calendar/checkin-calendar'
    })
  },

  // 跳转排行榜
  goToLeaderboard() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/leaderboard/leaderboard'
    })
  },

  // 会员卡片点击
  onMemberCardTap(e) {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/member/member'
    })
  }
})

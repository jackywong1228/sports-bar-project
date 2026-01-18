const app = getApp()

Page({
  data: {
    memberInfo: null,
    isLoggedIn: false,
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
      memberInfo: app.globalData.memberInfo
    })

    if (isLoggedIn && !app.globalData.memberInfo) {
      app.getMemberInfo()
      setTimeout(() => {
        this.setData({ memberInfo: app.globalData.memberInfo })
      }, 500)
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
  }
})
